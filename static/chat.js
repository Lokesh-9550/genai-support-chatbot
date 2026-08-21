const chatWindow = document.getElementById("chat-window");
const chatForm = document.getElementById("chat-form");
const chatInput = document.getElementById("chat-input");

function appendMessage(role, content, sources) {
  const msg = document.createElement("div");
  msg.className = `msg ${role}`;
  msg.textContent = content;
  chatWindow.appendChild(msg);

  if (sources && sources.length) {
    const src = document.createElement("div");
    src.className = "sources";
    src.textContent = "Sources: " + sources.map(s => `${s.title} (${s.score})`).join(", ");
    chatWindow.appendChild(src);
  }
  chatWindow.scrollTop = chatWindow.scrollHeight;
}

async function loadHistory() {
  const res = await fetch("/api/history");
  const data = await res.json();
  if (data.messages && data.messages.length) {
    data.messages.forEach(m => appendMessage(m.role, m.content));
  } else {
    appendMessage("assistant", "Hi! I'm your support assistant. Ask me about passwords, refunds, billing, the API, or your account.");
  }
}

chatForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const message = chatInput.value.trim();
  if (!message) return;

  appendMessage("user", message);
  chatInput.value = "";
  chatInput.disabled = true;

  try {
    const res = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message }),
    });
    const data = await res.json();
    if (data.error) {
      appendMessage("assistant", "Sorry, something went wrong: " + data.error);
    } else {
      appendMessage("assistant", data.answer, data.sources);
    }
  } catch (err) {
    appendMessage("assistant", "Network error — please try again.");
  } finally {
    chatInput.disabled = false;
    chatInput.focus();
  }
});

loadHistory();
