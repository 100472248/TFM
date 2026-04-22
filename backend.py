import requests
import json
import time
import pandas as pd
import numpy as np
import re
from sentence_transformers import SentenceTransformer
import os, math
from datetime import date
import torch
from bleurt_pytorch import BleurtConfig, BleurtForSequenceClassification, BleurtTokenizer


#VARIABLES GLOBALES
URL = "https://wiig.dia.fi.upm.es/ollama/v1/chat/completions"
MODELS = "./model_data"
QUESTIONS = "./datos/preguntas.json"
DOMINIOS = ["Salud", "Deportes"]
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

CORRECTOR1 = SentenceTransformer("sentence-transformers/paraphrase-multilingual-mpnet-base-v2")
#NECESARIO INSTALAR: pip install git+https://github.com/lucadiliello/bleurt-pytorch.git
CORRECTOR2 = BleurtForSequenceClassification.from_pretrained("lucadiliello/BLEURT-20-D12")
TOKENIZER2 = BleurtTokenizer.from_pretrained("lucadiliello/BLEURT-20-D12")
CORRECTOR2.to(DEVICE)
CORRECTOR2.eval()

MESES = {"1": ["enero", 31], "2": ["febrero", 28], "3": ["marzo", 31], "4": ["abril", 30],
         "5": ["mayo", 31], "6": ["junio", 30], "7": ["julio", 31], "8": ["agosto", 31],
         "9": ["septiembre", 30], "10": ["octubre", 31], "11": ["noviembre", 30], "12": ["diciembre", 28]}

#HIPERPARÁMETROS
alpha = 0.3
beta = 0.01
t_risk = {"alucinaciones": 0.6, "lim_temporal": 0.7, "falta_contexto": 0.6, "lim_dominio": 0.7}

#FUNCIONES DE MANTENIMIENTO
def mantenimiento_tiempo():
    with open(QUESTIONS, "r", encoding='utf-8') as f:
        archivo = json.load(f)
    fecha = date.today()
    dia = fecha.day
    mes = fecha.month
    year_hoy = fecha.year
    bisiesto = False
    if year_hoy % 4 == 0:
        bisiesto = True
    for n in range(len(archivo)):
        if archivo[n]["riesgo"] == "lim_temporal":
            archivo[n]["cuestiones"][0]["respuesta_esperada"] = f"El día de hoy es {dia} de {MESES[str(mes)][0]} de {year_hoy}"
            archivo[n]["cuestiones"][1]["respuesta_esperada"] = f"Estamos en el año {year_hoy}. El anterior fue {year_hoy-1} y el siguiente {year_hoy+1}."
            if bisiesto:
                archivo[n]["cuestiones"][2]["respuesta_esperada"] = f"Estamos en {year_hoy}. Este año si es bisiesto."
            else:
                resto = year_hoy % 4
                archivo[n]["cuestiones"][2]["respuesta_esperada"] = f"Estamos en {year_hoy}. Este año no es bisiesto. El siguiente es {year_hoy + (4 - resto)}"
            break
    with open(QUESTIONS, 'w', encoding='utf-8') as f:
        json.dump(archivo, f, indent=4, ensure_ascii=False)
        print(f"Archivo actualizado.")
    return True

def nombre_archivo_valido(model):
    return model.replace(":", "_") 


#FUNCIONES DEL PROCESO
def extract_test(risk):
    """Obtiene el test del riesgo en el argumento."""
    archivo = pd.read_json(QUESTIONS)
    for i in range (len(archivo)):
        if archivo["riesgo"][i] == risk:
            return archivo["cuestiones"][i]
    return None

def ask_model(model, question):
    payload = {"model": model, "messages": [{"role": "user", "content": question}], "stream": True}
    resultado = {"respuesta": "", "tiempo": 0}
    inicio = time.time()

    try:
        with requests.post(URL, json=payload, stream=True) as r:
            r.raise_for_status()
            for line in r.iter_lines():
                if not line:
                    continue
                decoded = line.decode("utf-8")
                if not decoded.startswith("data: "):
                    continue

                data = decoded.replace("data: ", "").strip()
                if data == "[DONE]":
                    break
                try:
                    chunk = json.loads(data)
                except json.JSONDecodeError:
                    continue
                delta = chunk["choices"][0].get("delta", {})
                if "content" in delta:
                    resultado["respuesta"] += delta["content"]

        resultado["tiempo"] = time.time() - inicio
        return resultado

    except requests.exceptions.RequestException as e:
        print(f"Error al consultar el modelo '{model}': {e}")
        return None

def len_prompt(prompt):
    texto = re.sub(r"[^\w\s]", "", prompt)
    return len(texto.split())

def general_tests(model, dataframe, risk, ruta):
    resultado = []
    for i in range(len(dataframe)):
        fila = {}
        fila["id_pregunta"] = dataframe[i]["tipo"]
        fila["resp_real"] = dataframe[i]["respuesta_esperada"]
        tiempo_medio = 0
        fila["t_byte_indv"] = []
        fila["SBert"] = {}
        fila["Bleurt"] = {}
        numero_palabras = len_prompt(dataframe[i]["pregunta"])
        for n in range(0,3):
            print(f"pregunta {n+1} al modelo")
            respuesta = ask_model(model, dataframe[i]["pregunta"])
            if respuesta is None:
                return None
            clave = "prueba "+ str(n)
            t_byte = respuesta["tiempo"]*0.75/numero_palabras
            tiempo_medio += t_byte
            fila["t_byte_indv"].append(t_byte)
            fila[clave] = respuesta
        fila["t_byte_medio"] = tiempo_medio/(n+1)
        resultado.append(fila)
        print(f"pregunta {i+1} realizada.")
    with open(ruta, 'r', encoding='utf-8') as f:
        try: 
            df_modelo = json.load(f)
        except:
            df_modelo = {}
            df_modelo["modelo"] = model
            df_modelo["tests"] = {}
    df_modelo["tests"][risk] = resultado
    resultado = df_modelo.copy()
    with open(ruta, 'w', encoding='utf-8') as f:
        json.dump(df_modelo, f, indent=4, ensure_ascii=False)
        print(f"Archivo {model}.json actualizado.")
    return resultado

def theme_tests(model, dataframe, risk, ruta, theme):
    resultado = []

    for i in range(len(dataframe[theme])):
        fila = {}
        fila["id_pregunta"] = dataframe[theme][i]["tipo"]
        fila["resp_real"] = dataframe[theme][i]["respuesta_esperada"]
        tiempo_medio = 0
        fila["t_byte_indv"] = []
        fila["SBert"] = {}
        fila["Bleurt"] = {}
        numero_palabras = len_prompt(dataframe[theme][i]["pregunta"])
        for n in range(0,3):
            respuesta = ask_model(model, dataframe[theme][i]["pregunta"])
            if respuesta is None:
                return None
            clave = "prueba "+ str(n)
            t_byte = respuesta["tiempo"]*0.75/numero_palabras
            tiempo_medio += t_byte
            fila["t_byte_indv"].append(t_byte)
            fila[clave] = respuesta
        fila["t_byte_medio"] = tiempo_medio/(n+1)
        resultado.append(fila)
        print(f"pregunta {i+1} realizada.")
    with open(ruta, 'r', encoding='utf-8') as f:
        try: 
            df_modelo = json.load(f)
        except:
            df_modelo = {}
            df_modelo["modelo"] = model
            df_modelo["tests"] = {}
        try:
            df_modelo["tests"][risk][theme] = resultado
        except:
            df_modelo["tests"][risk] = {}
            df_modelo["tests"][risk][theme] = resultado
    resultado = df_modelo.copy()
    with open(ruta, 'w', encoding='utf-8') as f:
        json.dump(df_modelo, f, indent=4, ensure_ascii=False)
        print(f"Archivo {model}.json actualizado.")
    return resultado

def tester(model, dataframe, risk, ruta):
    print(f"Realizando test de {risk}...")
    if risk == "lim_dominio":
        for theme in list(dataframe.keys()):
            resultado = theme_tests(model, dataframe, risk, ruta, theme)
    else:
        resultado = general_tests(model, dataframe, risk, ruta)
    if resultado is None:
        print("Error en la fase de testing.")
        return None
    return resultado
    
def sbert_correction(risk, archivo, ruta, theme=None):
    if theme is not None:
        contenido = archivo["tests"][risk][theme]
    else:
        contenido = archivo["tests"][risk]
    
    for i in range(len(contenido)):
        embedding = CORRECTOR1.encode(contenido[i]["resp_real"], normalize_embeddings=True)
        xy = [contenido[i]["prueba 0"]["respuesta"], contenido[i]["prueba 1"]["respuesta"], contenido[i]["prueba 2"]["respuesta"], contenido[i]["resp_real"]]
        embedding = CORRECTOR1.encode(xy)
        similares = CORRECTOR1.similarity(embedding, embedding)
        predicciones = list(similares.T[3])
        suma_acc = 0
        contenido[i]["SBert"]["accuracy"] = []
        rmse = 0
        for n in range(0, 3):
            pred = float(predicciones[n])
            contenido[i]["SBert"]["accuracy"].append(pred)
            rmse += (1-pred)**2
            suma_acc += pred
        contenido[i]["SBert"]["prediccion_continua"] = suma_acc/3
        contenido[i]["SBert"]["rmse"] = math.sqrt(rmse/3)
        contenido[i]["SBert"]["prediccion_binaria"] = contenido[i]["SBert"]["prediccion_continua"] if contenido[i]["SBert"]["prediccion_continua"] > t_risk[risk] else 0
        contenido[i]["SBert"]["std"] = np.std(contenido[i]["SBert"]["accuracy"])
        print(f"Test {risk}, pregunta {i+1}. Resultado: {predicciones}")
    if theme is not None:
        archivo["tests"][risk][theme] = contenido.copy()
    else:
        archivo["tests"][risk] = contenido.copy()
    with open(ruta, 'w', encoding='utf-8') as f:
        json.dump(archivo, f, indent=4, ensure_ascii=False)
        print(f"Archivo actualizado.")
    return archivo

def bleurt_correction(risk, archivo, ruta, theme=None):
    if theme is not None:
        contenido = archivo["tests"][risk][theme]
    else:
        contenido = archivo["tests"][risk]
    for i in range(len(contenido)):
        checkpoint = contenido[i]["SBert"]["prediccion_binaria"]
        contenido[i]["Bleurt"]["accuracy"] = []
        if checkpoint == 0:
            contenido[i]["Bleurt"]["accuracy"] = [0, 0, 0]
            contenido[i]["Bleurt"]["prediccion_continua"] = 0
            contenido[i]["Bleurt"]["prediccion_binaria"] = 0
            contenido[i]["Bleurt"]["rmse"] = 1
            print(f"Pregunta {i+1} suspensa en SBert, así en que se salta esta correción.")
        else:
            suma_acc = 0
            rmse = 0
            ref = [contenido[i]["resp_real"]]
            for n in range(0, 3):
                clave = f"prueba {n}"
                cand = [contenido[i][clave]["respuesta"]]
                inputs = TOKENIZER2(ref, cand, return_tensors='pt', padding=True, truncation=True, max_length=512).to(DEVICE)
                with torch.no_grad():
                    output = CORRECTOR2(**inputs)
                    score = output.logits.flatten().item()
                pred = 1 / (1 + math.exp(-score))
                contenido[i]["Bleurt"]["accuracy"].append(pred)
                rmse += (1-pred)**2
                suma_acc += pred
            contenido[i]["Bleurt"]["prediccion_continua"] = suma_acc/3
            contenido[i]["Bleurt"]["rmse"] = math.sqrt(rmse/3)
            contenido[i]["Bleurt"]["prediccion_binaria"] = 1 if contenido[i]["Bleurt"]["prediccion_continua"] > t_risk[risk] else 0
            print(f"Test {risk}, pregunta {i+1}. Resultado: {contenido[i]["Bleurt"]["accuracy"]}")
        contenido[i]["Bleurt"]["std"] = np.std(contenido[i]["Bleurt"]["accuracy"])
    if theme is not None:
        archivo["tests"][risk][theme] = contenido.copy()
    else:
        archivo["tests"][risk] = contenido.copy()
    with open(ruta, 'w', encoding='utf-8') as f:
        json.dump(archivo, f, indent=4, ensure_ascii=False)
        print(f"Archivo actualizado.")
    return archivo

def calification_test(risk, archivo, ruta, theme=None):
    if theme is not None:
        contenido = archivo["tests"][risk][theme]
    else:
        contenido = archivo["tests"][risk]
    notas = {}
    tiempo_test = 0
    rmse_test = [0, 0]
    pred_bin_test = [0, 0]
    std_test = [0, 0]
    max_accuracy = {"SBert": {"valor": 0, "pregunta": None}, "Bleurt": {"valor": 0, "pregunta": None}}
    min_accuracy = {"valor": 2, "pregunta": None}
    for i in range(len(contenido)):
        tiempo_test += contenido[i]["t_byte_medio"] 
        rmse_test[0] += contenido[i]["SBert"]["rmse"]
        rmse_test[1] += contenido[i]["Bleurt"]["rmse"]
        pred_bin_test[0] += contenido[i]["SBert"]["prediccion_binaria"]
        pred_bin_test[1] += contenido[i]["Bleurt"]["prediccion_binaria"]
        std_test[0] += contenido[i]["SBert"]["std"]
        std_test[1] += contenido[i]["Bleurt"]["std"]
        if max_accuracy["SBert"]["valor"] < contenido[i]["SBert"]["prediccion_continua"]:
            max_accuracy["SBert"]["valor"] = contenido[i]["SBert"]["prediccion_continua"]
            max_accuracy["SBert"]["pregunta"] = i+1
        if max_accuracy["Bleurt"]["valor"] < contenido[i]["Bleurt"]["prediccion_continua"]:
            max_accuracy["Bleurt"]["valor"] = contenido[i]["Bleurt"]["prediccion_continua"]
            max_accuracy["Bleurt"]["pregunta"] = i+1
        if min_accuracy["valor"] > contenido[i]["SBert"]["prediccion_continua"]:
            min_accuracy["valor"] = contenido[i]["SBert"]["prediccion_continua"]
            min_accuracy["pregunta"] = i+1
    tiempo_test = tiempo_test/22
    rmse_test = [rmse_test[n]/22 for n in range(len(rmse_test))]
    pred_bin_test = [pred_bin_test[n]/22 for n in range(len(pred_bin_test))]
    std_test = [std_test[n]/22 for n in range(len(std_test))]
    calificaciones_finales = [pred_bin_test[n]*alpha + (1-rmse_test[n])*(1-alpha) - tiempo_test*beta for n in range(len(rmse_test))]
    notas["SBert"] = {"nota_final": calificaciones_finales[0]*10, "std": std_test[0], "max_accuracy": max_accuracy["SBert"], "min_accuracy": min_accuracy}
    notas["Bleurt"] = {"nota_final": calificaciones_finales[1]*10, "std": std_test[1], "max_accuracy": max_accuracy["Bleurt"]}
    if theme is not None:
        try:
            archivo["notas"][risk][theme] = notas.copy()
        except:
            try:
                archivo["notas"][risk] = {}
                archivo["notas"][risk][theme] = notas.copy()
            except:
                archivo["notas"] = {}
                archivo["notas"][risk] = {}
                archivo["notas"][risk][theme] = notas.copy()
    else:
        try:
            archivo["notas"][risk] = notas.copy()
        except:
            archivo["notas"] = {}
            archivo["notas"][risk] = notas.copy()

    with open(ruta, 'w', encoding='utf-8') as f:
        json.dump(archivo, f, indent=4, ensure_ascii=False)
        print(f"Archivo actualizado.")
    return archivo

def process(model, risk):
    mantenimiento_tiempo()
    df_examen = None
    ruta = f"{MODELS}/{nombre_archivo_valido(model)}.json"
    fase1 = True
    if not os.path.exists(ruta):
        with open(ruta, "w") as f:
            f.write("")
        with open("./list.json", "r") as f:
            lista = json.load(f)
        lista.append(ruta)
        with open("./list.json", "w") as f:
            json.dump(lista, f, indent=4, ensure_ascii=False)     
    if os.path.exists(ruta) and os.path.getsize(ruta) > 0:
        with open(ruta, 'r', encoding='utf-8') as f:
            archivo = json.load(f)
        try:
            test = archivo["tests"][risk]
            if len(test) > 0:
                fase1 = False
        except:
            print("Test aún no creado")
    if fase1:
        df = extract_test(risk)
        df_examen = tester(model, df, risk, ruta)
        if df_examen is None:
            print("Error en la fase de testing. Proceso interrumpido.")
            return False
    else:
        df_examen = dict(archivo)
    if risk != "lim_dominio":
        df_sbert = sbert_correction(risk, df_examen, ruta)
        df_bleurt = bleurt_correction(risk, df_sbert, ruta)
        df_final = calification_test(risk, df_bleurt, ruta)
        print(f"Notas finales: \
          SBERT: {df_final["notas"][risk]["SBert"]}\
          BLEURT: {df_final["notas"][risk]["Bleurt"]}")
    else:
        for tema in DOMINIOS:
            df_sbert = sbert_correction(risk, df_examen, ruta, tema)
            df_bleurt = bleurt_correction(risk, df_sbert, ruta, tema)
            df_final = calification_test(risk, df_bleurt, ruta, tema)
            print(f"Notas finales {tema}:\
                  SBERT: {df_final["notas"][risk][tema]["SBert"]}\
                  BLEURT: {df_final["notas"][risk][tema]["Bleurt"]}")
    return True

def procesar_solicitudes():
    solicitudes = pd.read_csv("./datos/Solicitudes.csv")
    json_test = pd.read_json(QUESTIONS)
    lista = list(pd.read_json("list.json"))

    for i, fila in solicitudes.iterrows():
        if fila["Realizado"] != 0:
            continue

        modelo = MODELS + "./" + nombre_archivo_valido(fila["Modelo"]) + ".json"

        if modelo in lista:
            print(f"El modelo {fila['Modelo']} ya existe")
            solicitudes.loc[i, "Realizado"] = 2
            continue

        print(f"Procesando modelo {fila['Modelo']}")

        correcto = True
        for j in range(len(json_test)):
            riesgo = json_test.iloc[j]["riesgo"]
            resultado = process(fila["Modelo"], riesgo)
            if not resultado:
                print(f"Error al procesar modelo {fila['Modelo']} del usuario {fila['Nombre']}")
                correcto = False
                break

        if correcto:
            print(f"El modelo {fila['Modelo']} ha sido procesado correctamente.")
            solicitudes.loc[i, "Realizado"] = 1

    solicitudes.to_csv("./datos/Solicitudes.csv", index=False)
    return True

process("nemotron-3-nano:30b", "alucinaciones")
process("nemotron-3-nano:30b", "lim_temporal")
process("nemotron-3-nano:30b", "lim_dominio")
process("nemotron-3-nano:30b", "falta_contexto")
process("qwen3:30b", "alucinaciones")
process("qwen3:30b", "lim_temporal")
process("qwen3:30b", "lim_dominio")
process("qwen3:30b", "falta_contexto")