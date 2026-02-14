import streamlit as st
import httpx
from streamlit_autorefresh import st_autorefresh

# --- 🔐 CONFIGURATION (PASTE YOUR KEYS HERE) ---
SUPABASE_URL = "https://vzjnqlfprmggutawcqlg.supabase.co"
SUPABASE_KEY =  "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZ6am5xbGZwcm1nZ3V0YXdjcWxnIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzEwMzUyMjcsImV4cCI6MjA4NjYxMTIyN30.vC_UxPIF7E3u0CCm3WQMpH9K2-tgJt8zG_Q4vGrPW1I"

# --- 🚫 BANNED WORD LIST (Edit this list!) ---
# These words will trigger a block, even if hidden inside other words (e.g. "ass" blocks "pass")
BANNED_WORDS = [
    "fuck", "shit", "bitch", "ass", "idiot", "stupid", "dumb", 
    "hate", "kill", "die", "moron", "useless", "dick",
]

# --- 🔄 AUTO-REFRESH ---
st_autorefresh(interval=2000, key="chat_update_pulse")

# --- 🛠️ DATABASE HELPERS ---
def get_messages():
    url = f"{SUPABASE_URL}/rest/v1/messages?select=*&order=created_at.asc"
    headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
    try:
        with httpx.Client() as client:
            r = client.get(url, headers=headers, timeout=5.0)
            return r.json()
    except Exception:
        return []

def save_to_db(sender, original, rewritten, score):
    url = f"{SUPABASE_URL}/rest/v1/messages"
    headers = {
        "apikey": SUPABASE_KEY, 
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=minimal"
    }
    data = {
        "sender": sender,
        "original_text": original,
        "rewritten_text": rewritten,
        "toxicity_score": score
    }
    try:
        with httpx.Client() as client:
            client.post(url, headers=headers, json=data, timeout=5.0)
    except:
        pass

def clear_db():
    url = f"{SUPABASE_URL}/rest/v1/messages?id=gt.0"
    headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
    with httpx.Client() as client:
        client.delete(url, headers=headers)

# --- ⚡ INSTANT FILTER LOGIC (NO AI) ---
def check_message(text):
    text_lower = text.lower()
    
    # Check if any banned word is a substring of the message
    for bad_word in BANNED_WORDS:
        if bad_word in text_lower:
            # Found a match! Block it immediately.
            return {"rewritten": "msg restricted", "score": 100}
            
    # No bad words found
    return {"rewritten": text, "score": 0}

# --- 🎨 UI DESIGN ---
st.set_page_config(page_title="AEGIS: Hard Filter", page_icon="🛡️", layout="centered")

st.markdown("""
<style>
    .chat-bubble { padding: 12px 18px; border-radius: 12px; margin-bottom: 8px; width: fit-content; max-width: 80%; }
    .bubble-left { background-color: #F0F2F6; color: black; }
    .bubble-right { background-color: #007AFF; color: white; margin-left: auto; }
    .restricted-msg { font-style: italic; color: #888; background-color: #f8f9fa; border: 1px dashed #ccc; }
    .god-mode-box { font-size: 0.8em; color: #d32f2f; margin-top: 2px; text-align: right; font-family: monospace; }
</style>
""", unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.header("🛡️ AEGIS Filter")
    role = st.radio("Identity", ["Person A", "Person B"])
    st.divider()
    
    god_mode = False
    if role == "Person A":
        god_mode = st.toggle("God Mode", value=False)
            
    if st.button("Clear Chat"): 
        clear_db()
        st.rerun()

# --- CHAT ---
st.caption("Strict Keyword Filtering")

chat_container = st.container()
with chat_container:
    messages = get_messages()
    for m in messages:
        is_me = (m['sender'] == role)
        bubble_class = "bubble-right" if is_me else "bubble-left"
        
        # Check if restricted
        msg_text = m['rewritten_text']
        extra_style = ""
        
        if msg_text == "msg restricted":
            if is_me:
                # If I sent it, still show as blue bubble but maybe distinctive
                pass 
            else:
                # If they sent it, show as greyed out
                bubble_class += " restricted-msg"
        
        # Draw Message
        st.markdown(f"""
            <div class="chat-bubble {bubble_class}">
                <b>{m['sender']}</b>: {msg_text}
            </div>
        """, unsafe_allow_html=True)
        
        # God Mode Text (Only shows if message was actually blocked)
        if god_mode and m['original_text'] != m['rewritten_text']:
             st.markdown(f'<div class="god-mode-box">Blocked: "{m["original_text"]}"</div>', unsafe_allow_html=True)

# --- INPUT ---
st.divider()
with st.form("input_form", clear_on_submit=True):
    col1, col2 = st.columns([5, 1])
    with col1:
        user_msg = st.text_input("Msg", placeholder="Type...", label_visibility="collapsed")
    with col2:
        sent = st.form_submit_button("Send")
        
    if sent and user_msg:
        # Run Local Filter
        analysis = check_message(user_msg)
        save_to_db(role, user_msg, analysis['rewritten'], analysis['score'])
        st.rerun()
