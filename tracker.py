import streamlit as st
from supabase import create_client, Client, ClientOptions
from datetime import datetime
import pandas as pd
import time
import requests
import os
import extra_streamlit_components as stx
from dotenv import load_dotenv
import pytz
from streamlit_js_eval import get_geolocation

load_dotenv()

# --- PAGE CONFIG ---
st.set_page_config(page_title="MKS Tracker", page_icon="🥏", layout="wide")

# --- CSS: MOBILE OPTIMIZATIONS ---
st.markdown("""
<style>
/* iOS Sticky Footer */
div[data-testid="stVerticalBlock"] > div:has(div.sticky-nav) {
    position: fixed;
    bottom: 0;
    left: 0;
    width: 100%;
    background-color: #0E1117; /* Dark theme match */
    z-index: 1000;
    padding-top: 15px;
    padding-left: 1rem;
    padding-right: 1rem;
    padding-bottom: calc(1rem + env(safe-area-inset-bottom)); /* iOS Safe Area Fix */
    border-top: 1px solid #333;
    box-shadow: 0px -4px 10px rgba(0,0,0,0.5);
}

/* Hide Streamlit Branding features for cleaner app feel */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# Timezone
LOCAL_TZ = pytz.timezone('America/New_York')

# --- INITIALIZE COOKIE MANAGER ---
# --- INITIALIZE COOKIE MANAGER ---
cookie_manager = stx.CookieManager()

# --- INITIALIZE SESSION STATE ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if 'current_score_input' not in st.session_state:
    st.session_state.current_score_input = 3

if 'current_round' not in st.session_state:
    st.session_state.current_round = None

# --- RESTORE SESSION FROM COOKIES ---
# 1. Auth Restoration
if not st.session_state.logged_in:
    auth_token = cookie_manager.get('mks_refresh_token')
    if auth_token:
        try:
             # Refresh Session
             res = supabase.auth.refresh_session(auth_token)
             if res.user:
                 st.session_state.logged_in = True
                 st.session_state.supabase_session = res.session
                 st.success("Session Restored from Cookie! 🍪")
        except Exception as e:
            # Token invalid
            # cookie_manager.delete('mks_refresh_token') # Optional cleanup
            pass

# 2. Round Restoration
if not st.session_state.current_round:
    round_cookie = cookie_manager.get('mks_round_id')
    if round_cookie:
        # Fetch round details
        try:
             # Need to ensure supabase is ready (it is, unless offline)
             if not OFFLINE_MODE:
                 res = supabase.table("rounds").select("*").eq("id", round_cookie).execute()
                 if res.data:
                     st.session_state.current_round = res.data[0]
                     # Ensure we have selected_discs in session_state format
                     if 'selected_discs' not in st.session_state.current_round:
                          st.session_state.current_round['selected_discs'] = []
                 else:
                     # Round not found (maybe deleted?), clear cookie
                     cookie_manager.delete('mks_round_id')
        except: pass




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
                        
                        # Save Refresh Token to Cookie (30 days)
                        cookie_manager.set('mks_refresh_token', response.session.refresh_token, expires_at=datetime.now(LOCAL_TZ) + pd.Timedelta(days=30))
                        
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
    
    # clear cookies
    cookie_manager.delete('mks_refresh_token')
    cookie_manager.delete('mks_round_id')
    cookie_manager.delete('mks_hole_num')
    
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
    st.title("🥏 MKS Control (v2.0)")
    tournament_mode = st.toggle("🏆 Tournament Mode", help="Hides entry forms to focus on execution.")
    if st.button("Log Out"):
        logout()
    st.divider()

    # --- MAPPER MODE ---
    mapper_mode = st.toggle("🗺️ Mapper Mode", help="Enable GPS data collection for Teepads and Baskets.")
    
    st.header("📍 Loriella Park Conditions")
    weather = get_loriella_weather()
    if weather:
        c1, c2 = st.columns(2)
        with c1:
            st.metric("Temp", f"{weather['temp']}°F", f"{weather['feels_like']}°F")
        with c2:
            st.metric("Wind", f"{weather['wind_speed']} mph", f"{weather['wind_dir']} | Gust {weather['wind_gust']}")
    
    st.divider()
    st.divider()
    
    # --- ROUND MANAGEMENT ---
    if st.session_state.current_round:
        st.success(f"Ongoing Round\n\n**{st.session_state.current_round['name']}**")
        layout = st.session_state.current_round['layout'] # Force layout to match round
        st.caption(f"Layout: {layout}")
        
        if st.button("End Round", type="primary"):
            st.session_state.current_round = None
            cookie_manager.delete('mks_round_id')
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
            round_name = f"{datetime.now(LOCAL_TZ).strftime('%m-%d-%y-%I%M%p')}-{layout.split(' ')[0]}"
            
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
            if new_round_id:
                cookie_manager.set('mks_round_id', new_round_id, expires_at=datetime.now(LOCAL_TZ) + pd.Timedelta(days=1))
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
# Mobile Header (HUD) replaces the standard title

# Calculate Dynamic Target
# Logic: Target = -1 * floor(Attack Holes / 2)
# "50% of attack holes under par"
target_score = "EVEN PAR"
try:
    if not OFFLINE_MODE:
        # We need to know the layout context.
        # If a round is active, use that layout.
        # If not, we can default to the one selected in the sidebar (but that variable might not be in scope here if sidebar run first? Yes it is)
        # Sidebar runs top-to-bottom. 'layout' is defined in sidebar.
        
        # Verify layout is defined (it should be from sidebar)
        if 'layout' in locals() or 'layout' in globals():
             # Count Attack Holes
             res = supabase.table("course_metadata")\
                 .select("id", count="exact")\
                 .eq("layout", layout)\
                 .eq("Attack_Hole", "Yes")\
                 .execute()
             
             count = res.count
             if count is not None:
                 target_strokes = int(count // 2) # Floor division
                 if target_strokes > 0:
                     target_score = f"-{target_strokes}"
                 else:
                     target_score = "EVEN PAR"
except Exception as e:
    # Fallback
    pass

st.markdown(f"**Target:** {target_score}")

# Shared Hole Selection
# Restore Hole from Cookie if available and not set manually in session
default_hole = 1
cookie_hole = cookie_manager.get('mks_hole_num')
if cookie_hole:
    try:
        default_hole = int(cookie_hole)
    except: pass

# Callback to update cookie on change
# Callback to update cookie on change
def update_hole_cookie():
    cookie_manager.set('mks_hole_num', st.session_state.hole_input)

# Ensure session state is initialized for the widget key
if "hole_input" not in st.session_state:
    st.session_state.hole_input = default_hole

def change_hole(delta):
    new_val = st.session_state.hole_input + delta
    if 1 <= new_val <= 18:
        st.session_state.hole_input = new_val
        update_hole_cookie()

# Mobile Navigation
# Mobile Navigation - Moved to Sticky Footer later
# But we need input handling logic here for the session state score

# --- FIX: Ensure hole_num is defined from session state ---
hole_num = st.session_state.hole_input


# --- 1. RETRIEVE RELATIONAL STRATEGY & AXIOM ---
try:
    # Querying the metadata and joining the mindset_axioms table
    resp = supabase.table("course_metadata")\
        .select("protocol_notes, par, suggested_disc, Attack_Hole, shot_shape, execution_notes, mindset_axioms(short_name, title, corollary)")\
        .eq("hole_number", hole_num)\
        .eq("layout", layout)\
        .execute()

    # Defaults
    default_par = 3
    suggested_disc = None
    attack_hole = "No" # Default to No
    suggested_shape = None
    exec_notes = None

    if resp.data:
        data = resp.data[0]
        # notes = data.get('protocol_notes', "") # Legacy Column
        default_par = data.get('par', 3)
        suggested_disc = data.get('suggested_disc')
        attack_hole = data.get('Attack_Hole', "No")
        suggested_shape = data.get('shot_shape')
        exec_notes = data.get('execution_notes')
        
        # Flattening logic: handles cases where axiom comes back as a single-item list
        axiom_raw = data.get('mindset_axioms')
        axiom = axiom_raw[0] if isinstance(axiom_raw, list) and len(axiom_raw) > 0 else axiom_raw

        # BASKET LOGIC
        # Default: Shorts = Red, Longs = Yellow
        # Exception: Holes 1, 3, 10 are always Red
        basket_color = "Red"
        if "Longs" in layout:
             basket_color = "Yellow"
        
        if hole_num in [1, 3, 10]:
             basket_color = "Red"
             
        # Emoji mapping
        basket_emoji = "🔴" if basket_color == "Red" else "🟡"
        
        # Attack Status for Header
        if attack_hole == "Yes":
           attack_status = ":red[🔴 ATTACK]"
           status_color = "red"
        else:
           attack_status = ":green[🟢 SMART PLAY]"
           status_color = "green"
        
        # --- COMPACT HUD HEADER ---
        with st.container():
            c_hud_1, c_hud_2 = st.columns([2, 1])
            with c_hud_1:
                st.markdown(f"## Hole {hole_num} | Par {default_par}")
            with c_hud_2:
                st.markdown(f"### {attack_status}")
        
        # --- PROTOCOL & STRATEGY (COLLAPSIBLE) ---
        with st.expander("📋 Protocol & Strategy", expanded=True):
             c1, c2 = st.columns([1, 1])
             if suggested_disc:
                 c1.markdown(f"**🥏 Disc**: {suggested_disc}")
             if suggested_shape:
                 c2.markdown(f"**📐 Shape**: {suggested_shape}")
                 
             if exec_notes:
                  st.success(f"**Target**: {exec_notes}")

             # Axiom display
             if axiom:
                 st.divider()
                 st.markdown(f"**{axiom.get('short_name')}: {axiom.get('title')}**")
                 if axiom.get('corollary'):
                     st.caption(f"*{axiom.get('corollary')}*")
    else:
        st.warning(f"No protocol notes found for Hole {hole_num} on {layout}.")
except Exception as e:
    st.error(f"Error retrieving protocol: {e}")

# --- MAPPER MODE INTERFACE ---
if mapper_mode:
    st.write("---")
    st.subheader("🗺️ Mapper Mode")
    
    # 1. Check if already verified
    is_verified = False
    existing_geo = None
    try:
        geo_res = supabase.table("hole_geometry").select("*").eq("hole_number", hole_num).eq("layout", layout).execute()
        if geo_res.data:
            existing_geo = geo_res.data[0]
            if existing_geo.get('verified'):
                is_verified = True
    except Exception as e:
        st.error(f"Error checking geometry: {e}")

    if is_verified:
        st.success(f"✅ Geometry Verified for Hole {hole_num} ({layout})")
        if existing_geo:
             st.write(f"**Distance:** {existing_geo.get('distance_feet', 'N/A')} ft")
             st.caption(f"Tee: {existing_geo.get('tee_lat')}, {existing_geo.get('tee_lon')}")
             st.caption(f"Basket: {existing_geo.get('basket_lat')}, {existing_geo.get('basket_lon')}")
    else:
        c1, c2 = st.columns(2)
        
        # Helper to handle GPS save
        def save_gps(label, lat, lon):
            if not st.session_state.logged_in:
                st.error("Must be logged in to map.")
                return

            try:
                user_id = st.session_state.supabase_session.user.id
                
                # Check for existing to upsert
                payload = {
                    "hole_number": hole_num,
                    "layout": layout,
                    "mapped_by": user_id,
                    "verified": False 
                }
                
                if label == "tee":
                    payload["tee_lat"] = lat
                    payload["tee_lon"] = lon
                elif label == "basket":
                    payload["basket_lat"] = lat
                    payload["basket_lon"] = lon
                
                # We need to upsert. key is (hole_number, layout)
                # But supabase upsert needs all required fields or it might fail if row doesn't exist?
                # Actually, if we are creating a NEW row, we need hole_number and layout.
                # If updating, we just need the key.
                
                # First try to get existing again to merge?
                # Actually upsert with on_conflict should work if we provide the keys.
                
                # Merge with existing data if present in session (to avoid overwriting other point with null if partially mapped)
                # Better: SELECT first, then UPDATE/INSERT.
                
                current_data = {}
                if existing_geo:
                    current_data = existing_geo.copy()
                    # Remove id/created_at to avoid issues?
                    # actually just update the changed fields.
                    
                    if label == "tee":
                        supabase.table("hole_geometry").update({
                            "tee_lat": lat, 
                            "tee_lon": lon,
                            "mapped_by": user_id
                        }).eq("id", existing_geo['id']).execute()
                    else:
                         supabase.table("hole_geometry").update({
                            "basket_lat": lat, 
                            "basket_lon": lon,
                            "mapped_by": user_id
                        }).eq("id", existing_geo['id']).execute()
                else:
                    # Insert new
                    payload["distance_feet"] = None # Reset if new
                    payload["elevation_change_feet"] = None
                    supabase.table("hole_geometry").insert(payload).execute()
                    
                st.toast(f"{label.capitalize()} Set! ({lat:.5f}, {lon:.5f})", icon="📍")
                time.sleep(1)
                st.rerun()
                
            except Exception as e:
                st.error(f"Save failed: {e}")

        with c1:
            st.caption("Teepad")
            if existing_geo and existing_geo.get('tee_lat'):
                st.write(f"✅ {existing_geo['tee_lat']:.5f}, {existing_geo['tee_lon']:.5f}")
            
            # Button for Tee
            # Note: get_geolocation returns None initially, then a dict with 'coords'.
            # We use a key to force uniqueness.
            loc_tee = get_geolocation(component_key=f"gps_tee_{hole_num}_{layout}")
            if loc_tee and 'coords' in loc_tee:
                lat = loc_tee['coords']['latitude']
                lon = loc_tee['coords']['longitude']
                # Only save if different? Or just save.
                # To avoid infinite loop, we check if we just saved this.
                # We can store last_saved in session_state
                
                last_saved_key = f"last_saved_tee_{hole_num}_{layout}"
                if st.session_state.get(last_saved_key) != f"{lat},{lon}":
                     save_gps("tee", lat, lon)
                     st.session_state[last_saved_key] = f"{lat},{lon}"

        with c2:
            st.caption("Basket")
            if existing_geo and existing_geo.get('basket_lat'):
                 st.write(f"✅ {existing_geo['basket_lat']:.5f}, {existing_geo['basket_lon']:.5f}")
            
            loc_basket = get_geolocation(component_key=f"gps_basket_{hole_num}_{layout}")
            if loc_basket and 'coords' in loc_basket:
                lat = loc_basket['coords']['latitude']
                lon = loc_basket['coords']['longitude']
                
                last_saved_key = f"last_saved_basket_{hole_num}_{layout}"
                if st.session_state.get(last_saved_key) != f"{lat},{lon}":
                     save_gps("basket", lat, lon)
                     st.session_state[last_saved_key] = f"{lat},{lon}"


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
            
            # DEFAULT SHAPE Logic
            shape_options = ["Straight", "Hyzer", "Anhyzer", "Flex", "Flip"]
            default_shape_index = 0
            if suggested_shape and suggested_shape in shape_options:
                default_shape_index = shape_options.index(suggested_shape)
            
            # --- INPUT MODERNIZATION ---
            # 1. Disc Pills
            # Note: st.pills introduced in recent versions. Fallback to radio if older? We checked 1.54.
            disc_choice = st.pills("Disc Selection", all_discs, default=all_discs[default_disc_index] if all_discs else None, selection_mode="single")
            if not disc_choice and all_discs: 
                disc_choice = all_discs[default_disc_index]

            st.divider()

            # 2. Shot Shape Segmented Control
            shot_shape = st.segmented_control("Shape", shape_options, default=shape_options[default_shape_index], selection_mode="single")
            if not shot_shape: shot_shape = "Straight" # Default

            st.divider()
            
            # 3. Big Button Scoring
            st.caption("Score (Strokes)")
            c_score_sub, c_score_disp, c_score_add = st.columns([1, 2, 1])
            
            # Callbacks for score
            def decrement_score():
                if st.session_state.current_score_input > 1:
                    st.session_state.current_score_input -= 1
            def increment_score():
                 st.session_state.current_score_input += 1
            
            # Sync session state default if not set for this hole context logic (re-using old logic partially)
            # Actually, let's just default to Par content if we changed holes?
            # For simplicity, we stick to session state.
            
            with c_score_sub:
                st.button("➖", on_click=decrement_score, use_container_width=True)
            with c_score_disp:
                st.markdown(f"<h1 style='text-align: center; margin: 0; padding: 0;'>{st.session_state.current_score_input}</h1>", unsafe_allow_html=True)
            with c_score_add:
                st.button("➕", on_click=increment_score, use_container_width=True)
                
            rating = st.slider("Confidence", 1, 5, 3)
            notes_input = st.text_area("Adjustment Notes", placeholder="What happened?")
            
            # --- STICKY FOOTER ---
            # Wrapped in form submit button? No, the sticky footer needs to be outside the form if it contains navigation.
            # But the "Save Data" button IS the submit button for the form.
            # Streamlit forms cannot span outside containers easily. 
            # Solution: We close the form here with the submit button, 
            # BUT we want the buttons at the bottom.
            # CSS handles the position. We just need to make sure it's inside the form if it's the submit button.
            
            st.markdown('<div class="sticky-nav">', unsafe_allow_html=True)
            f1, f2, f3 = st.columns([1, 2, 1])
            with f1:
                if st.button("⬅️", use_container_width=True):
                    change_hole(-1)
                    st.rerun()
            with f2:
                if st.form_submit_button("✅ Save & Next", use_container_width=True):
                    data_entry = {
                        "hole_number": hole_num,
                        "layout": layout,
                        "disc_used": disc_choice,
                        "result_rating": rating,
                        "strokes": st.session_state.current_score_input,
                        "notes": f"[{shot_shape}] {notes_input}",
                        "created_at": datetime.now(LOCAL_TZ).isoformat(),
                        "round_id": st.session_state.current_round['id'] if st.session_state.current_round else None,
                        # Auto-log Weather
                        "temperature": weather['temp'] if weather else None,
                        "wind_speed": weather['wind_speed'] if weather else None,
                        "wind_gust": weather['wind_gust'] if weather else None,
                        "wind_direction": weather['wind_dir'] if weather else None
                    }
                    supabase.table("practice_notes").insert(data_entry).execute()
                    st.toast("Hole Saved!", icon="✅")
                    
                    # Auto Advance
                    change_hole(1)
                    time.sleep(0.5)
                    st.rerun()
            with f3:
                 if st.button("➡️", use_container_width=True):
                    change_hole(1)
                    st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

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
