import os
import ssl
import certifi
from openai import OpenAI
from config import OPENAI_API_KEYS
from utils.prompts import reply_prompt

# Keep this! It fixed your connection error
os.environ['SSL_CERT_FILE'] = certifi.where()

def get_reply(message, custom_prompt=None):
    """Attempt to get a response using each OpenAI key in order.

    Keys that are falsy are skipped automatically. Any exception raised
    while using a key is caught and the next key is tried silently. The
    first successful response is returned immediately. If no key can
    produce a result, a generic busy/fallback string is returned.
    """

    content = custom_prompt if custom_prompt is not None else reply_prompt(message)

    for key in OPENAI_API_KEYS:
        if not key:
            continue
        try:
            client = OpenAI(api_key=key, timeout=30.0)
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": content}],
                temperature=0.7,
            )
            return response.choices[0].message.content
        except Exception:
            # silently ignore and try next key
            continue

    # nothing worked
    return "All service keys are currently busy. Please try again later and plz make sure it is working well no single error should be there"