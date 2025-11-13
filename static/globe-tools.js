// globe-tools.js — sticky itinerary + AI place lookup chat
import { renderJSONItinerary, renderTextItinerary } from './itinerary-display.js';
console.log("🟢 globe-tools.js loaded");

// Inject CSS at runtime to ensure fresh styles are applied even if the
// browser cached the static file. This is a fallback to force the new
// chat styling to appear immediately.
function injectChatStyles() {
  if (document.getElementById('chat-ui-inline')) return;
  const css = `
    #map-chat-box{position:fixed;right:1rem;bottom:1rem;width:380px;max-width:calc(100% - 2rem);background:white;border-radius:12px;box-shadow:0 8px 24px rgba(10,20,30,0.12);display:flex;flex-direction:column;overflow:hidden;z-index:2000;border:1px solid rgba(10,20,30,0.04)}
    #map-chat-box.hidden{display:none}
    #map-chat-box .chat-box-header{display:flex;align-items:center;justify-content:space-between;padding:.5rem .75rem;background:linear-gradient(90deg,#0b5cff,#0a4fdc);color:white;font-weight:700;font-size:0.95rem}
    #map-chat-box .chat-messages{padding:.6rem;display:flex;flex-direction:column;gap:.5rem;max-height:260px;overflow:auto}
    #map-chat-box .chat-bubble{max-width:86%;padding:.5rem .7rem;border-radius:12px;line-height:1.28}
    #map-chat-box .chat-bubble.user{align-self:flex-end;background:#e9f2ff;color:#06203a;border:1px solid rgba(6,32,58,0.06)}
    #map-chat-box .chat-bubble.ai{align-self:flex-start;background:#f3f6fb;color:#06203a;border:1px solid rgba(11,43,74,0.06)}
    #map-chat-box .chat-input-row{display:flex;gap:.5rem;padding:.5rem;border-top:1px solid rgba(0,0,0,0.04)}
  #map-chat-box #map-chat-input{flex:1;resize:none;padding:.6rem .8rem;border-radius:10px;border:1px solid #e6eefb;font-size:1rem;min-height:56px}
    #map-chat-box .chat-send{background:#0b5cff;color:white;border:none;padding:.45rem .75rem;border-radius:9px;cursor:pointer}
  `;
  const s = document.createElement('style');
  s.id = 'chat-ui-inline';
  s.textContent = css;
  document.head.appendChild(s);
}
injectChatStyles();

function renderStickyItinerary() {
  const savedJSON = localStorage.getItem("itineraryJSON");
  const savedText = localStorage.getItem("itineraryText");
  const container = document.getElementById("sticky-itinerary");

  if (!container) return;

  container.innerHTML = "";

  if (savedJSON) {
    try {
      const itinerary = JSON.parse(savedJSON);
      // Use the shared renderer to keep the UI consistent with /itinerary
      renderJSONItinerary(itinerary, container);
      console.log(`✅ Sticky Itinerary Loaded (${Array.isArray(itinerary) ? itinerary.length : (itinerary.days||[]).length} days)`);
      return;
    } catch (err) {
      console.warn("⚠️ Invalid itineraryJSON:", err);
    }
  }

  if (savedText) {
    // Try parse as JSON first (some savedText may actually be JSON strings)
    try {
      const maybeArray = JSON.parse(savedText);
      renderJSONItinerary(maybeArray, container);
      return;
    } catch {
      // Not JSON — render as plain text
    }

    renderTextItinerary(savedText, container);
    console.log("✅ Sticky Itinerary Loaded (Text)");
  }
}

document.getElementById("ai-map-chat")?.addEventListener("click", () => {
  const box = document.getElementById("map-chat-box");
  if (!box) return;
  box.classList.toggle("hidden");
  box.setAttribute('aria-hidden', box.classList.contains('hidden') ? 'true' : 'false');
  // Focus input when opening
  if (!box.classList.contains('hidden')) {
    setTimeout(() => document.getElementById('map-chat-input')?.focus(), 120);
  }
});

function appendMessage(text, role = 'ai') {
  const container = document.getElementById('map-chat-messages');
  if (!container) return;
  const bubble = document.createElement('div');
  bubble.className = `chat-bubble ${role}`;
  // Render text safely using textContent to avoid injecting HTML
  const content = document.createElement('div');
  content.className = 'bubble-content';
  content.textContent = String(text);
  bubble.appendChild(content);
  container.appendChild(bubble);
  // scroll into view
  container.scrollTop = container.scrollHeight;
  return bubble;
}

function setTypingIndicator(show = true) {
  const container = document.getElementById('map-chat-messages');
  if (!container) return;
  if (show) {
    if (!container.querySelector('.chat-typing')) {
      const el = document.createElement('div');
      el.className = 'chat-bubble ai chat-typing';
      el.innerHTML = `<span class="chat-typing"><span class="dot"></span><span class="dot"></span><span class="dot"></span></span>`;
      container.appendChild(el);
      container.scrollTop = container.scrollHeight;
    }
  } else {
    const el = container.querySelector('.chat-typing');
    if (el) el.remove();
  }
}

async function sendMapChat() {
  const inputEl = document.getElementById('map-chat-input');
  const input = inputEl?.value.trim();
  if (!input) return;

  // Append user message
  appendMessage(input, 'user');
  inputEl.value = '';

  // Show typing indicator
  setTypingIndicator(true);

  const prompt = `You are an assistant that helps users find addresses or info about trip places. Answer concisely: "${input}"`;

  try {
    const res = await fetch('/api/ask', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ prompt })
    });

    setTypingIndicator(false);

    if (!res.ok) {
      console.error('AI Map Chat error:', res.status, res.statusText);
      appendMessage(`AI error: ${res.status}`, 'ai');
      return;
    }

    const data = await res.json().catch(() => ({}));

    if (data.error) {
      appendMessage(data.error, 'ai');
      return;
    }

    const reply = data.reply || '(no response)';
    appendMessage(reply, 'ai');
  } catch (err) {
    setTypingIndicator(false);
    console.error('AI Map Chat fetch error:', err);
    appendMessage('Error contacting AI.', 'ai');
  }
}

document.getElementById('map-chat-send')?.addEventListener('click', sendMapChat);

// Enable Enter to send in AI chat (Shift+Enter = new line)
document.getElementById("map-chat-input")?.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    document.getElementById("map-chat-send").click();
  }
});

// Close button
document.getElementById('map-chat-close')?.addEventListener('click', () => {
  const box = document.getElementById('map-chat-box');
  if (!box) return;
  box.classList.add('hidden');
  box.setAttribute('aria-hidden', 'true');
});

renderStickyItinerary();
