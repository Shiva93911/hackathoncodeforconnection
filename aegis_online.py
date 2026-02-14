import streamlit as st
import httpx
import uuid
from streamlit_autorefresh import st_autorefresh

# --- 🔐 CONFIGURATION ---
SUPABASE_URL = "https://vzjnqlfprmggutawcqlg.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZ6am5xbGZwcm1nZ3V0YXdjcWxnIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzEwMzUyMjcsImV4cCI6MjA4NjYxMTIyN30.vC_UxPIF7E3u0CCm3WQMpH9K2-tgJt8zG_Q4vGrPW1I"

# --- 🎨 PAGE SETUP ---
st.set_page_config(page_title="AEGIS", page_icon="🛡️", layout="centered")

# --- 💅 CUSTOM CSS (Styles the Native Components) ---
st.markdown("""
<style>
    /* Import Modern Font */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    /* Background - Deep Dark Blue/Grey */
    .stApp {
        background: linear-gradient(135deg, #0f172a 0%, #1e1e2e 100%);
    }

    /* Hide Header/Footer */
    header {visibility: hidden;}
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    /* Style the Chat Input */
    .stChatInput {
        padding-bottom: 20px;
    }
    
    /* Style user avatar/message container */
    [data-testid="stChatMessage"] {
        background-color: transparent;
        padding: 1rem;
        border-radius: 10px;
        transition: background-color 0.3s;
    }
    
    /* Highlight the current user's messages slightly */
    [data-testid="stChatMessage"][data-testid="user"] {
        background-color: rgba(59, 130, 246, 0.1); /* Subtle Blue Tint */
    }

    /* Status Dot Animation */
    @keyframes pulse {
        0% { opacity: 1; }
        50% { opacity: 0.5; }
        100% { opacity: 1; }
    }
    .status-dot {
        height: 10px;
        width: 10px;
        background-color: #4ade80; /* Green */
        border-radius: 50%;
        display: inline-block;
        animation: pulse 2s infinite;
        margin-right: 8px;
    }
</style>
""", unsafe_allow_html=True)

# --- 🔄 LOGIC: ROOMS & REFRESH ---
# Get Room ID from URL
query_params = st.query_params
if "room" in query_params:
    room_id = query_params["room"]
else:
    room_id = str(uuid.uuid4())[:6]
    st.query_params["room"] = room_id

# Auto-refresh every 2 seconds to pull new messages
st_autorefresh(interval=2000, key="chat_refresh")

# Banned Words List
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
            
    final_text = " ".join(clean_words)
    score = 100 if found_bad else 0
    return {"rewritten": final_text, "score": score}

# --- 📱 SIDEBAR ---
with st.sidebar:
    st.header("🛡️ AEGIS")
    st.markdown(f"**Room ID:** `{room_id}`")
    st.caption("Share the URL to invite a friend.")
    
    st.divider()
    username = st.text_input("Your Username", value="User")
    
    st.divider()
    if st.button("🗑️ Clear Room History", type="primary"): 
        url = f"{SUPABASE_URL}/rest/v1/messages?room_id=eq.{room_id}"
        headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
        with httpx.Client() as client:
            client.delete(url, headers=headers)
        st.rerun()

# --- 💬 MAIN CHAT INTERFACE ---
st.markdown("""
    <div style='display: flex; align-items: center; margin-bottom: 20px;'>
        <div class='status-dot'></div>
        <span style='color: #888; font-size: 0.9em;'>Secure Connection Live</span>
    </div>
""", unsafe_allow_html=True)

# 1. Load Messages
messages = get_messages(room_id)

# 2. Display Messages (Using Native Components for Stability)
if not messages:
    st.info("👋 No messages yet. Send one to start!")

for m in messages:
    # Determine alignment based on username
    if m['sender'] == username:
        with st.chat_message("user", avatar="⚡"):
            st.write(m['rewritten_text'])
    else:
        # Use first letter of sender as avatar
        initial = m['sender'][0].upper() if m['sender'] else "?"
        with st.chat_message(m['sender'], avatar="👤"):
            st.markdown(f"**{m['sender']}**")
            st.write(m['rewritten_text'])

# 3. Input Area (Pinned to bottom)
if prompt := st.chat_input(f"Message as {username}..."):
    # Filter the message
    analysis = check_message(prompt)
    
    # Save to Supabase
    save_to_db(room_id, username, prompt, analysis['rewritten'], analysis['score'])
    
    # Rerun immediately to show the new message
    st.rerun()
