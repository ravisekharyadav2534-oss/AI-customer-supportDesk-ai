from openai import OpenAI

from .config import OPENAI_API_KEY, OPENAI_BASE_URL, OPENAI_MODEL

client = (
    OpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL)
    if OPENAI_API_KEY
    else None
)

GUARDRAILS = (
    "You are a customer support assistant. Be concise, friendly and accurate. "
    "If you do not know something, say so and suggest contacting a human agent."
)


def ask_ai(instructions: str, history: list[dict]) -> str:
    if client is None:
        return (
            "[Demo mode - add OPENAI_API_KEY to your .env for real AI replies] "
            f"You said: {history[-1]['content']}"
        )
    messages = [{"role": "system", "content": f"{GUARDRAILS}\n\n{instructions}"}]
    messages += history[-20:]
    try:
        resp = client.chat.completions.create(
            model=OPENAI_MODEL, messages=messages, temperature=0.4
        )
        return resp.choices[0].message.content or ""
    except Exception as exc:
        return f"AI service error: {exc}"