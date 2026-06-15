import json
import re
from pathlib import Path
def escapar_latex(texto):
    """ Escapa los caracteres especiales que romperían la compilación de LaTeX. """
    if not isinstance(texto, str):
        return str(texto)
    caracteres_especiales = {
        '&': r'\&', '%': r'\%', '$': r'\$', '#': r'\#',
        '_': r'\_', '{': r'\{', '}': r'\}', '~': r'\textasciitilde{}',
        '^': r'\textasciicircum{}', '\\': r'\textbackslash{}'
    }
    regex = re.compile('|'.join(re.escape(str(key)) for key in caracteres_especiales.keys()))
    return regex.sub(lambda match: caracteres_especiales[match.group()], texto)

def construir_tabla_latex(titulo, lista_preguntas):
    """ Helper para construir el bloque de la tabla en LaTeX """
    lineas = []
    lineas.append(r"\begin{table}[htbp]")
    lineas.append(r"  \centering")
    lineas.append(f"  \\caption{{{titulo}}}")
    lineas.append(r"  \begin{tabularx}{\textwidth}{|X|X|X|}")
    lineas.append(r"    \hline")
    lineas.append(r"    \textbf{Objetivo} & \textbf{Pregunta} & \textbf{Respuesta Real} \\")
    lineas.append(r"    \hline")
    
    for cuestion in lista_preguntas:
        obj = escapar_latex(cuestion.get("objetivo", ""))
        preg = escapar_latex(cuestion.get("pregunta", ""))
        resp = escapar_latex(cuestion.get("respuesta_esperada", ""))
        
        lineas.append(f"    {obj} & {preg} & {resp} \\\\")
        lineas.append(r"    \hline")
    
    lineas.append(r"  \end{tabularx}")
    lineas.append(r"\end{table}")
    lineas.append("") # Línea en blanco
    return lineas

def generar_solo_tablas(archivo_json, salida_tex):
    ruta_script = Path(__file__).parent
    ruta_carpeta = (ruta_script / ".." / "backend" / "datos").resolve()
    ruta_json = ruta_carpeta / archivo_json
    ruta_salida_tex = ruta_script/ salida_tex
    with open(ruta_json, 'r', encoding='utf-8') as f:
        datos = json.load(f)
    
    lineas_latex = []
    
    for elemento in datos:
        riesgo = escapar_latex(elemento.get("riesgo", "Riesgo Sin Nombre"))
        cuestiones = elemento.get("cuestiones", [])
        
        # CASO 1: Es una lista -> El riesgo tiene un único test directo (No hay subtests)
        if isinstance(cuestiones, list):
            titulo_tabla = f"Riesgo: {riesgo}"
            lineas_latex.extend(construir_tabla_latex(titulo_tabla, cuestiones))
            
        # CASO 2: NO es una lista (es un diccionario) -> Tiene más de un test/subtest
        elif isinstance(cuestiones, dict):
            for nombre_subtest, lista_preguntas in cuestiones.items():
                subtest_escapado = escapar_latex(nombre_subtest)
                # Combinamos el nombre del riesgo con el del subtest
                titulo_tabla = f"Riesgo: {riesgo} - Subtest: {subtest_escapado}"
                lineas_latex.extend(construir_tabla_latex(titulo_tabla, lista_preguntas))
                
    # Guardar el resultado en el archivo .tex
    with open(ruta_salida_tex, 'w', encoding='utf-8') as f:
        f.write("\n".join(lineas_latex))
# --- Ejecución del programa ---
if __name__ == "__main__":
    # Cambia estos nombres por los de tus archivos
    archivo_json = "preguntas.json"
    archivo_salida_tex = "tablas_riesgos.tex"
    
    try:
        generar_solo_tablas(archivo_json, archivo_salida_tex)
        print(f"¡Hecho! Tablas guardadas limpiamente en '{archivo_salida_tex}'.")
    except FileNotFoundError:
        print(f"Error: Asegúrate de que existe el archivo '{archivo_json}'.")