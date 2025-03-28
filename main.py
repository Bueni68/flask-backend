from flask import Flask, render_template, jsonify, request
import json
import os
from datetime import datetime
import pytz
import qrcode

website_url = "https://flask-backend-fga2.onrender.com"

# QR-Code erstellen & speichern
qr = qrcode.make(website_url)
qr.save("static/qrcode.png")
print(" QR-Code wurde erstellt: static/qrcode.png")

app = Flask(__name__)

# Datei für Sensordaten-Speicherung
DATA_FILE = "data.json"

# Hilfsfunktion zum Laden der Daten
def load_data():
    # Standardwerte definieren, falls die Datei nicht existiert
    default_data = {
        "stations": {"Station 1": "frei", "Station 2": "frei"},
        "people_count": 0,
        "history": [],
        "estimated_times": [],
        "card_names": {}  # Hier wird die Kartennamen gespeichert
    }

    # Versuchen, die Datei zu öffnen und die Daten zu laden
    try:
        with open(DATA_FILE, "r") as file:
            data = json.load(file)

            # Falls "estimated_times" fehlt, füge es als leere Liste hinzu
            if "estimated_times" not in data:
                data["estimated_times"] = []

            # Falls "card_names" fehlt, füge es als leere Struktur hinzu
            if "card_names" not in data:
                data["card_names"] = {}

            # Falls die gespeicherten Daten fehlerhaft sind (z. B. zu viele Stationen), zurücksetzen
            if "stations" not in data or len(data["stations"]) > 2:
                return default_data

            return data
    except (FileNotFoundError, json.JSONDecodeError):
        # Falls Datei nicht existiert oder fehlerhaft ist, Standarddaten zurückgeben
        return default_data

# Hilfsfunktion zum Speichern der Daten
def save_data(data):
    with open(DATA_FILE, "w") as file:
        json.dump(data, file)

# Hilfsfunktion zum Zählen der belegten Stationen
def count_occupied_stations(stations):
    return sum(1 for status in stations.values() if status == "belegt")

# Hauptseite
@app.route("/")
def index():
    return render_template("index.html")

# API zum Abrufen des Status
@app.route("/status", methods=["GET"])
def get_status():
    data = load_data()
    
    # Berechnung der belegten Stationen
    occupied_stations = count_occupied_stations(data["stations"])
    
    return jsonify({
        "stations": data["stations"],
        "occupied_stations": occupied_stations,
        "history": data["history"],
        "estimated_times": data["estimated_times"]
    })

# API zum Aktualisieren der Sensordaten (vom ESP32 aufgerufen)
@app.route("/update", methods=["POST"])
def update_status():
    if not request.is_json:
        return jsonify({"error": "JSON-Daten erwartet"}), 400  # Falls keine JSON-Daten kommen

    new_data = request.get_json()
    current_data = load_data()

    # Hole die Zeitzone für Deutschland
    germany_tz = pytz.timezone('Europe/Berlin')

    # 1️. RESET (Falls vom ESP gesendet)
    if new_data.get("reset"):
        current_data = {
            "stations": {"Station 1": "frei", "Station 2": "frei"},
            "people_count": 0,
            "history": [],
            "estimated_times": [],
            "card_names": {}
        }
        save_data(current_data)
        return jsonify({"message": "Alle Daten zurückgesetzt!"})

    # 2️. Stationsstatus aktualisieren
    if "stations" in new_data:
        for station, status in new_data["stations"].items():
            current_data["stations"][station] = status  

    # 3️. Historie aktualisieren (Personen betreten/verlassen)
    if "history" in new_data:
        for entry in new_data["history"]:
            # Zeitstempel mit der richtigen Zeitzone (Deutschland)
            entry["timestamp"] = datetime.now(germany_tz).strftime("%Y-%m-%d %H:%M:%S")

            # Doppelten Eintrag verhindern
            if entry not in current_data["history"]:  
                current_data["history"].insert(0, entry)  # Neueste zuerst speichern
            else:
                print(" Doppelter Eintrag erkannt, wird ignoriert:", entry)

            if entry["action"] == "Betreten":
                current_data["stations"][entry["station"]] = "belegt"

        # Station direkt auf "frei" setzen, wenn eine Person die Station verlässt
        for entry in new_data["history"]:
            if entry["action"] == "Verlassen":
                current_data["stations"][entry["station"]] = "frei"

    save_data(current_data)
    return jsonify({"message": "Daten aktualisiert!"})

# API zum Setzen des Kartennamens (wird vom ESP32 verwendet)
@app.route("/set_card_name", methods=["POST"])
def set_card_name():
    try:
        data = request.json  # Empfange die Daten im JSON-Format
        card_uid = data["card_uid"]  # Hol die UID der Karte
        name = data["name"]  # Hol den Namen des Karteninhabers

        current_data = load_data()

        # Setze den Namen für die Karte (auch wenn die Karte schon einen Namen hat)
        current_data["card_names"][card_uid] = name
        save_data(current_data)

        return jsonify({"message": f"Name für Karte {card_uid} gesetzt!", "card_uid": card_uid, "name": name}), 200

    except Exception as e:
        return jsonify({"error": f"Fehler beim Setzen des Namens: {e}"}), 500

# Starten des Servers (Render nutzt einen dynamischen Port)
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
