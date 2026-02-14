import streamlit as st
import httpx
import uuid
import time
from streamlit_autorefresh import st_autorefresh

# --- 🔐 CONFIGURATION ---
SUPABASE_URL = "https://vzjnqlfprmggutawcqlg.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZ6am5xbGZwcm1nZ3V0YXdjcWxnIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzEwMzUyMjcsImV4cCI6MjA4NjYxMTIyN30.vC_UxPIF7E3u0CCm3WQMpH9K2-tgJt8zG_Q4vGrPW1I"

# --- 🔄 PAGE SETUP & THEME ---
st.set_page_config(page_title="AEGIS Chat", page_icon="🛡️", layout="wide", initial_sidebar_state="expanded")

# --- 🎨 REFINED CSS ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');
    
    /* Global Reset & Font */
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    /* Dark Theme Background */
    .stApp {
        background-color: #0E1117;
        background-image: radial-gradient(circle at 50% 0%, #1c1c2e 0%, #0E1117 70%);
        color: #E0E0E0;
    }
    
    /* Custom Scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    ::-webkit-scrollbar-track {
        background: transparent; 
    }
    ::-webkit-scrollbar-thumb {
        background: #2d2d44; 
        border-radius: 4px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: #4a4a6a; 
    }

    /* Chat Container Styling */
    .chat-container {
        display: flex;
        flex-direction: column;
        gap: 12px;
        padding: 10px;
    }

    /* Message Row (Avatar + Bubble) */
    .message-row {
        display: flex;
        align-items: flex-end;
        gap: 10px;
        margin-bottom: 8px;
        animation: fadeIn 0.3s ease-out forwards;
    }
    
    .row-right {
        flex-direction: row-reverse;
    }

    /* Avatar Circle */
    .avatar {
        width: 32px;
        height: 32px;
        border-radius: 50%;
        background: #3b3b58;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 14px;
        font-weight: 600;
        color: #fff;
        flex-shrink: 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.2);
    }
    
    .avatar-right {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }

    /* Chat Bubbles */
    .chat-bubble {
        padding: 10px 16px;
        border-radius: 18px;
        font-size: 15px;
        line-height: 1.5;
        max-width: 75%;
        position: relative;
        box-shadow: 0 2px 8px rgba(0,0,0,0.15);
        word-wrap: break-word;
    }
    
    .bubble-left {
        background-color: #262730;
        color: #e6e6e6;
        border-bottom-left-radius: 4px;
        border: 1px solid #363B47;
    }
    
    .bubble-right {
        background: linear-gradient(135deg, #007AFF 0%, #0062cc 100%);
        color: white;
        border-bottom-right-radius: 4px;
    }
    
    /* Sender Name (Tiny text above bubble) */
    .sender-name {
        font-size: 10px;
        color: #888;
        margin-bottom: 2px;
        margin-left: 4px;
    }
    
    /* Input Area Polish */
    .stTextInput > div > div > input {
        background-color: #1a1c24;
        color: white;
        border: 1px solid #363B47;
        border-radius: 12px;
        padding: 12px 15px;
        font-size: 15px;
    }
    .stTextInput > div > div > input:focus {
        border-color: #007AFF;
        box-shadow: 0 0 0 1px #007AFF;
    }
    
    /* Button Polish */
    .stButton > button {
        border-radius: 12px;
        height: 46px;
        font-weight: 600;
    }

    /* Animation Keyframes */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    /* Hide Default Header/Footer */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
</style>
""", unsafe_allow_html=True)

# --- 🔄 LOGIC SETUP ---
query_params = st.query_params
if "room" in query_params:
    room_id = query_params["room"]
else:
    room_id = str(uuid.uuid4())[:6]
    st.query_params["room"] = room_id

# Poll every 2.5s
st_autorefresh(interval=2500, key="chat_update_pulse")

# Banned Lists
BANNED_PARTIAL = ["fuck", "shit", "bitch", "idiot", "stupid", "moron", "cunt", "whore"]
BANNED_EXACT = ["ass", "die", "kill", "hate", "butt", "damn"]

# --- 🛠️ DATABASE HELPERS ---
def get_messages(room):
    url = f"{SUPABASE_URL}/rest/v1/messages?room_id=eq.{room}&select=*&order=created_at.asc"
    headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
    try:
        with httpx.Client() as client:
            r = client.get(url, headers=headers, timeout=5.0)
            if r.status_code == 200:
                return r.json()
            return []
    except:
        return []

def save_to_db(room, sender, original, rewritten, score):
    url = f"{SUPABASE_URL}/rest/v1/messages"
    headers = {
        "apikey": SUPABASE_KEY, 
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=minimal"
    }
    data = {
        "room_id": room,
        "sender": sender,
        "original_text": original,
        "rewritten_text": rewritten,
        "toxicity_score": int(score)
    }
    try:
        with httpx.Client() as client:
            client.post(url, headers=headers, json=data, timeout=5.0)
            return True
    except:
        return False

# --- ⚡ FILTER LOGIC ---
def check_message(text):
    words = text.split()
    clean_words = []
    found_bad = False
    
    for word in words:
        word_lower = word.lower()
        clean_word = word
        if word_lower in BANNED_EXACT:
            clean_word = "🤬" 
            found_bad = True
        else:
            for bad in BANNED_PARTIAL:
                if bad in word_lower:
                    clean_word = "🤬" 
                    found_bad = True
                    break
        clean_words.append(clean_word)
            
    final_text = " ".join(clean_words)
    score = 100 if found_bad else 0
    return {"rewritten": final_text, "score": score}

# --- 🎨 SIDEBAR ---
with st.sidebar:
    st.title("🛡️ AEGIS")
    st.markdown(f"<div style='background:#1a1c24; padding:10px; border-radius:8px; margin-bottom:20px; border:1px solid #363B47;'><b>Room:</b> <code style='color:#007AFF'>{room_id}</code></div>", unsafe_allow_html=True)
    
    st.caption("SETTINGS")
    username = st.text_input("Username", value="User")
    
    st.divider()
    
    if st.button("🗑️ Clear Room History", type="primary"): 
        url = f"{SUPABASE_URL}/rest/v1/messages?room_id=eq.{room_id}"
        headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
        with httpx.Client() as client:
            client.delete(url, headers=headers)
        st.rerun()

# --- 💬 MAIN CHAT AREA ---
col1, col2, col3 = st.columns([1, 8, 1])

with col2:
    # Header
    st.markdown("### 💬 Live Chat")
    
    # Message Container (Scrollable)
    messages_container = st.container(height=550, border=False)
    
    # Input Form (Fixed at bottom conceptually)
    with st.form("chat_input", clear_on_submit=True):
        col_in1, col_in2 = st.columns([8, 1])
        with col_in1:
            user_msg = st.text_input("Message", placeholder=f"Message as {username}...", label_visibility="collapsed")
        with col_in2:
            sent = st.form_submit_button("➤", type="primary")
            
        if sent and user_msg:
            analysis = check_message(user_msg)
            save_to_db(room_id, username, user_msg, analysis['rewritten'], analysis['score'])
            st.rerun()

    # Render Messages
    with messages_container:
        messages = get_messages(room_id)
        
        if not messages:
            st.markdown(
                """
                <div style='text-align:center; color:#555; margin-top:100px;'>
                    <h3>👋 Welcome to Room <span style='color:#007AFF'>""" + room_id + """</span></h3>
                    <p>Share the browser URL to invite friends.</p>
                </div>
                """, 
                unsafe_allow_html=True
            )
            
        for m in messages:
            is_me = (m['sender'] == username)
            row_class = "row-right" if is_me else "row-left"
            bubble_class = "bubble-right" if is_me else "bubble-left"
            avatar_class = "avatar-right" if is_me else "avatar-left"
            initial = m['sender'][0].upper() if m['sender'] else "?"
            
            # HTML Structure
            msg_html = f"""
            <div class="message-row {row_class}">
                <div class="avatar {avatar_class}">{initial}</div>
                <div style="display:flex; flex-direction:column;">
                    <div class="chat-bubble {bubble_class}">
                        {m['rewritten_text']}
                    </div>
                </div>
            </div>
            """
            st.markdown(msg_html, unsafe_allow_html=True)
