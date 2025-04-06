from flask import Flask, render_template
import os
from routes.status import status_bp
from routes.update import update_bp
from routes.user import user_bp
from routes.misc import misc_bp
from helpers import generate_qr

app = Flask(__name__)

# QR-Code erstellen
generate_qr()

# Register Blueprints
app.register_blueprint(status_bp)
app.register_blueprint(update_bp)
app.register_blueprint(user_bp)
app.register_blueprint(misc_bp)

@app.route("/")
def index():
    return render_template("index.html")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5550))
    app.run(host="0.0.0.0", port=port)