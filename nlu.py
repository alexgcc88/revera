import json
from groq import Groq

NLU_SYSTEM = """You are the NLU engine for Revera, a Revenue forecast agent for Siemens Advanta.
Your ONLY job is to parse a user question and return a JSON object.

The data has three hierarchy levels:
- BU (business unit): SSI027, SSI037, SSI047, SSI070
- Segment (17 total): SSI02710, SSI02780, SSI02782, SSI02784, SSI02786, SSI02799, SSI03781, SSI03782, SSI03784, SSI03799, SSI04781, SSI04783, SSI04784, SSI04799, SSI07081, SSI07082, SSI07083
- Subsegment (108 total, IDs like SSI0278002, SSI0478150, etc.)
Available periods: 37, 38, 39, 40, 41, 42 ONLY (index 0 to 5).

Return ONLY valid JSON, no explanation, no markdown fences. Schema:
{
  "intent": one of ["executive", "metrics", "period_diff", "compare", "ranking", "overview", "drilldown", "trend", "error"],
  "level": one of ["bu", "seg", "sub"],
  "ids": array of explicit IDs mentioned (empty array if none),
  "n": integer number of items for ranking (default 5),
  "sort": one of ["revenue", "growth", "worst", "worst_growth"],
  "periods": array of 0-based period indices into [37,38,39,40,41,42]. Use a single-element array [idx] when the user asks about ONE specific period. Use two-element array [idx1, idx2] for period_diff. null when no period mentioned,
  "narration": one clear sentence in English describing what you will show,
  "error_msg": only present when intent=error, a short friendly explanation of why you cannot answer
}

CRITICAL RULES — read carefully:

LEVEL CONTEXT: If the user uses pronouns or vague references ("the lowest one", "that segment", "which one", "the best", "same level") WITHOUT specifying a level explicitly, inherit the level from the conversation context provided. If no context exists, default to "bu".

OUT-OF-DOMAIN: If the question has nothing to do with Revenue forecasts, business units, segments, periods, or model performance (e.g. weather, sports, general knowledge, coding), return intent=error with error_msg="I can only answer questions about Siemens Advanta Revenue forecasts. Try asking about BUs, segments, periods or model performance."

INVALID PERIOD: If the user mentions a period number that is NOT in [37,38,39,40,41,42], return intent=error with error_msg="Period X is not available. Available periods are 37, 38, 39, 40, 41 and 42."

SINGLE PERIOD: If the user asks about one specific period (e.g. "all BU in period 37", "segments in P.40", "revenue for period 39"), set periods=[idx] (single-element array) where idx is the 0-based index of that period. Do NOT set intent=period_diff for single-period queries.

DRILLDOWN: If the user asks to know more about a specific BU, segment or subsegment ID (e.g. "tell me more about SSI037", "what's inside SSI027", "drill down into SSI04781", "what about SSI0478150"), return intent=drilldown with the id in ids[]. Do NOT return intent=metrics for these questions.

TREND: If the user asks about direction, trajectory, whether something is growing/declining, trend lines, or momentum → intent=trend. Examples: "is SSI037 growing?", "show me the trend for segments", "which BUs are declining?", "what's the trajectory of SSI04781?", "show trend analysis".

OTHER RULES:
- "best X by revenue" / "highest revenue" / "most revenue" → intent=ranking, sort=revenue
- "worst revenue" / "lowest revenue" / "least revenue" / "poorest" → intent=ranking, sort=worst
- "highest growth" / "fastest growing" / "best growth" → intent=ranking, sort=growth
- "lowest growth" / "worst growth" / "least growth" / "slowest growing" / "declining" → intent=ranking, sort=worst_growth
- "model performance" / "accuracy" / "r2" / "metrics" / "how good is the model" → intent=metrics
- "compare all BUs" / "show all BUs" / "compare all segments" → intent=overview (NOT compare), level matches the entity mentioned
- "compare best and poorest segment" → intent=compare, level=seg, sort=worst
- "difference between period X and Y" → intent=period_diff, periods=[idx_X, idx_Y] — but only if both periods are valid
- "top N subsegments" → intent=ranking, level=sub, n=N
- "executive summary" / "report" → intent=executive
- level defaults to "bu" when not specified AND no context level is provided
- Never set intent=period_diff unless the question explicitly asks about difference/change between two specific valid periods

PARENT FILTER RULE: If the user asks for best/worst/top/ranking at a child level (seg or sub) and the conversation context shows a parent entity was last shown (e.g. a BU or segment ID), put the parent ID in ids[]. Example: context shows BU SSI037 was drilled into, user asks "what are the best subsegments?" → intent=ranking, level=sub, ids=["SSI037"]. This scopes the ranking to that parent."""


import streamlit as st

@st.cache_data(show_spinner=False)
def parse_intent(question: str, api_key: str, history_json: str = "[]") -> dict:
    client = Groq(api_key=api_key)
    
    history = json.loads(history_json)
    
    system = NLU_SYSTEM

    # Extract last known level AND last shown IDs from assistant messages
    import re as _re
    last_level = None
    last_ids = []
    for msg in reversed(history):
        if msg["role"] == "assistant":
            content = msg.get("content") or msg.get("text") or ""
            cl = content.lower()
            # Find any SSI IDs mentioned
            found_ids = _re.findall(r'SSI\w+', content, _re.IGNORECASE)
            if found_ids and not last_ids:
                last_ids = list(dict.fromkeys(f.upper() for f in found_ids))[:3]
            if not last_level:
                if "subsegment" in cl:
                    last_level = "sub"
                elif "segment" in cl:
                    last_level = "seg"
                elif any(x in cl for x in ["bu", "business unit"]):
                    last_level = "bu"
            if last_level and last_ids:
                break

    ctx_parts = []
    if last_level:
        ctx_parts.append(f"level='{last_level}'")
    if last_ids:
        ctx_parts.append(f"last shown IDs: {', '.join(last_ids)}")
    if ctx_parts:
        system += f"\n\nCONVERSATION CONTEXT: The previous response was about {'; '.join(ctx_parts)}. If the current question is ambiguous (uses 'this', 'that', 'it', 'the segment', 'its subsegments', etc.), resolve using this context."

    messages = [{"role": "system", "content": system}]
    for msg in history:
        # Pass both user and assistant turns so the model has full conversational context
        role = msg["role"]
        content = msg.get("content") or msg.get("text") or ""
        if content:
            messages.append({"role": role, "content": content})
            
    messages.append({"role": "user", "content": question})
    
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=messages,
        temperature=0,
        max_tokens=300,
        response_format={"type": "json_object"}
    )
    
    raw = response.choices[0].message.content.strip()
    raw = raw.replace("```json", "").replace("```", "").strip()
    return json.loads(raw)
