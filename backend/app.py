import os
import json, csv
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from datetime import datetime
import pandas as pd
import traceback

app = Flask(__name__)
CORS(app)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATOS_DIR = os.path.join(BASE_DIR, "datos")
MODEL_DATA_DIR = os.path.join(BASE_DIR, "model_data")

LIST_JSON = os.path.join(DATOS_DIR, "list.json")
SOLICITUDES_CSV = os.path.join(DATOS_DIR, "Solicitudes.csv")
DESCRIPCIONES_JSON = os.path.join(DATOS_DIR, "descripciones.json")

def nombre_archivo_valido(model):
    return model.replace(":", "_") 

@app.route("/benchmark")
def index():
    return send_from_directory(".", "index.html")

@app.route("/solicitar", methods=["POST"])
def solicitar():
    try:
        print("CONTENT TYPE:", request.content_type, flush=True)
        print("FORM:", request.form.to_dict(), flush=True)
        print("JSON:", request.get_json(silent=True), flush=True)

        if request.is_json:
            datos = request.get_json()
            nombre = datos.get("nombre")
            correo = datos.get("correo")
            modelo = datos.get("modelo")
        else:
            nombre = request.form.get("nombre")
            correo = request.form.get("correo")
            modelo = request.form.get("modelo")

        if not modelo:
            return jsonify({"ok": False, "error": "Falta el modelo"}), 400

        columnas = [
            "Marca temporal",
            "Nombre",
            "Correo electrónico",
            "Modelo",
            "Realizado"
        ]

        if os.path.exists(SOLICITUDES_CSV):
            solicitudes = pd.read_csv(SOLICITUDES_CSV)
        else:
            solicitudes = pd.DataFrame(columns=columnas)

        modelos_existentes = solicitudes["Modelo"].astype(str).str.lower().str.strip()

        if modelo.lower().strip() in modelos_existentes.values:
            return jsonify({
                "ok": False,
                "error": "Este modelo ya ha sido solicitado."
            }), 400

        nueva_solicitud = pd.DataFrame([{
            "Marca temporal": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Nombre": nombre,
            "Correo electrónico": correo,
            "Modelo": modelo,
            "Realizado": 0
        }])

        solicitudes = pd.concat([solicitudes, nueva_solicitud], ignore_index=True)
        solicitudes.to_csv(SOLICITUDES_CSV, index=False)

        return jsonify({"ok": True, "mensaje": "Solicitud guardada correctamente"})

    except Exception as e:
        traceback.print_exc()
        return jsonify({"ok": False, "error": str(e)}), 500

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