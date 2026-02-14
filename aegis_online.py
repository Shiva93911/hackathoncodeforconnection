import streamlit as st
import httpx
import uuid
import time
from streamlit_autorefresh import st_autorefresh

# --- 🔐 CONFIGURATION ---
SUPABASE_URL = "https://vzjnqlfprmggutawcqlg.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZ6am5xbGZwcm1nZ3V0YXdjcWxnIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzEwMzUyMjcsImV4cCI6MjA4NjYxMTIyN30.vC_UxPIF7E3u0CCm3WQMpH9K2-tgJt8zG_Q4vGrPW1I"

# --- 🔄 PAGE SETUP & THEME ---
st.set_page_config(page_title="AEGIS Chat", page_icon="🛡️", layout="wide")

# Custom CSS for Modern UI
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap');
    
    /* Global Styles */
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    /* Chat Container */
    .stApp {
        background: linear-gradient(135deg, #1e1e2e 0%, #2d2d44 100%);
        color: white;
    }
    
    /* Chat Bubbles */
    .chat-bubble {
        padding: 12px 18px;
        border-radius: 18px;
        margin-bottom: 10px;
        max-width: 70%;
        width: fit-content;
        position: relative;
        font-size: 15px;
        line-height: 1.4;
        box-shadow: 0 2px 5px rgba(0,0,0,0.2);
    }
    
    /* Receiver Bubble (Left) */
    .bubble-left {
        background-color: #3b3b58;
        color: #e0e0e0;
        border-bottom-left-radius: 4px;
        margin-right: auto;
    }
    
    /* Sender Bubble (Right) */
    .bubble-right {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-bottom-right-radius: 4px;
        margin-left: auto;
    }
    
    /* Sender Name Label */
    .sender-label {
        font-size: 11px;
        opacity: 0.7;
        margin-bottom: 4px;
        display: block;
    }
    
    /* Input Area Styling */
    .stTextInput > div > div > input {
        background-color: #2d2d44;
        color: white;
        border: 1px solid #4a4a6a;
        border-radius: 25px;
        padding: 10px 15px;
    }
    
    /* Hide Streamlit Elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
</style>
""", unsafe_allow_html=True)

# --- 🔄 LOGIC SETUP ---
# Get Room ID
query_params = st.query_params
if "room" in query_params:
    room_id = query_params["room"]
else:
    room_id = str(uuid.uuid4())[:6]
    st.query_params["room"] = room_id

# Auto-refresh (3s for better performance)
st_autorefresh(interval=3000, key="chat_update_pulse")

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
            clean_word = "🤬" # Emoji replacement
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
    st.caption("Secure Chat Protocol")
    st.divider()
    
    # Connection Info
    st.markdown(f"**Room ID:** `{room_id}`")
    st.info("Share the URL to invite others!")
    
    st.divider()
    
    # User Settings
    username = st.text_input("Username", value="User")
    
    if st.button("🗑️ Clear History", type="primary"): 
        # Only clears messages for THIS room
        url = f"{SUPABASE_URL}/rest/v1/messages?room_id=eq.{room_id}"
        headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
        with httpx.Client() as client:
            client.delete(url, headers=headers)
        st.rerun()

# --- 💬 MAIN CHAT AREA ---
# Create a centered container for the chat
col1, col2, col3 = st.columns([1, 6, 1])

with col2:
    st.markdown("### 💬 Live Chat")
    
    # Container for messages
    messages_container = st.container(height=500, border=False)
    
    # Input area at the bottom
    with st.form("chat_input", clear_on_submit=True):
        col_in1, col_in2 = st.columns([6, 1])
        with col_in1:
            user_msg = st.text_input("Message", placeholder="Type a message...", label_visibility="collapsed")
        with col_in2:
            sent = st.form_submit_button("➤")
            
        if sent and user_msg:
            analysis = check_message(user_msg)
            save_to_db(room_id, username, user_msg, analysis['rewritten'], analysis['score'])
            st.rerun()

    # Render Messages inside the scrollable container
    with messages_container:
        messages = get_messages(room_id)
        
        if not messages:
            st.markdown("<div style='text-align:center; color:#888; margin-top:50px;'>No messages yet.<br>Share the link to start chatting!</div>", unsafe_allow_html=True)
            
        for m in messages:
            is_me = (m['sender'] == username)
            bubble_class = "bubble-right" if is_me else "bubble-left"
            align = "right" if is_me else "left"
            
            # HTML for the message block
            msg_html = f"""
            <div style="display: flex; flex-direction: column; align-items: { 'flex-end' if is_me else 'flex-start' };">
                <div class="chat-bubble {bubble_class}">
                    <span class="sender-label">{m['sender']}</span>
                    {m['rewritten_text']}
                </div>
            </div>
            """
            
            st.markdown(msg_html, unsafe_allow_html=True)
