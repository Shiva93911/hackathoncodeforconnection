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

# --- 🎨 PRO-TIER CSS STYLING ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');
    
    /* Global Reset & Font */
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    /* Deep Space Background */
    .stApp {
        background-color: #09090b;
        background-image: 
            radial-gradient(at 0% 0%, rgba(56, 189, 248, 0.1) 0px, transparent 50%), 
            radial-gradient(at 100% 100%, rgba(139, 92, 246, 0.1) 0px, transparent 50%);
    }

    /* Custom Scrollbar for Containers */
    ::-webkit-scrollbar {
        width: 6px;
        background: transparent;
    }
    ::-webkit-scrollbar-thumb {
        background: #27272a;
        border-radius: 10px;
    }

    /* --- CHAT BUBBLES --- */
    .message-row {
        display: flex;
        gap: 12px;
        margin-bottom: 16px;
        animation: slideIn 0.25s ease-out forwards;
        opacity: 0;
        transform: translateY(10px);
    }
    
    @keyframes slideIn {
        to { opacity: 1; transform: translateY(0); }
    }

    .row-reverse {
        flex-direction: row-reverse;
    }

    /* Avatars */
    .avatar {
        width: 36px;
        height: 36px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 600;
        font-size: 14px;
        color: white;
        flex-shrink: 0;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    .avatar-user { background: linear-gradient(135deg, #6366f1, #8b5cf6); } /* Indigo-Purple */
    .avatar-peer { background: linear-gradient(135deg, #3f3f46, #52525b); } /* Zinc */

    /* Bubble Styling */
    .bubble {
        padding: 12px 16px;
        border-radius: 20px;
        font-size: 15px;
        line-height: 1.5;
        max-width: 600px;
        position: relative;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    
    .bubble-user {
        background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
        color: white;
        border-bottom-right-radius: 4px;
    }
    
    .bubble-peer {
        background-color: #27272a;
        color: #e4e4e7;
        border: 1px solid #3f3f46;
        border-bottom-left-radius: 4px;
    }

    /* Name Label */
    .name-label {
        font-size: 11px;
        color: #a1a1aa;
        margin-bottom: 4px;
        margin-left: 2px;
    }

    /* Input Field Polish */
    .stTextInput > div > div > input {
        background-color: #18181b;
        color: white;
        border: 1px solid #27272a;
        border-radius: 12px;
        padding: 12px 16px;
        font-size: 15px;
        transition: all 0.2s;
    }
    .stTextInput > div > div > input:focus {
        border-color: #6366f1;
        box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.2);
    }
    
    /* Button Polish */
    div[data-testid="stFormSubmitButton"] > button {
        border-radius: 12px;
        background-color: #4f46e5;
        color: white;
        border: none;
        height: 48px;
        transition: transform 0.1s;
    }
    div[data-testid="stFormSubmitButton"] > button:hover {
        background-color: #4338ca;
        transform: scale(1.02);
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
    st.markdown(f"""
        <div style='background:#18181b; padding:12px; border-radius:12px; border:1px solid #27272a; margin-bottom:24px;'>
            <div style='font-size:10px; color:#a1a1aa; text-transform:uppercase; letter-spacing:1px; margin-bottom:4px;'>Current Room</div>
            <code style='font-size:18px; color:#818cf8; font-weight:600;'>{room_id}</code>
        </div>
    """, unsafe_allow_html=True)
    
    st.caption("IDENTITY")
    username = st.text_input("Display Name", value="User")
    
    st.divider()
    
    if st.button("🗑️ Clear Room", type="primary"): 
        url = f"{SUPABASE_URL}/rest/v1/messages?room_id=eq.{room_id}"
        headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
        with httpx.Client() as client:
            client.delete(url, headers=headers)
        st.rerun()

# --- 💬 MAIN CHAT AREA ---
col1, col2, col3 = st.columns([1, 8, 1])

with col2:
    # --- HEADER ---
    st.markdown("""
        <div style="display:flex; align-items:center; margin-bottom:20px;">
            <div style="width:10px; height:10px; background:#4ade80; border-radius:50%; margin-right:10px; box-shadow:0 0 10px #4ade80;"></div>
            <h3 style="margin:0; padding:0;">Live Chat</h3>
        </div>
    """, unsafe_allow_html=True)
    
    # --- MESSAGE CONTAINER ---
    # Using a fixed height container for the chat history
    messages_container = st.container(height=550)
    
    # --- INPUT AREA ---
    # Placed below the chat container
    with st.form("chat_input", clear_on_submit=True):
        col_in1, col_in2 = st.columns([8, 1])
        with col_in1:
            user_msg = st.text_input("Message", placeholder=f"Type message as {username}...", label_visibility="collapsed")
        with col_in2:
            sent = st.form_submit_button("➤", type="primary")
            
        if sent and user_msg:
            analysis = check_message(user_msg)
            save_to_db(room_id, username, user_msg, analysis['rewritten'], analysis['score'])
            st.rerun()

    # --- RENDER MESSAGES ---
    with messages_container:
        messages = get_messages(room_id)
        
        if not messages:
            st.markdown(
                """
                <div style='display:flex; flex-direction:column; align-items:center; justify-content:center; height:100%; color:#52525b;'>
                    <div style='font-size:48px; margin-bottom:10px;'>👋</div>
                    <div style='font-weight:500;'>No messages yet</div>
                    <div style='font-size:12px;'>Be the first to say hello!</div>
                </div>
                """, 
                unsafe_allow_html=True
            )
            
        for m in messages:
            is_me = (m['sender'] == username)
            
            # Dynamic Classes based on sender
            row_class = "row-reverse" if is_me else ""
            bubble_class = "bubble-user" if is_me else "bubble-peer"
            avatar_class = "avatar-user" if is_me else "avatar-peer"
            
            # Get Initials
            initial = m['sender'][0].upper() if m['sender'] else "?"
            
            # HTML Construction
            msg_html = f"""
            <div class="message-row {row_class}">
                <div class="avatar {avatar_class}">{initial}</div>
                
                <div style="display:flex; flex-direction:column; align-items: {'flex-end' if is_me else 'flex-start'};">
                    <span class="name-label">{m['sender']}</span>
                    <div class="bubble {bubble_class}">
                        {m['rewritten_text']}
                    </div>
                </div>
            </div>
            """
            st.markdown(msg_html, unsafe_allow_html=True)
