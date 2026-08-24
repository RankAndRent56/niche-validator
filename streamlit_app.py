import streamlit as st
import math
import json

st.set_page_config(page_title="Niche Validator", page_icon="📊", layout="wide")

def clamp(x, lo=0, hi=100):
    return max(lo, min(hi, float(x)))

def ticket_score(cpc):
    return clamp(20 + 2.83 * cpc, 0, 95)

def demand_score(s):
    if s <= 0: return 40
    if s < 300: return 40 + s/300*20
    if s < 700: return 60 + (s-300)/400*15
    if s < 1500: return 75 + (s-700)/800*10
    if s < 4000: return 85 + (s-1500)/2500*10
    return 95

def competition_score(d, w, strong):
    return clamp(55 + 6*d + 5*w - 8*strong, 20, 95)

def map_score(present, weak, strong, no_site):
    if not present: return 40
    weak_bonus = 35/(1 + math.log10(max(1, weak)+1))
    strong_penalty = min(20, 4*math.log10(max(1, strong)+1))
    return clamp(55 + weak_bonus - strong_penalty + 5*no_site, 20, 95)

def grade(s):
    return "A" if s >= 85 else "B" if s >= 70 else "C" if s >= 55 else "D" if s >= 40 else "F"

st.title("📊 Niche Validator")
st.caption("Reverse-engineered V1 local niche and market opportunity validator")

with st.expander("About this validator"):
    st.write("The overall scoring architecture and weights come from the reverse-engineering project. Component normalization formulas not uniquely recoverable from the benchmark reports are implemented as transparent calibrated approximations.")
    st.latex(r"Overall = 0.30T + 0.25D + 0.25C + 0.20M")

st.header("1. Market")
a,b,c = st.columns([2,2,1])
niche = a.text_input("Niche / Service", placeholder="Garage Door Repair")
city = b.text_input("City", placeholder="San Antonio")
state = c.text_input("State", placeholder="TX")

st.header("2. Core Keyword Data")
rows = st.data_editor(
    [
        {"Keyword":"", "Monthly Searches":0, "CPC":0.0},
        {"Keyword":"", "Monthly Searches":0, "CPC":0.0},
        {"Keyword":"", "Monthly Searches":0, "CPC":0.0},
    ],
    num_rows="dynamic",
    use_container_width=True,
    key="keywords"
)

searches = sum(float(r.get("Monthly Searches", 0) or 0) for r in rows)
cpcs = [float(r.get("CPC", 0) or 0) for r in rows if float(r.get("CPC", 0) or 0) > 0]
avg_cpc = sum(cpcs)/len(cpcs) if cpcs else 0

a,b = st.columns(2)
a.metric("Total Monthly Searches", f"{searches:,.0f}")
b.metric("Average Non-Zero CPC", f"${avg_cpc:,.2f}")

st.header("3. Organic SERP")
a,b,c = st.columns(3)
directories = a.number_input("Directories in top results", 0, 10, 2)
weak_local = b.number_input("Weak / small local sites", 0, 10, 2)
strong_competitors = c.number_input("Strong established competitors", 0, 10, 1)

st.header("4. Map Pack")
a,b = st.columns(2)
map_present = a.toggle("Map Pack present", True)
no_website = a.number_input("Businesses without real websites", 0, 20, 0)
weakest_reviews = b.number_input("Weakest competitor review count", 0, 100000, 10)
strongest_reviews = b.number_input("Strongest competitor review count", 0, 100000, 100)

st.divider()
if st.button("Calculate Opportunity Score", type="primary", use_container_width=True):
    T = ticket_score(avg_cpc)
    D = demand_score(searches)
    C = competition_score(directories, weak_local, strong_competitors)
    M = map_score(map_present, weakest_reviews, strongest_reviews, no_website)
    overall = round(0.30*T + 0.25*D + 0.25*C + 0.20*M)

    st.header("Results")
    st.metric("Overall Opportunity", f"{overall}/100 — Grade {grade(overall)}")
    a,b,c,d = st.columns(4)
    a.metric("Ticket Price", f"{round(T)}/100", "30% weight")
    b.metric("Local Demand", f"{round(D)}/100", "25% weight")
    c.metric("Competition", f"{round(C)}/100", "25% weight")
    d.metric("Map Pack", f"{round(M)}/100", "20% weight")

    st.subheader("Economic Opportunity")
    a,b,c = st.columns(3)
    a.metric("Estimated Job Value", f"${avg_cpc*100:,.0f}–${avg_cpc*250:,.0f}")
    a2, b2 = avg_cpc*2, avg_cpc*4
    b.metric("Estimated Lead Value", f"${a2:,.0f}–${b2:,.0f}")
    c.metric("Estimated Value of 10 Leads", f"${a2*10:,.0f}–${b2*10:,.0f}")

    analysis = {
        "market":{"niche":niche,"city":city,"state":state},
        "keywords":rows,
        "scores":{"ticket":round(T,2),"demand":round(D,2),"competition":round(C,2),"map":round(M,2),"overall":overall,"grade":grade(overall)}
    }
    st.download_button("Download Analysis JSON", json.dumps(analysis, indent=2), "niche-analysis.json", "application/json")
