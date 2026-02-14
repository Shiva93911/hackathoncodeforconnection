import streamlit as st
import google.generativeai as genai
import httpx
from streamlit_autorefresh import st_autorefresh

# --- 🔐 CONFIGURATION (PASTE YOUR KEYS HERE) ---
GOOGLE_API_KEY = "AIzaSyBScixlXW09c7ykg7QC7JkgYv8HTgkiiIo"
SUPABASE_URL = "https://vzjnqlfprmggutawcqlg.supabase.co"
SUPABASE_KEY =  "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZ6am5xbGZwcm1nZ3V0YXdjcWxnIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzEwMzUyMjcsImV4cCI6MjA4NjYxMTIyN30.vC_UxPIF7E3u0CCm3WQMpH9K2-tgJt8zG_Q4vGrPW1I"

# --- 🔄 AUTO-REFRESH (Set to 2 seconds for snappier feel) ---
st_autorefresh(interval=2000, key="chat_update_pulse")

# --- 🛠️ DATABASE HELPERS ---
def get_messages():
    url = f"{SUPABASE_URL}/rest/v1/messages?select=*&order=created_at.asc"
    headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
    try:
        with httpx.Client() as client:
            r = client.get(url, headers=headers, timeout=5.0)
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
    # Fire and forget (don't wait for response to speed up UI)
    try:
        with httpx.Client() as client:
            client.post(url, headers=headers, json=data, timeout=5.0)
    except:
        pass

def clear_db():
    url = f"{SUPABASE_URL}/rest/v1/messages?id=gt.0"
    headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
    with httpx.Client() as client:
        client.delete(url, headers=headers)

# --- 🧠 AI LOGIC (SPEED OPTIMIZED) ---
genai.configure(api_key=GOOGLE_API_KEY)

# Using the standard Flash model (Balance of speed and quota)
model = genai.GenerativeModel('gemini-1.5-flash') 

def aegis_rewrite(text, sender):
    # Short, punchy prompt for faster processing
    prompt = f"""
    Rewrite if rude. Keep if neutral.
    Input: "{text}"
    Output format: Clean Text || Score (0-10)
    """
    
    safety_settings = [
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
    ]

    try:
        response = model.generate_content(prompt, safety_settings=safety_settings)
        raw_text = response.text
        
        if "||" in raw_text:
            parts = raw_text.split("||")
            return {"rewritten": parts[0].strip(), "score": int(parts[1].strip()), "error": None}
        else:
            return {"rewritten": raw_text.strip(), "score": 0, "error": None}
            
    except Exception as e:
        # Fallback instantly if AI fails
        return {"rewritten": text, "score": 0, "error": str(e)}

# --- 🎨 UI DESIGN ---
st.set_page_config(page_title="AEGIS Lite", page_icon="⚡", layout="centered")

st.markdown("""
<style>
    .chat-bubble { padding: 10px 16px; border-radius: 12px; margin-bottom: 8px; width: fit-content; max-width: 80%; }
    .bubble-left { background-color: #F0F2F6; color: black; }
    .bubble-right { background-color: #007AFF; color: white; margin-left: auto; }
    .god-mode-box { font-size: 0.8em; color: #d32f2f; margin-top: 2px; text-align: right; }
</style>
""", unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.header("⚡ AEGIS Lite")
    role = st.radio("Identity", ["Person A", "Person B"])
    st.divider()
    
    god_mode = False
    if role == "Person A":
        god_mode = st.toggle("God Mode (View Original)", value=False)
            
    if st.button("Clear Chat"): 
        clear_db()
        st.rerun()

# --- CHAT ---
st.caption("High-Speed Conflict Filter")

chat_container = st.container()
with chat_container:
    messages = get_messages()
    for m in messages:
        is_me = (m['sender'] == role)
        bubble_class = "bubble-right" if is_me else "bubble-left"
        
        # Draw Message
        st.markdown(f"""
            <div class="chat-bubble {bubble_class}">
                <b>{m['sender']}</b>: {m['rewritten_text']}
            </div>
        """, unsafe_allow_html=True)
        
        # God Mode Text
        if god_mode and m['original_text'] != m['rewritten_text']:
             st.markdown(f'<div class="god-mode-box">Original: "{m["original_text"]}"</div>', unsafe_allow_html=True)

# --- INPUT ---
st.divider()
with st.form("input_form", clear_on_submit=True):
    col1, col2 = st.columns([5, 1])
    with col1:
        user_msg = st.text_input("Msg", placeholder="Type...", label_visibility="collapsed")
    with col2:
        sent = st.form_submit_button("Send")
        
    if sent and user_msg:
        analysis = aegis_rewrite(user_msg, role)
        save_to_db(role, user_msg, analysis['rewritten'], analysis['score'])
        st.rerun()

