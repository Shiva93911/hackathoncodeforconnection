import streamlit as st
from google.cloud import firestore
from google.oauth2 import service_account
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import HumanMessage, SystemMessage
import json
import time
import random

# --- CONFIG ---
st.set_page_config(page_title="Global Perspective Swapper", page_icon="🌎")

# --- AUTHENTICATION (Firebase & Gemini) ---
# In a real app, use st.secrets. For hackathon, we load locally.
try:
    # Load Firebase
    key_dict = json.load(open("firestore_key.json"))
    creds = service_account.Credentials.from_service_account_info(key_dict)
    db = firestore.Client(credentials=creds)
    st.sidebar.success("✅ Connected to Cloud Database")
except:
    st.error("❌ firestore_key.json not found! Download it from Firebase Console.")
    st.stop()

gemini_key = st.sidebar.text_input("Enter Google API Key (Gemini)", type="password")

# --- AI LOGIC ---
def filter_message(text):
    if not gemini_key: return text, False
    
    llm = ChatGoogleGenerativeAI(model="gemini-pro", google_api_key=gemini_key)
    prompt = f"""
    Rewrite this message to be constructive and polite. If it's already polite, return it unchanged.
    Message: "{text}"
    Return ONLY the rewritten text.
    """
    try:
        response = llm.invoke([HumanMessage(content=prompt)])
        return response.content, True
    except:
        return text, False

# --- UI & CONNECTION ---
st.title("🌎 Global Connection Bot")
st.caption("Connect with a stranger. The AI ensures the chat stays civil.")

# 1. LOBBY SYSTEM
if "room_id" not in st.session_state:
    st.subheader("Join a Room")
    col1, col2 = st.columns(2)
    with col1:
        username = st.text_input("Pick a Username", "Anon")
    with col2:
        room_choice = st.text_input("Enter Room Name (e.g., 'hackathon')", "hackathon")
    
    if st.button("Connect to Room"):
        st.session_state.room_id = room_choice
        st.session_state.username = username
        st.rerun()

# 2. CHAT ROOM
else:
    room_ref = db.collection("chat_rooms").document(st.session_state.room_id)
    
    # Header
    st.write(f"🟢 Connected to Room: **{st.session_state.room_id}** as *{st.session_state.username}*")
    if st.button("Leave Room"):
        del st.session_state.room_id
        st.rerun()
    
    st.divider()

    # 3. DISPLAY MESSAGES (Real-time polling)
    # Streamlit isn't auto-push, so we use a container that refreshes
    chat_container = st.empty()
    
    # We read the doc. Ideally use a snapshot listener, but polling is easier for Streamlit
    doc = room_ref.get()
    if doc.exists:
        data = doc.to_dict()
        messages = data.get("messages", [])
        
        with chat_container.container():
            for msg in messages:
                align = "text-align: right; background: #e6f3ff;" if msg['user'] == st.session_state.username else "text-align: left; background: #f0f0f0;"
                st.markdown(f"""
                <div style='{align}; padding: 10px; border-radius: 10px; margin: 5px; width: fit-content; max-width: 80%; margin-left: auto if "{align}" == "right" else 0;'>
                    <small><b>{msg['user']}</b></small><br>
                    {msg['text']}
                </div>
                """, unsafe_allow_html=True)
    else:
        # Create room if doesn't exist
        room_ref.set({"messages": []})
        st.info("Room created. Waiting for others...")

    # 4. SEND INPUT
    with st.form("chat_form", clear_on_submit=True):
        user_msg = st.text_input("Type your message...")
        submitted = st.form_submit_button("Send")
        
        if submitted and user_msg:
            # AI INTERVENTION HERE
            with st.spinner("AI is reviewing your tone..."):
                final_text, was_changed = filter_message(user_msg)
            
            # Send to Cloud
            new_msg_packet = {
                "user": st.session_state.username,
                "text": final_text,
                "timestamp": time.time()
            }
            
            # Atomic update to array
            room_ref.update({
                "messages": firestore.ArrayUnion([new_msg_packet])
            })
            
            if was_changed and final_text != user_msg:
                st.toast(f"AI rewrote your message to be nicer!", icon="🤖")
            
            st.rerun()

    # Simple auto-refresh mechanism (Hack for Streamlit)
    time.sleep(2) 
    st.rerun()
