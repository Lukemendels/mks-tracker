import streamlit as st
from supabase import create_client, Client
from datetime import datetime
import pandas as pd
import time

# --- PAGE CONFIG ---
st.set_page_config(page_title="MKS Tracker", page_icon="🥏", layout="wide")

# --- INITIALIZE SESSION STATE ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

# --- CONNECT TO SUPABASE ---
# Tries to connect via secrets. If fails, sets OFFLINE_MODE to True.
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

# --- THE MENDELSOHN PROTOCOL (VERBATIM) ---
DEFAULT_STRATEGIES = {
    "Shorts (Round 1)": {
        1: """Mindset: Tee Box Discipline. Do not step into the box until you see the flex line.
Disc: Firebird (RHFH Flat)
Execution: Aim left, trust the fade away from the guardian tree.
Corollary: If you hit the tree, 10-Second Rule applies immediately. Do not carry anger to Hole 2.""",
        2: """Mindset: Competing at the Ceiling. This is a scoring separation hole. Executing here is your gift to the field.
Disc: Firebird (Spike Hyzer)
Execution: Wide left, crash hard. Commit fully to the spike.""",
        3: """Mindset: Boring Golf (Axiom I). A stroke saved by safety is worth more than a stroke gained by brilliance.
Disc: Leopard3 (Hyzer Flip) -> Zone Approach
Execution: The goal is Par. Do not try to park it. Eat 2/3rds of the fairway, pitch up, take the 3.""",
        4: """Mindset: The One-Shot Round. Do not think about the 500' effective distance. Think only of the 250' drive.
Disc: Trail or Firebird
Execution: 250' Drive + 175' Approach. Don't be a hero.""",
        5: """Mindset: Data over Memory.
Disc: Firebird
Execution: Punch flat down the hill. Zone is too short for the second shot; stick with the Firebird or Trail to ensure you reach the green.""",
        6: """Mindset: Tee Box Discipline. If you doubt the Leopard3 turnover, step off.
Disc: Leopard3 (or Mako3 if testing lines)
Execution: RHFH Anhyzer. Commit to the angle. If you bail out early, you hit the left trees.""",
        7: """Mindset: Boring Golf.
Disc: Firebird/Trail
Execution: Wide left. Let it skip. Pitch up.""",
        8: """Mindset: Competing at the Ceiling. Simple execution is high-level play.
Disc: Firebird
Execution: 250' drive to landing zone -> 50' pitch.""",
        9: """Mindset: All Gas.
Disc: Leopard3 (Hyzer Flip)
Execution: Must finish right. Trust the flip.""",
        10: """Mindset: The McBeth Corollary. Ignore the water. It is just blue grass. Focus on the data: Distance + Disc Stability.
Disc: DX Teebird (Sacrificial/Trust) or 150g Roc3
Execution: Trust the stability. If you go in the water, 10-Second Rule. Do not let a lost disc become a lost round.""",
        11: """(DICTATED PLAN)
Strategy: Buzz -> Zone -> Putt.
Aiming Point: Locust Tree.
Reasoning: Buzz holds straight up the hill better than Zone. Zone approach for par.
Alternative: Zone-Zone is still the play if Buzz feels risky.""",
        12: """Mindset: Attack Mode.
Disc: Firebird
Execution: RHFH Crash wide left.""",
        13: """Mindset: Boring Audit. Birdie is a 1/40 chance. Do not chase it.
Disc: MVP Trail
Execution: Glidey straight shot. Zone pitch. Tap in Par.""",
        14: """Mindset: Data Correction. You got pinched last time? Aim wider.
Disc: Firebird
Execution: Wider stall hyzer.""",
        15: """(DICTATED PLAN)
The Geometry: A bunch of random trees. No clear lane. Right to Left movement.
Option 1: Leopard3 (Hyzer Flip/Turnover) - Consistent.
Option 2: Mako3 (Anhyzer).
Plan: Pick your path and hope you don't hit a tree. Throw both in practice, pick the 'luckier' one.""",
        16: """(DICTATED PLAN)
The Geometry: High ceiling available. Narrow left/right. Needs a hard right finish.
Disc: Saint (RHFH).
Execution: Slight hyzer release -> Flip to flat -> Reliable fade right.
Goal: Keep it straight!""",
        17: """Mindset: Competing at the Ceiling.
Disc: Firebird
Execution: Max power flex. Open field. If you park it, you earned it. If not, easy par.""",
        18: """Mindset: All Gas No Brakes. Finish strong to set the tone for Round 2.
Disc: MVP Trail
Execution: Needs height. Clear the ridge."""
    },
    "Longs (Round 2)": {
        1: """Disc: Firebird
Line: Aim left of the tree, play the flare skip right.
Goal: BIRDIE (2) or PAR (3).
Warning: Downhill slope behind basket. If you aren't parked (inside 15ft), LAY UP.""",
        2: """Disc: Firebird (Tee) -> Leopard3 (Approach)
Strategy: Firebird to flat. Smooth Leopard3 to glide the final 175ft to the pin.
Goal: Steal a 3. Accept a 4.""",
        3: """Disc: Leopard3
Line: Baby Hyzer flip (Low ceiling).
Note: Aim for the 2/3rds landing zone. Zone spike approach if needed.""",
        4: """Disc: Firebird -> Firebird -> Zone
Strategy: Smooth drive, smooth approach. Don't be a hero.
Goal: Easy Par (4).""",
        5: """Disc: Firebird -> Firebird (Flat)
Adjustment: Zone is too short for Shot 2. Punch the Firebird flat down the hill to get to the green.
Goal: Par (4).""",
        6: """Disc: Leopard3
Swing Thought: "Smooth." Hitting the gap is more important than distance.
Goal: Par (3).""",
        7: """Disc: Firebird (Leopard3 could also work here, use the driver that I am having the most success with)
Focus: Hit initial line and MISS FIRST AVAILABLE.
Power: 60%. Getting past the first tree guarantees a 3. Hitting it guarantees a 4.""",
        8: """Disc: Firebird (Drive) -> Zone/Leopard3 (Park Job)
Strategy: It's a soft Par 4. A clean drive leaves an easy upshot.
Goal: BIRDIE (3).
Safety: If you hit trees, PITCH OUT immediately.""",
        9: """Disc: Leopard3
Line: Baby Hyzer into the hill. (Straight then left).
Approach: Zone HIGH. Spike it over the pencil trees.
WARNING: DO NOT THROW A TURNOVER OFF TEE.""",
        10: """Disc: DX Teebird (Sacrificial)
Line: Clear the water. That is all.
Goal: Par (3).""",
        11: """Disc: Zone -> Zone
The Play: ZONE-ZONE.
Ritual: Throw 150ft to "Locust" tree -> Mark Lie Wipe Disc -> Throw 125ft to basket.
Goal: Stress-free Par (3).""",
        12: """Disc: Firebird (Tee) -> Leopard3 (Gap Shot)
Strategy: Firebird to landing zone. Use Leopard3 to penetrate the tight gap into the green. Let the trees that surround the basket stop the Leopard3 after making the gap.
Note: Don't think about the landing zone, just make the gap. Worst case you pitch up for a bogey. Leopard3 attack here gives a par look with no downside.
Goal: Steal a 3.""",
        13: """Disc: Trail
Line: Flat release, let it drift left and then fade right.
Strategy: Sets up the easy Zone pitch-up for Par (4).
Note: If I nail the landing zone off of the tee, I can attack the green for a birdie putt. Only throw over if I land the drive in my landing zone. Otherwise, pitch up to the landing zone.""",
        14: """Disc: Firebird
Line: WIDER Stall HYZER.
Note: You got pinched last time. Aim further left than you think.
Goal: Par (3).""",
        15: """Disc: Leopard3
Line: Hyzer Flip (Straight).
Note: Trust the disc stability.
Goal: Par (3).""",
        16: """Disc: Leopard3
Approach: ZONE HIGH.
Note: Respect the hill. Throw the approach high to land soft.
Goal: Par (3).""",
        17: """Condition: Coming out of the woods, can be a headwind or Right to Left here.
Disc: Firebird
Line: Max distance flex.
Note: Aim at the basket, let the wind/fade do the work.
Goal: Par (3).""",
        18: """Disc: Trail
Line: OVER THE HILL. (Swing thought - clear the hill by 5ft).
Strategy: This is a par 4. Even with a great drive, play safe and throw second to eat up of remaining distance. Lay-up and take the par.
Goal: Easy Par (4). Don't think about Birdie."""
    }
}

# --- AUTH GATEKEEPER ---
if not st.session_state.logged_in:
    login()
    st.stop()  # Stop execution here if not logged in

# --- MAIN APP (RUNS AFTER LOGIN) ---

# Sidebar Logout
with st.sidebar:
    st.caption("Logged in")
    if st.button("Log Out"):
        logout()
    st.divider()

st.title("🥏 The Mendelsohn Protocol: Tracker")
st.markdown("**Event:** Loriella Challenge (MA4) | **Target:** EVEN PAR")

if OFFLINE_MODE:
    st.warning("⚠️ Offline Mode: Data will not save. Configure Supabase secrets to enable saving.")

# --- SIDEBAR: SETTINGS ---
with st.sidebar:
    st.header("⚙️ Configuration")
    layout = st.radio("Select Layout", ["Shorts (Round 1)", "Longs (Round 2)"])
    
    st.divider()
    st.write("### 🎒 Bag Check")
    # Updated bag list based on user input
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

# --- MAIN INTERFACE ---
tab1, tab2 = st.tabs(["📝 Hole Entry", "📊 Analysis"])

with tab1:
    # Hole Selection
    col1, col2 = st.columns([1, 4])
    with col1:
        hole_num = st.number_input("Hole #", min_value=1, max_value=18, step=1, value=1)
    
    # 1. RETRIEVE STRATEGY
    # Check Database first (for practice notes), then Default Protocol
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
        except:
            pass

    # Display Strategy
    if layout in DEFAULT_STRATEGIES and hole_num in DEFAULT_STRATEGIES[layout]:
        protocol_note = DEFAULT_STRATEGIES[layout][hole_num]
        st.info(f"**📋 THE PROTOCOL (Hole {hole_num})**\n\n{protocol_note}")
    else:
        st.warning("No specific protocol found for this hole.")

    # Display Last Practice Result
    if db_note:
        with st.expander("🔍 View Last Practice Result", expanded=True):
            st.write(f"**Last Disc:** {db_note['disc_used']}")
            st.write(f"**Rating:** {db_note['result_rating']}/5")
            st.markdown(f"**Notes:** *{db_note['notes']}*")

    st.divider()

    # Input Form
    with st.form("entry_form"):
        st.subheader(f"Log Practice: Hole {hole_num}")
        
        all_discs = [d for sublist in bag_sections.values() for d in sublist]
        disc_choice = st.selectbox("Disc Used", all_discs)
        
        c1, c2 = st.columns(2)
        with c1:
            shot_shape = st.selectbox("Shape", ["Straight-to-Fade", "Hyzer Spike", "Flex/Anhyzer", "Hyzer Flip", "Roller", "Straight"])
        with c2:
            rating = st.slider("Rating", 1, 5, 3)
            
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
                
                # 1. Disc Confidence
                st.write("### Disc Confidence (Avg Rating)")
                disc_perf = df.groupby("disc_used")["result_rating"].mean().sort_values(ascending=False)
                st.bar_chart(disc_perf)
                
                # 2. Hole by Hole Breakdown
                st.write("### Hole Breakdown")
                for i in range(1, 19):
                    hole_data = df[df["hole_number"] == i].sort_values("created_at", ascending=False)
                    if not hole_data.empty:
                        latest = hole_data.iloc[0]
                        with st.expander(f"Hole {i}: {latest['disc_used']} ({latest['result_rating']}/5)"):
                            st.write(f"**Notes:** {latest['notes']}")
                            st.caption(f"Logged: {latest['created_at']}")
            else:
                st.info("No practice data logged for this layout yet.")
        except Exception as e:
            st.error(f"Error fetching stats: {e}")
