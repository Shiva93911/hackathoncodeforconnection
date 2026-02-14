import streamlit as st
import google.generativeai as genai
import httpx
import json
from streamlit_autorefresh import st_autorefresh

# --- 🔐 CONFIGURATION (PASTE YOUR KEYS HERE) ---
GOOGLE_API_KEY = "AIzaSyCqkhmUDXiQiqosXxM1RlFTUHBSeQB280A"
SUPABASE_URL = "https://vzjnqlfprmggutawcqlg.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZ6am5xbGZwcm1nZ3V0YXdjcWxnIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzEwMzUyMjcsImV4cCI6MjA4NjYxMTIyN30.vC_UxPIF7E3u0CCm3WQMpH9K2-tgJt8zG_Q4vGrPW1I"

# --- 🔄 AUTO-REFRESH ---
# Checks for new messages every 3 seconds for a faster feel
st_autorefresh(interval=3000, key="chat_update_pulse")

# --- 🛠️ DATABASE HELPERS ---
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
# Using the 2.0-flash model which is fast and smart
model = genai.GenerativeModel('gemini-2.0-flash')

def aegis_rewrite(text, sender):
    prompt = f"""
    You are AEGIS.
    Analyze this message: "{text}"
    1. If it is rude, aggressive, or toxic: Rewrite it to be polite and professional.
    2. If it is already okay: Return it EXACTLY as is.
    3. Score toxicity 0-100.
    Return JSON: {{"rewritten": "string", "score": int}}
    """
    try:
        response = model.generate_content(prompt, generation_config={"response_mime_type": "application/json"})
        return json.loads(response.text)
    except Exception:
        return {"rewritten": text, "score": 0}

# --- 🎨 UI DESIGN ---
st.set_page_config(page_title="AEGIS: Silent Shield", page_icon="🛡️", layout="centered")

st.markdown("""
<style>
    .chat-bubble { padding: 12px 18px; border-radius: 18px; margin-bottom: 8px; width: fit-content; max-width: 80%; font-size: 16px; line-height: 1.4; }
    .bubble-left { background-color: #F2F4F8; color: #1a1a1a; align-self: flex-start; border-bottom-left-radius: 4px; }
    .bubble-right { background-color: #007AFF; color: white; margin-left: auto; border-bottom-right-radius: 4px; }
    .sender-name { font-size: 0.75em; color: #666; margin-bottom: 2px; display: block; }
    
    /* God Mode Styles */
    .god-mode-box { background-color: #fff0f0; border-left: 3px solid #ff4444; padding: 5px 10px; margin-top: 5px; border-radius: 4px; font-size: 0.8em; color: #555; }
    .raw-label { font-weight: bold; color: #d32f2f; font-size: 0.9em; }
</style>
""", unsafe_allow_html=True)

# --- SIDEBAR & SETTINGS ---
with st.sidebar:
    st.header("🛡️ AEGIS Config")
    
    # Role Selection
    role = st.radio("Identity", ["Person A", "Person B"])
    
    st.divider()
    
    # GOD MODE (Only visible if you are Person A)
    god_mode = False
    if role == "Person A":
        st.subheader("Admin Controls")
        god_mode = st.toggle("👁️ God Mode (See Hidden Texts)", value=False)
        if god_mode:
            st.caption("Now seeing the raw, toxic messages.")
            
    st.divider()
    if st.button("🗑️ Wipe Conversation"): 
        clear_db()
        st.rerun()

# --- MAIN CHAT HEADER ---
st.title("🛡️ AEGIS")
if god_mode:
    st.caption("⚠️ GOD MODE ACTIVE: You can see what they REALLY typed.")
else:
    st.caption("Seamless Conflict Filtering")

# --- 💬 CHAT LOGIC ---
messages = get_messages()
chat_container = st.container()

with chat_container:
    for m in messages:
        is_me = (m['sender'] == role)
        
        # 1. Determine Styling
        bubble_class = "bubble-right" if is_me else "bubble-left"
        align_style = "right" if is_me else "left"
        
        # 2. Check if text was changed by AI
        was_changed = m['original_text'] != m['rewritten_text']
        
        # 3. Render the Main Bubble (The Clean Version)
        # Everyone sees this. It looks normal. No scolding.
        st.markdown(f"""
            <div style="display:flex; flex-direction:column; align-items:flex-{list(['start','end'])[is_me]};">
                <span class="sender-name">{m['sender']}</span>
                <div class="chat-bubble {bubble_class}">
                    {m['rewritten_text']}
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        # 4. God Mode Injection (Only if enabled AND text was changed)
        if god_mode and was_changed:
            st.markdown(f"""
                <div style="text-align:{align_style}; margin-bottom: 15px; width: fit-content; margin-left:{'auto' if is_me else '0'};">
                    <div class="god-mode-box">
                        <span class="raw-label">👁️ ORIGINAL (Hidden):</span><br>
                        "{m['original_text']}"
                    </div>
                </div>
            """, unsafe_allow_html=True)
        else:
            # Add a little spacer if no God Mode box
            st.markdown('<div style="margin-bottom: 10px;"></div>', unsafe_allow_html=True)

# --- ⌨️ INPUT AREA ---
# Fixed at bottom (optional styling choice, but standard form works best for Streamlit)
st.divider()
with st.form("input_form", clear_on_submit=True):
    col1, col2 = st.columns([5, 1])
    with col1:
        user_msg = st.text_input("Message", placeholder=f"Type as {role}...", label_visibility="collapsed")
    with col2:
        sent = st.form_submit_button("Send 🚀")
        
    if sent and user_msg:
        # No spinner needed for silent filtering, feels faster
        analysis = aegis_rewrite(user_msg, role)
        save_to_db(role, user_msg, analysis['rewritten'], analysis['score'])
        st.rerun()
