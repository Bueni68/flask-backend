import os
import pytz
import qrcode
from datetime import datetime
from database import stations_collection


def get_german_time(as_string=False, format="%Y-%m-%d %H:%M:%S"):
    germany_tz = pytz.timezone("Europe/Berlin")
    now = datetime.now(germany_tz)
    return now.strftime(format) if as_string else now


def update_station(station, action):
    new_status = "belegt" if action == "Betreten" else "frei"
    stations_collection.update_one({"station": station}, {"$set": {"status": new_status}})


def generate_qr():
    website_url = os.getenv("WEBSITE_URL")
    qr = qrcode.make(website_url)
    qr.save("static/qrcode.png")