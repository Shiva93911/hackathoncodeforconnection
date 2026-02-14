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
    Output format: Clean Text || Score (0-10
