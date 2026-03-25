def reply_prompt(message, tone="Professional"):
    return f"""
Act as a senior business communication expert.

Write a {tone.lower()} email reply that is:

• polite
• clear
• confident
• solution-oriented
• under 120 words

Client message:
{message}
"""


def analysis_prompt(message):
    return f"""
Analyze the client message.

Return:

Tone:
Urgency:
Intent:
Recommended Strategy:

Message:
{message}
"""


def followup_prompt(message):
    return f"""
Write a polite follow-up email for the message below.

Message:
{message}
"""