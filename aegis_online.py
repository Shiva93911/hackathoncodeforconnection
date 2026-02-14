import streamlit as st
import httpx
import uuid
from streamlit_autorefresh import st_autorefresh

# --- 🔐 CONFIGURATION ---
SUPABASE_URL = "https://vzjnqlfprmggutawcqlg.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZ6am5xbGZwcm1nZ3V0YXdjcWxnIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzEwMzUyMjcsImV4cCI6MjA4NjYxMTIyN30.vC_UxPIF7E3u0CCm3WQMpH9K2-tgJt8zG_Q4vGrPW1I"

# --- 🎨 PAGE SETUP ---
st.set_page_config(page_title="AEGIS Chat", page_icon="🛡️", layout="centered")

# --- 💅 THE ULTIMATE ALIGNMENT CSS ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

    /* ☀️ LIGHT BLUE BACKGROUND */
    .stApp {
        background: linear-gradient(180deg, #e0f2fe 0%, #bae6fd 100%);
    }

    /* Hide Headers */
    header, #MainMenu, footer { visibility: hidden; }

    /* --- MESSAGE ALIGNMENT --- */
    
    /* Target the container for each message */
    [data-testid="stChatMessage"] {
        display: flex;
        width: 100% !important;
        background-color: transparent !important; /* Remove default grey */
        margin-bottom: 10px;
    }

    /* RIGHT SIDE: YOUR MESSAGES */
    [data-testid="stChatMessage"][data-testid="chat-message-user"] {
        flex-direction: row-reverse; /* Flip avatar and bubble */
        text-align: right;
    }
    
    [data-testid="stChatMessage"][data-testid="chat-message-user"] .stChatMessageContent {
        background-color: #0284c7 !important; /* Sky Blue 600 */
        color: white !important;
        border-radius: 18px 18px 4px 18px !important;
        margin-left: 20%; /* Push away from the left */
        padding: 12px 16px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }

    /* LEFT SIDE: OTHER MESSAGES */
    [data-testid="stChatMessage"][data-testid="chat-message-assistant"] {
        flex-direction: row;
        text-align: left;
    }

    [data-testid="stChatMessage"][data-testid="chat-message-assistant"] .stChatMessageContent {
        background-color: #ffffff !important;
        color: #1e293b !important;
        border-radius: 18px 18px 18px 4px !important;
        margin-right: 20%; /* Push away from the right */
        padding: 12px 16px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }

    /* Reply Block Quote Styling */
    blockquote {
        border-left: 3px solid #94a3b8;
        background: rgba(0,0,0,0.05);
        padding: 8px;
        margin-bottom: 8px;
        border-radius: 4px;
        font-style: italic;
        font-size: 0.85em;
        text-align: left; /* Keep quote text left-aligned even in right bubbles */
    }

    /* Style the input bar */
    .stChatInputContainer {
        padding-bottom: 20px;
    }

</style>
""", unsafe_allow_html=True)

# --- 🔄 SESSION STATE & REFRESH ---
if "reply_to" not in st.session_state:
    st.session_state.reply_to = None

# Get/Create Room
query_params = st.query_params
if "room" in query_params:
    room_id = query_params["room"]
else:
    room_id = str(uuid.uuid4())[:6]
    st.query_params["room"] = room_id

st_autorefresh(interval=2500, key="chat_refresh")

# --- 🛠️ HELPERS ---
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
    headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}", "Content-Type": "application/json"}
    data = {"room_id": room, "sender": sender, "original_text": original, "rewritten_text": rewritten, "toxicity_score": int(score)}
    try:
        with httpx.Client() as client: client.post(url, headers=headers, json=data)
    except: pass

def check_message(text):
    BANNED = ["fuck", "shit", "bitch", "idiot", "stupid", "ass", "die", "kill"]
    found = False
    words = text.split()
    clean = []
    for w in words:
        if any(b in w.lower() for b in BANNED):
            clean.append("🤬")
            found = True
        else: clean.append(w)
    return {"rewritten": " ".join(clean), "score": 100 if found else 0}

# --- 📱 SIDEBAR ---
with st.sidebar:
    st.title("🛡️ AEGIS")
    st.info(f"**Room:** {room_id}")
    username = st.text_input("Name", value="User")
    if st.button("🗑️ Clear History"):
        headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
        httpx.delete(f"{SUPABASE_URL}/rest/v1/messages?room_id=eq.{room_id}", headers=headers)
        st.rerun()

# --- 💬 CHAT AREA ---
messages = get_messages(room_id)



for i, m in enumerate(messages):
    is_me = (m['sender'] == username)
    # Native "user" aligns right, "assistant" aligns left
    role = "user" if is_me else "assistant"
    avatar = "⚡" if is_me else "👤"

    with st.chat_message(role, avatar=avatar):
        # Header for others' messages
        if not is_me:
            st.markdown(f"**{m['sender']}**")
        
        # Display the message
        st.markdown(m['rewritten_text'])
        
        # Tiny reply button
        if st.button("↩️", key=f"btn_{i}"):
            st.session_state.reply_to = {"sender": m['sender'], "text": m['rewritten_text']}
            st.rerun()

# --- ⌨️ INPUT AREA ---
if st.session_state.reply_to:
    st.info(f"↩️ Replying to {st.session_state.reply_to['sender']}")
    if st.button("❌ Cancel"):
        st.session_state.reply_to = None
        st.rerun()

if prompt := st.chat_input(f"Message as {username}..."):
    final_text = prompt
    if st.session_state.reply_to:
        # Format the reply as a markdown blockquote
        final_text = f"> {st.session_state.reply_to['text']}\n\n{prompt}"
        st.session_state.reply_to = None
        
    res = check_message(final_text)
    save_to_db(room_id, username, final_text, res['rewritten'], res['score'])
    st.rerun()
