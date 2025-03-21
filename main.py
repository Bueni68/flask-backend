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

# Hilfsfunktion zum Zählen der belegten Stationen
def count_occupied_stations(stations):
    return sum(1 for status in stations.values() if status == "belegt")

# Hilfsfunktion zum Erstellen der RFID-Datei, falls sie nicht existiert
def create_rfid_users_file():
    if not os.path.exists("rfid_users.json"):
        # Erstelle eine leere JSON-Datei
        with open("rfid_users.json", "w") as file:
            json.dump({}, file, indent=4)  # Leeres Dictionary speichern

# Rufe die Funktion auf, wenn der Server startet
create_rfid_users_file()

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

    # Wenn der Name unbekannt ist, holen wir den Namen aus der rfid_users.json
    rfid_uid = new_data["history"][0]["rfid_uid"]
    with open("rfid_users.json", "r") as file:
        user_data = json.load(file)

    if rfid_uid in user_data:
        name = user_data[rfid_uid]
    else:
        name = "Unbekannt"

    # Update history mit dem Namen
    new_data["history"][0]["name"] = name
    # Speichern der Daten
    save_data(current_data)

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
    
# API zum Speichern einer neuen RFID-Karte
@app.route("/add_rfid", methods=["POST"])
def add_rfid():
    """Fügt eine neue RFID-Karte mit Platzhalternamen zur JSON-Datei hinzu."""
    try:
        data = request.get_json()
        rfid_uid = data.get("rfid_uid")
        name = data.get("name", "Unbekannt")  # Standardname ist "Unbekannt"

        if not rfid_uid:
            return jsonify({"error": "RFID-UID erforderlich!"}), 400

        # Bestehende RFID-Daten laden
        with open("rfid_users.json", "r") as file:
            user_data = json.load(file)

        # Prüfen, ob UID bereits existiert
        if rfid_uid in user_data:
            return jsonify({"error": "RFID-Karte existiert bereits!"}), 400

        # Neue UID mit Namen speichern (Standardname "Unbekannt")
        user_data[rfid_uid] = name

        # Aktualisierte Daten zurück in JSON-Datei speichern
        with open("rfid_users.json", "w") as file:
            json.dump(user_data, file, indent=4)

        return jsonify({"message": f"RFID-Karte {rfid_uid} wurde als {name} gespeichert."}), 200

    except Exception as e:
        return jsonify({"error": f"Fehler beim Speichern: {e}"}), 500

# Server starten und sicherstellen, dass die Datei vorhanden ist
if __name__ == "__main__":
    create_rfid_users_file()  # Stelle sicher, dass die Datei existiert
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
