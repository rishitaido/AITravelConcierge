// itinerary-display.js
// ===================================================
// JSON-based trip display — clean and smart
// Auto-detects JSON vs Text from localStorage
// ===================================================

/** Escape HTML entities to prevent XSS from LLM-generated itinerary fields */
function esc(str) {
  if (typeof str !== 'string') return String(str ?? '');
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

export function renderJSONItinerary(itineraryInput, target = "#viewer-output") {
  const container =
    typeof target === "string" ? document.querySelector(target) : target;

  if (!container || !itineraryInput) return;

  // Support both: array or { days: [...] }
  let days = [];
  if (Array.isArray(itineraryInput)) {
    days = itineraryInput;
  } else if (Array.isArray(itineraryInput.days)) {
    days = itineraryInput.days;
  }

  if (days.length === 0) return;

  container.innerHTML = ""; // Clear previous

  days.forEach(day => {
    const html = `
      <p><strong>Morning:</strong> ${esc(day.morning)}</p>
      <p><strong>Afternoon:</strong> ${esc(day.afternoon)}</p>
      <p><strong>Evening:</strong> ${esc(day.evening)}</p>
      ${day.estimated_cost ? `<p><strong>Estimated Cost:</strong> ${esc(day.estimated_cost)}</p>` : ""}
    `;

    const block = document.createElement("details");
    block.innerHTML = `
      <summary>Day ${esc(day.day)}</summary>
      <div style="margin-top: .5rem;">${html}</div>
    `;

    container.appendChild(block);
  });

  console.log(`✅ Rendered ${days.length} day(s) itinerary`);
}

export function renderTextItinerary(itineraryText, target = "#viewer-output") {
  const container =
    typeof target === "string" ? document.querySelector(target) : target;

  if (!container || !itineraryText) return;

  container.innerHTML = ""; // Clear previous

  const block = document.createElement("pre");
  block.className = "message ai";
  block.style.whiteSpace = "pre-wrap";
  block.style.padding = "1rem";
  block.textContent = itineraryText;

  container.appendChild(block);

  console.log("✅ Rendered text itinerary");
}

// ===================================================
// Auto-render cached itinerary on page load
// ===================================================

window.addEventListener("DOMContentLoaded", () => {
  const savedJSON = localStorage.getItem("itineraryJSON");
  const savedText = localStorage.getItem("itineraryText");
  const timestamp = localStorage.getItem("itineraryTimestamp");

  // Expire cache after 10 min
  if (timestamp && Date.now() - parseInt(timestamp) > 10 * 60 * 1000) {
    console.warn("⚠️ Cached itinerary expired — clearing.");
    localStorage.removeItem("itineraryJSON");
    localStorage.removeItem("itineraryText");
    localStorage.removeItem("itineraryTimestamp");
  }

  if (savedJSON) {
    try {
      const itinerary = JSON.parse(savedJSON);
      renderJSONItinerary(itinerary);
      return;
    } catch (err) {
      console.warn("⚠️ Invalid itineraryJSON:", err);
    }
  }

  if (savedText) {
    try {
      const maybeArray = JSON.parse(savedText);
      renderJSONItinerary(maybeArray);
      return;
    } catch {
      // Not JSON — treat as plain text
    }

    renderTextItinerary(savedText);
    return;
  }

  console.warn("⚠️ No cached itinerary found.");
});
