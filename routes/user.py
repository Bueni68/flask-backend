from flask import Blueprint, request, jsonify
from datetime import datetime
from database import users_collection, temp_users_collection, history_collection
from helpers import update_station, get_german_time
import pytz

user_bp = Blueprint("user", __name__)

@user_bp.route("/save_user", methods=["POST"])
def save_user():
    data = request.get_json()
    temp_user_id = data.get("temp_user_id")
    full_name = data.get("full_name")
    temp_user = temp_users_collection.find_one({'uid': temp_user_id})

    if temp_user:
        name, surname = full_name.split()
        user = {"uid": temp_user["uid"], "name": name, "surname": surname}
        user_id = users_collection.insert_one(user).inserted_id

        formatted_time = get_german_time(as_string=True)
        if temp_user["action"] == "Betreten":
            history_collection.insert_one({"uid": temp_user["uid"], "station": temp_user["station"], "start_time": formatted_time, "end_time": None, "duration": None, "edited_time": formatted_time})
        elif temp_user["action"] == "Verlassen":
            last_entry = history_collection.find_one({"uid": temp_user["uid"], "station": temp_user["station"], "end_time": None}, sort=[('_id', -1)])
            if last_entry:
                start_dt = datetime.strptime(last_entry["start_time"], "%Y-%m-%d %H:%M:%S")
                start_dt = pytz.timezone("Europe/Berlin").localize(start_dt)
                duration = get_german_time() - start_dt
                duration_str = f"{duration.seconds // 3600}h {duration.seconds % 3600 // 60}min"
                history_collection.update_one({"_id": last_entry["_id"]}, {"$set": {"end_time": formatted_time, "duration": duration_str, "edited_time": formatted_time}})

        update_station(temp_user["station"], temp_user["action"])
        temp_users_collection.delete_one({'uid': temp_user_id})

        return jsonify({'status': 'user_saved', 'user_id': str(user_id)})

    return jsonify({'status': 'error', 'message': 'TempUser nicht gefunden'})