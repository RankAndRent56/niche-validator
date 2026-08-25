import streamlit as st
import math
import json

st.set_page_config(page_title="Niche Validator", page_icon="📊", layout="wide")

# Reverse-engineered scoring architecture:
# Overall = 30% Ticket + 25% Demand + 25% Competition + 20% Map Pack.
# The component normalizations below are calibrated against the benchmark reports
# collected during the reverse-engineering project. They are intentionally exposed
# as calibrated estimates rather than claimed to be the original proprietary code.

def clamp(x, lo=0, hi=100):
    return max(lo, min(hi, float(x)))

def ticket_score(cpc):
    # Calibrates the observed transition: roughly $12 = C, $27+ = A.
    if cpc <= 0:
        return 0
    if cpc <= 15:
        return clamp(30 + 2.5 * cpc, 0, 95)
    return clamp(60 + 2.2 * (cpc - 15), 0, 95)

def demand_score(searches):
    if searches <= 0:
        return 0
    if searches < 300:
        return 45 + searches / 300 * 20       # ~280 -> C
    if searches < 700:
        return 65 + (searches - 300) / 400 * 12  # ~640 -> B
    if searches < 1500:
        return 77 + (searches - 700) / 800 * 10
    if searches < 4000:
        return 87 + (searches - 1500) / 2500 * 8
    return 95

def competition_score(directories, weak_sites, strong_sites):
    # More directories and more weak local sites help; strong established sites hurt.
    raw = 58 + 7.5 * directories + 6.5 * weak_sites - 8.5 * strong_sites
    return clamp(raw, 20, 95)

def map_score(map_present, weakest_reviews, strongest_reviews, no_website, no_map_mode):
    if not map_present:
        # The benchmark reports show that "no map pack" is not always scored the same.
        # It can mean open organic opportunity, or weak local intent. The original
        # validator uses additional SERP context that is not recoverable from a simple
        # present/absent toggle, so this explicit mode preserves that distinction.
        return 90 if no_map_mode == "Open organic opportunity" else 35

    weak = max(0, weakest_reviews)
    strong = max(0, strongest_reviews)
    # Low review counts at the bottom of the pack are the dominant positive signal.
    weak_factor = 40 / (1 + math.log10(weak + 1))
    strong_penalty = min(10, 1.0 * math.log10(strong + 1))
    raw = 73 + weak_factor - strong_penalty + min(12, 4 * no_website)
    return clamp(raw, 20, 95)

def grade(score):
    return "A" if score >= 85 else "B" if score >= 70 else "C" if score >= 55 else "D" if score >= 40 else "F"

def letter_color(letter):
    return {"A":"🟢","B":"🟢","C":"🟡","D":"🟠","F":"🔴"}.get(letter, "⚪")

BENCHMARKS = {
    "None / manual entry": None,
    "Plumbing — Tempe, AZ (90/100 benchmark)": {
        "niche":"Plumbing", "city":"Tempe", "state":"AZ",
        "rows":[
            {"Keyword":"plumber tempe", "Monthly Searches":880, "CPC":52.66},
            {"Keyword":"tempe plumber", "Monthly Searches":880, "CPC":52.66},
        ],
        "directories":2, "weak":2, "strong":0,
        "map_present":False, "no_website":0, "weakest":0, "strongest":0,
        "no_map_mode":"Open organic opportunity",
    },
    "Epoxy Flooring — Orlando, FL (75/100 benchmark)": {
        "niche":"Epoxy Flooring", "city":"Orlando", "state":"FL",
        "rows":[
            {"Keyword":"epoxy flooring orlando", "Monthly Searches":320, "CPC":11.98},
            {"Keyword":"orlando epoxy flooring", "Monthly Searches":320, "CPC":11.98},
        ],
        "directories":1, "weak":2, "strong":1,
        "map_present":True, "no_website":0, "weakest":11, "strongest":82,
        "no_map_mode":"Open organic opportunity",
    },
    "Garage Door Repair — Joliet, IL (77/100 benchmark)": {
        "niche":"Garage Door Repair", "city":"Joliet", "state":"IL",
        "rows":[
            {"Keyword":"garage door repair joliet", "Monthly Searches":140, "CPC":27.11},
            {"Keyword":"joliet garage door repair", "Monthly Searches":140, "CPC":27.11},
        ],
        "directories":1, "weak":2, "strong":1,
        "map_present":True, "no_website":0, "weakest":28, "strongest":2300,
        "no_map_mode":"Open organic opportunity",
    },
}

st.title("📊 Niche Validator")
st.caption("Reverse-engineered local niche and market opportunity validator — benchmark-calibrated build")

with st.expander("About this validator"):
    st.write("The overall architecture is reverse-engineered from the original validator and benchmark reports. The four component normalizations are calibrated approximations because the proprietary source formulas were not available.")
    st.latex(r"Overall = 0.30T + 0.25D + 0.25C + 0.20M")
    st.write("Important: a zero-filled keyword table does not mean zero market demand. The app now blocks calculation until real keyword/search/CPC data is entered.")

benchmark_choice = st.selectbox("Optional benchmark loader (for validation/testing)", list(BENCHMARKS.keys()))
benchmark = BENCHMARKS[benchmark_choice]

def default(name, fallback):
    return benchmark[name] if benchmark else fallback

st.header("1. Market")
a,b,c = st.columns([2,2,1])
niche = a.text_input("Niche / Service", value=default("niche", ""), placeholder="Garage Door Repair")
city = b.text_input("City", value=default("city", ""), placeholder="San Antonio")
state = c.text_input("State", value=default("state", ""), placeholder="TX")

st.header("2. Core Keyword Data")
default_rows = benchmark["rows"] if benchmark else [
    {"Keyword":"", "Monthly Searches":0, "CPC":0.0},
    {"Keyword":"", "Monthly Searches":0, "CPC":0.0},
    {"Keyword":"", "Monthly Searches":0, "CPC":0.0},
]
rows = st.data_editor(default_rows, num_rows="dynamic", use_container_width=True, key=f"keywords_{benchmark_choice}")

searches = sum(float(r.get("Monthly Searches", 0) or 0) for r in rows)
cpcs = [float(r.get("CPC", 0) or 0) for r in rows if float(r.get("CPC", 0) or 0) > 0]
avg_cpc = sum(cpcs) / len(cpcs) if cpcs else 0

a,b = st.columns(2)
a.metric("Total Monthly Searches", f"{searches:,.0f}")
b.metric("Average Non-Zero CPC", f"${avg_cpc:,.2f}")

st.header("3. Organic SERP")
a,b,c = st.columns(3)
directories = a.number_input("Directories in top results", 0, 10, int(default("directories", 0)))
weak_local = b.number_input("Weak / small local sites", 0, 10, int(default("weak", 0)))
strong_competitors = c.number_input("Strong established competitors", 0, 10, int(default("strong", 0)))

st.header("4. Map Pack")
a,b = st.columns(2)
map_present = a.toggle("Map Pack present", value=bool(default("map_present", True)))
no_website = a.number_input("Businesses without real websites", 0, 20, int(default("no_website", 0)))
weakest_reviews = b.number_input("Weakest competitor review count", 0, 100000, int(default("weakest", 0)))
strongest_reviews = b.number_input("Strongest competitor review count", 0, 100000, int(default("strongest", 0)))
no_map_mode = st.selectbox(
    "If no map pack appears, how should the SERP be interpreted?",
    ["Open organic opportunity", "Weak local-intent signal"],
    index=0 if default("no_map_mode", "Open organic opportunity") == "Open organic opportunity" else 1,
    help="This explicit distinction is necessary because the benchmark reports scored different no-map SERPs differently."
)

st.divider()
if st.button("Calculate Opportunity Score", type="primary", use_container_width=True):
    errors = []
    if searches <= 0: errors.append("Enter at least one keyword with monthly search volume.")
    if avg_cpc <= 0: errors.append("Enter at least one non-zero CPC value.")
    if errors:
        for e in errors: st.error(e)
        st.stop()

    T = ticket_score(avg_cpc)
    D = demand_score(searches)
    C = competition_score(directories, weak_local, strong_competitors)
    M = map_score(map_present, weakest_reviews, strongest_reviews, no_website, no_map_mode)
    overall = round(0.30*T + 0.25*D + 0.25*C + 0.20*M)

    st.header("Results")
    st.metric("Overall Opportunity", f"{overall}/100 — Grade {grade(overall)}")
    a,b,c,d = st.columns(4)
    a.metric("Ticket Price", f"{round(T)}/100 — {grade(T)}", "30% weight")
    b.metric("Local Demand", f"{round(D)}/100 — {grade(D)}", "25% weight")
    c.metric("Competition", f"{round(C)}/100 — {grade(C)}", "25% weight")
    d.metric("Map Pack", f"{round(M)}/100 — {grade(M)}", "20% weight")

    st.subheader("Economic Opportunity")
    a,b,c = st.columns(3)
    a.metric("Estimated Job Value", f"${avg_cpc*100:,.0f}–${avg_cpc*250:,.0f}")
    a2, b2 = avg_cpc*2, avg_cpc*4
    b.metric("Estimated Lead Value", f"${a2:,.0f}–${b2:,.0f}")
    c.metric("Estimated Value of 10 Leads", f"${a2*10:,.0f}–${b2*10:,.0f}")

    st.subheader("Score Check")
    st.write(f"{letter_color(grade(T))} Ticket: {grade(T)}  •  {letter_color(grade(D))} Demand: {grade(D)}  •  {letter_color(grade(C))} Competition: {grade(C)}  •  {letter_color(grade(M))} Map: {grade(M)}")

    analysis = {
        "market":{"niche":niche,"city":city,"state":state},
        "keywords":rows,
        "inputs":{"directories":directories,"weak_local_sites":weak_local,"strong_competitors":strong_competitors,"map_present":map_present,"no_website":no_website,"weakest_reviews":weakest_reviews,"strongest_reviews":strongest_reviews,"no_map_mode":no_map_mode},
        "scores":{"ticket":round(T,2),"demand":round(D,2),"competition":round(C,2),"map":round(M,2),"overall":overall,"grade":grade(overall)}
    }
    st.download_button("Download Analysis JSON", json.dumps(analysis, indent=2), "niche-analysis.json", "application/json")
