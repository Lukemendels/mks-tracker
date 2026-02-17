import streamlit as st
from supabase import create_client, Client, ClientOptions
from datetime import datetime
import pandas as pd
import time
import requests
import os
from dotenv import load_dotenv

load_dotenv()

# --- PAGE CONFIG ---
st.set_page_config(page_title="MKS Tracker", page_icon="🥏", layout="wide")

# --- INITIALIZE SESSION STATE ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if 'current_round' not in st.session_state:
    st.session_state.current_round = None


# --- CONNECT TO SUPABASE ---
# --- CONNECT TO SUPABASE ---
# --- CONNECT TO SUPABASE ---
try:
    # 1. Try local environment variables first
    SUPABASE_URL = os.environ.get("SUPABASE_URL")
    SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY") or os.environ.get("SUPABASE_KEY")

    # 2. Fallback to Streamlit secrets (Exact keys from original code)
    if not SUPABASE_URL and "SUPABASE_URL" in st.secrets:
        SUPABASE_URL = st.secrets["SUPABASE_URL"]
    
    if not SUPABASE_KEY and "SUPABASE_KEY" in st.secrets:
        SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

    if not SUPABASE_URL or not SUPABASE_KEY:
        raise ValueError("Supabase credentials not found.")

    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    # Restore session if it exists
    if "supabase_session" in st.session_state:
        try:
            supabase.auth.set_session(
                st.session_state.supabase_session.access_token, 
                st.session_state.supabase_session.refresh_token
            )
        except Exception as e:
            # Session might be expired
            del st.session_state.supabase_session
            
    OFFLINE_MODE = False
except Exception as e:
    st.error(f"Connection Error: {e}")
    st.caption("Please check your .streamlit/secrets.toml or Streamlit Cloud Secrets.")
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
                    response = supabase.auth.sign_in_with_password({"email": email, "password": password})
                    if response.user:
                        st.session_state.logged_in = True
                        st.session_state.supabase_session = response.session
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
    if "supabase_session" in st.session_state:
        del st.session_state.supabase_session
    st.session_state.logged_in = False
    st.rerun()

# @st.cache_data(ttl=3600) <- CAUSING ISSUES WITH AUTH STATE
def get_bag():
    """Fetch all discs from Supabase."""
    if OFFLINE_MODE:
        return []
    try:
        response = supabase.table("discs").select("*").order("name").execute()
        return response.data if response.data else []
    except Exception as e:
        st.error(f"Error fetching discs: {e}")
        return []

# --- WEATHER FUNCTIONS ---
def get_wind_direction(degrees):
    directions = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
    index = round(degrees / (360. / len(directions))) % len(directions)
    return directions[index]

@st.cache_data(ttl=600)
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

# --- SIDEBAR & GLOBAL SETTINGS ---
with st.sidebar:
    st.title("🥏 MKS Control")
    tournament_mode = st.toggle("🏆 Tournament Mode", help="Hides entry forms to focus on execution.")
    if st.button("Log Out"):
        logout()
    st.divider()

    st.header("📍 Loriella Park Conditions")
    weather = get_loriella_weather()
    if weather:
        c1, c2 = st.columns(2)
        with c1:
            st.metric("Temp", f"{weather['temp']}°F", f"{weather['feels_like']}°F")
        with c2:
            st.metric("Wind", f"{weather['wind_speed']} mph", f"{weather['wind_dir']}")
    
    st.divider()
    st.divider()
    
    # --- ROUND MANAGEMENT ---
    if st.session_state.current_round:
        st.success(f"Ongoing Round\n\n**{st.session_state.current_round['name']}**")
        layout = st.session_state.current_round['layout'] # Force layout to match round
        st.caption(f"Layout: {layout}")
        
        if st.button("End Round", type="primary"):
            st.session_state.current_round = None
            st.rerun()
    else:
        st.subheader("🚀 Start New Round")
        layout = st.radio("Layout", ["Shorts (Round 1)", "Longs (Round 2)"])
        
        # Bag Selection
        all_discs_data = get_bag() # Fetch all to pick from
        default_discs = [d['name'] for d in all_discs_data] if all_discs_data else []
        
        with st.expander("🎒 Bag Setup", expanded=False):
            selected_bag = st.multiselect("Select Discs for Round", default_discs, default=default_discs)
        
        if st.button("Start Round", type="primary"):
            round_name = f"{datetime.now().strftime('%m-%d-%y-%I%M%p')}-{layout.split(' ')[0]}"
            
            # Create Round in DB
            new_round_id = None
            if not OFFLINE_MODE:
                try:
                    res = supabase.table("rounds").insert({
                        "name": round_name,
                        "layout": layout,
                        "selected_discs": selected_bag
                    }).execute()
                    if res.data:
                        new_round_id = res.data[0]['id']
                except Exception as e:
                    st.error(f"Failed to start round: {e}")
            
            # Set Session
            st.session_state.current_round = {
                "id": new_round_id,
                "name": round_name,
                "layout": layout,
                "selected_discs": selected_bag
            }
            st.rerun()

    
    if not tournament_mode:
        st.divider()
        st.write("### 🎒 Bag Check")
        
        bag_data = get_bag()
        # Filter if round is active
        if st.session_state.current_round and bag_data:
             allowed = set(st.session_state.current_round['selected_discs'])
             bag_data = [d for d in bag_data if d['name'] in allowed]
             
        if bag_data:
            # Grouping logic
            categories = {
                "Putters": ["Putter", "Approach"],
                "Mids": ["Midrange"],
                "Fairways": ["Fairway Driver"],
                "Distance": ["Distance Driver"]
            }
            
            for cat_name, types in categories.items():
                st.markdown(f"**{cat_name}**")
                # Filter discs for this category
                current_discs = [d for d in bag_data if d.get('disc_type') in types]
                
                for d in current_discs:
                    # Format: Name (Plastic) - Speed/Glide/Turn/Fade
                    flight_nums = f"{d.get('speed')}/{d.get('glide')}/{d.get('turn')}/{d.get('fade')}"
                    # Handle decimals cleanly (e.g. 5.0 -> 5)
                    flight_nums = flight_nums.replace('.0', '')
                    
                    note = f"• **{d['name']}** ({d.get('plastic', 'N/A')}) | *{flight_nums}*"
                    st.caption(note)
        else:
            st.warning("No discs found in database.")

# --- MAIN UI ---
st.title("The Mendelsohn Protocol")
st.markdown("**Target:** EVEN PAR")

# Shared Hole Selection
hole_num = st.number_input("Hole #", min_value=1, max_value=18, step=1, value=1)

# --- 1. RETRIEVE RELATIONAL STRATEGY & AXIOM ---
try:
    # Querying the metadata and joining the mindset_axioms table
    resp = supabase.table("course_metadata")\
        .select("protocol_notes, par, suggested_disc, Attack_Hole, mindset_axioms(short_name, title, corollary)")\
        .eq("hole_number", hole_num)\
        .eq("layout", layout)\
        .execute()

    # Defaults
    default_par = 3
    suggested_disc = None
    attack_hole = "No" # Default to No

    if resp.data:
        data = resp.data[0]
        notes = data.get('protocol_notes', "")
        default_par = data.get('par', 3)
        suggested_disc = data.get('suggested_disc')
        attack_hole = data.get('Attack_Hole', "No")
        
        # Flattening logic: handles cases where axiom comes back as a single-item list
        axiom_raw = data.get('mindset_axioms')
        axiom = axiom_raw[0] if isinstance(axiom_raw, list) and len(axiom_raw) > 0 else axiom_raw

        st.markdown(f"# 📋 The Protocol: Hole {hole_num}")
        
        # Enhanced Markdown formatting: catching both Shorts and Longs terminology
        if notes:
            parts = notes.split(". ")
            for p in parts:
                if any(k in p for k in ["Mindset:", "Strategy:", "Plan:", "The Play:"]): 
                    st.markdown(f"### 🧠 {p}")
                elif "Disc:" in p: 
                    st.markdown(f"### 🥏 {p}")
                elif any(k in p for k in ["Execution:", "Line:", "Geometry:"]): 
                    st.markdown(f"### 🎯 {p}")
                else:
                    st.write(p)

        # Axiom display: The core of the MKS Tracker
        if axiom:
            st.divider()
            st.success(f"**{axiom.get('short_name')}: {axiom.get('title')}**")
            if axiom.get('corollary'):
                st.info(f"*{axiom.get('corollary')}*")
        else:
            st.info("No specific Mindset Axiom linked to this hole yet.")
            
        # Attack Hole Indicator
        st.divider()
        if attack_hole == "Yes":
            st.success("🟢 **ATTACK HOLE**: Go for it! Be aggressive.")
        else:
            st.warning("⚠️ **SMART PLAY**: Play safe, hit your line, get the par, move on.")
        st.divider()
    else:
        st.warning(f"No protocol notes found for Hole {hole_num} on {layout}.")
except Exception as e:
    st.error(f"Error retrieving protocol: {e}")

# --- 2. CONDITIONAL CONTENT ---
if not tournament_mode:
    tab1, tab2, tab3 = st.tabs(["📝 Hole Entry", "📊 Analysis", "📂 History & Export"])
    
    with tab1:
        # Retrieve Last Practice result
        db_note = None
        if not OFFLINE_MODE:
            try:
                res = supabase.table("practice_notes")\
                    .select("*")\
                    .eq("hole_number", hole_num)\
                    .eq("layout", layout)\
                    .order("created_at", desc=True)\
                    .limit(1)\
                    .execute()
                if res.data:
                    db_note = res.data[0]
            except: pass

        if db_note:
            with st.expander("🔍 Last Practice Result", expanded=False):
                st.write(f"**Disc:** {db_note['disc_used']} | **Strokes:** {db_note.get('strokes', 'N/A')}")
                st.markdown(f"*{db_note['notes']}*")

        if st.session_state.current_round:
            st.info(f"💾 Saving to Round: {st.session_state.current_round['name']}")

        with st.form("entry_form"):
            st.subheader(f"Log Practice: Hole {hole_num}")
            
            # Fetch discs and sort
            bag_data = get_bag()
            
            # Filter by active round
            if st.session_state.current_round and bag_data:
                allowed = set(st.session_state.current_round['selected_discs'])
                bag_data = [d for d in bag_data if d['name'] in allowed]
            
            # Custom Sort Order: Fairway -> Distance -> Mid -> Putter
            type_order = {
                "Fairway Driver": 0, 
                "Distance Driver": 1, 
                "Midrange": 2, 
                "Putter": 3, 
                "Approach": 4
            }
            
            if bag_data:
                 bag_data.sort(key=lambda x: (type_order.get(x.get('disc_type', ''), 99), x['name']))

            all_discs = [d['name'] for d in bag_data] if bag_data else ["Unknown"]
            
            # Determine Index for Suggested Disc
            default_disc_index = 0
            if suggested_disc:
                try:
                    default_disc_index = all_discs.index(suggested_disc)
                except ValueError:
                    pass # Suggested disc not in current bag
            
            disc_choice = st.selectbox("Disc Used", all_discs, index=default_disc_index)
            c1, c2, c3 = st.columns(3)
            with c1: shot_shape = st.selectbox("Shape", ["Straight", "Hyzer", "Anhyzer", "Flex", "Flip"])
            with c2: rating = st.slider("Confidence", 1, 5, 3)
            with c3: strokes = st.number_input("Strokes", 1, 15, value=default_par)
            notes_input = st.text_area("Adjustment Notes")
            
            if st.form_submit_button("💾 Save Data", use_container_width=True):
                data_entry = {
                    "hole_number": hole_num,
                    "layout": layout,
                    "disc_used": disc_choice,
                    "result_rating": rating,
                    "strokes": strokes,
                    "notes": f"[{shot_shape}] {notes_input}",
                    "created_at": datetime.now().isoformat(),
                    "round_id": st.session_state.current_round['id'] if st.session_state.current_round else None
                }
            if st.form_submit_button("💾 Save Data", use_container_width=True):
                data_entry = {
                    "hole_number": hole_num,
                    "layout": layout,
                    "disc_used": disc_choice,
                    "result_rating": rating,
                    "strokes": strokes,
                    "notes": f"[{shot_shape}] {notes_input}",
                    "created_at": datetime.now().isoformat(),
                    "round_id": st.session_state.current_round['id'] if st.session_state.current_round else None,
                    # Auto-log Weather
                    "temperature": weather['temp'] if weather else None,
                    "wind_speed": weather['wind_speed'] if weather else None,
                    "wind_direction": weather['wind_dir'] if weather else None
                }
                supabase.table("practice_notes").insert(data_entry).execute()
                st.toast("Hole Saved!", icon="✅")
                time.sleep(1)
                st.rerun()

    with tab2:
        st.subheader("📊 Performance Review & Analysis")
        view_layout = st.selectbox("Filter Analysis", ["Shorts (Round 1)", "Longs (Round 2)"])
        try:
            response = supabase.table("practice_notes").select("*").eq("layout", view_layout).execute()
            if response.data:
                df = pd.DataFrame(response.data)
                col_a, col_b = st.columns(2)
                with col_a: st.metric("Avg Strokes", f"{df['strokes'].mean():.2f}")
                with col_b: st.metric("Entries", len(df))
                st.write("### Disc Confidence (Avg Rating)")
                st.bar_chart(df.groupby("disc_used")["result_rating"].mean())
                st.write("### Stroke Trends per Hole")
                st.line_chart(df.groupby("hole_number")["strokes"].mean())
            else:
                st.info("No data logged for this layout.")
        except Exception as e:
            st.error(f"Error loading stats: {e}")

    with tab3:
        st.subheader("📂 Round History & Export")
        
        # 1. Fetch Rounds
        if not OFFLINE_MODE:
            try:
                rounds_res = supabase.table("rounds").select("*").order("created_at", desc=True).limit(20).execute()
                rounds = rounds_res.data if rounds_res.data else []
                
                if rounds:
                    # Select Round to Export
                    round_names = [f"{r['name']} ({r['layout']})" for r in rounds]
                    selected_round_name = st.selectbox("Select Round to Export", round_names)
                    
                    if selected_round_name:
                        # Find selected round object
                        selected_round = next(r for r in rounds if f"{r['name']} ({r['layout']})" == selected_round_name)
                        
                        # Fetch notes for this round
                        notes_res = supabase.table("practice_notes").select("*").eq("round_id", selected_round['id']).execute()
                        round_data = {
                            "round_info": selected_round,
                            "shots": notes_res.data if notes_res.data else []
                        }
                        
                        st.write("### Round Data (JSON)")
                        import json
                        json_str = json.dumps(round_data, indent=2, default=str)
                        st.code(json_str, language="json")
                        
                        st.download_button(
                            label="📥 Download JSON",
                            data=json_str,
                            file_name=f"{selected_round['name']}.json",
                            mime="application/json"
                        )
                        
                    st.divider()
                    st.write("### Bulk Export (Last 50 Rounds)")
                    if st.button("Generate Bulk Export"):
                        # Fetch all recent rounds + notes
                        # Note: This is a heavy query, keeping it simple for now
                        all_rounds = supabase.table("rounds").select("*, practice_notes(*)").order("created_at", desc=True).limit(50).execute()
                        
                        if all_rounds.data:
                            bulk_json = json.dumps(all_rounds.data, indent=2, default=str)
                            st.download_button(
                                label="📥 Download Bulk Export",
                                data=bulk_json,
                                file_name=f"mks_bulk_export_{datetime.now().strftime('%Y%m%d')}.json",
                                mime="application/json"
                            )
                else:
                    st.info("No rounds recorded yet.")
            except Exception as e:
                st.error(f"Error fetching history: {e}")

else:
    st.success("🏆 Tournament Mode Active. Focus on the Axioms. Execution only.")
