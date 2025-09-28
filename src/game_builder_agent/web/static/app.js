const promptForm = document.getElementById("prompt-form");
const promptInput = document.getElementById("prompt-input");
const clarificationSection = document.getElementById("clarification-section");
const clarificationForm = document.getElementById("clarification-form");
const clarificationList = document.getElementById("clarification-list");
const planSection = document.getElementById("plan-section");
const planJson = document.getElementById("plan-json");
const acknowledgement = document.getElementById("acknowledgement");
const revisionForm = document.getElementById("revision-form");
const revisionInput = document.getElementById("revision-input");
const approveButton = document.getElementById("approve-button");
const resultSection = document.getElementById("result-section");
const resultMessage = document.getElementById("result-message");

let sessionId = null;

function hide(el) {
  el.classList.add("hidden");
}

function show(el) {
  el.classList.remove("hidden");
}

function renderClarifications(clarifications) {
  clarificationList.innerHTML = "";
  clarifications.forEach((question, index) => {
    const li = document.createElement("li");
    const label = document.createElement("label");
    label.className = "field";

    const span = document.createElement("span");
    span.textContent = question;

    const input = document.createElement("textarea");
    input.name = `answer-${index}`;
    input.required = true;
    input.rows = 2;

    label.appendChild(span);
    label.appendChild(input);
    li.appendChild(label);
    clarificationList.appendChild(li);
  });
}

function renderPlan(plan) {
  if (plan) {
    planJson.textContent = JSON.stringify(plan, null, 2);
  }
}

function updateAcknowledgement(text) {
  if (text) {
    acknowledgement.textContent = text;
    show(acknowledgement);
  } else {
    acknowledgement.textContent = "";
    hide(acknowledgement);
  }
}

async function postJSON(url, payload) {
  const response = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const detail = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(detail.detail || "Request failed");
  }

  return response.json();
}

promptForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  hide(clarificationSection);
  hide(planSection);
  hide(resultSection);
  updateAcknowledgement(null);

  try {
    const data = await postJSON("/api/sessions", { prompt: promptInput.value });
    sessionId = data.session_id;
    renderClarifications(data.clarifications);
    show(clarificationSection);
  } catch (error) {
    alert(error.message);
  }
});

clarificationForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  if (!sessionId) return;

  const answers = Array.from(clarificationList.querySelectorAll("textarea")).map((el) => el.value.trim());

  try {
    const data = await postJSON(`/api/sessions/${sessionId}/answers`, { answers });
    renderPlan(data.plan);
    updateAcknowledgement(data.last_acknowledgement);
    show(planSection);
  } catch (error) {
    alert(error.message);
  }
});

revisionForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  if (!sessionId) return;

  const notes = revisionInput.value
    .split(";")
    .map((note) => note.trim())
    .filter(Boolean);

  if (notes.length === 0) {
    alert("Please supply at least one adjustment note.");
    return;
  }

  try {
    revisionForm.querySelector("button").disabled = true;
    const data = await postJSON(`/api/sessions/${sessionId}/revise`, { notes });
    renderPlan(data.plan);
    updateAcknowledgement(data.last_acknowledgement);
    revisionInput.value = "";
  } catch (error) {
    alert(error.message);
  } finally {
    revisionForm.querySelector("button").disabled = false;
  }
});

approveButton.addEventListener("click", async () => {
  if (!sessionId) return;
  approveButton.disabled = true;
  approveButton.textContent = "Scaffolding...";

  try {
    const response = await postJSON(`/api/sessions/${sessionId}/approve`, {});
    const { session } = response;
    renderPlan(session.plan);
    resultMessage.textContent = `Repository generated at: ${session.repo_path}`;
    show(resultSection);
  } catch (error) {
    alert(error.message);
  } finally {
    approveButton.disabled = false;
    approveButton.textContent = "Approve plan & scaffold repo";
  }
});
