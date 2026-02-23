# ai_routes.py — OpenRouter AI Assistant
# ==================================================

from flask import Blueprint, request, jsonify
from dotenv import load_dotenv
import os
import requests
import functools
import logging

from cache import init_cache_db, get_cached_response, save_response_to_cache
from limiter_config import limiter

logger = logging.getLogger(__name__)


MAX_PROMPT_LEN = 1000
MAX_FIELD_LEN = 200
REQUEST_TIMEOUT = 90
ALLOWED_ROLES = {"user", "assistant"}


def _strip_control(s: str) -> str:
    """Remove non-printable control characters (except newline/tab)."""
    return ''.join(c for c in s if c in ('\n', '\t') or (c.isprintable()))


load_dotenv(override=True)

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
MODEL = "tngtech/tng-r1t-chimera:free"
# NOTE: many environments resolve the public host `openrouter.ai` but not
# the `api.` subdomain. Use the main host path as the default and allow an
# environment override via OPENROUTER_URL when needed (e.g. a proxy).
OPENROUTER_URL = os.getenv(
    "OPENROUTER_URL",
    "https://openrouter.ai/api/v1/chat/completions"
)
HEADERS = {
    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
    "Content-Type": "application/json"
}

ai_routes = Blueprint("ai_routes", __name__)
init_cache_db()

# SYSTEM prompt for itineraries (ONLY for /api/itinerary)
SYSTEM_INSTR_ITINERARY = """
You are TripMate, a friendly and helpful AI travel planner for airplanes.life.

When asked for an itinerary, return ONLY valid JSON — no text, no comments — in this format:

{
  "exchange_rate": "1 USD = X.XX LocalCurrency",
  "days": [
    {
      "day": 1,
      "morning": "Full paragraph — 2 to 3 sentences — describing morning activities. Include times, place names, what the traveler will experience or learn. Mention if this is arrival day or if the traveler is arriving by air.",
      "afternoon": "2–3 sentences describing afternoon experiences. Include any relevant breaks or pacing for comfort. Mention local spots, markets, nature, or cultural experiences.",
      "evening": "2–3 sentences describing the evening. Include good options for local food or drinks, music, shows, or relaxing experiences.",
      "estimated_cost": "[amount in local currency] (~USD equivalent)"
    },
    ...
  ]
}

You will receive:

- City / destination
- Days (trip length)
- Theme (Food & Culture, Outdoors, Museums, etc)
- Region type (Beach, Mountains, Urban, Island...)
- Budget (Backpacker, Mid-range, Luxury)
- Travel pace (Relaxed, Balanced, Packed)
- Traveler type (Solo, Couple, Family...)

IMPORTANT:

✅ If it is the **first day**, start with arrival and suggest good first activities after flight (taking into account morning or afternoon arrival).
✅ If it is the **last day**, include suggestions for morning and safe timing for afternoon flights.
✅ For each time block (morning / afternoon / evening), write full sentences — NOT just lists or short lines.
✅ Mention local food, drinks, music, markets, events.
✅ Pacing should match the "Travel pace" and "Traveler type" — families with kids = lighter, Solo or Couples = more flexible.
✅ Include realistic breaks, snacks, or "rest time" for balance.

Tone: Friendly, human, helpful — write like a **good local tour guide**.

Return ONLY valid JSON, exactly as shown. Do NOT include lists, tables, or extra explanations — just the JSON.


"""

# SYSTEM prompt for general AI chat (/api/ask)
SYSTEM_INSTR_CHAT = """
You are TripMate, a friendly AI travel assistant for airplanes.life.

Your goal is to be helpful, direct, and fun.

CRITICAL INSTRUCTION:
When a user mentions a destination (e.g., "I want to go to Paris"), you MUST provide **specific recommendations immediately**.
- Suggest 3-4 top things to do or see.
- Suggest 1-2 local foods to try.
- Do **NOT** ask a list of clarifying questions (budget, dates, who with, etc.).
- Do **NOT** say "To help me give you the best recommendations...".
- Just give the recommendations!

If the user gives NO destination, only THEN can you ask where they are going.

Style:
- Be conversational and enthusiastic.
- Use bolding for place names.
- Use bullet points for lists.
- Keep it under 200 words.
- Use Markdown formatting to make your response easy to read.

IMPORTANT:
- You are part of a continuous conversation.
- Remember previous details the user shared.
- If the user refers to "it" or "there", use the context from previous messages to understand.
"""


def call_openrouter(prompt: str | None = None, *, messages: list | None = None, max_tokens: int = 1200, system_prompt: str = SYSTEM_INSTR_CHAT) -> str:
    if messages is None:
        messages = [
            {"role": "system", "content": system_prompt.strip()},
            {"role": "user",   "content": prompt.strip()}
        ]

    payload = {
        "model": MODEL,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": 0.7
    }
    if not OPENROUTER_API_KEY:
        raise RuntimeError("OPENROUTER_API_KEY is missing.")
    r = requests.post(OPENROUTER_URL, headers=HEADERS, json=payload, timeout=REQUEST_TIMEOUT)
    try:
        r.raise_for_status()
    except requests.HTTPError as he:
        # Log full details server-side but do NOT expose to client
        text = r.text if r is not None else ""
        logger.error("OpenRouter HTTP %s: %s", r.status_code, text[:500])
        raise RuntimeError(f"AI provider returned HTTP {r.status_code}") from he
    data = r.json()
    return data["choices"][0]["message"]["content"].strip()


def ai_endpoint(default_days: int | None = None):
    def decorator(fn):
        @functools.wraps(fn)
        def wrapper():
            data = request.get_json(force=True, silent=True) or {}

            # Extract history if available
            history = data.get("history", [])
            if not isinstance(history, list):
                history = []

            prompt_data = data.get("prompt")
            if isinstance(prompt_data, dict):
                city = _strip_control(prompt_data.get("city", "").strip())[:MAX_FIELD_LEN]
                days_field = prompt_data.get("days", "")
                theme = _strip_control(prompt_data.get("theme", "").strip())[:MAX_FIELD_LEN]
                region = _strip_control(prompt_data.get("region", "").strip())[:MAX_FIELD_LEN]
                budget = _strip_control(prompt_data.get("budget", "").strip())[:MAX_FIELD_LEN]
                pace = _strip_control(prompt_data.get("pace", "").strip())[:MAX_FIELD_LEN]
                traveler = _strip_control(prompt_data.get("traveler", "").strip())[:MAX_FIELD_LEN]

                prompt = f"""Plan a {days_field}-day trip to {city}.
                Theme: {theme}.
                Region type: {region}.
                Budget level: {budget}.
                Travel pace: {pace}.
                Traveler type: {traveler}.
                """
            else:
                prompt = (prompt_data or "").strip()

            if not prompt:
                return jsonify({"error": "Prompt is required"}), 400

            # Check length of NEW prompt only
            if len(prompt) > MAX_PROMPT_LEN:
                return jsonify({"error": f'Prompt too long (max {MAX_PROMPT_LEN} chars)'}), 413

            req_days = data.get("days")
            try:
                req_days = int(req_days) if req_days else None
            except ValueError:
                req_days = None

            days = req_days or default_days
            if days:
                prompt += f"\n\nReturn exactly {days} days."

            if cached := get_cached_response(prompt):
                # cached may contain an error marker — return structured error
                if isinstance(cached, str) and cached.startswith("[ERROR]"):
                    return jsonify({"error": cached}), 502
                return jsonify({"reply": cached})

            try:
                dynamic_max = 400 + (days or 0) * 180
                dynamic_max = min(dynamic_max, 2048)

                if fn.__name__ == "api_itinerary":
                    system_prompt = SYSTEM_INSTR_ITINERARY
                    # Itinerary usually doesn't use history in this specific implementation,
                    # but if we wanted to, we could. For now, keep it simple.
                    reply = call_openrouter(prompt, max_tokens=dynamic_max, system_prompt=system_prompt)
                else:
                    system_prompt = SYSTEM_INSTR_CHAT
                    # Construct full message history
                    # 1. System prompt
                    messages = [{"role": "system", "content": system_prompt.strip()}]

                    # 2. History (limit to last 10 to be safe, though frontend should also limit)
                    # Validate history items
                    valid_history = []
                    for h in history:
                        if isinstance(h, dict) and h.get("role") in ALLOWED_ROLES and "content" in h:
                            content = str(h["content"])[:MAX_PROMPT_LEN]
                            valid_history.append({"role": h["role"], "content": content})

                    messages.extend(valid_history[-10:])

                    # 3. Current user prompt
                    messages.append({"role": "user", "content": prompt})

                    reply = call_openrouter(messages=messages, max_tokens=dynamic_max)
                if not reply:
                    raise RuntimeError("Empty response from AI")
            except requests.Timeout:
                reply = "[ERROR] AI request timed out"
            except Exception as e:
                logger.error(f"AI request failed: {e}", exc_info=True)
                reply = "[ERROR] AI service temporarily unavailable"

            # If AI produced an error marker, return a structured error response
            if isinstance(reply, str) and reply.startswith("[ERROR]"):
                # Do not cache error responses
                return jsonify({"error": reply}), 502

            save_response_to_cache(prompt, reply)
            return jsonify({"reply": reply})

        return wrapper
    return decorator

# Routes


@ai_routes.route("/api/ask", methods=["POST"])
@limiter.limit("5 per minute")
@ai_endpoint(default_days=None)
def api_ask():
    pass


@ai_routes.route("/api/itinerary", methods=["POST"])
@limiter.limit("4 per minute")
@ai_endpoint(default_days=3)
def api_itinerary():
    pass
