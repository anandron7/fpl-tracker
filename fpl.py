import json
import os
from datetime import datetime, timezone
import requests

TEAM_ID = 2521217
BASE = "https://fantasy.premierleague.com/api"

session = requests.Session()
session.headers.update({"User-Agent": "Mozilla/5.0 (compatible; FPLTracker/1.0)"})

def get_json(path):
    r = session.get(f"{BASE}{path}", timeout=30)
    r.raise_for_status()
    return r.json()

bootstrap = get_json("/bootstrap-static/")
entry = get_json(f"/entry/{TEAM_ID}/")
history = get_json(f"/entry/{TEAM_ID}/history/")
transfers = get_json(f"/entry/{TEAM_ID}/transfers/")

events = bootstrap["events"]
current_gw = next((e["id"] for e in events if e.get("is_current")), None)
if current_gw is None:
    finished = [e["id"] for e in events if e.get("finished")]
    current_gw = max(finished) if finished else 1

try:
    picks = get_json(f"/entry/{TEAM_ID}/event/{current_gw}/picks/")
except Exception:
    picks = None

players = {
    p["id"]: {
        "name": p["web_name"],
        "team_id": p["team"],
        "position_id": p["element_type"],
        "price": p["now_cost"] / 10,
        "status": p["status"],
        "news": p["news"],
        "total_points": p["total_points"],
        "selected_by_percent": p["selected_by_percent"],
        "form": p["form"],
        "chance_of_playing_next_round": p.get("chance_of_playing_next_round"),
    }
    for p in bootstrap["elements"]
}
teams = {t["id"]: t["short_name"] for t in bootstrap["teams"]}
positions = {1: "GK", 2: "DEF", 3: "MID", 4: "FWD"}

squad = []
entry_history = None
if picks:
    entry_history = picks.get("entry_history")
    for pick in picks["picks"]:
        p = players[pick["element"]]
        squad.append({
            "player_id": pick["element"],
            "name": p["name"],
            "club": teams[p["team_id"]],
            "position": positions[p["position_id"]],
            "price": p["price"],
            "squad_position": pick["position"],
            "captain": pick["is_captain"],
            "vice_captain": pick["is_vice_captain"],
            "multiplier": pick["multiplier"],
            "status": p["status"],
            "news": p["news"],
            "chance_of_playing_next_round": p["chance_of_playing_next_round"],
            "season_points": p["total_points"],
            "form": p["form"],
            "selected_by_percent": p["selected_by_percent"],
        })

mini_leagues = []
for league in entry.get("leagues", {}).get("classic", []):
    item = {
        "id": league["id"],
        "name": league["name"],
        "entry_rank": league.get("entry_rank"),
        "entry_last_rank": league.get("entry_last_rank"),
        "league_type": league.get("league_type"),
        "standings": None,
    }
    if league.get("league_type") == "x":
        try:
            st = get_json(f"/leagues-classic/{league['id']}/standings/?page_standings=1")
            item["standings"] = [
                {
                    "rank": r.get("rank"),
                    "entry": r.get("entry"),
                    "entry_name": r.get("entry_name"),
                    "player_name": r.get("player_name"),
                    "event_total": r.get("event_total"),
                    "total": r.get("total"),
                    "is_you": r.get("entry") == TEAM_ID,
                }
                for r in st.get("standings", {}).get("results", [])
            ]
        except Exception as exc:
            item["standings_error"] = str(exc)
    mini_leagues.append(item)

output = {
    "updated_at_utc": datetime.now(timezone.utc).isoformat(),
    "team_id": TEAM_ID,
    "team_name": entry.get("name"),
    "manager": {
        "first_name": entry.get("player_first_name"),
        "last_name": entry.get("player_last_name"),
    },
    "overall": {
        "points": entry.get("summary_overall_points"),
        "rank": entry.get("summary_overall_rank"),
        "event_points": entry.get("summary_event_points"),
        "event_rank": entry.get("summary_event_rank"),
    },
    "gameweek": {
        "current": current_gw,
        "entry_history": entry_history,
    },
    "squad": squad,
    "chips": history.get("chips", []),
    "history": history.get("current", []),
    "transfers": transfers,
    "mini_leagues": mini_leagues,
}

os.makedirs("public", exist_ok=True)
with open("public/fpl.json", "w", encoding="utf-8") as f:
    json.dump(output, f, indent=2, ensure_ascii=False)

print("Wrote public/fpl.json")
