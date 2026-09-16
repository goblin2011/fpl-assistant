# FPL Assistant

A free, personal recommendation dashboard for Fantasy Premier League. Pulls
live data from the official (public, no key needed) FPL API and scores
players on form, upcoming fixture difficulty, underlying stats (xG/xA), and
value for money.

## Run it

All files live in one flat folder (no subfolders) so it's easy to upload
manually to GitHub — `main.py`, `model.py`, `optimizer.py`, `fpl_client.py`
are the backend; `index.html` is the whole frontend.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

Then open `index.html` in a browser (or serve it with
`python3 -m http.server 5500` from this same folder).

## What it does

- **Rankings** — every player scored and ranked, filterable by position/price.
- **Suggested Squad** — builds a valid 15-man squad (2/5/5/3, £100m budget,
  max 3 per club) and picks a starting XI + captain/vice-captain.
- **My Team** — paste your FPL team ID to see your current squad ranked by
  the model, plus transfer suggestions.

## Model (v2)

Weighted blend, each factor normalized 0-1 across all players, plus a flat
set-piece-duty bonus:

| Factor | Weight | Source |
|---|---|---|
| Recent form | 28% | FPL `form` field |
| Fixture ease (next 3 GWs) | 20% | FPL fixture difficulty ratings |
| Availability (injury/suspension-aware) | 18% | FPL `status` code + chance of playing |
| Value (points per £m) | 12% | total points / price |
| Underlying stats (xG/xA per 90) | 12% | FPL expected stats |
| Minutes security | 10% | starts / finished gameweeks |
| Set-piece duty | flat bonus | penalty/corner/free-kick taker order |

Weights live in `model.py` — tune them as you see how recommendations
perform week to week.

## Notes

- Not affiliated with the Premier League or FPL — uses their public API.
- Squad optimizer is a greedy heuristic, not a full ILP solver — good enough
  for a v1, can be swapped for a proper solver (e.g. PuLP) later.
