import os
import json, csv
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from datetime import datetime

app = Flask(__name__)
CORS(app)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATOS_DIR = os.path.join(BASE_DIR, "datos")
MODEL_DATA_DIR = os.path.join(BASE_DIR, "model_data")

LIST_JSON = os.path.join(DATOS_DIR, "list.json")
SOLICITUDES_CSV = os.path.join(DATOS_DIR, "Solicitudes.csv")
DESCRIPCIONES_JSON = os.path.join(DATOS_DIR, "descripciones.json")

@app.route("/")
def index():
    return send_from_directory(".", "index.html")

@app.route("/solicitar", methods=["POST"])
def solicitar_modelo():
    data = request.json

    print("ESCRIBIENDO EN:", SOLICITUDES_CSV, flush=True)
    os.makedirs(os.path.dirname(SOLICITUDES_CSV), exist_ok=True)

    existe = os.path.exists(SOLICITUDES_CSV)

    with open(SOLICITUDES_CSV, "a", newline="", encoding="utf-8") as f:
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

@app.route("/api/modelos")
def obtener_modelos():
    print("LEYENDO LIST_JSON:", LIST_JSON)

    with open(LIST_JSON, encoding="utf-8") as f:
        modelos = json.load(f)

    return jsonify(modelos)

@app.route("/api/modelos/<path:nombre_archivo>")
def obtener_modelo(nombre_archivo):
    ruta_modelo = os.path.join(MODEL_DATA_DIR, nombre_archivo)

    if not os.path.exists(ruta_modelo):
        print("NO EXISTE MODELO:", ruta_modelo)
        return jsonify({"error": "Modelo no encontrado"}), 404

    with open(ruta_modelo, encoding="utf-8") as f:
        datos = json.load(f)

    return jsonify(datos)

@app.route("/api/descripciones")
def obtener_descripciones():
    if not os.path.exists(DESCRIPCIONES_JSON):
        print("NO EXISTE DESCRIPCIONES:", DESCRIPCIONES_JSON)
        return jsonify({"error": "descripciones.json no encontrado"}), 404

    with open(DESCRIPCIONES_JSON, encoding="utf-8") as f:
        descripciones = json.load(f)

    return jsonify(descripciones)

@app.route("/<path:path>")
def static_files(path):
    return send_from_directory(".", path)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)