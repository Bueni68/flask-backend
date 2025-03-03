from flask import Flask, render_template, jsonify, request
import json

app = Flask(__name__)

# Datei, um Sensordaten zu speichern
DATA_FILE = "data.json"

# Hilfsfunktion zum Laden der Daten
def load_data():
    try:
        with open(DATA_FILE, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return {"stations": {"Station 1": "frei", "Station 2": "frei"}, "people_count": 0, "history": []}

# Hilfsfunktion zum Speichern der Daten
def save_data(data):
    with open(DATA_FILE, "w") as file:
        json.dump(data, file)

# Webseite anzeigen
@app.route("/")
def index():
    return render_template("index.html")

# API zum Abrufen des Status
@app.route("/status", methods=["GET"])
def get_status():
    return jsonify(load_data())

# API zum Aktualisieren der Sensordaten (wird von den Sensoren aufgerufen)
from datetime import datetime  # Import für Datum & Uhrzeit

@app.route("/update", methods=["POST"])
def update_status():
    new_data = request.json  
    current_data = load_data()  

    # 🔴 1️⃣ KOMPLETT-RESET: Belegung & Historie zurücksetzen (nur manuell)
    if "reset" in new_data and new_data["reset"]:
        current_data["stations"] = {station: "frei" for station in current_data["stations"]}
        current_data["people_count"] = 0
        current_data["history"] = []
        save_data(current_data)
        return jsonify({"message": "Alle Daten zurückgesetzt!"})

    # 🔵 2️⃣ Stationsstatus aktualisieren (falls gesendet)
    if "stations" in new_data:
        for station, status in new_data["stations"].items():
            current_data["stations"][station] = status  

    # 🔴 3️⃣ Historie aktualisieren & neue Personen setzen automatisch Station auf "belegt"
    if "history" in new_data:
        for entry in new_data["history"]:
            entry["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            if entry["action"] == "Betreten":
                current_data["stations"][entry["station"]] = "belegt"  # 🔴 Station belegen

        current_data["history"] = new_data["history"] + current_data["history"]  # Neueste zuerst

    # 🔴 4️⃣ Überprüfen, ob eine Station "frei" werden kann  
    station_occupancy = {station: set() for station in current_data["stations"]}  # Speichert aktive Personen pro Station

    # Durchlaufe die Historie und tracke Personen in den Stationen
    for entry in current_data["history"]:
        name = entry["name"]
        station = entry["station"]
        action = entry["action"]

        if action == "Betreten":
            station_occupancy[station].add(name)  # Füge Person zur Station hinzu
        elif action == "Verlassen":
            station_occupancy[station].discard(name)  # Entferne Person aus der Station

    # Falls eine Station leer ist, setze sie auf "frei"
    for station, people in station_occupancy.items():
        if not people:  # Keine Personen mehr in der Station
            current_data["stations"][station] = "frei"

    save_data(current_data)
    return jsonify({"message": "Daten aktualisiert!"})



if __name__ == "__main__":
    app.run(debug=True, port=5005)
