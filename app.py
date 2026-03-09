"""
🤖 Sport AI Ágens - Focimeccs Elemző
=====================================
Elemzi a meccseket és visszaadja:
- 🟨 Sok sárga lapra esélyes meccsek
- ⚽ Sok gólra esélyes meccsek (Over 2.5)
- ✅ Mindkét csapat szerez (BTTS)
- 📊 Csapat részletes elemzése

Használat:
- "Elemezd a holnapi meccseket"
- "2024-03-15 meccsek"
- "Liverpool elemzés"
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
from datetime import datetime, timedelta
import os
from anthropic import Anthropic

app = Flask(__name__)
CORS(app)  # Engedélyezi a cross-origin kéréseket (fontos a weboldalhoz)

# ============================================
# 🔑 API KULCSOK (környezeti változókból)
# ============================================
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "your-anthropic-key-here")
FOOTBALL_API_KEY = os.getenv("FOOTBALL_API_KEY", "your-football-api-key-here")

# API-Football.com beállítások
FOOTBALL_API_BASE = "https://v3.football.api-sports.io"
FOOTBALL_HEADERS = {
    "x-apisports-key": FOOTBALL_API_KEY
}

# Claude kliens
anthropic = Anthropic(api_key=ANTHROPIC_API_KEY)

# ============================================
# 📊 FOOTBALL API FÜGGVÉNYEK
# ============================================

def get_fixtures_by_date(date_str: str) -> list:
    """
    Lekéri az adott napi meccseket.
    date_str formátum: "YYYY-MM-DD"
    """
    url = f"{FOOTBALL_API_BASE}/fixtures"
    params = {"date": date_str}
    
    try:
        response = requests.get(url, headers=FOOTBALL_HEADERS, params=params)
        data = response.json()
        
        if data.get("response"):
            return data["response"]
        return []
    except Exception as e:
        print(f"API hiba: {e}")
        return []


def get_team_statistics(team_id: int, league_id: int, season: int = 2024) -> dict:
    """
    Lekéri egy csapat részletes statisztikáit.
    """
    url = f"{FOOTBALL_API_BASE}/teams/statistics"
    params = {
        "team": team_id,
        "league": league_id,
        "season": season
    }
    
    try:
        response = requests.get(url, headers=FOOTBALL_HEADERS, params=params)
        data = response.json()
        
        if data.get("response"):
            return data["response"]
        return {}
    except Exception as e:
        print(f"API hiba: {e}")
        return {}


def get_h2h(team1_id: int, team2_id: int) -> list:
    """
    Lekéri két csapat egymás elleni eredményeit.
    """
    url = f"{FOOTBALL_API_BASE}/fixtures/headtohead"
    params = {"h2h": f"{team1_id}-{team2_id}", "last": 10}
    
    try:
        response = requests.get(url, headers=FOOTBALL_HEADERS, params=params)
        data = response.json()
        
        if data.get("response"):
            return data["response"]
        return []
    except Exception as e:
        print(f"API hiba: {e}")
        return []


def search_team(team_name: str) -> dict:
    """
    Keres egy csapatot név alapján.
    """
    url = f"{FOOTBALL_API_BASE}/teams"
    params = {"search": team_name}
    
    try:
        response = requests.get(url, headers=FOOTBALL_HEADERS, params=params)
        data = response.json()
        
        if data.get("response") and len(data["response"]) > 0:
            return data["response"][0]
        return {}
    except Exception as e:
        print(f"API hiba: {e}")
        return {}


def get_fixture_statistics(fixture_id: int) -> list:
    """
    Lekéri egy meccs részletes statisztikáit (ha már lejátszották).
    """
    url = f"{FOOTBALL_API_BASE}/fixtures/statistics"
    params = {"fixture": fixture_id}
    
    try:
        response = requests.get(url, headers=FOOTBALL_HEADERS, params=params)
        data = response.json()
        
        if data.get("response"):
            return data["response"]
        return []
    except Exception as e:
        print(f"API hiba: {e}")
        return []


def get_predictions(fixture_id: int) -> dict:
    """
    Lekéri az API előrejelzéseit egy meccsre.
    """
    url = f"{FOOTBALL_API_BASE}/predictions"
    params = {"fixture": fixture_id}
    
    try:
        response = requests.get(url, headers=FOOTBALL_HEADERS, params=params)
        data = response.json()
        
        if data.get("response") and len(data["response"]) > 0:
            return data["response"][0]
        return {}
    except Exception as e:
        print(f"API hiba: {e}")
        return {}


# ============================================
# 🧠 ELEMZŐ FÜGGVÉNYEK
# ============================================

def analyze_fixtures_for_cards(fixtures: list) -> list:
    """
    Elemzi a meccseket sárga lap szempontjából.
    Visszaadja a top 10 legesélyesebb meccset.
    """
    scored_fixtures = []
    
    for fixture in fixtures:
        fixture_id = fixture.get("fixture", {}).get("id")
        home_team = fixture.get("teams", {}).get("home", {}).get("name", "?")
        away_team = fixture.get("teams", {}).get("away", {}).get("name", "?")
        league = fixture.get("league", {}).get("name", "?")
        
        # Predictions API hívás (tartalmaz sárga lap adatokat is)
        predictions = get_predictions(fixture_id) if fixture_id else {}
        
        # Egyszerű pontozás (ezt a predictions adatok alapján finomíthatod)
        card_score = 0
        
        if predictions:
            # Ha van comparison adat
            comparison = predictions.get("comparison", {})
            
            # Forma és támadás alapján becsüljük a meccs intenzitását
            home_form = predictions.get("teams", {}).get("home", {}).get("league", {}).get("form", "")
            away_form = predictions.get("teams", {}).get("away", {}).get("league", {}).get("form", "")
            
            # Ha mindkét csapat jó formában van, intenzívebb meccs várható
            if home_form and away_form:
                wins_home = home_form.count("W")
                wins_away = away_form.count("W")
                # Ha mindkét csapat nyerő formában, több összecsapás várható
                if wins_home >= 3 and wins_away >= 3:
                    card_score += 30
                elif wins_home >= 2 and wins_away >= 2:
                    card_score += 20
            
            # Derby vagy rivális meccsek (liga alapján)
            if "derby" in league.lower() or "clásico" in league.lower():
                card_score += 20
        
        scored_fixtures.append({
            "fixture_id": fixture_id,
            "home": home_team,
            "away": away_team,
            "league": league,
            "kickoff": fixture.get("fixture", {}).get("date", ""),
            "card_score": card_score,
            "predictions": predictions
        })
    
    # Rendezés pontszám szerint
    scored_fixtures.sort(key=lambda x: x["card_score"], reverse=True)
    
    return scored_fixtures[:10]


def analyze_fixtures_for_goals(fixtures: list) -> list:
    """
    Elemzi a meccseket gól szempontjából (Over 2.5).
    """
    scored_fixtures = []
    
    for fixture in fixtures:
        fixture_id = fixture.get("fixture", {}).get("id")
        home_team = fixture.get("teams", {}).get("home", {}).get("name", "?")
        away_team = fixture.get("teams", {}).get("away", {}).get("name", "?")
        league = fixture.get("league", {}).get("name", "?")
        
        predictions = get_predictions(fixture_id) if fixture_id else {}
        
        goal_score = 0
        over_25_prediction = None
        
        if predictions:
            # Goals prediction
            goals = predictions.get("predictions", {}).get("goals", {})
            home_goals = goals.get("home")
            away_goals = goals.get("away")
            
            if home_goals and away_goals:
                try:
                    total = float(home_goals) + float(away_goals)
                    goal_score = int(total * 20)
                    if total > 2.5:
                        over_25_prediction = True
                except:
                    pass
            
            # Under/Over prediction
            under_over = predictions.get("predictions", {}).get("under_over")
            if under_over:
                if "+" in str(under_over):
                    goal_score += 20
        
        scored_fixtures.append({
            "fixture_id": fixture_id,
            "home": home_team,
            "away": away_team,
            "league": league,
            "kickoff": fixture.get("fixture", {}).get("date", ""),
            "goal_score": goal_score,
            "over_25": over_25_prediction,
            "predictions": predictions
        })
    
    scored_fixtures.sort(key=lambda x: x["goal_score"], reverse=True)
    
    return scored_fixtures[:10]


def analyze_fixtures_for_btts(fixtures: list) -> list:
    """
    Elemzi a meccseket BTTS (mindkét csapat szerez) szempontjából.
    """
    scored_fixtures = []
    
    for fixture in fixtures:
        fixture_id = fixture.get("fixture", {}).get("id")
        home_team = fixture.get("teams", {}).get("home", {}).get("name", "?")
        away_team = fixture.get("teams", {}).get("away", {}).get("name", "?")
        league = fixture.get("league", {}).get("name", "?")
        
        predictions = get_predictions(fixture_id) if fixture_id else {}
        
        btts_score = 0
        btts_prediction = None
        
        if predictions:
            # BTTS prediction
            btts = predictions.get("predictions", {}).get("goals", {})
            home_goals = btts.get("home")
            away_goals = btts.get("away")
            
            if home_goals and away_goals:
                try:
                    if float(home_goals) >= 1 and float(away_goals) >= 1:
                        btts_score = 80
                        btts_prediction = True
                    elif float(home_goals) >= 0.5 and float(away_goals) >= 0.5:
                        btts_score = 50
                except:
                    pass
            
            # Comparison - attack strengths
            comparison = predictions.get("comparison", {})
            att_home = comparison.get("att", {}).get("home", "0%").replace("%", "")
            att_away = comparison.get("att", {}).get("away", "0%").replace("%", "")
            
            try:
                if int(att_home) > 40 and int(att_away) > 40:
                    btts_score += 20
            except:
                pass
        
        scored_fixtures.append({
            "fixture_id": fixture_id,
            "home": home_team,
            "away": away_team,
            "league": league,
            "kickoff": fixture.get("fixture", {}).get("date", ""),
            "btts_score": btts_score,
            "btts": btts_prediction,
            "predictions": predictions
        })
    
    scored_fixtures.sort(key=lambda x: x["btts_score"], reverse=True)
    
    return scored_fixtures[:10]


# ============================================
# 🤖 CLAUDE AI ELEMZÉS
# ============================================

def ask_claude(user_message: str, context: str = "") -> str:
    """
    Claude AI-val elemeztet.
    """
    system_prompt = """Te egy profi sportfogadási elemző AI vagy. 
    
A felhasználó kérdései alapján elemzed a focimeccseket és visszaadod:
- 🟨 Sok sárga lapra esélyes meccsek (intenzív, rivális meccsek)
- ⚽ Sok gólra esélyes meccsek (Over 2.5)
- ✅ Mindkét csapat szerez gólt (BTTS)

Ha csapatot kérdeznek, adj részletes elemzést:
- Forma (utolsó 5 meccs)
- Gólátlag
- Kapott gólok
- Sárga lap átlag
- Erősségek és gyengeségek

Mindig magyarul válaszolj, legyél tömör de informatív.
Használj emojit a könnyebb olvashatóságért.
Ha nincs elég adat, jelezd őszintén.

FONTOS: Ez nem pénzügyi tanács, csak szórakoztatási célú elemzés."""

    try:
        response = anthropic.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2000,
            system=system_prompt,
            messages=[
                {
                    "role": "user",
                    "content": f"{user_message}\n\nKontextus adatok:\n{context}"
                }
            ]
        )
        return response.content[0].text
    except Exception as e:
        return f"Hiba történt az elemzés során: {str(e)}"


# ============================================
# 🌐 API VÉGPONTOK
# ============================================

@app.route("/")
def home():
    return jsonify({
        "status": "running",
        "name": "Sport AI Ágens",
        "version": "1.0",
        "endpoints": {
            "/chat": "POST - Chat az ágenssel",
            "/fixtures/{date}": "GET - Napi meccsek",
            "/analyze/cards/{date}": "GET - Sárga lap elemzés",
            "/analyze/goals/{date}": "GET - Gól elemzés",
            "/analyze/btts/{date}": "GET - BTTS elemzés",
            "/team/{name}": "GET - Csapat keresés"
        }
    })


@app.route("/chat", methods=["POST"])
def chat():
    """
    Fő chat végpont - itt beszélgetsz az ágenssel.
    """
    data = request.json
    user_message = data.get("message", "")
    
    if not user_message:
        return jsonify({"error": "Üres üzenet"}), 400
    
    # Dátum kinyerése az üzenetből
    context = ""
    
    # Ha dátumot említ
    if "holnap" in user_message.lower():
        target_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        fixtures = get_fixtures_by_date(target_date)
        context = f"Holnapi meccsek ({target_date}): {len(fixtures)} meccs található.\n"
        
        if fixtures:
            # Elemzések
            cards = analyze_fixtures_for_cards(fixtures[:20])  # Limit az API hívások miatt
            goals = analyze_fixtures_for_goals(fixtures[:20])
            btts = analyze_fixtures_for_btts(fixtures[:20])
            
            context += f"\n🟨 TOP SÁRGA LAP ESÉLYES:\n"
            for m in cards[:5]:
                context += f"- {m['home']} vs {m['away']} ({m['league']})\n"
            
            context += f"\n⚽ TOP GÓL ESÉLYES (Over 2.5):\n"
            for m in goals[:5]:
                context += f"- {m['home']} vs {m['away']} ({m['league']})\n"
            
            context += f"\n✅ TOP BTTS ESÉLYES:\n"
            for m in btts[:5]:
                context += f"- {m['home']} vs {m['away']} ({m['league']})\n"
    
    elif "ma" in user_message.lower():
        target_date = datetime.now().strftime("%Y-%m-%d")
        fixtures = get_fixtures_by_date(target_date)
        context = f"Mai meccsek ({target_date}): {len(fixtures)} meccs található.\n"
        
        if fixtures:
            cards = analyze_fixtures_for_cards(fixtures[:20])
            goals = analyze_fixtures_for_goals(fixtures[:20])
            btts = analyze_fixtures_for_btts(fixtures[:20])
            
            context += f"\n🟨 TOP SÁRGA LAP ESÉLYES:\n"
            for m in cards[:5]:
                context += f"- {m['home']} vs {m['away']} ({m['league']})\n"
            
            context += f"\n⚽ TOP GÓL ESÉLYES:\n"
            for m in goals[:5]:
                context += f"- {m['home']} vs {m['away']} ({m['league']})\n"
            
            context += f"\n✅ TOP BTTS ESÉLYES:\n"
            for m in btts[:5]:
                context += f"- {m['home']} vs {m['away']} ({m['league']})\n"
    
    # Ha csapat nevet említ
    team_keywords = ["elemzés", "elemezd", "statisztika", "forma"]
    if any(kw in user_message.lower() for kw in team_keywords):
        # Próbáljuk kinyerni a csapat nevét
        words = user_message.split()
        for word in words:
            if len(word) > 3 and word.lower() not in team_keywords + ["a", "az", "és", "vagy"]:
                team = search_team(word)
                if team:
                    team_info = team.get("team", {})
                    context += f"\nCsapat találat: {team_info.get('name', '?')}\n"
                    context += f"Ország: {team_info.get('country', '?')}\n"
                    context += f"Alapítva: {team_info.get('founded', '?')}\n"
                    break
    
    # Claude válasz
    response = ask_claude(user_message, context)
    
    return jsonify({
        "response": response,
        "context_used": bool(context)
    })


@app.route("/fixtures/<date>")
def fixtures_by_date(date):
    """
    Lekéri az adott napi meccseket.
    """
    fixtures = get_fixtures_by_date(date)
    return jsonify({
        "date": date,
        "count": len(fixtures),
        "fixtures": fixtures[:50]  # Max 50
    })


@app.route("/analyze/cards/<date>")
def analyze_cards(date):
    """
    Sárga lap elemzés egy adott napra.
    """
    fixtures = get_fixtures_by_date(date)
    analyzed = analyze_fixtures_for_cards(fixtures[:30])
    return jsonify({
        "date": date,
        "type": "yellow_cards",
        "top_fixtures": analyzed
    })


@app.route("/analyze/goals/<date>")
def analyze_goals(date):
    """
    Gól elemzés egy adott napra (Over 2.5).
    """
    fixtures = get_fixtures_by_date(date)
    analyzed = analyze_fixtures_for_goals(fixtures[:30])
    return jsonify({
        "date": date,
        "type": "over_25_goals",
        "top_fixtures": analyzed
    })


@app.route("/analyze/btts/<date>")
def analyze_btts(date):
    """
    BTTS elemzés egy adott napra.
    """
    fixtures = get_fixtures_by_date(date)
    analyzed = analyze_fixtures_for_btts(fixtures[:30])
    return jsonify({
        "date": date,
        "type": "btts",
        "top_fixtures": analyzed
    })


@app.route("/team/<name>")
def team_search(name):
    """
    Csapat keresés.
    """
    team = search_team(name)
    return jsonify(team)


# ============================================
# 🚀 INDÍTÁS
# ============================================

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
