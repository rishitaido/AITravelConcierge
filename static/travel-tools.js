// travel-tools.js — mini-app tools for index.html
// =======================================================
// 1. Quick Tokyo trip demo → sends to /api/ask
// 2. “View Airport Map” button → /airports
// 3. (future) Visualize flight path
// =======================================================

document.getElementById("quick-itinerary")?.addEventListener("click", async () => {
  const demoPrompt = `
    You are a travel planner.
    Create a detailed 3-day Tokyo itinerary focused on food and culture.
    Return the itinerary in JSON format:
    [
      { "day": 1, "morning": "...", "afternoon": "...", "evening": "..." },
      { "day": 2, "morning": "...", "afternoon": "...", "evening": "..." },
      { "day": 3, "morning": "...", "afternoon": "...", "evening": "..." }
    ]
    Return ONLY the JSON array. No extra text.
  `.trim();

  try {
    const res = await fetch("/api/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ prompt: demoPrompt })
    });

    const data = await res.json().catch(() => ({}));

    if (!res.ok || data.error) {
      const errMsg = data.error || `[HTTP ${res.status}] ${res.statusText}`;
      console.error("AI demo error:", errMsg);
      window.showToast ? showToast(`AI Error: ${errMsg}`, 'error') : alert(`AI Error: ${errMsg}`);
      return;
    }

    try {
      // Be resilient to code-fenced JSON (```json ... ```)
      const stripCodeFences = (s) => {
        if (typeof s !== 'string') return s;
        s = s.trim();
        s = s.replace(/^```\s*json\s*/i, '');
        s = s.replace(/^```\s*/i, '');
        s = s.replace(/```\s*$/i, '');
        return s.trim();
      };

      let reply = data.reply;
      if (typeof reply === 'string') reply = stripCodeFences(reply);

      const parsed = typeof reply === 'object' ? reply : JSON.parse(reply);
      console.log("✅ Demo itinerary:", parsed);

      // Save to localStorage for /itinerary
      localStorage.setItem("itineraryJSON", JSON.stringify(parsed));

      // Optional: show quick notification:
      window.showToast ? showToast(`Tokyo itinerary saved — ${parsed.length} days! Go to /itinerary to view.`, 'success') : alert(`Tokyo itinerary saved — ${parsed.length} days! Go to /itinerary to view.`);
    } catch (err) {
      console.error("AI reply is not JSON:", err);
      window.showToast ? showToast("Error: AI did not return a valid itinerary.", 'warning') : alert("Error: AI did not return a valid itinerary.");
    }
  } catch (err) {
    console.error(err);
    window.showToast ? showToast(`Couldn't fetch demo itinerary — ${err.message}`, 'error') : alert(`Couldn’t fetch demo itinerary — ${err.message}`);
  }
});

// ----------- “View Airport Map” button → /airports -----------------
document
  .getElementById("show-airport")
  ?.addEventListener("click", () => {
    window.location.href = "/globe";
  });

// ----------- “Visualize Flight Path” button — future -----------------
document
  .getElementById("show-flight")
  ?.addEventListener("click", () => {
    window.showToast ? showToast("Coming soon: Flight path visualization!", 'info') : alert("Coming soon: Flight path visualization!");
  });
