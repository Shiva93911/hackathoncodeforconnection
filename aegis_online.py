import streamlit as st
import httpx
import uuid
import time
from streamlit_autorefresh import st_autorefresh

# --- 🔐 CONFIGURATION ---
SUPABASE_URL = "https://vzjnqlfprmggutawcqlg.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZ6am5xbGZwcm1nZ3V0YXdjcWxnIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzEwMzUyMjcsImV4cCI6MjA4NjYxMTIyN30.vC_UxPIF7E3u0CCm3WQMpH9K2-tgJt8zG_Q4vGrPW1I"

# --- 🎨 PAGE SETUP ---
st.set_page_config(page_title="AEGIS Chat", page_icon="🛡️", layout="centered")

# --- CUSTOM CSS (Just for polish, not layout) ---
st.markdown("""
<style>
    /* Import Font */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    /* Hide standard headers */
    header {visibility: hidden;}
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Subtle background gradient */
    .stApp {
        background: linear-gradient(180deg, #0e1117 0%, #161b22 100%);
    }
    
    /* Customize the chat input container */
    .stChatInput {
        padding-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)

# --- 🔄 LOGIC SETUP ---
query_params = st.query_params
if "room" in query_params:
    room_id = query_params["room"]
else:
    room_id = str(uuid.uuid4())[:6]
    st.query_params["room"] = room_id

# Poll for new messages every 3 seconds
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

# --- 📱 SIDEBAR ---
with st.sidebar:
    st.title("🛡️ AEGIS")
    st.info(f"Room: {room_id}")
    st.divider()
    
    username = st.text_input("Your Name", value="User")
    
    st.divider()
    if st.button("Clear Room History", type="primary"): 
        url = f"{SUPABASE_URL}/rest/v1/messages?room_id=eq.{room_id}"
        headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
        with httpx.Client() as client:
            client.delete(url, headers=headers)
        st.rerun()

# --- 💬 MAIN CHAT INTERFACE ---
st.markdown("### 💬 Live Chat")

# 1. Load History
messages = get_messages(room_id)

# 2. Display History (Using Native Streamlit Chat)
if not messages:
    st.markdown(
        """
        <div style='text-align:center; color:#555; margin-top:50px; margin-bottom:50px;'>
            <p>No messages yet. Be the first to say hi!</p>
        </div>
        """, unsafe_allow_html=True
    )

for m in messages:
    is_me = (m['sender'] == username)
    
    # Choose avatar based on sender
    avatar_icon = "👤"
    if is_me:
        avatar_icon = "⚡"
    
    # Render using native components
    with st.chat_message(m['sender'], avatar=avatar_icon):
        st.write(m['rewritten_text'])

# 3. Chat Input (Fixed at bottom)
if prompt := st.chat_input(f"Message as {username}..."):
    # Filter
    analysis = check_message(prompt)
    
    # Save
    save_to_db(room_id, username, prompt, analysis['rewritten'], analysis['score'])
    
    # Rerun to show new message immediately
    st.rerun()
