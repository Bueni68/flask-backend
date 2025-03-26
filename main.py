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
    default_data = {
        "stations": {"Station 1": "frei", "Station 2": "frei"},
        "people_count": 0,
        "history": [],
        "estimated_times": []
    }

    try:
        with open(DATA_FILE, "r") as file:
            data = json.load(file)

            if "estimated_times" not in data:
                data["estimated_times"] = []

            if "stations" not in data or len(data["stations"]) > 2:
                return default_data

            return data
    except (FileNotFoundError, json.JSONDecodeError):
        return default_data

# Hilfsfunktion zum Speichern der Daten
def save_data(data):
    with open(DATA_FILE, "w") as file:
        json.dump(data, file, indent=4)

# Hilfsfunktion zum Zählen der belegten Stationen
def count_occupied_stations(stations):
    return sum(1 for status in stations.values() if status == "belegt")

# RFID-Datei erstellen, falls sie nicht existiert
def create_rfid_users_file():
    if not os.path.exists("rfid_users.json"):
        with open("rfid_users.json", "w") as file:
            json.dump({}, file, indent=4)

create_rfid_users_file()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/status", methods=["GET"])
def get_status():
    data = load_data()
    occupied_stations = count_occupied_stations(data["stations"])
    
    return jsonify({
        "stations": data["stations"],
        "occupied_stations": occupied_stations,
        "history": data["history"],
        "estimated_times": data["estimated_times"]
    })

@app.route("/update", methods=["POST"])
def update_status():
    try:
        if not request.is_json:
            return jsonify({"error": "JSON-Daten erwartet"}), 400

        new_data = request.get_json()
        current_data = load_data()
        germany_tz = pytz.timezone('Europe/Berlin')

        # Debugging: Empfangene Daten ausgeben
        print("Empfangene Daten:", new_data)

        # Falls RFID-UID existiert, Namen zuweisen
        if "history" in new_data and len(new_data["history"]) > 0:
            for entry in new_data["history"]:
                entry["timestamp"] = datetime.now(germany_tz).strftime("%Y-%m-%d %H:%M:%S")

                rfid_uid = entry.get("rfid_uid", "unbekannt")

                with open("rfid_users.json", "r") as file:
                    user_data = json.load(file)

                entry["name"] = user_data.get(rfid_uid, "Unbekannt")

                if entry not in current_data["history"]:
                    current_data["history"].insert(0, entry)
                else:
                    print("Doppelter Eintrag erkannt, wird ignoriert:", entry)

                if entry["action"] == "Betreten":
                    current_data["stations"][entry["station"]] = "belegt"

            for entry in new_data["history"]:
                if entry["action"] == "Verlassen":
                    current_data["stations"][entry["station"]] = "frei"

        save_data(current_data)
        return jsonify({"message": "Daten aktualisiert!"})

    except Exception as e:
        print("Fehler in /update:", e)
        return jsonify({"error": str(e)}), 500

@app.route("/set_leave_time", methods=["POST"])
def set_leave_time():
    try:
        data = request.json
        station = data["station"]
        leave_time = data["leave_time"]

        current_data = load_data()

        if station not in current_data["stations"]:
            return jsonify({"error": "Ungültige Station!"}), 400

        if current_data["stations"].get(station) != "belegt":
            return jsonify({"error": f"{station} ist derzeit nicht belegt."}), 400

        print("Aktuelle Daten vor dem Speichern:", current_data)

        current_data["estimated_times"].append(f"{station}: {leave_time}")
        save_data(current_data)

        return jsonify({"message": "Verlassenszeit gespeichert"}), 200
    except Exception as e:
        return jsonify({"error": f"Fehler beim Speichern der Verlassenszeit: {e}"}), 500

@app.route("/add_rfid", methods=["POST"])
def add_rfid():
    try:
        data = request.get_json()
        rfid_uid = data.get("rfid_uid")
        name = data.get("name", "Unbekannt")

        if not rfid_uid:
            return jsonify({"error": "RFID-UID erforderlich!"}), 400

        with open("rfid_users.json", "r") as file:
            user_data = json.load(file)

        if rfid_uid in user_data:
            return jsonify({"error": "RFID-Karte existiert bereits!"}), 400

        user_data[rfid_uid] = name

        with open("rfid_users.json", "w") as file:
            json.dump(user_data, file, indent=4)

        return jsonify({"message": f"RFID-Karte {rfid_uid} wurde als {name} gespeichert."}), 200

    except Exception as e:
        return jsonify({"error": f"Fehler beim Speichern: {e}"}), 500

if __name__ == "__main__":
    create_rfid_users_file()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
