import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# OpenAI / ChatGPT API Keys (multiple for fallback when quota exhausted)
# You can either set OPENAI_API_KEYS in the .env as a comma-separated string or
# edit the list below directly. The code will always prioritize the list (env overrides).
env_keys = os.getenv("OPENAI_API_KEYS")
if env_keys:
    OPENAI_API_KEYS = [k.strip() for k in env_keys.split(",") if k.strip()]
else:
    # Try single key from .env, fallback to empty list
    single_key = os.getenv("OPENAI_API_KEY")
    OPENAI_API_KEYS = [single_key] if single_key else []

# Keep a single-key fallback variable for compatibility but unused in rotation
OPENAI_API_KEY = OPENAI_API_KEYS[0] if OPENAI_API_KEYS else None

# Google Gemini API Key (single value, retained for backward compatibility)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Optional list of Gemini API keys for rotation/failover.
# Set GEMINI_API_KEYS as a comma-separated string in your .env.
env_gemini_keys = os.getenv("GEMINI_API_KEYS")
if env_gemini_keys:
    GEMINI_API_KEYS = [k.strip() for k in env_gemini_keys.split(",") if k.strip()]
else:
    GEMINI_API_KEYS = [GEMINI_API_KEY] if GEMINI_API_KEY else []

# Groq API Keys (multiple for fallback when quota exhausted)
env_groq_keys = os.getenv("GROQ_API_KEYS")
if env_groq_keys:
    GROQ_API_KEYS = [k.strip() for k in env_groq_keys.split(",") if k.strip()]
else:
    # Fallback to single key from .env
    single_groq_key = os.getenv("GROQ_API_KEY")
    GROQ_API_KEYS = [single_groq_key] if single_groq_key else []

GROQ_API_KEY = GROQ_API_KEYS[0] if GROQ_API_KEYS else None


def validate_keys():
    """
    Ensures all required API keys are present.
    Run this at app startup to avoid runtime errors.
    """
    missing = []

    # Check the lists that the services actually use for rotation.
    if not OPENAI_API_KEYS:
        missing.append("OPENAI_API_KEYS or OPENAI_API_KEY")

    if not GEMINI_API_KEYS:
        missing.append("GEMINI_API_KEYS or GEMINI_API_KEY")

    if not GROQ_API_KEYS:
        missing.append("GROQ_API_KEYS or GROQ_API_KEY")

    if missing:
        raise ValueError(
            f"Missing API Keys: {', '.join(missing)}\n"
            "Please add them to your .env file or use the sidebar."
        )

    return True