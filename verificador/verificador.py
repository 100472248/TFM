import pandas as pd
import matplotlib.pyplot as plt 
import math, json
from pathlib import Path
from collections import Counter

ruta_script = Path(__file__).parent
ruta_json = ruta_script / "verificador.json"
with open(ruta_json, 'r', encoding='utf-8') as f:
    VERIFICADOR = json.load(f)
CARPETA_MODELOS = (ruta_script / ".." / "backend" / "model_data").resolve()
DOMINIOS = ["Salud", "Deportes"]
LIMITES = {
    "SBert": {
        "alucinaciones": 0.6,
        "lim_temporal": 0.7,
        "falta_contexto": 0.6,
        "lim_dominio": 0.7,
        "min": 0.5
    },
    "Bleurt": [0.55, 0.4]
    }


def formula_SBert(nota, riesgo):
    if nota < LIMITES["SBert"]["min"]:
        return 0
    else:
        if nota < LIMITES["SBert"][riesgo]:
            return 1
        else:
            return 2


def formula_Bleurt(nota):
    if nota < LIMITES["Bleurt"][1]:
        return 0
    else:
        if nota < LIMITES["Bleurt"][0]:
            return 1
        else:
            return 2


def formula_credibilidad(nota_modelo, nota_humana):
    diferencia = abs(nota_modelo - nota_humana)
    return 2 - diferencia


def calculo_resultados():
    tests = {}
    for riesgo in VERIFICADOR:
        if riesgo["riesgo"] != "lim_dominio":
            datos = {}
            for i in range(1, 4):
                prueba = riesgo[f"modelo_{i}"]
                if not prueba:
                    continue
                archivo = f"{prueba['nombre']}.json"
                ruta_modelo = CARPETA_MODELOS / archivo
                with open(ruta_modelo, 'r', encoding='utf-8') as f:
                    modelo = json.load(f)
                valores_SBert, valores_Bleurt = {}, {}
                valores_humanos = prueba["check"]
                credibilidad = {"SBert": 0, "Bleurt": 0}
                num_Bleurt = 0
                for n in range(0, len(valores_humanos.values())):
                    nota_SBert = modelo["tests"][riesgo["riesgo"]][n]["SBert"]["prediccion_continua"]
                    nota_Bleurt = modelo["tests"][riesgo["riesgo"]][n]["Bleurt"]["prediccion_continua"]
                    
                    valores_SBert[f"{n+1}"] = formula_SBert(nota_SBert, riesgo["riesgo"])
                    credibilidad["SBert"] += formula_credibilidad(valores_SBert[f"{n+1}"], valores_humanos[f"{n+1}"])
                    if nota_Bleurt != 0:
                        valores_Bleurt[f"{n+1}"] = formula_Bleurt(nota_Bleurt)
                        credibilidad["Bleurt"] += formula_credibilidad(valores_Bleurt[f"{n+1}"], valores_humanos[f"{n+1}"])
                        num_Bleurt += 1
                    else:
                        valores_Bleurt[f"{n+1}"] = -1

                credibilidad["SBert"] = credibilidad["SBert"] * 10 / 44
                credibilidad["Bleurt"] = credibilidad["Bleurt"] * 10 / (num_Bleurt * 2) if num_Bleurt > 0 else 0
                datos_prueba = {
                    "modelo": prueba["nombre"],
                    "notas_humanas": valores_humanos,
                    "notas_SBert": valores_SBert,
                    "notas_Bleurt": valores_Bleurt,
                    "credibilidad": credibilidad
                }
                datos[f"prueba_{i}"] = datos_prueba
            
            # Cálculo de credibilidad media para el riesgo estándar
            credibilidad_media = {"SBert": 0, "Bleurt": 0}
            num_pruebas = len([k for k in datos.keys() if k.startswith("prueba_")])
            if num_pruebas > 0:
                for k in datos.keys():
                    if k.startswith("prueba_"):
                        credibilidad_media["SBert"] += datos[k]["credibilidad"]["SBert"]
                        credibilidad_media["Bleurt"] += datos[k]["credibilidad"]["Bleurt"]
                credibilidad_media["SBert"] /= num_pruebas
                credibilidad_media["Bleurt"] /= num_pruebas
            datos["credibilidad_media"] = credibilidad_media
            
            # Guardamos el riesgo directo
            tests[riesgo["riesgo"]] = datos

        else:
            # CASO ESPECIAL: lim_dominio se divide en sub-temas independientes
            pruebas = riesgo["dominios"]
            for m in range(0, len(pruebas)):
                tema = pruebas[m]
                nombre_tema = tema["tema"]  # "Salud" o "Deportes"
                datos_tema = {}  # Diccionario propio y exclusivo para este tema
                
                for i in range(1, 4):
                    prueba = tema[f"modelo_{i}"]
                    if not prueba:
                        continue      
                    archivo = f"{prueba['nombre']}.json"
                    ruta_modelo = CARPETA_MODELOS / archivo
                    with open(ruta_modelo, 'r', encoding='utf-8') as f:
                        modelo = json.load(f)             
                    valores_SBert, valores_Bleurt = {}, {}
                    valores_humanos = prueba["check"]
                    credibilidad = {"SBert": 0, "Bleurt": 0}
                    num_Bleurt = 0
                    for n in range(0, len(valores_humanos.values())):
                        nota_SBert = modelo["tests"][riesgo["riesgo"]][nombre_tema][n]["SBert"]["prediccion_continua"]
                        nota_Bleurt = modelo["tests"][riesgo["riesgo"]][nombre_tema][n]["Bleurt"]["prediccion_continua"]
                        
                        valores_SBert[f"{n+1}"] = formula_SBert(nota_SBert, riesgo["riesgo"])
                        credibilidad["SBert"] += formula_credibilidad(valores_SBert[f"{n+1}"], valores_humanos[f"{n+1}"])
                        if nota_Bleurt != 0:
                            valores_Bleurt[f"{n+1}"] = formula_Bleurt(nota_Bleurt)
                            credibilidad["Bleurt"] += formula_credibilidad(valores_Bleurt[f"{n+1}"], valores_humanos[f"{n+1}"])
                            num_Bleurt += 1
                        else:
                            valores_Bleurt[f"{n+1}"] = -1

                    credibilidad["SBert"] = credibilidad["SBert"] * 10 / 44
                    credibilidad["Bleurt"] = credibilidad["Bleurt"] * 10 / (num_Bleurt * 2) if num_Bleurt > 0 else 0
                    datos_prueba = {
                        "dominio": nombre_tema,
                        "modelo": prueba["nombre"],
                        "notas_humanas": valores_humanos,
                        "notas_SBert": valores_SBert,
                        "notas_Bleurt": valores_Bleurt,
                        "credibilidad": credibilidad
                    }
                    datos_tema[f"prueba_{i}"] = datos_prueba
                
                # Cálculo de credibilidad media exclusivo para este TEMA
                credibilidad_media_tema = {"SBert": 0, "Bleurt": 0}
                num_pruebas_tema = len([k for k in datos_tema.keys() if k.startswith("prueba_")])
                if num_pruebas_tema > 0:
                    for k in datos_tema.keys():
                        if k.startswith("prueba_"):
                            credibilidad_media_tema["SBert"] += datos_tema[k]["credibilidad"]["SBert"]
                            credibilidad_media_tema["Bleurt"] += datos_tema[k]["credibilidad"]["Bleurt"]
                    credibilidad_media_tema["SBert"] /= num_pruebas_tema
                    credibilidad_media_tema["Bleurt"] /= num_pruebas_tema
                datos_tema["credibilidad_media"] = credibilidad_media_tema
                
                # Guardamos de forma separada en el diccionario maestro usando una clave única
                tests[f"lim_dominio_{nombre_tema}"] = datos_tema

    return tests


def graficas_resultados(tests_dict):
    """
    Genera los bloques de gráficas solicitados para el TFM.
    """
    # Configuramos estilo general básico
    plt.rcParams.update({'font.size': 10, 'figure.titlesize': 14})
    
    # -----------------------------------------------------------------
    # REQUISITO 0: Comparación de Credibilidad Media ENTRE Riesgos/Temas
    # -----------------------------------------------------------------
    riesgos_globales = []
    media_sbert_global = []
    media_bleurt_global = []
    
    for clave_riesgo, datos in tests_dict.items():
        if "credibilidad_media" in datos:
            riesgos_globales.append(clave_riesgo)
            media_sbert_global.append(datos["credibilidad_media"]["SBert"])
            media_bleurt_global.append(datos["credibilidad_media"]["Bleurt"])
            
    if riesgos_globales:
        x_global = range(len(riesgos_globales))
        fig, ax = plt.subplots(figsize=(10, 5))
        
        ax.bar([i - 0.2 for i in x_global], media_sbert_global, width=0.4, label='Media SBert', color='#2ecc71')
        ax.bar([i + 0.2 for i in x_global], media_bleurt_global, width=0.4, label='Media Bleurt', color='#34495e')
        
        ax.set_title("Comparación de Credibilidad Media entre Riesgos y Dominios", pad=15)
        ax.set_xticks(x_global)
        ax.set_xticklabels(riesgos_globales, rotation=15, ha='right')
        ax.set_ylabel("Puntuación de Credibilidad Media (0-10)")
        ax.set_ylim(0, 10)
        ax.grid(axis='y', linestyle='--', alpha=0.7)
        ax.legend()
        plt.tight_layout()
        plt.show()

    # -----------------------------------------------------------------
    # REQUISITO 1: Credibilidad de SBert y Bleurt por modelo en cada riesgo
    # -----------------------------------------------------------------
    for clave_riesgo, datos in tests_dict.items():
        modelos = []
        cred_sbert = []
        cred_bleurt = []
        
        for k, v in datos.items():
            if k.startswith("prueba_"):
                nombre_label = f"{v['modelo']} ({v['dominio']})" if "dominio" in v else v['modelo']
                modelos.append(nombre_label)
                cred_sbert.append(v["credibilidad"]["SBert"])
                cred_bleurt.append(v["credibilidad"]["Bleurt"])
        
        if not modelos:
            continue
            
        x = range(len(modelos))
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.bar([i - 0.2 for i in x], cred_sbert, width=0.4, label='SBert', color='#3498db')
        ax.bar([i + 0.2 for i in x], cred_bleurt, width=0.4, label='Bleurt', color='#e74c3c')
        
        ax.set_title(f"Credibilidad de Modelos en Riesgo: {clave_riesgo}")
        ax.set_xticks(x)
        ax.set_xticklabels(modelos, rotation=15, ha='right')
        ax.set_ylabel("Puntuación de Credibilidad")
        ax.set_ylim(0, 10)
        ax.legend()
        plt.tight_layout()
        plt.show()

    # -----------------------------------------------------------------
    # REQUISITO 2: Preguntas calificadas por Bleurt (TODO EN UNA MISMA GRÁFICA)
    # -----------------------------------------------------------------
    list_riesgos = []
    p1_valores = []
    p2_valores = []
    p3_valores = []
    medias_valores = []
    
    # Extraemos los datos de todos los riesgos/temas para agruparlos
    for clave_riesgo, datos in tests_dict.items():
        # Contamos preguntas válidas (!= -1)
        p1 = sum(1 for nota in datos.get("prueba_1", {}).get("notas_Bleurt", {}).values() if nota != -1)
        p2 = sum(1 for nota in datos.get("prueba_2", {}).get("notas_Bleurt", {}).values() if nota != -1)
        p3 = sum(1 for nota in datos.get("prueba_3", {}).get("notas_Bleurt", {}).values() if nota != -1)
        
        num_pruebas = sum(1 for k in datos.keys() if k.startswith("prueba_"))
        if num_pruebas == 0:
            continue
            
        media = round((p1 + p2 + p3) / num_pruebas, 1)
        
        # Guardamos en las listas globales para la gráfica
        list_riesgos.append(clave_riesgo)
        p1_valores.append(p1)
        p2_valores.append(p2)
        p3_valores.append(p3)
        medias_valores.append(media)

    if list_riesgos:
        import numpy as np
        x = np.arange(len(list_riesgos))  # Localizaciones de los grupos de riesgos
        ancho_barra = 0.18               # Ancho de cada una de las 4 barras
        
        fig, ax = plt.subplots(figsize=(12, 6))
        
        # Dibujamos las 4 columnas desplazándolas en el eje X
        b1 = ax.bar(x - 1.5 * ancho_barra, p1_valores, ancho_barra, label='1ª Prueba', color='#34495e')
        b2 = ax.bar(x - 0.5 * ancho_barra, p2_valores, ancho_barra, label='2ª Prueba', color='#5dade2')
        b3 = ax.bar(x + 0.5 * ancho_barra, p3_valores, ancho_barra, label='3ª Prueba', color='#aeb6bf')
        b4 = ax.bar(x + 1.5 * ancho_barra, medias_valores, ancho_barra, label='Media Riesgo', color='#2ecc71', edgecolor='black')
        
        # Aplicamos el estilo discontinuo a todas las barras de la media
        for barra in b4:
            barra.set_linestyle('--')
            barra.set_linewidth(1.2)
            
        # Configuración de la estética del gráfico global
        ax.set_title("Preguntas Evaluadas por Bleurt por Prueba y Riesgo/Dominio (Máx. 22)", pad=20)
        ax.set_ylabel("Nº de Preguntas Validadas")
        ax.set_xticks(x)
        ax.set_xticklabels(list_riesgos, rotation=15, ha='right')
        ax.set_ylim(0, 26)
        ax.grid(axis='y', linestyle=':', alpha=0.6)
        ax.legend(loc='upper right')
        
        # Añadir los valores numéricos encima de cada barra individual para que sea legible
        for conjunto_barras in [b1, b2, b3, b4]:
            for barra in conjunto_barras:
                altura = barra.get_height()
                ax.text(barra.get_x() + barra.get_width()/2., altura + 0.3, 
                        f"{altura}", ha='center', va='bottom', fontsize=8, fontweight='bold')
                
        plt.tight_layout()
        plt.show()

    # -----------------------------------------------------------------
    # REQUISITO 3: Número de 0, 1 y 2 dados por cada corrector por riesgo
    # -----------------------------------------------------------------
    for clave_riesgo, datos in tests_dict.items():
        counts = {
            "Humano": {0: 0, 1: 0, 2: 0},
            "SBert": {0: 0, 1: 0, 2: 0},
            "Bleurt": {0: 0, 1: 0, 2: 0}
        }
        
        for k, v in datos.items():
            if k.startswith("prueba_"):
                for nota in v["notas_humanas"].values():
                    counts["Humano"][int(nota)] = counts["Humano"].get(int(nota), 0) + 1
                for nota in v["notas_SBert"].values():
                    counts["SBert"][int(nota)] = counts["SBert"].get(int(nota), 0) + 1
                for nota in v["notas_Bleurt"].values():
                    if nota != -1:
                        counts["Bleurt"][int(nota)] = counts["Bleurt"].get(int(nota), 0) + 1
                        
        fig, ax = plt.subplots(figsize=(8, 4))
        correctores = ["Humano", "SBert", "Bleurt"]
        zeros = [counts[c][0] for c in correctores]
        ones = [counts[c][1] for c in correctores]
        twos = [counts[c][2] for c in correctores]
        
        x = range(len(correctores))
        ax.bar([i - 0.25 for i in x], zeros, width=0.25, label='Nota 0', color='#e74c3c')
        ax.bar(list(x), ones, width=0.25, label='Nota 1', color='#f1c40f')
        ax.bar([i + 0.25 for i in x], twos, width=0.25, label='Nota 2', color='#2ecc71')
        
        ax.set_title(f"Distribución de Notas (0, 1, 2) por Corrector - {clave_riesgo}")
        ax.set_xticks(x)
        ax.set_xticklabels(correctores)
        ax.set_ylabel("Frecuencia de notas dadas")
        ax.legend()
        plt.tight_layout()
        plt.show()

    # -----------------------------------------------------------------
    # REQUISITO 4: Sistema de puntuación Top 3 por riesgo
    # -----------------------------------------------------------------
    puntuacion_modelos = Counter()
    
    for clave_riesgo, datos in tests_dict.items():
        if "prueba_1" in datos:
            puntuacion_modelos[datos["prueba_1"]["modelo"]] += 3
        if "prueba_2" in datos:
            puntuacion_modelos[datos["prueba_2"]["modelo"]] += 2
        if "prueba_3" in datos:
            puntuacion_modelos[datos["prueba_3"]["modelo"]] += 1

    modelos_ordenados = puntuacion_modelos.most_common()
    if modelos_ordenados:
        nombres_m, puntos_m = zip(*modelos_ordenados)
        
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.barh(nombres_m, puntos_m, color='#9b59b6', edgecolor='black')
        ax.invert_yaxis()  
        ax.set_title("Ranking Global de Modelos (Ponderado por presencia en Top 3 por Riesgo)")
        ax.set_xlabel("Puntuación Acumulada (1º=3pts, 2º=2pts, 3º=1pt)")
        ax.set_ylabel("Modelos")
        for i, v in enumerate(puntos_m):
            ax.text(v + 0.2, i, f" {v} pts", va='center', fontweight='bold')
        plt.tight_layout()
        plt.show()

if __name__ == "__main__":
    # Para poder hacer las gráficas de manera limpia sin romper los tipos de datos,
    # ejecutamos la extracción del diccionario base antes de volverlo DataFrame.
    
    # 1. Obtenemos el diccionario crudo modificando un segundo la salida para las gráficas:
    # (Hacemos un truco rápido para mantener tu estructura de DataFrame intacta si la usas en otro lado)
    
    # Ejecutamos tu función
    diccionario_tests = calculo_resultados()
    print("Muestra de credibilidad media (Alucinaciones):")
    print(diccionario_tests["alucinaciones"]["credibilidad_media"])
    
    
    # Lanzamos el módulo visual
    graficas_resultados(diccionario_tests)