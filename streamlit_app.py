
import streamlit as st
import math
import json

st.set_page_config(page_title="Niche Validator", page_icon="📊", layout="wide")

# -----------------------------
# Calibrated reverse-engineered engine
# -----------------------------
def clamp(x, lo=0, hi=100):
    return max(lo, min(hi, float(x)))

def ticket_score(cpc):
    if cpc <= 0:
        return 0
    if cpc <= 15:
        return clamp(30 + 2.5 * cpc, 0, 95)
    return clamp(60 + 2.2 * (cpc - 15), 0, 95)

def demand_score(searches):
    if searches <= 0:
        return 0
    if searches < 300:
        return 45 + searches / 300 * 20
    if searches < 700:
        return 65 + (searches - 300) / 400 * 12
    if searches < 1500:
        return 77 + (searches - 700) / 800 * 10
    if searches < 4000:
        return 87 + (searches - 1500) / 2500 * 8
    return 95

def competition_score(directories, weak_sites, strong_sites):
    raw = 58 + 7.5 * directories + 6.5 * weak_sites - 8.5 * strong_sites
    return clamp(raw, 20, 95)

def map_score(map_present, weakest_reviews, strongest_reviews, no_website, no_map_mode):
    if not map_present:
        return 90 if no_map_mode == "Open organic opportunity" else 35
    weak = max(0, weakest_reviews)
    strong = max(0, strongest_reviews)
    weak_factor = 40 / (1 + math.log10(weak + 1))
    strong_penalty = min(10, 1.0 * math.log10(strong + 1))
    raw = 73 + weak_factor - strong_penalty + min(12, 4 * no_website)
    return clamp(raw, 20, 95)

def grade(score):
    return "A" if score >= 85 else "B" if score >= 70 else "C" if score >= 55 else "D" if score >= 40 else "F"

def grade_color(g):
    return {"A":"#72c985","B":"#9dd63c","C":"#e3c75f","D":"#ff9a3d","F":"#f56b6b"}[g]

BENCHMARKS = {
    "Manual entry": None,
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
}

DEFAULT_ROWS = [
    {"Keyword":"", "Monthly Searches":0, "CPC":0.0},
    {"Keyword":"", "Monthly Searches":0, "CPC":0.0},
    {"Keyword":"", "Monthly Searches":0, "CPC":0.0},
]

# -----------------------------
# CSS
# -----------------------------
st.markdown("""
<style>
.block-container {max-width: 1180px; padding-top: 2.2rem; padding-bottom: 4rem;}
.report-shell {background:#172338; border-radius:18px; padding:28px; color:#edf2f8; border:1px solid #30415a;}
.report-shell h1,.report-shell h2,.report-shell h3,.report-shell p {color:#edf2f8;}
.brand {letter-spacing:.16em; font-weight:700; color:#9bd77b; font-size:.9rem;}
.score-card {background:#202d43; border:1px solid #3b4b64; border-radius:14px; padding:18px; text-align:center; min-height:92px;}
.score-letter {font-size:2rem; font-weight:800;}
.signal-label {font-size:1rem; font-weight:700;}
.signal-note {color:#aeb9c8; font-size:.92rem;}
.money-card {background:#182336; border:1px solid #3b4b64; border-radius:14px; padding:18px; text-align:center;}
.money-value {color:#72c985; font-size:1.6rem; font-weight:800;}
.narrative {background:#20373c; border:1px solid #365a60; border-radius:10px; padding:18px; line-height:1.6;}
.raw-box {background:#182336; border:1px solid #3b4b64; border-radius:12px; padding:18px; margin-top:18px;}
.smallcap {letter-spacing:.14em; font-size:.72rem; font-weight:800; color:#9eabba;}
.stButton>button {border-radius:8px; font-weight:700;}
</style>
""", unsafe_allow_html=True)

# -----------------------------
# State initialization
# -----------------------------
if "market_niche" not in st.session_state:
    st.session_state.market_niche = ""
if "market_city" not in st.session_state:
    st.session_state.market_city = ""
if "market_state" not in st.session_state:
    st.session_state.market_state = ""
if "keyword_rows" not in st.session_state:
    st.session_state.keyword_rows = DEFAULT_ROWS.copy()
if "directories" not in st.session_state:
    st.session_state.directories = 0
if "weak_local" not in st.session_state:
    st.session_state.weak_local = 0
if "strong_competitors" not in st.session_state:
    st.session_state.strong_competitors = 0
if "map_present" not in st.session_state:
    st.session_state.map_present = True
if "no_website" not in st.session_state:
    st.session_state.no_website = 0
if "weakest_reviews" not in st.session_state:
    st.session_state.weakest_reviews = 0
if "strongest_reviews" not in st.session_state:
    st.session_state.strongest_reviews = 0
if "no_map_mode" not in st.session_state:
    st.session_state.no_map_mode = "Open organic opportunity"

def load_selected_benchmark():
    choice = st.session_state.benchmark_choice
    b = BENCHMARKS[choice]
    if b is None:
        st.session_state.market_niche = ""
        st.session_state.market_city = ""
        st.session_state.market_state = ""
        st.session_state.keyword_rows = DEFAULT_ROWS.copy()
        st.session_state.directories = 0
        st.session_state.weak_local = 0
        st.session_state.strong_competitors = 0
        st.session_state.map_present = True
        st.session_state.no_website = 0
        st.session_state.weakest_reviews = 0
        st.session_state.strongest_reviews = 0
        st.session_state.no_map_mode = "Open organic opportunity"
    else:
        st.session_state.market_niche = b["niche"]
        st.session_state.market_city = b["city"]
        st.session_state.market_state = b["state"]
        # The key fix: update the editor's actual session-state data.
        st.session_state.keyword_rows = [dict(r) for r in b["rows"]]
        st.session_state.directories = b["directories"]
        st.session_state.weak_local = b["weak"]
        st.session_state.strong_competitors = b["strong"]
        st.session_state.map_present = b["map_present"]
        st.session_state.no_website = b["no_website"]
        st.session_state.weakest_reviews = b["weakest"]
        st.session_state.strongest_reviews = b["strongest"]
        st.session_state.no_map_mode = b["no_map_mode"]

# -----------------------------
# Input screen
# -----------------------------
st.title("📊 Niche Validator")
st.caption("Reverse-engineered local niche and market opportunity validator — benchmark-calibrated build")

st.selectbox(
    "Benchmark loader (testing only)",
    list(BENCHMARKS.keys()),
    key="benchmark_choice",
    on_change=load_selected_benchmark,
)

with st.expander("About this validator"):
    st.write("This build reverse-engineers the scoring architecture from benchmark reports. It does not claim access to the original proprietary source code.")
    st.latex(r"Overall = 0.30T + 0.25D + 0.25C + 0.20M")

st.header("1. Market")
a,b,c = st.columns([2,2,1])
niche = a.text_input("Niche / Service", key="market_niche")
city = b.text_input("City", key="market_city")
state = c.text_input("State", key="market_state")

st.header("2. Core Keyword Data")
rows = st.data_editor(
    st.session_state.keyword_rows,
    num_rows="dynamic",
    use_container_width=True,
    key="keyword_editor",
    column_config={
        "Keyword": st.column_config.TextColumn("Keyword"),
        "Monthly Searches": st.column_config.NumberColumn("Monthly Searches", min_value=0, step=10),
        "CPC": st.column_config.NumberColumn("CPC", min_value=0.0, step=0.01, format="$%.2f"),
    }
)
st.session_state.keyword_rows = rows

searches = sum(float(r.get("Monthly Searches", 0) or 0) for r in rows)
cpcs = [float(r.get("CPC", 0) or 0) for r in rows if float(r.get("CPC", 0) or 0) > 0]
avg_cpc = sum(cpcs) / len(cpcs) if cpcs else 0

x,y = st.columns(2)
x.metric("Total Monthly Searches", f"{searches:,.0f}")
y.metric("Average Non-Zero CPC", f"${avg_cpc:,.2f}")

st.header("3. Organic SERP")
a,b,c = st.columns(3)
directories = a.number_input("Directories in top results", 0, 10, key="directories")
weak_local = b.number_input("Weak / small local sites", 0, 10, key="weak_local")
strong_competitors = c.number_input("Strong established competitors", 0, 10, key="strong_competitors")

st.header("4. Map Pack")
a,b = st.columns(2)
map_present = a.toggle("Map Pack present", key="map_present")
no_website = a.number_input("Businesses without real websites", 0, 20, key="no_website")
weakest_reviews = b.number_input("Weakest competitor review count", 0, 100000, key="weakest_reviews")
strongest_reviews = b.number_input("Strongest competitor review count", 0, 100000, key="strongest_reviews")
no_map_mode = st.selectbox(
    "If no map pack appears, how should the SERP be interpreted?",
    ["Open organic opportunity", "Weak local-intent signal"],
    key="no_map_mode"
)

st.divider()
calculate = st.button("Calculate Opportunity Score", type="primary", use_container_width=True)

if calculate:
    errors = []
    if searches <= 0:
        errors.append("Enter at least one keyword with monthly search volume.")
    if avg_cpc <= 0:
        errors.append("Enter at least one non-zero CPC value.")
    if errors:
        for e in errors:
            st.error(e)
        st.stop()

    T = ticket_score(avg_cpc)
    D = demand_score(searches)
    C = competition_score(directories, weak_local, strong_competitors)
    M = map_score(map_present, weakest_reviews, strongest_reviews, no_website, no_map_mode)
    overall = round(0.30*T + 0.25*D + 0.25*C + 0.20*M)

    job_low, job_high = avg_cpc * 100, avg_cpc * 250
    lead_low, lead_high = avg_cpc * 2, avg_cpc * 4

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="report-shell">', unsafe_allow_html=True)
    st.markdown('<div class="brand">RANK EXPAND ACADEMY · NICHE VALIDATOR</div>', unsafe_allow_html=True)
    st.markdown(f"<h1 style='text-align:center;margin-bottom:0'>{niche}</h1>", unsafe_allow_html=True)
    st.markdown(f"<p style='text-align:center;color:#aeb9c8;margin-top:0'>{city}, {state}</p>", unsafe_allow_html=True)

    g = grade(overall)
    st.markdown(
        f"<div style='text-align:center;margin:22px 0 28px'><div style='font-size:4rem;font-weight:800;color:{grade_color(g)}'>{overall}</div>"
        f"<div style='color:#aeb9c8'>out of 100</div><div style='font-size:1.5rem;font-weight:800;color:{grade_color(g)}'>Grade {g}</div></div>",
        unsafe_allow_html=True
    )

    cols = st.columns(4)
    for col, label, score in zip(cols, ["Ticket price","Local demand","Competition","Map pack opportunity"], [T,D,C,M]):
        gr = grade(score)
        col.markdown(
            f"<div class='score-card'><div class='score-letter' style='color:{grade_color(gr)}'>{gr}</div>"
            f"<div>{label}</div></div>", unsafe_allow_html=True
        )

    narrative = (
        f"Advertisers are paying around ${avg_cpc:,.2f} per click here, which indicates meaningful customer value. "
        f"Search demand totals about {searches:,.0f} monthly searches across the core terms. "
        f"The competitive picture is based on {directories} directory results, {weak_local} weak or small local sites, "
        f"and {strong_competitors} strong established competitors. "
    )
    if not map_present and no_map_mode == "Open organic opportunity":
        narrative += "No map pack is appearing, so this report treats the organic results as an open opportunity."
    elif not map_present:
        narrative += "No map pack is appearing, but this report treats that SERP as a weaker local-intent signal."
    else:
        narrative += f"The map pack is present, with review strength ranging from {weakest_reviews:,} to {strongest_reviews:,} among the competitors entered."
    st.markdown(f"<div class='narrative'>{narrative}</div>", unsafe_allow_html=True)

    st.markdown("<div class='smallcap' style='margin-top:24px'>WHAT THIS NICHE PAYS</div>", unsafe_allow_html=True)
    a,b,c = st.columns(3)
    for col, value, label in [
        (a, f"${job_low:,.0f} – ${job_high:,.0f}", "What an average job is worth"),
        (b, f"${lead_low:,.0f} – ${lead_high:,.0f}", "What one lead sells for"),
        (c, f"${lead_low*10:,.0f} – ${lead_high*10:,.0f}/mo", "One site sending 10 leads a month"),
    ]:
        col.markdown(f"<div class='money-card'><div class='money-value'>{value}</div><div style='color:#aeb9c8'>{label}</div></div>", unsafe_allow_html=True)

    st.markdown("<div class='smallcap' style='margin-top:24px'>THE SIGNALS AT A GLANCE</div>", unsafe_allow_html=True)
    notes = [
        ("Ticket price", T, f"Businesses pay ${avg_cpc:,.2f} for one ad click."),
        ("Local demand", D, f"{searches:,.0f} searches a month across the core terms."),
        ("Competition", C, f"{directories} directory results, {weak_local} weak sites, and {strong_competitors} strong competitors entered."),
        ("Map pack opportunity", M, "Map-pack interpretation is based on the inputs above."),
    ]
    for label, score, note in notes:
        gr = grade(score)
        pct = round(score)
        st.markdown(
            f"<div style='margin-top:14px'><div class='signal-label'>{label} "
            f"<span style='float:right;color:{grade_color(gr)}'>{gr}</span></div>"
            f"<div style='height:8px;background:#344257;border-radius:8px;margin:8px 0'>"
            f"<div style='width:{pct}%;height:8px;background:{grade_color(gr)};border-radius:8px'></div></div>"
            f"<div class='signal-note'>{note}</div></div>",
            unsafe_allow_html=True
        )

    st.markdown("<div class='raw-box'><div class='smallcap'>RAW DATA USED FOR THIS SCORE</div>", unsafe_allow_html=True)
    st.dataframe(rows, use_container_width=True, hide_index=True)
    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    analysis = {
        "market":{"niche":niche,"city":city,"state":state},
        "keywords":rows,
        "inputs":{"directories":directories,"weak_local_sites":weak_local,"strong_competitors":strong_competitors,
                  "map_present":map_present,"no_website":no_website,"weakest_reviews":weakest_reviews,
                  "strongest_reviews":strongest_reviews,"no_map_mode":no_map_mode},
        "scores":{"ticket":round(T,2),"demand":round(D,2),"competition":round(C,2),"map":round(M,2),
                  "overall":overall,"grade":g}
    }
    st.download_button("Download Analysis JSON", json.dumps(analysis, indent=2), "niche-analysis.json", "application/json")
