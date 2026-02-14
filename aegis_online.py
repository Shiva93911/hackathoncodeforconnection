import streamlit as st
import httpx
import uuid
from streamlit_autorefresh import st_autorefresh

# --- 🔐 CONFIGURATION ---
SUPABASE_URL = "https://vzjnqlfprmggutawcqlg.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZ6am5xbGZwcm1nZ3V0YXdjcWxnIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzEwMzUyMjcsImV4cCI6MjA4NjYxMTIyN30.vC_UxPIF7E3u0CCm3WQMpH9K2-tgJt8zG_Q4vGrPW1I"

# --- 🚫 BANNED LISTS ---
BANNED_PARTIAL = ["fuck", "shit", "bitch", "idiot", "stupid", "moron", "cunt", "whore", "chutiya" , "puk" ,"lanj" , "P U k" , "kojja", "k o j ","munda", "m u n"]
BANNED_EXACT = ["ass", "die", "kill", "hate", "butt", "damn"]

# --- 🔄 PAGE SETUP & ROOM ID ---
st.set_page_config(page_title="AEGIS Connect", page_icon="🛡️", layout="centered")

# Get Room ID from URL or Create New One
query_params = st.query_params
if "room" in query_params:
    room_id = query_params["room"]
else:
    room_id = str(uuid.uuid4())[:8] # Generate a short random ID
    st.query_params["room"] = room_id

# Auto-refresh to pull new messages
st_autorefresh(interval=2000, key="chat_update_pulse")

# --- 🛠️ DATABASE HELPERS ---
def get_messages(room):
    # FILTER: Only get messages for THIS room_id
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
        "room_id": room,   # Save to specific room
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

# --- ⚡ LOGIC: SMART FILTER ---
def check_message(text):
    words = text.split()
    clean_words = []
    found_bad = False
    
    for word in words:
        word_lower = word.lower()
        clean_word = word
        if word_lower in BANNED_EXACT:
            clean_word = "*" * len(word)
            found_bad = True
        else:
            for bad in BANNED_PARTIAL:
                if bad in word_lower:
                    clean_word = "*" * len(word)
                    found_bad = True
                    break
        clean_words.append(clean_word)
            
    final_text = " ".join(clean_words)
    score = 100 if found_bad else 0
    return {"rewritten": final_text, "score": score}

# --- 🎨 UI DESIGN ---
st.markdown("""
<style>
    .chat-bubble { padding: 12px 18px; border-radius: 12px; margin-bottom: 8px; width: fit-content; max-width: 80%; }
    .bubble-left { background-color: #F0F2F6; color: black; }
    .bubble-right { background-color: #007AFF; color: white; margin-left: auto; }
    .god-mode-box { font-size: 0.8em; color: #d32f2f; margin-top: 2px; text-align: right; font-family: monospace; }
</style>
""", unsafe_allow_html=True)

# --- SIDEBAR: CONNECTIVITY ---
with st.sidebar:
    st.header("🔗 Invite a Friend")
    st.caption("Send this link to someone to chat with them privately.")
    
    # Show the current URL (Constructed manually because Streamlit local varies)
    st.code(f"?room={room_id}", language="text")
    st.info("Copy the URL from your browser address bar!")
    
    st.divider()
    
    # Identity Choice
    username = st.text_input("Your Name", value="Anonymous")
    
    # God Mode (Only for "Admin" or specific user check)
    god_mode = st.toggle("God Mode (View Original)", value=False)
            
    if st.button("New Room"): 
        st.query_params.clear()
        st.rerun()

# --- CHAT WINDOW ---
st.caption(f"Connected to Room: {room_id}")

chat_container = st.container()
with chat_container:
    messages = get_messages(room_id)
    
    if not messages:
        st.markdown("*Waiting for someone to join...*")
        
    for m in messages:
        is_me = (m['sender'] == username)
        bubble_class = "bubble-right" if is_me else "bubble-left"
        
        st.markdown(f"""
            <div class="chat-bubble {bubble_class}">
                <b>{m['sender']}</b>: {m['rewritten_text']}
            </div>
        """, unsafe_allow_html=True)
        
        if god_mode and m['original_text'] != m['rewritten_text']:
             st.markdown(f'<div class="god-mode-box">Original: "{m["original_text"]}"</div>', unsafe_allow_html=True)

# --- INPUT AREA ---
st.divider()
with st.form("input_form", clear_on_submit=True):
    col1, col2 = st.columns([5, 1])
    with col1:
        user_msg = st.text_input("Msg", placeholder="Type...", label_visibility="collapsed")
    with col2:
        sent = st.form_submit_button("Send")
        
    if sent and user_msg:
        analysis = check_message(user_msg)
        save_to_db(room_id, username, user_msg, analysis['rewritten'], analysis['score'])
        st.rerun()




