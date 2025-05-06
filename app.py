from flask import Flask, render_template, request, redirect, url_for
import requests
from datetime import datetime

app = Flask(__name__)
user_points = 100

def get_today_games():
    today = datetime.today().strftime('%Y-%m-%d')
    url = f"https://www.balldontlie.io/api/v1/games?start_date={today}&end_date={today}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json().get("data", [])
    except Exception as e:
        print("Error getting games:", e)
        return []

def get_player_id(player_name):
    try:
        response = requests.get(f"https://www.balldontlie.io/api/v1/players?search={player_name}")
        response.raise_for_status()
        data = response.json().get("data", [])
        return data[0]["id"] if data else None
    except Exception as e:
        print("Error getting player ID:", e)
        return None

def get_player_stat(player_name, game_id):
    try:
        player_id = get_player_id(player_name)
        if not player_id:
            return None

        stats_url = f"https://www.balldontlie.io/api/v1/stats?game_ids[]={game_id}&player_ids[]={player_id}"
        stats_resp = requests.get(stats_url)
        stats_resp.raise_for_status()
        stats = stats_resp.json().get("data", [])
        if not stats:
            return None

        return stats[0]["pts"]
    except Exception as e:
        print("Error getting player stats:", e)
        return None

@app.route("/")
def index():
    games = get_today_games()
    return render_template("index.html", games=games, points=user_points)

@app.route("/predict", methods=["GET", "POST"])
def predict():
    global user_points

    if request.method == "POST":
        player = request.form["player"]
        prediction = int(request.form["prediction"])
        wager = int(request.form["wager"])
        game_id = request.form["game_id"]

        if wager > user_points or wager <= 0:
            return "Invalid wager"

        actual = get_player_stat(player, game_id)

        if actual is None:
            return "Stat not available yet. Try again later."

        success = abs(actual - prediction) <= 3
        winnings = wager * 2 if success else 0
        user_points = user_points + winnings if success else user_points - wager

        return render_template("result.html",
                               player=player,
                               predicted=prediction,
                               actual=actual,
                               success=success,
                               winnings=winnings,
                               points=user_points)
    else:
        games = get_today_games()
        return render_template("predict.html", games=games, points=user_points)

if __name__ == "__main__":
    app.run(debug=True)
