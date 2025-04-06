from flask import Blueprint, jsonify
from datetime import timedelta
from database import stations_collection, users_collection, history_collection, estimated_times_collection
from helpers import get_german_time

status_bp = Blueprint("status", __name__)

@status_bp.route("/status", methods=["GET"])
def get_status():
    stations_raw = list(stations_collection.find())
    stations = [{k: v for k, v in s.items() if k != "_id"} for s in stations_raw]

    raw_history = list(history_collection.find().sort("edited_time", -1).limit(10))
    history = []
    for entry in raw_history:
        uid = entry.get("uid")
        user = users_collection.find_one({"uid": uid})
        full_name = f"{user.get('name', '')} {user.get('surname', '')}" if user else "Unbekannt"

        history.append({
            "uid": uid,
            "station": entry.get("station", "Unbekannt"),
            "action": "verlassen" if entry.get("end_time") else "betreten",
            "timestamp": entry.get("end_time") or entry.get("start_time"),
            "userFullName": full_name.strip(),
            "duration": entry.get("duration")
        })

    occupied_stations = sum(1 for s in stations if s["status"] == "belegt")

    now = get_german_time()
    estimated_times_collection.delete_many({"leave_time": {"$lt": now - timedelta(hours=24)}})

    raw_times = estimated_times_collection.find()
    station_status_map = {s["station"]: s["status"] for s in stations}
    estimated_times = [
        {"station": t["station"], "leave_time": str(t["leave_time"])}
        for t in raw_times
        if t.get("leave_time") and station_status_map.get(t["station"]) == "belegt"
    ]

    return jsonify({
        "stations": stations,
        "history": history,
        "occupied_stations": occupied_stations,
        "estimated_times": estimated_times
    })