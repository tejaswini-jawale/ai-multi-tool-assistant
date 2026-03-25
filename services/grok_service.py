import os
from openai import OpenAI
from dotenv import load_dotenv

from config import GROQ_API_KEYS
from utils.prompts import reply_prompt

# Load environment variables
load_dotenv()

def get_reply(message, custom_prompt=None):
    """Try each Groq key until one succeeds, with model fallback.

    A single list is built from `GROQ_API_KEYS` or the legacy
    `GROK_API_KEY`. Empty keys are skipped. Errors are caught and the
    loop continues; the first good response is returned. If all keys
    fail, the generic busy message is returned.
    """

    content = custom_prompt if custom_prompt is not None else reply_prompt(message)

    keys = GROQ_API_KEYS

    for key in keys:
        if not key:
            continue
        client = OpenAI(api_key=key, base_url="https://api.groq.com/openai/v1")
        try:
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": content}],
                temperature=0.7,
            )
            return response.choices[0].message.content
        except Exception as e:
            err = str(e).lower()
            # attempt model fallback on decommission errors
            if "decommissioned" in err or "400" in err:
                try:
                    response = client.chat.completions.create(
                        model="openai/gpt-oss-120b",
                        messages=[{"role": "user", "content": content}],
                    )
                    return response.choices[0].message.content
                except Exception:
                    pass
            # otherwise just move to the next key
            continue

    return "All service keys are currently busy. Please try again later and plz make sure it is working well no single error should be there" 