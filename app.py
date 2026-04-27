from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from datetime import datetime
import csv
import os

app = Flask(__name__, static_folder=".", static_url_path="")
CORS(app)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(BASE_DIR, "datos", "Solicitudes.csv")

@app.route("/")
def index():
    return send_from_directory(".", "index.html")

@app.route("/solicitar", methods=["POST"])
def solicitar_modelo():
    data = request.json

    print("ESCRIBIENDO EN:", CSV_PATH, flush=True)
    os.makedirs(os.path.dirname(CSV_PATH), exist_ok=True)

    existe = os.path.exists(CSV_PATH)

    with open(CSV_PATH, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)

        if not existe:
            writer.writerow([
                "Marca temporal",
                "Nombre",
                "Correo electrónico",
                "Modelo",
                "Realizado"
            ])

        writer.writerow([
            datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            data.get("nombre", ""),
            data.get("correo", ""),
            data.get("modelo", ""),
            0
        ])
    return jsonify({
    "ok": True,
    "mensaje": "Solicitud registrada"
})

@app.route("/<path:path>")
def static_files(path):
    return send_from_directory(".", path)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)