# **🥏 MKS Disc Golf Tracker: The Mendelsohn Protocol**

"I am the standard. They have to beat me; I will not beat myself."

## **Overview**

This application is the digital enforcement of **The Mendelsohn Kernel Standard (MKS)**, a strategic mental framework designed for competitive play at Loriella Park. It replaces "feeling" with **data** and "deliberation" with **execution**.

The app serves two critical functions:

1. **The Protocol (The Caddie):** Displays the specific, pre-determined game plan for every hole (Shorts & Longs) by linking tactical notes to core mental axioms.  
2. **The Kernel (The Analyst):** Logs performance data (Disc selection, Shot shape, Strokes) to identify "ghosts" in the system and refine the bag for Tournament Day.

## **The Core Axioms (MKS v1.0)**

* **Axiom I: THE LAW OF BORING GOLF:** The Sexton Principle. A stroke saved by safety is worth more than a stroke gained by brilliance.  
* **Axiom II: EMOTIONAL NEUTRALITY:** The Conrad Doctrine. All thinking happens *behind* the box. Inside the box is for execution only.  
* **Axiom III: DATA OVER MEMORY:** The McBeth Corollary. Trust the physics of the disc and the recorded data over the "feeling" of the previous hole.  
* **Axiom IV: ALL GAS UNTIL NO BRAKES ARE NEEDED:** The Klein Strategy. Identify the commit point and execute with 100% conviction.  
* **Axiom V: COMPETING AT THE CEILING:** Maximizing potential through aggressive landing zone penetration and tactical positioning.

## **Tech Stack**

* **Frontend:** Streamlit (Python)  
* **Database:** Supabase (PostgreSQL)  
* **Auth:** Supabase Auth (JWT-based session management)  
* **Weather:** Open-Meteo API (Loriella Park coordinates)

## **Setup & Installation**

### **1\. Clone the Repository**

git clone \[https://github.com/Lukemendels/mks-tracker.git\](https://github.com/Lukemendels/mks-tracker.git)  
cd mks-tracker

### **2\. Install Dependencies**

python3 \-m venv venv  
source venv/bin/activate  
pip install \-r requirements.txt

### **3\. Configure Secrets**

Create a .streamlit/secrets.toml file (**Do not commit this\!**):

SUPABASE\_URL \= "your\_project\_url"  
SUPABASE\_KEY \= "your\_public\_anon\_key"

## **Database Setup (Supabase SQL)**

To initialize the MKS backend, run the following script in your Supabase SQL Editor. This establishes the relational integrity between your mental axioms and hole-by-hole tactics.

\-- Create the mental framework table  
CREATE TABLE mindset\_axioms (  
    id SERIAL PRIMARY KEY,  
    short\_name VARCHAR(20) NOT NULL,  
    title VARCHAR(255) NOT NULL,  
    corollary TEXT,  
    created\_at TIMESTAMPTZ DEFAULT NOW()  
);

\-- Create the strategy table  
CREATE TABLE course\_metadata (  
    id SERIAL PRIMARY KEY,  
    hole\_number INTEGER NOT NULL,  
    layout VARCHAR(50) NOT NULL,  
    protocol\_notes TEXT,  
    axiom\_id INTEGER REFERENCES mindset\_axioms(id),  
    created\_at TIMESTAMPTZ DEFAULT NOW(),  
    UNIQUE(hole\_number, layout)  
);

\-- Create the performance log table  
CREATE TABLE practice\_notes (  
    id SERIAL PRIMARY KEY,  
    hole\_number INTEGER NOT NULL,  
    layout VARCHAR(50) NOT NULL,  
    disc\_used VARCHAR(100),  
    result\_rating INTEGER CHECK (result\_rating BETWEEN 1 AND 5),  
    strokes INTEGER,  
    notes TEXT,  
    created\_at TIMESTAMPTZ DEFAULT NOW()  
);

\-- Enable Row Level Security (RLS)  
ALTER TABLE mindset\_axioms ENABLE ROW LEVEL SECURITY;  
ALTER TABLE course\_metadata ENABLE ROW LEVEL SECURITY;  
ALTER TABLE practice\_notes ENABLE ROW LEVEL SECURITY;

\-- Seed the Axioms  
INSERT INTO mindset\_axioms (id, short\_name, title, corollary) VALUES  
(1, 'Axiom I', 'THE LAW OF BORING GOLF', 'The Sexton Principle'),  
(2, 'Axiom II', 'EMOTIONAL NEUTRALITY', 'The Conrad Doctrine'),  
(3, 'Axiom III', 'DATA OVER MEMORY', 'The McBeth Corollary'),  
(4, 'Axiom IV', 'ALL GAS UNTIL NO BRAKES ARE NEEDED', 'The Klein Strategy'),  
(5, 'Axiom V', 'COMPETING AT THE CEILING', 'Maximizing potential through execution');

## **🎒 Bag Configuration (RHFH Primary)**

The Mendelsohn Protocol is optimized for **Right-Hand Forehand** execution.

* **Distance:** Star Wraith (Max D), MVP Neutron Trail (Control)  
* **Fairway:** Champion Firebird (OS Utility), Champion Thunderbird (Stable), Star Leopard3 (Understable), DX Teebird (Beat-in)  
* **Midrange:** Champion Caiman (OS), Star Mako3 (Neutral), Halo Star Fox (Understable)  
* **Approach/Putter:** ESP FLX Zone (Overstable), MVP Neutron Watt (Neutral)

*Developed by Focus Flow Systems LLC.*
