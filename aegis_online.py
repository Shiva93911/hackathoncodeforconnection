import streamlit as st
import httpx
import uuid
import datetime
from streamlit_autorefresh import st_autorefresh

# --- 🔐 CONFIGURATION ---
SUPABASE_URL = "https://vzjnqlfprmggutawcqlg.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZ6am5xbGZwcm1nZ3V0YXdjcWxnIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzEwMzUyMjcsImV4cCI6MjA4NjYxMTIyN30.vC_UxPIF7E3u0CCm3WQMpH9K2-tgJt8zG_Q4vGrPW1I"

# --- 🎨 PAGE SETUP ---
st.set_page_config(page_title="AEGIS Premium", page_icon="🛡️", layout="centered")

# --- 🌓 THEME TOGGLE ---
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = True

# --- 💅 REFINED CSS ---
if st.session_state.dark_mode:
    bg = "linear-gradient(135deg, #0f172a 0%, #020617 100%)"
    me_bubble = "linear-gradient(135deg, #3b82f6 0%, #2563eb 100%)"
    peer_bubble = "#1e293b"
    text_main = "#f8fafc"
    text_sub = "#94a3b8"
    border = "rgba(255,255,255,0.1)"
else:
    bg = "linear-gradient(180deg, #f0f9ff 0%, #e0f2fe 100%)"
    me_bubble = "linear-gradient(135deg, #0ea5e9 0%, #0284c7 100%)"
    peer_bubble = "#ffffff"
    text_main = "#0f172a"
    text_sub = "#64748b"
    border = "rgba(0,0,0,0.05)"

st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');
    html, body, [class*="css"] {{ font-family: 'Inter', sans-serif; }}

    .stApp {{ background: {bg}; color: {text_main}; }}
    header, #MainMenu, footer {{ visibility: hidden; }}

    /* Glassmorphism Sidebar */
    [data-testid="stSidebar"] {{
        background-color: rgba(0,0,0,0.05) !important;
        backdrop-filter: blur(10px);
    }}

    /* MESSAGE ALIGNMENT & GLASS EFFECTS */
    [data-testid="stChatMessage"] {{
        display: flex;
        width: 100% !important;
        background-color: transparent !important;
        margin-bottom: 8px;
        transition: all 0.3s ease;
    }}

    /* YOUR MESSAGES (RIGHT) */
    [data-testid="stChatMessage"][data-testid="chat-message-user"] {{
        flex-direction: row-reverse;
    }}
    [data-testid="stChatMessage"][data-testid="chat-message-user"] .stChatMessageContent {{
        background: {me_bubble} !important;
        color: white !important;
        border-radius: 20px 20px 4px 20px !important;
        margin-left: 15%;
        padding: 12px 18px;
        box-shadow: 0 4px 15px rgba(37, 99, 235, 0.2);
    }}

    /* PEER MESSAGES (LEFT) */
    [data-testid="stChatMessage"][data-testid="chat-message-assistant"] {{
        flex-direction: row;
    }}
    [data-testid="stChatMessage"][data-testid="chat-message-assistant"] .stChatMessageContent {{
        background-color: {peer_bubble} !important;
        color: {text_main} !important;
        border-radius: 20px 20px 20px 4px !important;
        margin-right: 15%;
        padding: 12px 18px;
        border: 1px solid {border};
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05);
    }}

    /* TOXICITY ALERT STYLE */
    .toxic-glow {{
        border: 2px solid #ef4444 !important;
        box-shadow: 0 0 15px rgba(239, 68, 68, 0.4) !important;
    }}

    /* REPLY BANNER */
    .reply-banner {{
        background: rgba(0,0,0,0.1);
        padding: 10px;
        border-radius: 12px;
        border-left: 4px solid #3b82f6;
        margin-bottom: 10px;
        font-size: 0.85em;
    }}
</style>
""", unsafe_allow_html=True)

# --- 🔄 LOGIC ---
if "reply_to" not in st.session_state: st.session_state.reply_to = None
query_params = st.query_params
room_id = query_params.get("room", str(uuid.uuid4())[:6])
st.query_params["room"] = room_id
invite_link = f"https://aegis-chat.streamlit.app/?room={room_id}"

st_autorefresh(interval=2500, key="chat_refresh")

# --- 🛠️ HELPERS ---
def get_messages(room):
    url = f"{SUPABASE_URL}/rest/v1/messages?room_id=eq.{room}&select=*&order=created_at.asc"
    headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
    try:
        with httpx.Client() as client:
            r = client.get(url, headers=headers, timeout=5.0)
            return r.json() if r.status_code == 200 else []
    except: return []

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
            clean.append("🤬"); found = True
        else: clean.append(w)
    return {"rewritten": " ".join(clean), "score": 100 if found else 0}

# --- 📱 SIDEBAR ---
with st.sidebar:
    st.title("🛡️ AEGIS")
    st.session_state.dark_mode = st.toggle("🌙 Dark Mode", value=st.session_state.dark_mode)
    
    st.divider()
    username = st.text_input("Name", value="User", max_chars=12)
    st.text_input("Invite Link", value=invite_link, disabled=True)
    
    with st.expander("🛠️ Developer Tools"):
        st.code(open(__file__).read(), language="python")
        if st.button("🗑️ Wipe Room Data"):
            headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
            httpx.delete(f"{SUPABASE_URL}/rest/v1/messages?room_id=eq.{room_id}", headers=headers)
            st.rerun()

# --- 💬 CHAT AREA ---
st.caption(f"🛡️ SECURE ROOM: {room_id}")



messages = get_messages(room_id)
for i, m in enumerate(messages):
    is_me = (m['sender'] == username)
    role = "user" if is_me else "assistant"
    
    # Toxicity Alert: Apply CSS class if score > 0
    bubble_style = "toxic-glow" if m['toxicity_score'] > 0 else ""

    with st.chat_message(role, avatar="⚡" if is_me else "👤"):
        if not is_me: st.markdown(f"**{m['sender']}**")
        
        # Displaying with potential toxic styling
        if m['toxicity_score'] > 0:
            st.markdown(f"""<div class="toxic-glow" style="padding:10px; border-radius:10px;">{m['rewritten_text']}</div>""", unsafe_allow_html=True)
        else:
            st.markdown(m['rewritten_text'])
            
        if st.button("↩️", key=f"btn_{i}"):
            st.session_state.reply_to = {"sender": m['sender'], "text": m['rewritten_text']}
            st.rerun()

# --- ⌨️ INPUT AREA ---
if st.session_state.reply_to:
    st.markdown(f"""<div class="reply-banner">↩️ Replying to <b>{st.session_state.reply_to['sender']}</b></div>""", unsafe_allow_html=True)
    if st.button("❌ Cancel"):
        st.session_state.reply_to = None; st.rerun()

if prompt := st.chat_input(f"Message as {username}..."):
    final_text = prompt
    if st.session_state.reply_to:
        final_text = f"> {st.session_state.reply_to['text']}\n\n{prompt}"
        st.session_state.reply_to = None
    
    res = check_message(final_text)
    save_to_db(room_id, username, final_text, res['rewritten'], res['score'])
    st.rerun()
