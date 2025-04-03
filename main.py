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
        "rfid_users": {}  # Neu: RFID-Karten und ihre Namen
    }

    # Versuchen, die Datei zu öffnen und die Daten zu laden
    try:
        with open(DATA_FILE, "r") as file:
            data = json.load(file)

            # Sicherstellen, dass alle Schlüssel vorhanden sind
            if "rfid_users" not in data:
                data["rfid_users"] = {}

            return data
    except (FileNotFoundError, json.JSONDecodeError):
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
            "estimated_times": []
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

            # RFID-Nutzer personalisieren
            rfid = entry.get("rfid")
            if rfid:
                entry["name"] = current_data["rfid_users"].get(rfid, "Unbekannt")

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

# API zum Speichern der geplanten Verlassenszeit
@app.route("/set_leave_time", methods=["POST"])
def set_leave_time():
    try:
        data = request.json  # Empfange die Daten im JSON-Format
        station = data["station"]  # Hol die Station
        leave_time = data["leave_time"]  # Hol die Verlassenszeit

        current_data = load_data()

        # Prüfen, ob die Station existiert
        if station not in current_data["stations"]:
            return jsonify({"error": "Ungültige Station!"}), 400

        # Prüfen, ob die ausgewählte Station belegt ist
        if current_data["stations"].get(station) != "belegt":
            return jsonify({"error": f"{station} ist derzeit nicht belegt. Bitte wähle eine andere Station."}), 400

        # Debug-Ausgabe: Überprüfen, was in current_data gespeichert ist
        print("Aktuelle Daten vor dem Speichern:", current_data)

        # Speichern der Verlassenszeit für die spezifische Station
        current_data["estimated_times"].append(f"{station}: {leave_time}")
        save_data(current_data)

        return jsonify({"message": "Verlassenszeit gespeichert"}), 200
    except Exception as e:
        return jsonify({"error": f"Fehler beim Speichern der Verlassenszeit: {e}"}), 500

# API zum Personalisieren der RFID-Karte
@app.route("/personalize_rfid", methods=["POST"])
def personalize_rfid():
    try:
        data = request.json
        rfid = data.get("rfid")
        name = data.get("name")

        if not rfid or not name:
            return jsonify({"error": "RFID und Name sind erforderlich"}), 400

        current_data = load_data()

        # RFID-Karte mit Namen verknüpfen
        current_data["rfid_users"][rfid] = name
        save_data(current_data)

        return jsonify({"message": f"RFID {rfid} wurde mit dem Namen {name} verknüpft."}), 200
    except Exception as e:
        return jsonify({"error": f"Fehler beim Personalisieren der RFID-Karte: {e}"}), 500

# API zum Überprüfen der UID
@app.route("/check_uid", methods=["POST"])
def check_uid():
    try:
        data = request.json
        uid = data.get("uid")

        if not uid:
            return jsonify({"error": "UID ist erforderlich"}), 400

        current_data = load_data()

        # Überprüfen, ob die UID bereits personalisiert ist
        if uid in current_data["rfid_users"]:
            name = current_data["rfid_users"][uid]
            return jsonify({"uid": uid, "name": name, "status": "known"}), 200
        else:
            return jsonify({"uid": uid, "status": "unknown"}), 200
    except Exception as e:
        return jsonify({"error": f"Fehler beim Überprüfen der UID: {e}"}), 500

# API zum Speichern des Namens für eine UID
@app.route("/save_name", methods=["POST"])
def save_name():
    try:
        data = request.json
        uid = data.get("uid")
        name = data.get("name")

        if not uid or not name:
            return jsonify({"error": "UID und Name sind erforderlich"}), 400

        current_data = load_data()

        # UID mit Namen verknüpfen
        current_data["rfid_users"][uid] = name
        save_data(current_data)

        return jsonify({"message": f"UID {uid} wurde mit dem Namen {name} verknüpft."}), 200
    except Exception as e:
        return jsonify({"error": f"Fehler beim Speichern des Namens: {e}"}), 500

# Starten des Servers (Render nutzt einen dynamischen Port)
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
