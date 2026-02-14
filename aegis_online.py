import streamlit as st
import httpx
from streamlit_autorefresh import st_autorefresh

# --- 🔐 CONFIGURATION ---
SUPABASE_URL = "https://vzjnqlfprmggutawcqlg.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZ6am5xbGZwcm1nZ3V0YXdjcWxnIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzEwMzUyMjcsImV4cCI6MjA4NjYxMTIyN30.vC_UxPIF7E3u0CCm3WQMpH9K2-tgJt8zG_Q4vGrPW1I"

# --- 🔄 AUTO-REFRESH ---
st_autorefresh(interval=2000, key="chat_update_pulse")

# --- 🚫 BANNED LISTS ---
# Partial Match: Blocks word even if hidden inside another (e.g. "dumb" blocks "dumbass")
BANNED_PARTIAL = ["fuck", "shit", "bitch", "idiot", "stupid", "moron", "cunt", "whore", "dumbass", "dumb", "chuthiya", "lowda", "chut", "puka", "lanja", "kojja", "lanjodaka", "gudda", "modda", "dengi", "dengu"]

# Exact Match: Blocks ONLY if it's the whole word (e.g. blocks "ass" but allows "class")
BANNED_EXACT = ["ass", "die", "kill", "hate", "butt", "damn"]

# --- 🛠️ DATABASE HELPERS ---
def get_messages():
    url = f"{SUPABASE_URL}/rest/v1/messages?select=*&order=created_at.asc"
    headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
    try:
        with httpx.Client() as client:
            r = client.get(url, headers=headers, timeout=5.0)
            if r.status_code == 200:
                return r.json()
            return []
    except:
        return []

def save_to_db(sender, original, rewritten, score):
    url = f"{SUPABASE_URL}/rest/v1/messages"
    headers = {
        "apikey": SUPABASE_KEY, 
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=minimal"
    }
    
    data = {
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

def clear_db():
    url = f"{SUPABASE_URL}/rest/v1/messages?id=gt.0"
    headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
    with httpx.Client() as client:
        client.delete(url, headers=headers)

# --- ⚡ LOGIC: SMART FILTER ---
def check_message(text):
    words = text.split()
    clean_words = []
    found_bad = False
    
    for word in words:
        word_lower = word.lower()
        clean_word = word
        
        # 1. Check Exact Match
        if word_lower in BANNED_EXACT:
            clean_word = "*" * len(word)
            found_bad = True
        
        # 2. Check Partial Match
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
st.set_page_config(page_title="AEGIS", page_icon="🛡️", layout="centered")

st.markdown("""
<style>
    .chat-bubble { padding: 12px 18px; border-radius: 12px; margin-bottom: 8px; width: fit-content; max-width: 80%; }
    .bubble-left { background-color: #F0F2F6; color: black; }
    .bubble-right { background-color: #007AFF; color: white; margin-left: auto; }
    .god-mode-box { font-size: 0.8em; color: #d32f2f; margin-top: 2px; text-align: right; font-family: monospace; }
</style>
""", unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.header("🛡️ AEGIS")
    role = st.radio("Identity", ["Person A", "Person B"])
    st.divider()
    
    # GOD MODE TOGGLE
    god_mode = False
    if role == "Person A":
        god_mode = st.toggle("God Mode (View Original)", value=False)
            
    if st.button("Clear Chat"): 
        clear_db()
        st.rerun()

# --- CHAT WINDOW ---
st.caption("Smart Filter Active")

chat_container = st.container()
with chat_container:
    messages = get_messages()
    for m in messages:
        is_me = (m['sender'] == role)
        bubble_class = "bubble-right" if is_me else "bubble-left"
        
        # 1. Show the clean message
        st.markdown(f"""
            <div class="chat-bubble {bubble_class}">
                <b>{m['sender']}</b>: {m['rewritten_text']}
            </div>
        """, unsafe_allow_html=True)
        
        # 2. God Mode: Show original if it was changed
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
        save_to_db(role, user_msg, analysis['rewritten'], analysis['score'])
        st.rerun()


