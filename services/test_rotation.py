"""Simple script to verify API key rotation for OpenAI and Groq services.

Run with: python -m services.test_rotation (from project root)
"""

from services import openai_service, grok_service

# --- helper fakes -----------------------------------------------------------

class DummyResp:
    def __init__(self, text):
        class Msg:
            def __init__(self, c):
                self.content = c
        class Choice:
            def __init__(self, m):
                self.message = Msg(m)
        self.choices = [Choice(text)]

class DummyClient:
    def __init__(self, fail_until=0, fail_msg="insufficient_quota"):
        self.count = 0
        self.fail_until = fail_until
        self.fail_msg = fail_msg

    class chat:
        class completions:
            @staticmethod
            def create(model, messages, temperature=None):
                DummyClient.instance.count += 1
                if DummyClient.instance.count <= DummyClient.instance.fail_until:
                    raise Exception(DummyClient.instance.fail_msg)
                return DummyResp("success")

# attach the singleton instance so the static method can access it
# (simplest hack for demo purposes)

# --- test logic -------------------------------------------------------------

def test_openai_rotation():
    print("Testing OpenAI rotation...")
    # prepare fake keys and a client that fails twice before succeeding
    openai_service.OPENAI_API_KEYS = ["k1", "k2", "k3"]
    dummy = DummyClient(fail_until=2)
    DummyClient.instance = dummy
    # monkeypatch the OpenAI constructor so every call returns our dummy
    openai_service.OpenAI = lambda api_key, timeout=None: dummy

    result = openai_service.get_reply("foo")
    assert result == "success"
    # dummy should have been called three times (two failures then success)
    assert DummyClient.instance.count == 3, "should have tried two keys before succeeding"
    print("OpenAI rotation passed, attempts", DummyClient.instance.count)


def test_groq_rotation():
    print("Testing Groq rotation...")
    grok_service.GROQ_API_KEYS = ["g1", "g2"]
    dummy = DummyClient(fail_until=1, fail_msg="quota exceeded")
    DummyClient.instance = dummy
    grok_service.OpenAI = lambda api_key, base_url=None: dummy

    result = grok_service.get_reply("bar")
    assert result == "success"
    assert DummyClient.instance.count == 2, "should have tried the first key then succeeded with second"
    print("Groq rotation passed, attempts", DummyClient.instance.count)



def test_openai_fallback():
    print("Testing OpenAI fallback message...")
    openai_service.OPENAI_API_KEYS = ["k1", "k2"]
    dummy = DummyClient(fail_until=100)  # always fail
    DummyClient.instance = dummy
    openai_service.OpenAI = lambda api_key, timeout=None: dummy

    result = openai_service.get_reply("foo")
    assert result.startswith("All service keys are currently busy"), result
    print("OpenAI fallback returned correct message")


def test_groq_fallback():
    print("Testing Groq fallback message...")
    grok_service.GROQ_API_KEYS = ["g1"]
    dummy = DummyClient(fail_until=100)
    DummyClient.instance = dummy
    grok_service.OpenAI = lambda api_key, base_url=None: dummy

    result = grok_service.get_reply("bar")
    assert result.startswith("All service keys are currently busy"), result
    print("Groq fallback returned correct message")


def test_gemini_rotation():
    print("Testing Gemini rotation...")
    import services.gemini_service as gs
    gs.GEMINI_API_KEYS = ["x1", "x2", "x3"]
    dummy = DummyClient(fail_until=2)
    DummyClient.instance = dummy
    gs.genai.Client = lambda api_key: dummy

    result = gs.get_reply("baz")
    assert result == "success"
    assert DummyClient.instance.count == 3
    print("Gemini rotation passed, attempts", DummyClient.instance.count)


if __name__ == "__main__":
    test_openai_rotation()
    test_groq_rotation()
    test_openai_fallback()
    test_groq_fallback()
    test_gemini_rotation()
    print("All rotation tests succeeded.")