# Niche Validator — Revised Build

This revision addresses the first deployed-version problems found during live testing.

## What changed
- Prevents calculation with an empty keyword table (the source of the misleading 46/100 result in the latest test).
- Adds benchmark loaders for Plumbing/Tempe, Epoxy Flooring/Orlando, and Garage Door Repair/Joliet.
- Refines the ticket-price, competition, and map-pack calibration.
- Separates the two benchmark-observed meanings of "no map pack": open organic opportunity vs. weak local-intent signal.
- Keeps the reverse-engineered overall weighting: 30% Ticket, 25% Demand, 25% Competition, 20% Map Pack.

## Deploy
Replace the existing `streamlit_app.py` in the GitHub repository with the revised file. Streamlit should automatically redeploy.

Repository files:
- `streamlit_app.py`
- `requirements.txt`
- `README.md`
