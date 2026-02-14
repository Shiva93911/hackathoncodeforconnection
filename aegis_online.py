import streamlit as st
import httpx
import uuid
from streamlit_autorefresh import st_autorefresh

# --- 🔐 CONFIGURATION ---
SUPABASE_URL = "https://vzjnqlfprmggutawcqlg.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZ6am5xbGZwcm1nZ3V0YXdjcWxnIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzEwMzUyMjcsImV4cCI6MjA4NjYxMTIyN30.vC_UxPIF7E3u0CCm3WQMpH9K2-tgJt8zG_Q4vGrPW1I"

# --- 🎨 PAGE SETUP ---
st.set_page_config(page_title="AEGIS Light", page_icon="🛡️", layout="centered")

# --- 💅 CUSTOM CSS (Light Mode) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; color: #1e293b; }

    /* ☀️ LIGHT BLUE BACKGROUND */
    .stApp {
        background: linear-gradient(180deg, #e0f2fe 0%, #bae6fd 100%); /* Sky Blue Gradient */
    }

    /* Hide Headers */
    header, #MainMenu, footer { visibility: hidden; }

    /* Input Area Styling */
    .stChatInput { padding-bottom: 20px; }
    
    /* Input Box Background */
    .stTextInput > div > div > input {
        background-color: #ffffff;
        color: #0f172a;
        border: 1px solid #cbd5e1;
    }

    /* Message Styling */
    [data-testid="stChatMessage"] {
        padding: 1rem;
        border-radius: 12px;
        margin-bottom: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }

    /* 🔵 User Message (Blue Bubble, White Text) */
    [data-testid="stChatMessage"][data-testid="user"] {
        background-color: #0284c7; /* Sky Blue 600 */
        color: #ffffff;
        border: none;
    }
    
    /* ⚪ Peer Message (White Bubble, Dark Text) */
    [data-testid="stChatMessage"][data-testid="assistant"] {
        background-color: #ffffff;
        color: #334155; /* Slate 700 */
        border: 1px solid #e2e8f0;
    }
    
    /* Avatar Icons */
    [data-testid="stChatMessageAvatar"] {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
    }

    /* Reply Block inside message */
    blockquote {
        border-left: 3px solid #cbd5e1;
        padding-left: 10px;
        color: inherit;
        opacity: 0.8;
        font-size: 0.9em;
        margin-bottom: 8px;
        background: rgba(0,0,0,0.05);
        padding: 5px;
        border-radius: 4px;
    }
    
    /* Small Reply Button */
    div[data-testid="stButton"] > button {
        padding: 0px 8px;
        font-size: 12px;
        height: 24px;
        min-height: 24px;
        border: 1px solid #94a3b8;
        background: rgba(255,255,255,0.5);
        color: #475569;
    }
    div[data-testid="stButton"] > button:hover {
        border-color: #0284c7;
        color: #0284c7;
        background: #ffffff;
    }

</style>
""", unsafe_allow_html=True)

# --- 🔄 SESSION STATE INIT ---
if "reply_to" not in st.session_state:
    st.session_state.reply_to = None

# --- 🔄 LOGIC ---
query_params = st.query_params
if "room" in query_params:
    room_id = query_params["room"]
else:
    room_id = str(uuid.uuid4())[:6]
    st.query_params["room"] = room_id

st_autorefresh(interval=2500, key="chat_refresh")

BANNED_PARTIAL = ["fuck", "shit", "bitch", "idiot", "stupid", "moron", "cunt", "whore"]
BANNED_EXACT = ["ass", "die", "kill", "hate", "butt", "damn"]

# --- 🛠️ HELPER FUNCTIONS ---
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

def check_message(text):
    words = text.split()
    clean_words = []
    found_bad = False
    for word in words:
        if word.lower() in BANNED_EXACT:
            clean_words.append("🤬")
            found_bad = True
        else:
            is_p = False
            for bad in BANNED_PARTIAL:
                if bad in word.lower():
                    clean_words.append("🤬")
                    found_bad = True
                    is_p = True
                    break
            if not is_p: clean_words.append(word)
    return {"rewritten": " ".join(clean_words), "score": 100 if found_bad else 0}

# --- 📱 SIDEBAR ---
with st.sidebar:
    st.title("🛡️ AEGIS")
    st.markdown(f"**Room:** `{room_id}`")
    username = st.text_input("Username", value="User")
    st.divider()
    if st.button("🗑️ Clear Chat"):
        url = f"{SUPABASE_URL}/rest/v1/messages?room_id=eq.{room_id}"
        headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
        with httpx.Client() as client:
            client.delete(url, headers=headers)
        st.rerun()

# --- 💬 CHAT AREA ---
messages = get_messages(room_id)

if not messages:
    st.info("No messages yet.")

for i, m in enumerate(messages):
    is_me = (m['sender'] == username)
    role = "user" if is_me else "assistant" 
    avatar = "⚡" if is_me else "👤"

    with st.chat_message(role, avatar=avatar):
        # Header (Name + Reply Button)
        c1, c2 = st.columns([8, 1])
        with c1:
            if not is_me: st.markdown(f"**{m['sender']}**")
        with c2:
            if st.button("↩️", key=f"reply_{i}"):
                st.session_state.reply_to = f"> *Replying to {m['sender']}:* \"{m['rewritten_text']}\"\n\n"
                st.rerun()
        
        st.markdown(m['rewritten_text'])

# --- ⌨️ INPUT AREA ---
if st.session_state.reply_to:
    st.markdown(f"""
        <div style="background:#ffffff; padding:10px; border-radius:8px; margin-bottom:10px; border-left:4px solid #0284c7; box-shadow: 0 2px 4px rgba(0,0,0,0.1); display:flex; justify-content:space-between; align-items:center;">
            <span style="color:#334155; font-size:14px;">↩️ Replying...</span>
        </div>
    """, unsafe_allow_html=True)
    if st.button("❌ Cancel Reply", key="cancel_reply"):
        st.session_state.reply_to = None
        st.rerun()

if prompt := st.chat_input(f"Message as {username}..."):
    final_msg = prompt
    if st.session_state.reply_to:
        final_msg = st.session_state.reply_to + prompt
        st.session_state.reply_to = None 
        
    analysis = check_message(final_msg)
    save_to_db(room_id, username, final_msg, analysis['rewritten'], analysis['score'])
    st.rerun()
