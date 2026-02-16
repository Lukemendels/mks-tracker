import streamlit as st
from supabase import create_client, Client
from datetime import datetime
import pandas as pd
import time
import requests

# --- PAGE CONFIG ---
st.set_page_config(page_title="MKS Tracker", page_icon="🥏", layout="wide")

# --- INITIALIZE SESSION STATE ---
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

# --- AUTHENTICATION FUNCTIONS ---
def login():
    st.title("🥏 MKS Protocol Login")
    st.caption("Enter your Supabase credentials to access the Game Plan.")
    
    with st.form("login_form"):
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Log In", use_container_width=True)
        
        if submit:
            if OFFLINE_MODE:
                st.error("Cannot log in: Supabase secrets are missing.")
            else:
                try:
                    response = supabase.auth.sign_in_with_password({
                        "email": email, 
                        "password": password
                    })
                    if response.user:
                        st.session_state.logged_in = True
                        st.success("Login Successful!")
                        time.sleep(0.5)
                        st.rerun()
                except Exception as e:
                    st.error(f"Login Failed: {str(e)}")

def logout():
    try:
        supabase.auth.sign_out()
    except:
        pass
    st.session_state.logged_in = False
    st.rerun()

# --- WEATHER FUNCTIONS ---
def get_wind_direction(degrees):
    directions = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
    index = round(degrees / (360. / len(directions))) % len(directions)
    return directions[index]

def get_loriella_weather():
    URL = "https://api.open-meteo.com/v1/forecast?latitude=38.2544&longitude=-77.5443&current=temperature_2m,apparent_temperature,wind_speed_10m,wind_direction_10m,wind_gusts_10m&temperature_unit=fahrenheit&wind_speed_unit=mph&precipitation_unit=inch"
    try:
        response = requests.get(URL)
        data = response.json()
        current = data['current']
        return {
            "temp": round(current['temperature_2m']),
            "feels_like": round(current['apparent_temperature']),
            "wind_speed": round(current['wind_speed_10m']),
            "wind_gust": round(current['wind_gusts_10m']),
            "wind_dir": get_wind_direction(current['wind_direction_10m'])
        }
    except Exception as e:
        return None

# --- AUTH GATEKEEPER ---
if not st.session_state.logged_in:
    login()
    st.stop()

# --- MAIN APP ---
with st.sidebar:
    st.caption("Logged in")
    if st.button("Log Out"):
        logout()
    st.divider()

st.title("🥏 The Mendelsohn Protocol: Tracker")
st.markdown("**Event:** Loriella Challenge (MA4) | **Target:** EVEN PAR")

if OFFLINE_MODE:
    st.warning("⚠️ Offline Mode: Data will not save.")

with st.sidebar:
    st.header("📍 Loriella Park Conditions")
    weather = get_loriella_weather()
    if weather:
        c1, c2 = st.columns(2)
        with c1:
            st.metric("Temp", f"{weather['temp']}°F", f"{weather['feels_like']}°F (Feels)")
        with c2:
            st.metric("Wind", f"{weather['wind_speed']} mph", f"{weather['wind_dir']} (Gust {weather['wind_gust']})")
    
    st.divider()
    st.header("⚙️ Configuration")
    layout = st.radio("Select Layout", ["Shorts (Round 1)", "Longs (Round 2)"])
    
    st.divider()
    st.write("### 🎒 Bag Check")
    bag_sections = {
        "Putters": ["Watt (Putter)", "Zone (Approach)"],
        "Mids": ["Caiman (Over)", "Mako3 (Neutral)", "Buzz (Neutral)"],
        "Fairways": ["Leopard3 (Under)", "TL3 (Straight)", "Teebird (Stable)", "Saint (Control)", "Firebird (Utility)"],
        "Distance": ["Trail (Glide)", "Wraith (Headwind)", "DX Destroyer (Max D)"]
    }
    for section, discs in bag_sections.items():
        st.markdown(f"**{section}**")
        for d in discs:
            st.caption(f"• {d}")

tab1, tab2 = st.tabs(["📝 Hole Entry", "📊 Analysis"])

with tab1:
    col1, col2 = st.columns([1, 4])
    with col1:
        hole_num = st.number_input("Hole #", min_value=1, max_value=18, step=1, value=1)
    
    # 1. RETRIEVE STRATEGY FROM DATABASE
    protocol_note = "No specific protocol found for this hole."
    try:
        meta_resp = supabase.table("course_metadata")\
            .select("protocol_notes")\
            .eq("hole_number", hole_num)\
            .eq("layout", layout)\
            .execute()
        if meta_resp.data:
            protocol_note = meta_resp.data[0]['protocol_notes']
            st.info(f"**📋 THE PROTOCOL (Hole {hole_num})**\n\n{protocol_note}")
        else:
            st.warning(protocol_note)
    except Exception as e:
        st.error(f"Error fetching protocol: {e}")

    # 2. RETRIEVE LAST PRACTICE NOTE
    db_note = None
    if not OFFLINE_MODE:
        try:
            response = supabase.table("practice_notes")\
                .select("*")\
                .eq("hole_number", hole_num)\
                .eq("layout", layout)\
                .order("created_at", desc=True)\
                .limit(1)\
                .execute()
            if response.data:
                db_note = response.data[0]
        except Exception as e:
            pass

    # 3. DISPLAY LAST PRACTICE RESULT
    if db_note:
        with st.expander("🔍 View Last Practice Result", expanded=True):
            st.write(f"**Last Disc:** {db_note['disc_used']}")
            st.write(f"**Rating:** {db_note['result_rating']}/5")
            if "strokes" in db_note:
                st.write(f"**Strokes:** {db_note['strokes']}")
            st.markdown(f"**Notes:** *{db_note['notes']}*")

    st.divider()

    # 4. INPUT FORM
    with st.form("entry_form"):
        st.subheader(f"Log Practice: Hole {hole_num}")
        all_discs = [d for sublist in bag_sections.values() for d in sublist]
        disc_choice = st.selectbox("Disc Used", all_discs)
        
        c1, c2, c3 = st.columns(3)
        with c1:
            shot_shape = st.selectbox("Shape", ["Straight-to-Fade", "Hyzer Spike", "Flex/Anhyzer", "Hyzer Flip", "Roller", "Straight"])
        with c2:
            rating = st.slider("Confidence", 1, 5, 3)
        with c3:
            strokes = st.number_input("Strokes", min_value=1, max_value=15, value=3)

        notes = st.text_area("Adjustment Notes", placeholder="e.g. Saint held straight, good height usage.")
        submitted = st.form_submit_button("💾 Save Data", use_container_width=True)
        
        if submitted:
            if OFFLINE_MODE:
                st.error("Cannot save in Offline Mode.")
            else:
                data = {
                    "hole_number": hole_num,
                    "layout": layout,
                    "disc_used": disc_choice,
                    "result_rating": rating,
                    "strokes": strokes,
                    "notes": f"[{shot_shape}] {notes}",
                    "created_at": datetime.now().isoformat()
                }
                try:
                    supabase.table("practice_notes").insert(data).execute()
                    st.toast(f"Hole {hole_num} Saved!", icon="✅")
                    time.sleep(1)
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")

with tab2:
    st.subheader("Evening Review")
    if OFFLINE_MODE:
        st.info("Connect database to see analytics.")
    else:
        view_layout = st.selectbox("Filter Layout", ["Shorts (Round 1)", "Longs (Round 2)"])
        try:
            response = supabase.table("practice_notes")\
                .select("*")\
                .eq("layout", view_layout)\
                .order("hole_number")\
                .execute()
            
            if response.data:
                df = pd.DataFrame(response.data)
                st.write("### Disc Confidence (Avg Rating)")
                disc_perf = df.groupby("disc_used")["result_rating"].mean().sort_values(ascending=False)
                st.bar_chart(disc_perf)
                
                st.write("### Hole Breakdown")
                for i in range(1, 19):
                    hole_data = df[df["hole_number"] == i].sort_values("created_at", ascending=False)
                    if not hole_data.empty:
                        latest = hole_data.iloc[0]
                        score_text = f" | Strokes: {latest['strokes']}" if 'strokes' in latest else ""
                        with st.expander(f"Hole {i}: {latest['disc_used']} ({latest['result_rating']}/5){score_text}"):
                            st.write(f"**Notes:** {latest['notes']}")
                            st.caption(f"Logged: {latest['created_at']}")
            else:
                st.info("No practice data logged for this layout yet.")
        except Exception as e:
            st.error(f"Error fetching stats: {e}")
