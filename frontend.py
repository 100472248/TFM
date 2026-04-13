from flask import Flask, render_template, request
import json, os
import backend
import pandas as pd

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/risks')
def risks():
    riesgo = request.args.get("riesgo", "alucinaciones")
    descripcion = obtener_descripcion(riesgo)

    if riesgo == "lim_dominio":
        tablas_por_tema = construir_tablas_lim_dominio()
        return render_template(
            "risks.html",
            riesgo=riesgo,
            descripcion=descripcion,
            tablas_por_tema=tablas_por_tema,
            filas=None
        )

    filas = construir_tabla(riesgo)
    return render_template(
        "risks.html",
        riesgo=riesgo,
        filas=filas,
        descripcion=descripcion,
        tablas_por_tema=None
    )


def cargar_resultados(carpeta="./model_data"):
    resultados = {"modelos": [], "notas": []}
    extra = []

    if not os.path.exists(carpeta):
        return resultados, extra

    for nombre_archivo in os.listdir(carpeta):
        if nombre_archivo.endswith(".json"):
            ruta = os.path.join(carpeta, nombre_archivo)

            with open(ruta, "r", encoding="utf-8") as f:
                try:
                    datos = json.load(f)
                    modelo, _ = nombre_archivo.split(".json")
                    resultados["modelos"].append(modelo)
                    calificaciones = datos["notas"]
                    resultados["notas"].append(calificaciones)
                except json.JSONDecodeError:
                    print(f"Error leyendo {ruta}")

    return resultados, extra

def ordenar_resultados(resultados, risk):

    if len(resultados["modelos"]) < 2:
        return resultados
    
    datos = []
    for i in range(len(resultados["modelos"])):
        try:
            nota = resultados["notas"][i][risk]
            score = (nota["SBert"] + nota["Bleurt"]) / 2
            datos.append({"modelo": resultados["modelos"][i], "nota": nota, "score": score})
        except:
            pass

    # Ordenar por score descendente
    datos.sort(key=lambda x: x["score"], reverse=True)

    # Reconstruir estructura
    modelos_ordenados = [d["modelo"] for d in datos]
    notas_ordenadas = [d["nota"] for d in datos]
    return {"modelos": modelos_ordenados, "notas": notas_ordenadas}

def construir_tabla(riesgo, carpeta="model_data"):
    archivos, _ = cargar_resultados(carpeta)
    archivos_riesgo = ordenar_resultados(archivos, riesgo)
    filas = []
    for i in range(len(archivos_riesgo["modelos"])):
        modelo = archivos_riesgo["modelos"][i]
        test = archivos_riesgo["notas"][i]

        sbert = round(float(test["SBert"]), 2)
        bleurt = round(float(test["Bleurt"]), 2)

        fila = {
            "modelo": modelo,
            "calificacion_sbert": sbert,
            "calificacion_bleurt": bleurt
        }
        filas.append(fila)

    return filas

def construir_tablas_lim_dominio(carpeta="model_data"):
    archivos, _ = cargar_resultados(carpeta)
    tablas = {}

    for i in range(len(archivos["modelos"])):
        modelo = archivos["modelos"][i]

        try:
            notas_lim_dominio = archivos["notas"][i]["lim_dominio"]
        except:
            continue

        for tema, nota in notas_lim_dominio.items():
            if tema not in tablas:
                tablas[tema] = []

            fila = {
                "modelo": modelo,
                "calificacion_sbert": round(float(nota["SBert"]), 2),
                "calificacion_bleurt": round(float(nota["Bleurt"]), 2)
            }
            tablas[tema].append(fila)

    for tema in tablas:
        tablas[tema].sort(
            key=lambda x: (x["calificacion_sbert"] + x["calificacion_bleurt"]) / 2,
            reverse=True
        )

    return tablas


def obtener_descripcion(riesgo):
    descripciones = pd.read_json("descripciones.json", orient="index").to_dict()[0]
    return descripciones.get(riesgo, "Descripción no disponible.")


@app.route("/ask", methods=["GET", "POST"])
def ask():
    if request.method == "POST":
        modelo = request.form.get("modelo")
        # Validación rápida antes de procesar todo
        test = backend.ask_model(modelo, "Hola")
        if test is None:
            return render_template("ask.html", error="El modelo no existe en Ollama.")
        archivos, _ = cargar_resultados("./model_data")
        traducido = modelo.replace(":", "_")
        if traducido in archivos["modelos"]:
            return render_template("ask.html", error="El modelo ya existe. Por favor, elige otro nombre.")
        with open("solicitudes.json", "r", encoding="utf-8") as f:
            solicitudes = json.load(f)
        diccionario = {"usuario": request.form.get("usuario"), "gmail": request.form.get("gmail"), "modelo": modelo}
        solicitudes["procesar"].append(diccionario)
        with open("solicitudes.json", "w", encoding="utf-8") as f:
            json.dump(solicitudes, f, indent=4, ensure_ascii=False)
        return render_template("ask.html", success="Solicitud enviada correctamente.")
    return render_template("ask.html")
if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)
