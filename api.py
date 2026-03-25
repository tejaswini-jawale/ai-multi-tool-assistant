from fastapi import FastAPI
from pydantic import BaseModel

# Import your AI services
from services.openai_service import get_reply as chatgpt_reply
from services.gemini_service import get_reply as gemini_reply
from services.grok_service import get_reply as grok_reply
from services.analyzer import analyze_message

app = FastAPI(
    title="AI Reply Assistant API",
    description="Generate professional replies using multiple AI models",
    version="1.0"
)

# -----------------------------
# Request Model for POST
# -----------------------------

class ConversationRequest(BaseModel):
    conversation: str
    tone: str


# -----------------------------
# Prompt Builder
# -----------------------------

def enhance_message(convo, tone_style):
    return f"""
You are a professional business assistant.

Below is a conversation between a client and a professional.

Write the next professional reply in the conversation.

Tone: {tone_style}

Conversation:
{convo}

Professional Reply:
"""


# -----------------------------
# Home Route
# -----------------------------

@app.get("/")
def home():
    return {
        "message": "AI Reply Assistant API is running",
        "test_get": "/professional-conversation",
        "test_post": "/generate-replies",
        "docs": "/docs"
    }


# -----------------------------
# GET Endpoint (Browser Friendly)
# -----------------------------

@app.post("/professional-conversation")
def get_conversation():

    conversation = """
Client: Hi, can the project be completed by Friday instead of Monday?

You: Currently our team is working with the Monday timeline, but we can review the schedule.

Client: Friday would help us align with our internal product launch.
"""

    tone = "Professional"

    enhanced_message = enhance_message(conversation, tone)

    analysis = analyze_message(conversation)

    reply1 = chatgpt_reply(enhanced_message)
    reply2 = gemini_reply(enhanced_message)
    reply3 = grok_reply(enhanced_message)

    return {
        "conversation": conversation,
        "tone": tone,
        "analysis": analysis,
        "chatgpt_reply": reply1,
        "gemini_reply": reply2,
        "grok_reply": reply3
    }


# -----------------------------
# POST Endpoint (Main API)
# -----------------------------

@app.post("/generate-replies")
def generate_replies(data: ConversationRequest):

    enhanced_message = enhance_message(data.conversation, data.tone)

    analysis = analyze_message(data.conversation)

    reply1 = chatgpt_reply(enhanced_message)
    reply2 = gemini_reply(enhanced_message)
    reply3 = grok_reply(enhanced_message)

    return {
        "conversation": data.conversation,
        "tone": data.tone,
        "analysis": analysis,
        "chatgpt_reply": reply1,
        "gemini_reply": reply2,
        "grok_reply": reply3
    }