import streamlit as st
import os
import json
from dotenv import load_dotenv, set_key
from config import validate_keys
import config
from services.openai_service import get_reply as chatgpt_reply
from services.gemini_service import get_reply as gemini_reply
from services.grok_service import get_reply as groq_reply
from services.analyzer import analyze_message

# ---------------------------------
# LOAD ENV
# ---------------------------------

HISTORY_FILE = "chat_history.json"

def load_history():
    """Load chats from local JSON file."""
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_history_to_disk(history):
    """Save the entire history dictionary to disk."""
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=4)


load_dotenv()

# ---------------------------------
# PAGE CONFIG
# ---------------------------------
st.set_page_config(page_title="AI Email Assistant", layout="wide")

# ---------------------------------
# VALIDATE KEYS
# ---------------------------------
try:
    validate_keys()
except ValueError as e:
    st.error(f"🔴 API Key Error: {e}")
    st.info("Please add your API keys in the sidebar to continue.")
    st.stop()

# ---------------------------------
# API KEY MANAGER (SIDEBAR)
# ---------------------------------

st.sidebar.header("🔑 API Key Manager")

openai_key_input = st.sidebar.text_input(
    "OpenAI API Key",
    value=os.getenv("OPENAI_API_KEY", ""),
    type="password"
)

gemini_key_input = st.sidebar.text_input(
    "Gemini API Key",
    value=os.getenv("GEMINI_API_KEY", ""),
    type="password"
)

groq_key_input = st.sidebar.text_input(
    "Groq API Key",
    value=os.getenv("GROQ_API_KEY", ""),
    type="password"
)

if st.sidebar.button("Save API Keys", type="primary"):
    env_path = ".env"

    if openai_key_input:
        set_key(env_path, "OPENAI_API_KEY", openai_key_input)
        os.environ["OPENAI_API_KEY"] = openai_key_input
        config.OPENAI_API_KEYS.clear()
        config.OPENAI_API_KEYS.append(openai_key_input)

    if gemini_key_input:
        set_key(env_path, "GEMINI_API_KEY", gemini_key_input)
        os.environ["GEMINI_API_KEY"] = gemini_key_input
        config.GEMINI_API_KEYS.clear()
        config.GEMINI_API_KEYS.append(gemini_key_input)

    if groq_key_input:
        set_key(env_path, "GROQ_API_KEY", groq_key_input)
        os.environ["GROQ_API_KEY"] = groq_key_input
        config.GROQ_API_KEYS.clear()
        config.GROQ_API_KEYS.append(groq_key_input)

    st.sidebar.success("API Keys saved successfully!")
    st.experimental_rerun()

# ---------------------------------
# VALIDATE KEYS
# ---------------------------------
try:
    validate_keys()
except ValueError as e:
    st.error(f"🔴 API Key Error: {e}")
    st.info("Please add your API keys in the sidebar to continue.")
    st.stop()

# ---------------------------------
# DEFAULT DATA
# ---------------------------------

default_conversation = """


placeholder_text = "Paste the client's email or your draft here..."

# ---------------------------------
# SESSION STATE
# ---------------------------------

if "history_store" not in st.session_state:
    st.session_state.history_store = load_history()

# Determine the initial chat
if "current_chat" not in st.session_state:
    if st.session_state.history_store:
        st.session_state.current_chat = next(iter(st.session_state.history_store))
    else:
        st.session_state.current_chat = "Chat 1"

# Load data for the initial chat if it's the first run
if "conversation" not in st.session_state:
    chat_data = st.session_state.history_store.get(st.session_state.current_chat, {})
    st.session_state.conversation = chat_data.get("conversation", default_conversation)
    st.session_state.chat_history = chat_data.get("chat_history", [])
    st.session_state.summary = chat_data.get("summary", "")
    st.session_state.analysis = chat_data.get("analysis", "")
    st.session_state.reply1 = ""
    st.session_state.reply2 = ""
    st.session_state.reply3 = ""
    st.session_state.show_translate_options = False
    st.session_state.translation = ""

if "active_tool" not in st.session_state:
    st.session_state.active_tool = "chat"

if "theme" not in st.session_state:
    st.session_state.theme = "Dark"

# ---------------------------------
# AUTO SAVE FUNCTION
# ---------------------------------

def auto_save_chat():
    """Syncs current session state into the history store and saves to disk."""
    if "current_chat" not in st.session_state:
        return

    st.session_state.history_store[st.session_state.current_chat] = {
        "conversation": st.session_state.conversation,
        "chat_history": st.session_state.chat_history,
        "summary": st.session_state.get("summary", ""),
        "analysis": st.session_state.get("analysis", "")
    }
    save_history_to_disk(st.session_state.history_store)

# ---------------------------------
# THEME SETTINGS
# ---------------------------------
st.sidebar.divider()
st.sidebar.header("🌗 Theme Settings")

theme_choice = st.sidebar.radio(
    "Select Theme",
    ["Dark", "Light"],
    index=0 if st.session_state.theme == "Dark" else 1,
    horizontal=True,
    label_visibility="collapsed"
)
if theme_choice != st.session_state.theme:
    st.session_state.theme = theme_choice
    st.rerun()

# ---------------------------------
# CHAT HISTORY SIDEBAR
# ---------------------------------

st.sidebar.divider()
st.sidebar.header("📂 Chat Management")

# --- NEW & SAVE BUTTONS ---
col_new, col_save = st.sidebar.columns(2)

with col_new:
    if st.button("➕ New Chat", use_container_width=True):
        # Generate a unique name for the new chat
        new_chat_num = len(st.session_state.history_store) + 1
        new_chat_name = f"Chat {new_chat_num}"
        while new_chat_name in st.session_state.history_store:
            new_chat_num += 1
            new_chat_name = f"Chat {new_chat_num}"
            
        # Reset session state for a fresh start
        st.session_state.current_chat = new_chat_name
        st.session_state.conversation = ""
        st.session_state.chat_history = []
        st.session_state.summary = ""
        st.session_state.analysis = ""
        auto_save_chat()
        st.rerun()

with col_save:
    if st.button("💾 Save", use_container_width=True):
        auto_save_chat()
        st.sidebar.success(f"Saved {st.session_state.current_chat}!")

# --- CHAT SELECTION LIST ---
if st.session_state.history_store:
    chat_names = list(st.session_state.history_store.keys())
    
    # Find index of current chat to keep radio button synced
    try:
        current_index = chat_names.index(st.session_state.current_chat)
    except ValueError:
        current_index = 0
        
    selected_chat = st.sidebar.radio(
        "Select a chat:",
        chat_names,
        index=current_index
    )
    
    # Switch chat data if a different one is selected
    if selected_chat != st.session_state.current_chat:
        chat_data = st.session_state.history_store[selected_chat]
        st.session_state.conversation = chat_data.get("conversation", "")
        st.session_state.chat_history = chat_data.get("chat_history", [])
        st.session_state.summary = chat_data.get("summary", "")
        st.session_state.analysis = chat_data.get("analysis", "")
        st.session_state.current_chat = selected_chat
        st.rerun()
else:
    st.sidebar.caption("No saved chats yet. Click 'New Chat' to start.")

# --- RENAME CURRENT CHAT ---
st.sidebar.divider()
st.sidebar.subheader("✏️ Rename Chat")
new_name_input = st.sidebar.text_input("New name:", value=st.session_state.current_chat)

if st.sidebar.button("Update Name", use_container_width=True):
    old_name = st.session_state.current_chat
    if new_name_input and new_name_input != old_name:
        if new_name_input not in st.session_state.history_store:
            # Transfer data to new key and delete old key
            if old_name in st.session_state.history_store:
                st.session_state.history_store[new_name_input] = st.session_state.history_store.pop(old_name)
                save_history_to_disk(st.session_state.history_store)
            st.session_state.current_chat = new_name_input
            st.rerun()
        else:
            st.sidebar.error("This name already exists!")

# ---------------------------------
# TOOL SELECTION
# ---------------------------------

if "active_tool" not in st.session_state:
    st.session_state.active_tool = "chat"

# ---------------------------------
# CSS
# ---------------------------------
# --- Professional Matte 3D Neon Aesthetic ---
if st.session_state.theme == "Light":
    # --- Light Mode Ice-Glass ---
    text_color = "#1E293B"  # Slate 800
    heading_color = "#0F172A" # Deep Navy
    sidebar_bg = "#F1F5F9"  # Ice Blue
    sidebar_border = "#E2E8F0"
    card_bg = "#FFFFFF"     # Solid Matte White
    card_border = "#E2E8F0"
    card_shadow = "0 8px 30px rgba(0,0,0,0.04)"
    input_bg = "#FFFFFF"
    input_border = "#CBD5E1"
    input_bg_focus = "#FFFFFF"
    input_text = "#1E293B"
    accent_color = "#00D2FF" # Cyber-Cyan
    neon_glow = "rgba(0, 210, 255, 0.3)"
    neon_glow_strong = "rgba(0, 210, 255, 0.5)"
    
    # Subtle Ice-Glass Background
    bg_grad_1 = "#F8FAFC"
    bg_grad_2 = "#F1F5F9"
    bg_grad_3 = "#FFFFFF"
    bg_grad_4 = "#F8FAFC"

    button_bg = "#FFFFFF"
    button_hover = "#F8FAFC"
    button_border = "#CBD5E1"
    button_3d_shadow = "#CBD5E1"
    primary_button_3d = "#00A3CC"
    
    scrollbar_thumb = "#CBD5E1"
    scrollbar_thumb_hover = "#94A3B8"
    chat_bg = "#FFFFFF"
    chat_border = "#E2E8F0"

else:
    # --- Dark Mode Cyber Neon ---
    text_color = "#F8FAFC"
    heading_color = "#F8FAFC"
    sidebar_bg = "#0B0F19"
    sidebar_border = "#1E293B"
    card_bg = "#161B22"     # Solid Matte Slate/Black
    card_border = "#30363D"
    card_shadow = "0 2px 8px rgba(0, 0, 0, 0.2)"
    input_bg = "#0B0F19"
    input_border = "#30363D"
    input_bg_focus = "#161B22"
    input_text = "#F8FAFC"
    accent_color = "#00D2FF"  # Cyber Cyan
    neon_glow = "rgba(0, 210, 255, 0.4)"          # Cyan flow
    neon_glow_strong = "rgba(175, 76, 255, 0.7)"  # Purple pulse shade

    # Deep Matte Animated Background
    bg_grad_1 = "#0B0F19"
    bg_grad_2 = "#0F172A"
    bg_grad_3 = "#1A0B2E"     # Deep Purple hint
    bg_grad_4 = "#111827"

    button_bg = "#161B22"
    button_hover = "#1E293B"
    button_border = "#30363D"
    button_3d_shadow = "#020617"
    primary_button_3d = "#008B99"

    scrollbar_thumb = "#475569"
    scrollbar_thumb_hover = "#64748B"
    chat_bg = "#1E293B"
    chat_border = "#30363D"

st.markdown(f"""
<style>
/* --- Keyframes for Animations --- */
@keyframes ambient-bg {{
    0% {{ background-position: 0% 50%; }}
    50% {{ background-position: 100% 50%; }}
    100% {{ background-position: 0% 50%; }}
}}

@keyframes fadeIn {{
    from {{ opacity: 0; transform: translateY(10px); }}
    to {{ opacity: 1; transform: translateY(0); }}
}}

@keyframes float {{
    0% {{ transform: translateY(0px); }}
    50% {{ transform: translateY(-3px); }}
    100% {{ transform: translateY(0px); }}
}}

/* --- Global Styles & Animated Background --- */
html, body {{
    font-family: "Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
}}
* {{
    color: {text_color} !important;
}}
:root {{
    --accent: {accent_color};
}}
body {{
    background: linear-gradient(270deg, {bg_grad_1}, {bg_grad_2}, {bg_grad_3}, {bg_grad_4});
    background-size: 300% 300%;
    animation: ambient-bg 15s ease infinite;
}}
[data-testid="stAppViewContainer"], [data-testid="stHeader"], [data-testid="stMain"] {{
    background: transparent !important;
}}

/* --- Matte Containers (No Glass Blur) --- */
.block-container, [data-testid="stSidebar"], .stAlert, .stInfo, .stSuccess, .stWarning, .stError, div[data-testid="stChatMessage"] {{
    background: {card_bg} !important;
    border: 1px solid {card_border} !important;
    border-radius: 12px !important;
    animation: fadeIn 0.4s ease-out forwards;
    box-shadow: {card_shadow};
}}
[data-testid="stSidebar"] {{
    background: {sidebar_bg} !important;
    border-right: 1px solid {sidebar_border} !important;
    box-shadow: none !important;
}}

/* --- Typography --- */
h1, h2, h3, h4, h5, h6 {{
    color: {heading_color} !important;
    font-weight: 700 !important;
}}

/* --- Inputs (Matte with Neon Focus) --- */
.stTextInput input, .stTextArea textarea, div[data-baseweb="select"] > div, div[data-baseweb="select"] * {{
    background: {input_bg} !important;
    color: {input_text} !important;
    border: 1px solid {input_border} !important;
    border-radius: 8px;
    transition: all 0.3s ease;
}}
.stTextInput input:focus, .stTextArea textarea:focus, div[data-baseweb="select"] > div:focus-within {{
    background: {input_bg_focus} !important;
    border-color: var(--accent) !important;
    box-shadow: 0 0 12px {neon_glow} !important;
}}

/* --- Matte 3D Buttons with Neon Outer Glow --- */
.stButton > button {{
    border-radius: 8px !important;
    background: {button_bg} !important;
    border: 1px solid {button_border} !important;
    color: {text_color} !important;
    font-weight: 600 !important;
    box-shadow: 0 4px 0 {button_3d_shadow} !important;
    transition: all 0.15s ease-in-out !important;
    transform: translateY(0);
}}
.stButton > button:hover {{
    background: {button_hover} !important;
    border-color: var(--accent) !important;
    transform: translateY(-2px);
    box-shadow: 0 6px 0 {button_3d_shadow}, 0 0 15px {neon_glow} !important;
}}
.stButton > button:active {{
    transform: translateY(4px) !important;
    box-shadow: 0 0 0 {button_3d_shadow}, 0 0 8px {neon_glow_strong} !important;
}}

/* --- Primary Buttons --- */
.stButton > button[kind="primary"] {{
    background: var(--accent) !important;
    color: #ffffff !important;
    border: none !important;
    box-shadow: 0 4px 0 {primary_button_3d} !important;
}}
.stButton > button[kind="primary"]:hover {{
    box-shadow: 0 6px 0 {primary_button_3d}, 0 0 20px {neon_glow_strong} !important;
}}

/* --- Radio Pills --- */
div[data-testid="stRadio"] > div > label {{
    border-radius: 8px;
    background: {button_bg};
    border: 1px solid {button_border};
    transition: all 0.2s ease;
}}
div[data-testid="stRadio"] > div > label:hover {{
    border-color: var(--accent);
    box-shadow: 0 0 8px {neon_glow};
}}
div[data-testid="stRadio"] input[type="radio"] {{ display: none; }}
div[data-testid="stRadio"] > div > label:has(input:checked) {{
    background: var(--accent) !important;
    border: 1px solid var(--accent) !important;
    color: {'#FFFFFF' if st.session_state.theme == 'Dark' else '#0D0C1D'} !important;
    box-shadow: 0 0 15px {neon_glow_strong} !important;
}}

/* --- Chat Bubbles (Float Animation & Neon Glow on Hover) --- */
div[data-testid="stChatMessage"] {{
    background: {chat_bg} !important;
    border: 1px solid {chat_border} !important;
    transition: transform 0.3s ease, box-shadow 0.3s ease;
}}
div[data-testid="stChatMessage"]:hover {{
    animation: float 2s ease-in-out infinite;
    border-color: var(--accent) !important;
    box-shadow: 0 8px 15px -3px rgba(0,0,0,0.1), 0 0 12px {neon_glow};
}}

/* --- Scrollbar --- */
::-webkit-scrollbar {{ width: 8px; }}
::-webkit-scrollbar-track {{ background: transparent; }}
::-webkit-scrollbar-thumb {{ background: {scrollbar_thumb}; border-radius: 8px; }}
::-webkit-scrollbar-thumb:hover {{ background: {scrollbar_thumb_hover}; }}

/* --- Fix for sidebar button overrides --- */
[data-testid="stSidebar"] .stButton > button {{
    box-shadow: 0 3px 0 {button_3d_shadow} !important;
}}
[data-testid="stSidebar"] .stButton > button:active {{
    transform: translateY(3px) !important;
    box-shadow: 0 0 0 {button_3d_shadow}, 0 0 5px {neon_glow_strong} !important;
}}

/* --- Microinteractions & 3D UI Animations --- */

/* Sidebar Headings Hover */
[data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3, [data-testid="stSidebar"] h4, [data-testid="stSidebar"] h5, [data-testid="stSidebar"] h6 {{
    transition: transform 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275), color 0.3s ease;
    display: inline-block;
    width: 100%;
}}
[data-testid="stSidebar"] h1:hover, [data-testid="stSidebar"] h2:hover, [data-testid="stSidebar"] h3:hover, [data-testid="stSidebar"] h4:hover, [data-testid="stSidebar"] h5:hover, [data-testid="stSidebar"] h6:hover {{
    transform: translateX(8px);
    color: var(--accent) !important;
    text-shadow: 0 0 8px {neon_glow};
}}

/* Sidebar Input Focus & Hover */
[data-testid="stSidebar"] .stTextInput input {{
    transition: transform 0.3s cubic-bezier(0.25, 0.8, 0.25, 1), box-shadow 0.3s ease, border-color 0.3s ease !important;
}}
[data-testid="stSidebar"] .stTextInput input:hover {{
    transform: translateY(-2px);
}}
[data-testid="stSidebar"] .stTextInput input:focus {{
    transform: scale(1.02) translateY(-2px);
    box-shadow: 0 8px 15px {neon_glow} !important;
}}

/* Sidebar Radio Items (Chat List) */
[data-testid="stSidebar"] div[data-testid="stRadio"] label {{
    transition: all 0.2s cubic-bezier(0.25, 0.8, 0.25, 1) !important;
    border-left: 3px solid transparent;
    padding-left: 8px;
    border-radius: 4px;
}}
[data-testid="stSidebar"] div[data-testid="stRadio"] label:hover {{
    transform: translateX(8px) scale(1.02);
    border-left: 3px solid var(--accent) !important;
    background: rgba(175, 76, 255, 0.1) !important;
}}

/* Alert/Output Cards Hover Lift */
.stAlert, .stInfo, .stSuccess, .stWarning, .stError {{
    transition: transform 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275), box-shadow 0.3s ease !important;
    transform-style: preserve-3d;
}}
.stAlert:hover, .stInfo:hover, .stSuccess:hover, .stWarning:hover, .stError:hover {{
    transform: perspective(800px) translateZ(15px) translateY(-5px) scale(1.01) !important;
    box-shadow: 0 15px 30px rgba(0,0,0,0.3), 0 0 20px {neon_glow} !important;
    border-color: var(--accent) !important;
    z-index: 10;
}}

/* Text Area Focus Pulse */
@keyframes focus-pulse {{
    0% {{ box-shadow: 0 0 5px {neon_glow}; border-color: var(--accent); }}
    100% {{ box-shadow: 0 0 20px {neon_glow_strong}; border-color: #AF4CFF; }}
}}
.stTextArea textarea:focus {{
    animation: focus-pulse 1.5s infinite alternate ease-in-out !important;
    transform: scale(1.005);
    transition: transform 0.2s ease;
}}

/* Pop effect on Main Radio pills click */
div[data-testid="stRadio"] > div > label:active {{
    transform: scale(0.95);
}}

</style>
""", unsafe_allow_html=True)

# ---------------------------------
st.markdown(f"""
<style>
@keyframes aurora-bg {{
    0% {{ background-position: 0% 50%; }}
    100% {{ background-position: 200% 50%; }}
}}
@keyframes glow-pulse {{
    0% {{ opacity: 0.3; filter: blur(8px); }}
    100% {{ opacity: 0.7; filter: blur(14px); }}
}}
@keyframes particle-drift {{
    0% {{ transform: translate(0px, 0px) scale(0.6); opacity: 0; }}
    25% {{ opacity: 0.5; }}
    75% {{ opacity: 0.3; }}
    100% {{ transform: translate(40px, -30px) scale(1.4); opacity: 0; }}
}}
@keyframes icon-float {{
    0% {{ transform: translateY(0px) rotate(0deg); filter: drop-shadow(0 0 6px {accent_color}); }}
    50% {{ transform: translateY(-5px) rotate(8deg); filter: drop-shadow(0 0 14px #AF4CFF); }}
    100% {{ transform: translateY(0px) rotate(0deg); filter: drop-shadow(0 0 6px {accent_color}); }}
}}

.title-wrapper {{
    position: relative;
    display: flex;
    align-items: center;
    margin-bottom: 25px;
    margin-top: -10px;
    padding: 10px 0;
}}

.title-particles {{
    position: absolute;
    top: 0; left: 0; width: 100%; height: 100%;
    pointer-events: none;
    z-index: 0;
}}

.particle {{
    position: absolute;
    background: radial-gradient(circle, {accent_color} 0%, transparent 70%);
    border-radius: 50%;
    mix-blend-mode: screen;
}}

.particle-1 {{ width: 35px; height: 35px; top: 15%; left: 10%; animation: particle-drift 6s infinite ease-in-out; }}
.particle-2 {{ width: 50px; height: 50px; top: 35%; left: 40%; animation: particle-drift 8s infinite ease-in-out 2s; background: radial-gradient(circle, #AF4CFF 0%, transparent 70%); }}
.particle-3 {{ width: 25px; height: 25px; top: 20%; left: 70%; animation: particle-drift 5s infinite ease-in-out 1s; }}

.ai-icon {{
    width: 42px;
    height: 42px;
    margin-right: 18px;
    z-index: 2;
    animation: icon-float 5s ease-in-out infinite;
}}

.aurora-title {{
    position: relative;
    z-index: 2;
    background: linear-gradient(270deg, {accent_color} 0%, #AF4CFF 25%, #00D2FF 50%, #AF4CFF 75%, {accent_color} 100%);
    background-size: 200% auto;
    color: transparent;
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    animation: aurora-bg 6s linear infinite;
    font-size: 2.2rem;
    font-weight: 800;
    letter-spacing: 1.5px;
    text-transform: uppercase;
}}
    top: 0;
    z-index: -1;
    background: inherit;
    background-size: inherit;
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    animation: aurora-bg 6s linear infinite, glow-pulse 3s ease-in-out infinite alternate;
}}
</style>
<div style="display: flex; align-items: center; margin-bottom: 20px; margin-top: -10px;">
    <span class="title-emoji"></span>
    <span class="animated-title"></span>

<div class="title-wrapper">
        <div class="particle particle-3"></div>
    </div>
    <svg class="ai-icon" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M12 2L14.4 9.6L22 12L14.4 14.4L12 22L9.6 14.4L2 12L9.6 9.6L12 2Z" fill="url(#ai-gradient)" />
        <path d="M19 3L19.8 4.8L21.5 5.5L19.8 6.2L19 8L18.2 6.2L16.5 5.5L18.2 4.8L19 3Z" fill="url(#ai-gradient)" />
        <path d="M5 18L5.6 19.3L7 20L5.6 20.7L5 22L4.4 20.7L3 20L4.4 19.3L5 18Z" fill="url(#ai-gradient)" />
        <defs>
            <linearGradient id="ai-gradient" x1="2" y1="2" x2="22" y2="22" gradientUnits="userSpaceOnUse">
                <stop stop-color="{accent_color}" />
                <stop offset="1" stop-color="#AF4CFF" />
            </linearGradient>
        </defs>
    </svg>
    <span class="aurora-title" data-text="">AI MULTITOOL ASSISTANT</span>
</div>
""", unsafe_allow_html=True)

conversation = st.text_area(
    "Message Body",
    value=st.session_state.conversation,
    height=250,
    placeholder=placeholder_text
)

st.session_state.conversation = conversation

# ---------------------------------
# PROMPT BUILDER
# ---------------------------------

def enhance_message(convo,tone):

    return f"""
You are a professional email assistant.

Write a professional email reply.

Return format:

Reply:
<email reply>

Tone: {tone}

Conversation:
{convo}
"""


def bullet_point_prompt(text):
    return f"""
Extract the most important key information from the following text and present it as a clean, professional bulleted list.
Use a clear heading for the list.

Text:
{text}
"""


def title_generator_prompt(text):
    return f"""
You are a creative content strategist.

Generate 5-10 catchy, SEO-friendly, and professional titles for the following content or topic:

{text}
"""


def quiz_generator_prompt(text):
    return f"Act as a teacher. Create a 5-question multiple-choice quiz about: {text}. Include options A-D and the correct answer at the end of each question."

def hashtag_generator_prompt(text):
    return f"""
Act as a social media growth expert. Generate 15-20 trending and highly relevant hashtags for the topic: {text}.
Organize them into three groups: Popular, Niche, and Low Competition.
"""

def sentiment_analyzer_prompt(text):
    return f"""
Act as an expert psychological and linguistic sentiment analyzer.
Analyze the sentiment of the following text and provide:
1. Overall Sentiment (Positive, Negative, Neutral)
2. Key Emotions Detected
3. Tone and Intent
4. A brief explanation of the analysis

Text:
{text}
"""

def image_prompt_generator_prompt(text):
    return f"""
Act as an expert prompt engineer for AI image generators (like Midjourney, DALL-E 3, Stable Diffusion).
Based on the following topic or text, generate 3-5 highly detailed and creative image generation prompts.
Include specific details about style, lighting, composition, colors, and camera settings where applicable.

Topic/Text:
{text}
"""

def build_tool_prompt(tool, text, tone=None):
    if tool == "bullet":
        return bullet_point_prompt(text)
    if tool == "title":
        return title_generator_prompt(text)
    if tool == "quiz":
        return quiz_generator_prompt(text)
    if tool == "hashtag":
        return hashtag_generator_prompt(text)
    if tool == "sentiment":
        return sentiment_analyzer_prompt(text)
    if tool == "image_prompt":
        return image_prompt_generator_prompt(text)
    # default to chat assistant
    return enhance_message(text, tone or "Professional")

# ---------------------------------
# EXTRACT SUBJECT + BODY
# ---------------------------------

def extract_email_parts(text):

    body = text

    if "Reply:" in text:
        body = text.split("Reply:")[1].strip()

    return body


def format_as_markdown_list(text: str) -> str:
    """Ensure the AI output renders cleanly as a markdown list."""

    if not text:
        return ""

    lines = [line.strip() for line in text.strip().splitlines() if line.strip()]
    if not lines:
        return ""

    formatted = []
    for line in lines:
        if line.startswith(('-', '*')) or line[0].isdigit():
            formatted.append(line)
        else:
            formatted.append(f"- {line}")

    return "\n".join(formatted)


def render_tool_output(label: str, content: str, key: str = None):
    """Render AI tool output based on the currently selected tool."""

    if st.session_state.active_tool in ("quiz", "hashtag", "sentiment", "image_prompt"):
        st.markdown(f"### {label}")
        with st.container(height=300):
            st.markdown(content)
    elif st.session_state.active_tool in ("bullet", "title"):
        st.markdown(f"### {label}")
        with st.container(height=300):
            st.markdown(format_as_markdown_list(content))
    else:
        st.text_area(label, content, height=200, key=key)

# ---------------------------------
# SAFE CALL
# ---------------------------------

def safe_call(func, *args):
    try:
        return func(*args)
    except Exception as e:
        return f"Error: {str(e)}"

# ---------------------------------
# GENERATE REPLIES
# ---------------------------------
def summarize_email(convo):

    return f"""
You are an AI assistant.

Summarize the email conversation in 3-4 bullet points.

Rules:
- Ignore the subject line
- Ignore greetings like Dear/Hi/Hello
- Ignore signatures and closing lines
- Focus only on the main message content

Email Conversation:
{convo}
"""
# ---------------------------------
# TRANSLATE EMAIL PROMPT
# ---------------------------------

def translate_email(convo, language):

    return f"""
You are a professional translator.

Translate the email below into {language}.

Rules:
- The output must be ONLY in {language}
- Do NOT include English
- Do NOT explain the translation
- Do NOT include phrases like "Here is the translation"
- Keep the same meaning as the original email
- Preserve paragraph formatting

Email:
{convo}
"""

# ---------------------------------
# AI CHAT POPUP FUNCTION
# ---------------------------------

@st.dialog("🤖 AI Assistant Chat")
def ai_chat_popup():

    chat_container = st.container(height=400)

    with chat_container:
        for message in st.session_state.chat_history:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
                
    user_prompt = st.chat_input("Ask Assistant...")

    if user_prompt:
        st.session_state.chat_history.append(
            {"role": "user", "content": user_prompt}
        )

        # Render the user's message immediately inside the container
        with chat_container:
            with st.chat_message("user"):
                st.markdown(user_prompt)

        chat_prompt_for_grok = f"""
You are Grok AI helping the user write and improve emails.

Current Email Conversation:
{st.session_state.conversation}

User Question:
{user_prompt}
"""

        with chat_container:
            with st.spinner("Groq is thinking..."):
                reply = safe_call(groq_reply, "", chat_prompt_for_grok)

        st.session_state.chat_history.append(
            {"role": "assistant", "content": reply}
        )

        # Render the AI's reply immediately inside the container
        with chat_container:
            with st.chat_message("assistant"):
                st.markdown(reply)
                
        # Save to your local JSON so it's not lost on full page reloads
        auto_save_chat()

# ---------------------------------
# TOOLBAR (Modes & Actions)
# ---------------------------------

st.divider()
 
toolbar1, toolbar2 = st.columns([12, 1])

with toolbar1:
    st.markdown("### 🛠️ Toolbar")

with toolbar2:
    if st.button("💬", help="Open AI Assistant"):
        ai_chat_popup()

tool_options = {
    "chat": "🗨️ Chat Assistant",
    "bullet": "📝 Bullet Point Extractor",
    "title": "🏷️ Title Generator",
    "quiz": "📚 Quiz Generator",
    "hashtag": "#️⃣ Hashtag Generator",
    "sentiment": "🎭 Sentiment Analyzer",
    "image_prompt": "🖼️ Image Prompt Generator",
}

tool_ids = list(tool_options.keys())
try:
    active_tool_index = tool_ids.index(st.session_state.active_tool)
except ValueError:
    active_tool_index = 0
    st.session_state.active_tool = tool_ids[0]

selected_tool_id = st.radio(
    "Select a tool",
    options=tool_ids,
    format_func=lambda x: tool_options[x],
    index=active_tool_index,
    label_visibility="collapsed",
    horizontal=True
)

if selected_tool_id != st.session_state.active_tool:
    st.session_state.active_tool = selected_tool_id
    if selected_tool_id == 'quiz':
        st.session_state.conversation = ""
    st.rerun()

st.write("") # Add a tiny spacer for visual breathing room

col1, col2, col3, col4 = st.columns(4)

# Clear Chat
with col1:
    if st.button("🗑 Clear Chat", use_container_width=True):

        # Clear chat
        st.session_state.chat_history = []

        # Clear summary and analysis
        st.session_state.summary = ""
        st.session_state.analysis = ""


        # Clear translation
        st.session_state.translation = ""
        

        # Clear AI replies
        st.session_state.reply1 = ""
        st.session_state.reply2 = ""
        st.session_state.reply3 = ""

        st.rerun()

# Summarize Email
with col2:
    if st.button("🧾 Summarize Email", use_container_width=True):

        prompt = summarize_email(st.session_state.conversation)

        with st.spinner("Summarizing email..."):
            st.session_state.summary = safe_call(groq_reply, "", prompt)

# Generate Replies
with col3:
    if st.button("✨ Generate AI Replies", type="primary", use_container_width=True):

        prompt = build_tool_prompt(
            st.session_state.active_tool,
            st.session_state.conversation,
            "Professional",
        )

        if st.session_state.active_tool == "chat":
            with st.spinner("Analyzing message..."):
                st.session_state.analysis = analyze_message(st.session_state.conversation)
        else:
            st.session_state.analysis = "" # Skip analysis for non-chat tools

        with st.spinner(f"Generating {'quiz' if st.session_state.active_tool == 'quiz' else 'replies'}..."):
            st.session_state.reply1 = safe_call(chatgpt_reply, "", prompt)
            st.session_state.reply2 = safe_call(gemini_reply, "", prompt)
            st.session_state.reply3 = safe_call(groq_reply, "", prompt)
# Translate Email
with col4:
    if st.button("🌍 Translate", use_container_width=True):
        st.session_state.show_translate_options = not st.session_state.show_translate_options

# ---------------------------------
# TRANSLATION OPTIONS
# ---------------------------------

if st.session_state.show_translate_options:

    st.markdown("#### 🌍 Translate Email")
    t_col1, t_col2 = st.columns([3, 1])
    
    with t_col1:
        language = st.selectbox(
            "Select Language",
            ["Spanish", "French", "German", "Hindi", "Marathi", "Chinese", "Japanese"],
            label_visibility="collapsed"
        )

    with t_col2:
        if st.button("Translate Now", type="primary", use_container_width=True):
            prompt = translate_email(st.session_state.conversation, language)
            with st.spinner("Translating email..."):
                st.session_state.translation = safe_call(groq_reply, "", prompt)

# ---------------------------------
# FULL WIDTH OUTPUT
# ---------------------------------

if st.session_state.summary:
    st.subheader("📄 Email Summary")
    st.info(st.session_state.summary)

if st.session_state.analysis:
    st.subheader("🧠 Message Analysis")
    st.info(st.session_state.analysis)
# ---------------------------------
# AI REPLIES
# ---------------------------------

if (
st.session_state.reply1
or st.session_state.reply2
or st.session_state.reply3
):

    if st.session_state.active_tool == "quiz":
        st.subheader("📚 Generated Quizzes")
    else:
        st.subheader("✉️ Reply Options")

    col1,col2,col3 = st.columns(3)

    # ChatGPT
    with col1:

        render_tool_output("🤖 ChatGPT", st.session_state.reply1, key="reply1")

        if st.button("Use ChatGPT", key="use_chatgpt", type="primary"):

            body = extract_email_parts(st.session_state.reply1)

            st.session_state.conversation += "\n\nYou:\n"+body

            auto_save_chat()

            st.rerun()

    # Gemini
    with col2:

        render_tool_output("🌐 Gemini", st.session_state.reply2, key="reply2")

        if st.button("Use Gemini", key="use_gemini", type="primary"):

            body = extract_email_parts(st.session_state.reply2)

            st.session_state.conversation += "\n\nYou:\n"+body

            auto_save_chat()

            st.rerun()

    # Grok
    with col3:

        render_tool_output("🚀 Groq", st.session_state.reply3, key="reply3")

        if st.button("Use Groq", key="use_grok", type="primary"):

            body = extract_email_parts(st.session_state.reply3)

            st.session_state.conversation += "\n\nYou:\n"+body

            auto_save_chat()

            st.rerun()

# ---------------------------------
# TRANSLATION OUTPUT
# ---------------------------------

if st.session_state.translation:

    st.subheader("🌍 Translated Email")

    st.success(st.session_state.translation)

# ---------------------------------
    # ---------------------------------
# ---------------------------------

st.divider()
st.caption("Built using ChatGPT, Gemini & Groq APIs")
