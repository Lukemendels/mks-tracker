import streamlit as st
from supabase import create_client, Client
from datetime import datetime
import pandas as pd
import time
import requests

# --- PAGE CONFIG ---
st.set_page_config(page_title="MKS Tracker", page_icon="🥏", layout="wide")

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

# --- CONNECT TO SUPABASE ---
try:
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    OFFLINE_MODE = False
except Exception as e:
    OFFLINE_MODE = True

# --- AUTHENTICATION ---
def login():
    st.title("🥏 MKS Protocol Login")
    with st.form("login_form"):
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        if st.form_submit_button("Log In", use_container_width=True):
            try:
                response = supabase.auth.sign_in_with_password({"email": email, "password": password})
                if response.user:
                    st.session_state.logged_in = True
                    st.rerun()
            except Exception as e:
                st.error(f"Login Failed: {e}")

if not st.session_state.logged_in:
    login()
    st.stop()

# --- WEATHER (CACHED) ---
@st.cache_data(ttl=600)
def get_loriella_weather():
    URL = "https://api.open-meteo.com/v1/forecast?latitude=38.2544&longitude=-77.5443&current=temperature_2m,wind_speed_10m,wind_direction_10m&temperature_unit=fahrenheit&wind_speed_unit=mph"
    try:
        data = requests.get(URL).json()['current']
        return data
    except: return None

# --- SIDEBAR & TOURNAMENT MODE ---
with st.sidebar:
    st.title("🥏 MKS Control")
    tournament_mode = st.toggle("🏆 Tournament Mode", help="Hides entry forms to focus on execution.")
    if st.button("Log Out"):
        supabase.auth.sign_out()
        st.session_state.logged_in = False
        st.rerun()
    st.divider()
    
    weather = get_loriella_weather()
    if weather:
        st.metric("Temp", f"{weather['temperature_2m']}°F")
        st.metric("Wind", f"{weather['wind_speed_10m']} mph")
    
    st.divider()
    layout = st.radio("Layout", ["Shorts (Round 1)", "Longs (Round 2)"])

# --- MAIN UI ---
st.title("The Mendelsohn Protocol")
hole_num = st.number_input("Hole #", 1, 18, 1)

# 1. RETRIEVE RELATIONAL STRATEGY & AXIOM
try:
    # This query joins the metadata with the linked axiom
    resp = supabase.table("course_metadata")\
        .select("protocol_notes, mindset_axioms(short_name, title, corollary)")\
        .eq("hole_number", hole_num)\
        .eq("layout", layout)\
        .execute()

    if resp.data:
        data = resp.data[0]
        notes = data['protocol_notes']
        axiom = data['mindset_axioms']

        # Format Note Breakdown
        st.markdown(f"# 📋 The Protocol: Hole {hole_num}")
        
        # Split logic for Mindset, Disc, Execution headers
        for line in notes.split(". "):
            if "Mindset:" in line: st.markdown(f"## {line}")
            elif "Disc:" in line: st.markdown(f"## {line}")
            elif "Execution:" in line: st.markdown(f"## {line}")

        # Axiom Display
        if axiom:
            st.divider()
            st.markdown(f"### {axiom['short_name']}: {axiom['title']}")
            st.markdown(f"#### \"{axiom['corollary']}\"")
            st.divider()
    else:
        st.warning("No strategy linked for this hole.")
except Exception as e:
    st.error(f"Data Error: {e}")

# 2. ENTRY & ANALYSIS (OFF IN TOURNAMENT MODE)
if not tournament_mode:
    tab1, tab2 = st.tabs(["📝 Entry", "📊 Review"])
    
    with tab1:
        with st.form("entry"):
            disc = st.selectbox("Disc", ["Watt", "Zone", "Caiman", "Mako3", "Leopard3", "Teebird", "Firebird", "Trail", "Wraith"])
            c1, c2 = st.columns(2)
            with c1: strokes = st.number_input("Strokes", 1, 15, 3)
            with c2: rating = st.slider("Confidence", 1, 5, 3)
            notes = st.text_area("Adjustment Notes")
            if st.form_submit_button("Save Data"):
                entry = {
                    "hole_number": hole_num, "layout": layout, "disc_used": disc,
                    "strokes": strokes, "result_rating": rating, "notes": notes,
                    "created_at": datetime.now().isoformat()
                }
                supabase.table("practice_notes").insert(entry).execute()
                st.toast("Saved!")
                time.sleep(0.5)
                st.rerun()

    with tab2:
        res = supabase.table("practice_notes").select("*").eq("layout", layout).execute()
        if res.data:
            df = pd.DataFrame(res.data)
            st.line_chart(df.groupby("hole_number")["strokes"].mean())
else:
    st.success("🏆 Tournament Mode Active: Focus on the Line.")
