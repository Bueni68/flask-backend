from flask import Blueprint, jsonify, request
from database import temp_users_collection, stations_collection, estimated_times_collection
from helpers import get_german_time

misc_bp = Blueprint("misc", __name__)

@misc_bp.route("/temp_user_status")
def temp_user_status():
    temp_user = temp_users_collection.find_one()
    return jsonify({"temp_user_created": bool(temp_user), "temp_user_id": temp_user["uid"] if temp_user else None})

@misc_bp.route("/delete_temp_user", methods=["POST"])
def cancel_temp_user():
    temp_user = temp_users_collection.find_one()
    if temp_user:
        temp_users_collection.delete_one({'uid': temp_user["uid"]})
        return jsonify({"status": "deleted"})
    return jsonify({"status": "error"}), 400

@misc_bp.route("/set_leave_time", methods=["POST"])
def set_leave_time():
    data = request.json
    station_name = data.get("station")
    leave_time_str = data.get("leave_time")
    if not station_name or not leave_time_str:
        return jsonify({"error": "Station und leave_time müssen angegeben werden"}), 400

    station = stations_collection.find_one({"station": station_name})
    if not station or station.get("status") != "belegt":
        return jsonify({"error": f"Station '{station_name}' ist nicht belegt oder existiert nicht"}), 400

    estimated_times_collection.update_one(
        {"station": station_name},
        {"$set": {"leave_time": leave_time_str}},
        upsert=True
    )

    return jsonify({"status": "leave_time_saved"})