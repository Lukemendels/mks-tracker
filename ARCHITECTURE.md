# MKS Tracker - Architecture & System Guide

## 1. Project Overview
**MKS Tracker** is a specialized Disc Golf application designed to implement "The Mendelsohn Protocol" at **Loriella Park**. It focuses on:
-   **Mindset**: Delivering specific "Mindset Axioms" per hole.
-   **Strategy**: Providing structured shot protocols (Disc, Shape, Execution Notes) based on the course layout.
-   **Data Collection**: Logging shots, disc selection, and weather conditions for analysis.

## 2. Tech Stack
-   **Frontend/Backend**: [Streamlit](https://streamlit.io/) (Python)
-   **Database**: [Supabase](https://supabase.com/) (PostgreSQL)
-   **Authentication**: Supabase Auth (Email/Password)
-   **Weather API**: [Open-Meteo](https://open-meteo.com/) (Free, no key required)
-   **State Persistence**: `extra-streamlit-components` (Cookie Manager)
-   **Timezone**: `pytz` (America/New_York)

## 3. Database Schema (Supabase)

### `course_metadata`
Stores the static "Protocol" for each hole/layout combination.
-   `id`: UUID
-   `hole_number`: Integer (1-18)
-   `layout`: Text ("Shorts (Round 1)" or "Longs (Round 2)")
-   `par`: Integer
-   `suggested_disc`: Text (FK -> `discs.name`)
-   `shot_shape`: Text (e.g., "RHFH Flat", "RHBH Hyzer")
-   `execution_notes`: Text (Specific aiming points/warnings)
-   `Attack_Hole`: Text ("Yes"/"No") - Determines dynamic scoring target.
-   `mindset_axiom_id`: (FK -> `mindset_axioms.id` - *Note: Schema implementation details may vary, currently joined in query*)

### `discs`
The user's bag inventory.
-   `id`: Serial
-   `name`: Text (Unique)
-   `plastic`: Text
-   `speed`, `glide`, `turn`, `fade`: Numeric
-   `disc_type`: Text (Putter, Approach, Midrange, Fairway Driver, Distance Driver)

### `rounds`
Sessions of play.
-   `id`: UUID
-   `name`: Text (Timestamp-based, e.g., "02-18-26-0705AM-Shorts")
-   `layout`: Text
-   `selected_discs`: Array of Text (Subset of `discs.name` carried for this round)
-   `created_at`: Timestamptz

### `practice_notes`
Individual shot logs.
-   `id`: Serial
-   `round_id`: UUID (FK -> `rounds.id`)
-   `hole_number`: Integer
-   `layout`: Text
-   `disc_used`: Text
-   `strokes`: Integer
-   `result_rating`: Integer (1-5 Confidence)
-   `notes`: Text
-   `temperature`: Integer
-   `wind_speed`: Integer
-   `wind_gust`: Integer
-   `wind_direction`: Text
-   `created_at`: Timestamptz

### `mindset_axioms`
Psychological principles linked to holes.
-   `id`: Serial
-   `short_name`: Text (e.g., "Axiom I")
-   `title`: Text
-   `corollary`: Text

## 4. Application Logic & State Management

### Authentication & Persistence
The app uses a dual-layer state approach to handle the "Close App / Reopen App" workflow typical of disc golf:
1.  **Streamlit Session State**: Valid only while the tab is open.
2.  **Browser Cookies** (via `CookieManager`):
    -   `mks_refresh_token`: Keeps user logged in for 30 days.
    -   `mks_round_id`: Remembers the active `round_id` for 24 hours.
    -   `mks_hole_num`: Remembers the last viewed hole number.

**Startup Flow:**
1.  App loads -> Checks `st.session_state`.
2.  Empty? -> Checks Cookies.
3.  Cookie found? -> Calls `supabase.auth.refresh_session()` and restores Round/Hole state from DB.

### Dynamic Target Calculation
The app calculates a "Target Score" dynamically based on the layout:
-   **Logic**: `Target = -1 * floor(Count(Attack_Hole="Yes") / 2)`
-   **Example**: 6 Attack holes -> Target -3.

### Weather Integration
-   Fetches from Open-Meteo API based on Loriella Park coordinates (`38.2544, -77.5443`).
-   **Display**: Compact 2-column widget in Sidebar (Temp | Wind + Gust/Dir).
-   **Logging**: Automatically saves snapshot of weather with every `practice_note`.

## 5. User Experience (UX) Flow
1.  **Login**: One-time (persisted via cookie).
2.  **Sidebar**:
    -   **Weather**: Instant check of conditions.
    -   **Start Round**: Select Layout (Shorts/Longs) + Filter Bag (select which discs you are carrying).
3.  **Main Screen**:
    -   **Header**: `🔴 Red Basket: Hole 1 | 🟢 ATTACK` (Unified status line).
    -   **Navigation**: Big `⬅️` `➡️` buttons for mobile use.
    -   **Protocol**: 
        -   Shows Disc, Shape, and Notes.
        -   Shows Mindset Axiom (The "Why").
    -   **Logging (Tab 1)**:
        -   Auto-fills "Disc Used" if one is suggested.
        -   Auto-fills "Shape" if suggested.
        -   One-tap "Save Data" (Toasts success, stays on hole or moves next? *Currently re-runs*).
4.  **Analysis (Tab 2)**:
    -   View average strokes and disc confidence for the current layout.
5.  **Export (Tab 3)**:
    -   Download JSON of round history for AI analysis.

## 6. Future Context / Handover Notes
-   **Timezones**: All `datetime` operations utilize `pytz.timezone('America/New_York')`.
-   **Deployment**: Sensitive keys utilize `st.secrets` in Cloud, `.env` locally.
-   **Mobile Optimization**: The UI is explicitly tuned for mobile (collapsed inputs, large buttons, compact headers).
-   **Supabase Client**: Uses `supabase-py`. The schema is stable.
