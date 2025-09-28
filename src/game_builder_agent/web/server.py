"""FastAPI application powering the Game Builder Agent web UI."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, List, Optional

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from game_builder_agent.clarifier import Clarifier
from game_builder_agent.config import Settings, load_settings
from game_builder_agent.executor import PlanExecutor
from game_builder_agent.feedback import FeedbackSynthesizer
from game_builder_agent.llm_client import OllamaClient
from game_builder_agent.planner import Planner
from game_builder_agent.schemas import GamePlan

from .sessions import SessionState, SessionStore

BASE_DIR = Path(__file__).resolve().parent


def get_settings() -> Settings:
    return load_settings()


def get_session_store() -> SessionStore:
    # Simple singleton for the process lifetime. In production, consider Redis or a database.
    if not hasattr(get_session_store, "_store"):
        get_session_store._store = SessionStore()  # type: ignore[attr-defined]
    return get_session_store._store  # type: ignore[attr-defined]


class SessionCreate(BaseModel):
    prompt: str


class AnswerPayload(BaseModel):
    answers: List[str]


class RevisionPayload(BaseModel):
    notes: List[str]


class SessionResponse(BaseModel):
    session_id: str
    prompt: str
    clarifications: List[str]
    answered: List[str]
    notes: List[str]
    last_acknowledgement: Optional[str]
    plan: Optional[GamePlan]
    repo_path: Optional[str]
    status: str


class ExecuteResponse(BaseModel):
    session: SessionResponse


def _serialize(session: SessionState) -> SessionResponse:
    return SessionResponse(
        session_id=session.session_id,
        prompt=session.prompt,
        clarifications=session.clarifications,
        answered=session.answered,
        notes=session.notes,
        last_acknowledgement=session.last_acknowledgement,
        plan=session.plan,
        repo_path=session.repo_path,
        status=session.status,
    )


def _answer_questions(clarifications: List[str], answers: Iterable[str]) -> List[str]:
    pairs: List[str] = []
    for question, answer in zip(clarifications, answers):
        pairs.append(f"Q: {question}\nA: {answer.strip()}")
    return pairs


def _generate_clarifications(settings: Settings, prompt: str) -> List[str]:
    client = OllamaClient(settings)
    try:
        clarifier = Clarifier(client)
        return clarifier.ask(prompt)
    finally:
        client.close()


def _generate_plan(
    settings: Settings,
    prompt: str,
    clarifications: List[str],
    answered: List[str],
    notes: Iterable[str],
) -> GamePlan:
    client = OllamaClient(settings)
    try:
        planner = Planner(client)
        return planner.create_plan(prompt, clarifications, [*answered, *notes])
    finally:
        client.close()


def _summarize_feedback(settings: Settings, notes: Iterable[str]) -> str:
    client = OllamaClient(settings)
    try:
        synthesizer = FeedbackSynthesizer(client)
        feedback = synthesizer.summarize(list(notes))
        return feedback.acknowledgement
    finally:
        client.close()


def _execute_plan(
    settings: Settings,
    plan: GamePlan,
    reviewer_notes: Iterable[str],
) -> str:
    client = OllamaClient(settings)
    executor = PlanExecutor(settings, client)
    try:
        project_path = executor.execute(plan, reviewer_notes=reviewer_notes)
        return str(project_path)
    finally:
        client.close()


app = FastAPI(title="Game Builder Agent Web UI")
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


@app.get("/")
def home(request: Request) -> JSONResponse:
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/api/sessions", response_model=SessionResponse)
def create_session(
    payload: SessionCreate,
    settings: Settings = Depends(get_settings),
    store: SessionStore = Depends(get_session_store),
) -> SessionResponse:
    clarifications = _generate_clarifications(settings, payload.prompt)
    session = store.create(prompt=payload.prompt.strip(), clarifications=clarifications)
    return _serialize(session)


@app.get("/api/sessions/{session_id}", response_model=SessionResponse)
def read_session(session_id: str, store: SessionStore = Depends(get_session_store)) -> SessionResponse:
    try:
        session = store.get(session_id)
    except KeyError as exc:  # pragma: no cover - defensive guard
        raise HTTPException(status_code=404, detail="Session not found") from exc
    return _serialize(session)


@app.post("/api/sessions/{session_id}/answers", response_model=SessionResponse)
def submit_answers(
    session_id: str,
    payload: AnswerPayload,
    settings: Settings = Depends(get_settings),
    store: SessionStore = Depends(get_session_store),
) -> SessionResponse:
    session = store.get(session_id)
    if len(payload.answers) != len(session.clarifications):
        raise HTTPException(status_code=400, detail="Answers must match the number of clarifications")

    session.answered = _answer_questions(session.clarifications, payload.answers)
    session.plan = _generate_plan(
        settings,
        session.prompt,
        session.clarifications,
        session.answered,
        session.notes,
    )
    session.status = "awaiting_plan_review"
    store.update(session)
    return _serialize(session)


@app.post("/api/sessions/{session_id}/revise", response_model=SessionResponse)
def request_revision(
    session_id: str,
    payload: RevisionPayload,
    settings: Settings = Depends(get_settings),
    store: SessionStore = Depends(get_session_store),
) -> SessionResponse:
    session = store.get(session_id)
    if not payload.notes:
        raise HTTPException(status_code=400, detail="Provide at least one note for revision")

    session.notes.extend(note.strip() for note in payload.notes if note.strip())
    acknowledgement = _summarize_feedback(settings, session.notes[-len(payload.notes) :])
    session.last_acknowledgement = acknowledgement
    session.plan = _generate_plan(
        settings,
        session.prompt,
        session.clarifications,
        session.answered,
        session.notes,
    )
    session.status = "awaiting_plan_review"
    store.update(session)
    return _serialize(session)


@app.post("/api/sessions/{session_id}/approve", response_model=ExecuteResponse)
def approve_plan(
    session_id: str,
    settings: Settings = Depends(get_settings),
    store: SessionStore = Depends(get_session_store),
) -> ExecuteResponse:
    session = store.get(session_id)
    if session.plan is None:
        raise HTTPException(status_code=400, detail="Plan not generated yet")

    session.status = "executing"
    store.update(session)

    repo_path = _execute_plan(settings, session.plan, session.notes or ["Plan approved via web UI"])
    session.repo_path = repo_path
    session.status = "completed"
    store.update(session)
    return ExecuteResponse(session=_serialize(session))


def create_app() -> FastAPI:
    return app


def run() -> None:  # pragma: no cover - entrypoint helper
    import uvicorn

    uvicorn.run("game_builder_agent.web.server:app", host="0.0.0.0", port=8000, reload=False)
