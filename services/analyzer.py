from openai import OpenAI
from config import OPENAI_API_KEYS

# Note: analyzer was previously tied to a single OPENAI_API_KEY.  We
# now iterate through OPENAI_API_KEYS in case the primary key runs out
# of quota.

def analyze_message(message: str) -> str:
    """
    Analyze the client message and return:
    - tone
    - urgency
    - intent
    - recommended response strategy
    """

    if not message.strip():
        return "No message provided."

    for key in OPENAI_API_KEYS:
        if not key:
            continue
        try:
            client = OpenAI(api_key=key)
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are an expert business communication analyst."
                        ),
                    },
                    {
                        "role": "user",
                        "content": f"""
Analyze the client message below.

Return your analysis in this format:

Tone:
Urgency:
Intent:
Recommended Strategy:

Client message:
{message}
""",
                    },
                ],
                temperature=0.2,
                max_tokens=150,
            )

            return response.choices[0].message.content

        except Exception:
            # try the next key silently
            continue

    return "All service keys are currently busy. Please try again later and plz make sure it is working well no single error should be there"