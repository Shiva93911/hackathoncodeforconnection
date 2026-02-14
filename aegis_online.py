import streamlit as st
import httpx
import uuid
from streamlit_autorefresh import st_autorefresh

# --- 🔐 CONFIGURATION ---
SUPABASE_URL = "https://vzjnqlfprmggutawcqlg.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZ6am5xbGZwcm1nZ3V0YXdjcWxnIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzEwMzUyMjcsImV4cCI6MjA4NjYxMTIyN30.vC_UxPIF7E3u0CCm3WQMpH9K2-tgJt8zG_Q4vGrPW1I"

# --- 🎨 PAGE CONFIG ---
st.set_page_config(page_title="AEGIS", page_icon="🛡️", layout="centered")

# --- 💅 CUSTOM CSS ---
st.markdown("""
<style>
    /* Global Font */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

    /* Hide Default Header/Footer */
    header {visibility: hidden;}
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    /* Chat Container Spacing */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 10rem; /* Space for input bar */
    }

    /* Message Row */
    .chat-row {
        display: flex;
        align-items: flex-end;
        margin-bottom: 12px;
        width: 100%;
        animation: fadeIn 0.3s ease-out;
    }

    /* Alignment */
    .row-right { flex-direction: row-reverse; }
    .row-left { flex-direction: row; }

    /* Avatar */
    .avatar {
        width: 35px;
        height: 35px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: bold;
        color: white;
        font-size: 14px;
        flex-shrink: 0;
        box-shadow: 0 2px 5px rgba(0,0,0,0.2);
    }
    .av-right { background: linear-gradient(135deg, #007AFF, #00C6FF); margin-left: 10px; }
    .av-left { background: #3A3D4A; margin-right: 10px; }

    /* Bubbles */
    .bubble {
        padding: 12px 16px;
        border-radius: 18px;
        font-size: 15px;
        line-height: 1.4;
        max-width: 75%;
        position: relative;
        box-shadow: 0 1px 2px rgba(0,0,0,0.1);
        word-wrap: break-word;
    }
    
    /* User Bubble (Right) */
    .bubble-right {
        background: #007AFF; /* iMessage Blue */
        color: white;
        border-bottom-right-radius: 4px;
    }
    
    /* Peer Bubble (Left) */
    .bubble-left {
        background: #262629; /* Dark Grey */
        color: #E9E9EB;
        border: 1px solid #3A3D4A;
        border-bottom-left-radius: 4px;
    }
    
    /* Sender Name */
    .sender-name {
        font-size: 11px;
        color: #888;
        margin-bottom: 4px;
    }

    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
</style>
""", unsafe_allow_html=True)

# --- 🔄 LOGIC ---
query_params = st.query_params
if "room" in query_params:
    room_id = query_params["room"]
else:
    room_id = str(uuid.uuid4())[:6]
    st.query_params["room"] = room_id

# Auto-refresh every 2s
st_autorefresh(interval=2000, key="chat_refresh")

# Banned Words
BANNED_PARTIAL = ["fuck", "shit", "bitch", "idiot", "stupid", "moron", "cunt", "whore"]
BANNED_EXACT = ["ass", "die", "kill", "hate", "butt", "damn"]

# --- 🛠️ DATABASE ---
def get_messages(room):
    url = f"{SUPABASE_URL}/rest/v1/messages?room_id=eq.{room}&select=*&order=created_at.asc"
    headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
    try:
        with httpx.Client() as client:
            r = client.get(url, headers=headers, timeout=5.0)
            return r.json() if r.status_code == 200 else []
    except:
        return []

def save_to_db(room, sender, original, rewritten, score):
    url = f"{SUPABASE_URL}/rest/v1/messages"
    headers = {
        "apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json", "Prefer": "return=minimal"
    }
    data = {
        "room_id": room, "sender": sender,
        "original_text": original, "rewritten_text": rewritten,
        "toxicity_score": int(score)
    }
    try:
        with httpx.Client() as client:
            client.post(url, headers=headers, json=data, timeout=5.0)
    except:
        pass

# --- ⚡ FILTER ---
def check_message(text):
    words = text.split()
    clean_words = []
    found_bad = False
    for word in words:
        word_lower = word.lower()
        if word_lower in BANNED_EXACT:
            clean_words.append("🤬")
            found_bad = True
        else:
            is_partial = False
            for bad in BANNED_PARTIAL:
                if bad in word_lower:
                    clean_words.append("🤬")
                    found_bad = True
                    is_partial = True
                    break
            if not is_partial:
                clean_words.append(word)
    return {"rewritten": " ".join(clean_words), "score": 100 if found_bad else 0}

# --- 📱 SIDEBAR ---
with st.sidebar:
    st.header("🛡️ AEGIS")
    st.caption(f"Room: {room_id}")
    username = st.text_input("Username", value="User")
    st.divider()
    if st.button("Clear Chat", type="primary"):
        url = f"{SUPABASE_URL}/rest/v1/messages?room_id=eq.{room_id}"
        headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
        with httpx.Client() as client:
            client.delete(url, headers=headers)
        st.rerun()

# --- 💬 CHAT AREA ---
# 1. Fetch
messages = get_messages(room_id)

# 2. Render
if not messages:
    st.markdown(f"<div style='text-align:center; color:#666; margin-top:50px;'>No messages in Room {room_id}</div>", unsafe_allow_html=True)

for m in messages:
    is_me = (m['sender'] == username)
    row_cls = "row-right" if is_me else "row-left"
    bubble_cls = "bubble-right" if is_me else "bubble-left"
    av_cls = "av-right" if is_me else "av-left"
    initial = m['sender'][0].upper() if m['sender'] else "?"
    
    # HTML Block
    html = f"""
    <div class="chat-row {row_cls}">
        <div class="avatar {av_cls}">{initial}</div>
        <div style="display:flex; flex-direction:column; align-items: {'flex-end' if is_me else 'flex-start'}; width: 100%;">
            <span class="sender-name">{m['sender']}</span>
            <div class="bubble {bubble_cls}">{m['rewritten_text']}</div>
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

# 3. Input
if prompt := st.chat_input("Type a message..."):
    res = check_message(prompt)
    save_to_db(room_id, username, prompt, res['rewritten'], res['score'])
    st.rerun()
