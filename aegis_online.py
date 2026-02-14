import streamlit as st
import google.generativeai as genai
import httpx
import json
from streamlit_autorefresh import st_autorefresh

# --- 🔐 CONFIGURATION (PASTE YOUR KEYS HERE) ---
# Get these from your Google AI Studio and Supabase Dashboard
GOOGLE_API_KEY = "AIzaSyCqkhmUDXiQiqosXxM1RlFTUHBSeQB280A"
SUPABASE_URL = "https://vzjnqlfprmggutawcqlg.supabase.co"
SUPABASE_KEY"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZ6am5xbGZwcm1nZ3V0YXdjcWxnIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzEwMzUyMjcsImV4cCI6MjA4NjYxMTIyN30.vC_UxPIF7E3u0CCm3WQMpH9K2-tgJt8zG_Q4vGrPW1I"

# --- 🔄 AUTO-REFRESH ---
# This pulls new messages from the database every 5 seconds
st_autorefresh(interval=5000, key="chat_update_pulse")

# --- 🛠️ DATABASE HELPERS (Using HTTPX for no-error installs) ---
def get_messages():
    url = f"{SUPABASE_URL}/rest/v1/messages?select=*&order=created_at.asc"
    headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
    try:
        with httpx.Client() as client:
            r = client.get(url, headers=headers)
            return r.json()
    except Exception:
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
        "toxicity_score": score
    }
    with httpx.Client() as client:
        client.post(url, headers=headers, json=data)

def clear_db():
    url = f"{SUPABASE_URL}/rest/v1/messages?id=gt.0"
    headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
    with httpx.Client() as client:
        client.delete(url, headers=headers)

# --- 🧠 AI LOGIC ---
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash')

def aegis_rewrite(text, sender):
    prompt = f"""
    You are AEGIS, a conflict de-escalation shield. 
    Analyze this message from {sender}: "{text}"
    Rules:
    1. If toxic/rude, rewrite to be professional and calm.
    2. If neutral, return exactly as is.
    3. Score toxicity 0-100.
    Return JSON: {{"rewritten": "string", "score": int, "changed": bool}}
    """
    try:
        response = model.generate_content(prompt, generation_config={"response_mime_type": "application/json"})
        return json.loads(response.text)
    except Exception:
        return {"rewritten": text, "score": 0, "changed": False}

# --- 🎨 UI DESIGN ---
st.set_page_config(page_title="AEGIS: Conflict Shield", page_icon="🛡️", layout="centered")

st.markdown("""
<style>
    .chat-bubble { padding: 12px; border-radius: 15px; margin-bottom: 10px; width: fit-content; max-width: 85%; box-shadow: 1px 1px 3px rgba(0,0,0,0.1); }
    .bubble-left { background-color: #F0F2F6; align-self: flex-start; border-bottom-left-radius: 2px; }
    .bubble-right { background-color: #DCF8C6; margin-left: auto; border-bottom-right-radius: 2px; }
    .toxic-pill { color: #D32F2F; font-size: 0.75em; font-weight: bold; background: #FFEBEE; padding: 2px 6px; border-radius: 4px; margin-top: 5px; display: block; }
    .strike { text-decoration: line-through; color: #999; }
</style>
""", unsafe_allow_html=True)

# Header
st.title("🛡️ AEGIS")
st.caption("Real-time de-escalation for difficult conversations.")

# Sidebar Settings
with st.sidebar:
    st.header("Identify Yourself")
    role = st.radio("Choose your side:", ["Person A", "Person B"])
    st.divider()
    if st.button("🗑️ Clear Chat History"): 
        clear_db()
        st.rerun()
    st.info(f"Connected as {role}. App refreshes every 5s.")

# --- 💬 CHAT DISPLAY ---
messages = get_messages()
chat_container = st.container()

with chat_container:
    for m in messages:
        is_my_msg = (m['sender'] == role)
        bubble_style = "bubble-right" if is_my_msg else "bubble-left"
        
        st.markdown(f"""
            <div class="chat-bubble {bubble_style}">
                <small><b>{m['sender']}</b></small><br>
                {m['rewritten_text']}
            </div>
        """, unsafe_allow_html=True)
        
        # Show "Aegis Shield" notice if message was modified
        if m['original_text'] != m['rewritten_text']:
            st.markdown(f"""
                <div style="text-align: {'right' if is_my_msg else 'left'}; margin-top: -10px; margin-bottom: 15px;">
                    <span class="toxic-pill">🛡️ Filtered: <span class="strike">"{m['original_text']}"</span> (Score: {m['toxicity_score']})</span>
                </div>
            """, unsafe_allow_html=True)

# --- ⌨️ INPUT AREA ---
st.divider()
with st.form("message_input", clear_on_submit=True):
    user_text = st.text_input(f"Sending as {role}...", placeholder="Type something...")
    if st.form_submit_button("Send to Bridge 🚀"):
        if user_text:
            with st.spinner("AEGIS is shielding..."):
                analysis = aegis_rewrite(user_text, role)
                save_to_db(role, user_text, analysis['rewritten'], analysis['score'])
                st.rerun()