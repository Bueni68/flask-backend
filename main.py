from flask import Flask, render_template, jsonify, request
import json
import os
from datetime import datetime
import qrcode

website_url = "https://flask-backend-fga2.onrender.com"  # Deine Render-URL

# QR-Code erstellen
qr = qrcode.make(website_url)

# QR-Code speichern
qr.save("static/qrcode.png")

print("✅ QR-Code wurde erstellt: static/qrcode.png")


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
        "estimated_times": []
    }

    # Versuchen, die Datei zu öffnen und die Daten zu laden
    try:
        with open(DATA_FILE, "r") as file:
            data = json.load(file)

            # Falls "estimated_times" fehlt, füge es als leere Liste hinzu
            if "estimated_times" not in data:
                data["estimated_times"] = []

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

# Hauptseite
@app.route("/")
def index():
    return render_template("index.html")

# API zum Abrufen des Status
@app.route("/status", methods=["GET"])
def get_status():
    return jsonify(load_data())

# API zum Aktualisieren der Sensordaten (vom ESP32 aufgerufen)
@app.route("/update", methods=["POST"])
def update_status():
    if not request.is_json:
        return jsonify({"error": "JSON-Daten erwartet"}), 400  # Falls keine JSON-Daten kommen

    new_data = request.get_json()
    current_data = load_data()

    # 1️⃣ RESET (Falls vom ESP gesendet)
    if new_data.get("reset"):
        current_data = {
            "stations": {"Station 1": "frei", "Station 2": "frei"},
            "people_count": 0,
            "history": [],
            "estimated_times": []
        }
        save_data(current_data)
        return jsonify({"message": "Alle Daten zurückgesetzt!"})

    # 2️⃣ Stationsstatus aktualisieren
    if "stations" in new_data:
        for station, status in new_data["stations"].items():
            current_data["stations"][station] = status  

    # 3️⃣ Historie aktualisieren (Personen betreten/verlassen)
    if "history" in new_data:
        for entry in new_data["history"]:
            entry["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # 🛑 NEU: Doppelten Eintrag verhindern!
            if current_data["history"]:
                last_entry = current_data["history"][0]  # Letzter Eintrag
                if last_entry["action"] == entry["action"] and last_entry["station"] == entry["station"]:
                    return jsonify({"message": "Doppelter Eintrag erkannt, nicht gespeichert!"})

            if entry["action"] == "Betreten":
                current_data["stations"][entry["station"]] = "belegt"

        current_data["history"] = new_data["history"] + current_data["history"]

    # 🔴 Station direkt auf "frei" setzen, wenn eine Person die Station verlässt
    if "history" in new_data:
        for entry in new_data["history"]:
            entry["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            if entry["action"] == "Betreten":
                current_data["stations"][entry["station"]] = "belegt"  # 🔴 Station belegen
        
            elif entry["action"] == "Verlassen":
                current_data["stations"][entry["station"]] = "frei"  # 🔵 Station sofort freigeben

        current_data["history"] = new_data["history"] + current_data["history"]  # Neueste zuerst

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

        # Speichern der Verlassenszeit für die spezifische Station
        current_data["estimated_times"].append(f"{station}: {leave_time}")
        save_data(current_data)

        return jsonify({"message": "Verlassenszeit gespeichert"}), 200
    except Exception as e:
        return jsonify({"error": f"Fehler beim Speichern der Verlassenszeit: {e}"}), 500

# Starten des Servers (Render nutzt einen dynamischen Port)
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
