// chat.js — AI chat + itinerary hand-off
// ======================================
//  ▸ Sends prompts to /api/ask
//  ▸ Renders replies (stream or JSON)
//  ▸ Detects itinerary payloads → localStorage → /itinerary

//--------------------------------------------------------------
// Config
//--------------------------------------------------------------
const API_CHAT = "/api/ask";
const API_GREETING = null;               // set to "/api/greeting" if you add one

import { renderJSONItinerary } from "./itinerary-display.js";

//--------------------------------------------------------------
// Greeting banner
//--------------------------------------------------------------
const greetEl = document.getElementById("greeting");
if (greetEl) {
  const DEFAULT_MSG =
    "Hello there! I’m your AI travel concierge — ask me anything ✈️";

  if (API_GREETING) {
    fetch(API_GREETING)
      .then(r => (r.ok ? r.json() : null))
      .then(d => (greetEl.textContent = d?.msg ?? DEFAULT_MSG))
      .catch(() => (greetEl.textContent = DEFAULT_MSG));
  } else {
    greetEl.textContent = DEFAULT_MSG;
  }
}

//--------------------------------------------------------------
// DOM helpers
//--------------------------------------------------------------
const chatWrap = document.getElementById("chat-container");
const inputEl = document.getElementById("chat-input");
const sendBtn = document.getElementById("send-button");
const quickBtn = document.getElementById("quick-itinerary");

const addMsg = (role, text = "") => {
  const div = document.createElement("div");
  div.className = `message ${role}`;
  div.textContent = role === "ai" ? `AI: ${text}` : text;
  chatWrap.appendChild(div);
  chatWrap.scrollTop = chatWrap.scrollHeight;
  return div;
};

const saveItinerary = (replyText) => {
  localStorage.setItem("itineraryText", replyText);
  const btn = document.getElementById("open-itinerary");
  if (btn) {
    btn.hidden = false;
    btn.onclick = () => (window.location.href = "/itinerary");
  }
};

//--------------------------------------------------------------
// State
//--------------------------------------------------------------
let conversationHistory = [];
const MAX_HISTORY = 10;

//--------------------------------------------------------------
// Main send logic (plain chat or optional override)
//--------------------------------------------------------------
const sendMessage = async (promptOverride = null) => {
  const userPrompt = promptOverride ?? inputEl.value.trim();
  if (!userPrompt) return;

  // UI: push user bubble + clear input (for plain chat only)
  addMsg("user", userPrompt);
  if (!promptOverride) {
    inputEl.value = "";
    inputEl.focus();
  }

  const aiDiv = addMsg("ai", "…");
  // Remove "AI: " prefix logic from addMsg if we want pure markdown, 
  // or handle it carefully. For now, let's keep addMsg simple and override innerHTML here.
  aiDiv.innerHTML = "<em>Thinking...</em>";
  sendBtn.disabled = true;

  try {
    const res = await fetch(API_CHAT, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        prompt: userPrompt,
        history: conversationHistory
      })
    });

    const isJSON = res.headers.get("content-type")?.includes("application/json");

    let replyText = "";

    if (isJSON) {
      // ---------- JSON reply ----------
      const data = await res.json().catch(() => ({}));

      // Structured error from backend or non-2xx status
      if (!res.ok || data.error) {
        const errMsg = data.error || `[HTTP ${res.status}] ${res.statusText}`;
        console.error("AI error:", errMsg);
        aiDiv.textContent = `AI: ${errMsg}`;
        return;
      }

      try {
        const parsed = JSON.parse(data.reply);
        if (Array.isArray(parsed)) {
          renderJSONItinerary(parsed, aiDiv);
          localStorage.setItem("itineraryJSON", JSON.stringify(parsed));
          saveItinerary(data.reply);   // ✅ ONLY save if parsed array!

          // For itinerary, we might not want to add to history as it's a complex object,
          // but the user prompt was added. Let's add a summary or just the text.
          replyText = data.reply;
        }
      } catch (err) {
        console.log("AI reply is not JSON — fallback to plain text.");
      }

      if (!replyText) {
        // Fallback — plain text
        replyText = data.reply;
        aiDiv.innerHTML = marked.parse(replyText);
      }

    } else {
      // ---------- Streaming fallback ----------
      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";
      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        const chunk = decoder.decode(value, { stream: true });
        buffer += chunk;
        aiDiv.innerHTML = marked.parse(buffer);
        chatWrap.scrollTop = chatWrap.scrollHeight;
      }
      replyText = buffer;
    }

    // Update history
    conversationHistory.push({ role: "user", content: userPrompt });
    conversationHistory.push({ role: "assistant", content: replyText });

    // Prune history
    if (conversationHistory.length > MAX_HISTORY * 2) {
      conversationHistory = conversationHistory.slice(-MAX_HISTORY * 2);
    }

  } catch (err) {
    console.error(err);
    aiDiv.textContent = `AI: [ERROR] ${err.message}`;
  } finally {
    sendBtn.disabled = false;
  }
};

//--------------------------------------------------------------
// UI wiring
//--------------------------------------------------------------

// Send button click
sendBtn?.addEventListener("click", (e) => {
  e.preventDefault();
  sendMessage();
});

// Enter key
inputEl?.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
});

// Form submit fallback
const inputArea = document.getElementById("input-area");
if (inputArea?.tagName === "FORM") {
  inputArea.addEventListener("submit", (e) => {
    e.preventDefault();
    sendMessage();
  });
}

// Tokyo demo button
quickBtn?.addEventListener("click", () => {
  const demoPrompt =
    "You are a travel planner. Create a detailed 3‑day Tokyo itinerary focused on food and culture. " +
    "Label each day ('Day 1', 'Day 2', 'Day 3') and include morning, afternoon, evening activities.";
  sendMessage(demoPrompt);
});
