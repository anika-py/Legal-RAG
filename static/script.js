let currentMode = "large"; // Default

function formatAnswer(text) {
  return text
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>') // bold
    .replace(/:\s*/g, ':<br>') // line breaks after colons
    .replace(/\n/g, '<br>');
}

// Helper to show chat UI
function showChatUI() {
  document.getElementById("header").style.display = "none";
  document.getElementById("navbar").classList.remove("hidden");
}

// Helper to create a chat entry
function createChatEntry(question, answerHTML) {
  const entryWrapper = document.createElement("div");
  entryWrapper.className = "chat-entry";

  const questionDiv = document.createElement("div");
  questionDiv.className = "question-box";
  questionDiv.innerHTML = `
    <div class="bubble">${question}</div>
    <img src="/static/user_icon.png" alt="User" class="avatar">
  `;

  const answerDiv = document.createElement("div");
  answerDiv.className = "answer-box";
  answerDiv.innerHTML = answerHTML;

  entryWrapper.appendChild(questionDiv);
  entryWrapper.appendChild(answerDiv);

  return entryWrapper;
}

// Load chat history from server
function loadHistory() {
  fetch("/history")
    .then(res => res.json())
    .then(history => {
      const chatBox = document.getElementById("chatBox");
      chatBox.innerHTML = "";

      if (history.length > 0) {
        history.forEach(entry => {
          // entry.question -> user bubble
          // entry.answer -> bot bubble
          const answerHTML = `
            <img src="/static/bot_icon.png" alt="Bot" class="avatar">
            <div class="bubble">${formatAnswer(entry.answer)}</div>
          `;
          chatBox.appendChild(createChatEntry(entry.question, answerHTML));
        });
        showChatUI();
      } else {
        resetMode();
      }

      updateModeUI();
    })
    .catch(err => console.error("Error loading history:", err));
}

// Submit user query
function submitQuery() {
  const questionInput = document.getElementById("question");
  const question = questionInput.value.trim();
  if (!question) return;

  showChatUI();

  // Create initial chat entry with "Thinking..." in bot bubble
  const answerHTML = `
    <img src="/static/bot_icon.png" alt="Bot" class="avatar">
    <div class="bubble"><em>Thinking...</em></div>
  `;
  const entryWrapper = createChatEntry(question, answerHTML);
  document.getElementById("chatBox").appendChild(entryWrapper);

  questionInput.value = "";

  const endpoint = currentMode === "small" ? "/ask-small" : "/ask";

  fetch(endpoint, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query: question }),
  })
    .then(res => res.json())
    .then(data => {
      // Update only the bot bubble
      const bubble = entryWrapper.querySelector(".answer-box .bubble");
      bubble.innerHTML = formatAnswer(data.response);
    })
    .catch(() => {
      const bubble = entryWrapper.querySelector(".answer-box .bubble");
      bubble.innerHTML = `❌ Error fetching answer.`;
    });
}

// Clear history and reset app
function clearHistoryAndReset() {
  fetch("/clear_history", { method: "POST" })
    .then(() => {
      resetMode();
      resetApp();
      updateModeUI();
    })
    .catch(err => console.error("Error clearing history:", err));
}

// Reset mode to default large
function resetMode() {
  currentMode = "large";
  localStorage.setItem("avocadoMode", currentMode);
}

// Reset app UI
function resetApp() {
  document.getElementById("header").style.display = "block";
  document.getElementById("navbar").classList.add("hidden");
  document.getElementById("chatBox").innerHTML = "";
  document.getElementById("question").value = "";
}

// Switch mode
function switchMode() {
  currentMode = currentMode === "small" ? "large" : "small";
  localStorage.setItem("avocadoMode", currentMode);
  updateModeUI();
  clearHistoryAndReset();
}

// Update navbar labels
function updateModeUI() {
  const title = document.querySelector(".navbar-title");
  const subtitle = document.getElementById("mode-label");
  const toggleButton = document.getElementById("mode-toggle");

  title.textContent = currentMode === "small" ? "Avocado-Small" : "Avocado-Large";
  subtitle.textContent = currentMode === "small"
    ? "🌰 Small mode (less data)"
    : "📚 Large mode (more data)";
  toggleButton.textContent = currentMode === "small"
    ? "🔄 Switch to Avocado-Large"
    : "🔄 Switch to Avocado-Small";
  toggleButton.dataset.mode = currentMode;
}

// --- Event Listeners ---
document.addEventListener("DOMContentLoaded", () => {
  const savedMode = localStorage.getItem("avocadoMode");
  if (savedMode) currentMode = savedMode;

  loadHistory();

  // Enter key submission
  const questionInput = document.getElementById("question");
  questionInput.addEventListener("keydown", e => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      submitQuery();
    }
  });

  // Navbar click clears history
  document.querySelectorAll(".navbar-logo, .navbar-title")
    .forEach(el => el.addEventListener("click", clearHistoryAndReset));

  // Mode toggle button
  document.getElementById("mode-toggle").addEventListener("click", switchMode);
});
