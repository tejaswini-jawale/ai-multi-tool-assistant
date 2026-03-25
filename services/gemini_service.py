from google import genai
from config import GEMINI_API_KEYS
from utils.prompts import reply_prompt

# We will instantiate a client inside the loop for each key

def get_reply(message, custom_prompt=None):
    """Return text from the first working Gemini API key.

    Iterates through the list of keys in `GEMINI_API_KEYS`.
    Silent failures are ignored until all keys are exhausted.
    """

    content = custom_prompt if custom_prompt is not None else reply_prompt(message)

    for key in GEMINI_API_KEYS:
        if not key:
            continue
        try:
            client = genai.Client(api_key=key)
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=content,
            )
            return response.text if response.text else "⚠️ No reply generated."
        except Exception:
            continue

    # fallback when no key produced a response
    return "All service keys are currently busy. Please try again later and plz make sure it is working well no single error should be there"