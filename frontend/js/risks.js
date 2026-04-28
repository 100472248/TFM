const API_URL = "http://localhost:5000";
console.log("RISKS.JS CARGADO");
const titulos = {
    alucinaciones: "Alucinaciones",
    lim_temporal: "Limitaciones temporales",
    falta_contexto: "Limitaciones de conversación",
    lim_dominio: "Limitaciones de dominio"
};

async function cargarDescripcion(riesgo) {
    try {
        const response = await fetch(`${API_URL}/api/descripciones`);
        const descripciones = await response.json();

        return descripciones[riesgo] || "Descripción no disponible.";
    } catch (error) {
        console.error("Error cargando descripciones:", error);
        return "Descripción no disponible.";
    }
}
function formatearTitulo(texto) {
    return texto
        .replaceAll("_", " ")
        .replace(/\b\w/g, l => l.toUpperCase());
}

async function cargarRutasModelos() {
    const response = await fetch(`${API_URL}/api/modelos`);

    if (!response.ok) {
        throw new Error("No se pudo cargar la lista de modelos");
    }

    return await response.json();
}

function ordenarResultados(resultados, riesgo) {
    const datos = [];

    for (const archivo of resultados) {
        const modelo = archivo.modelo_nombre;
        const notas = archivo.notas;

        if (!notas || !notas[riesgo]) continue;

        try {
            const nota = notas[riesgo];

            const sbert = nota?.SBert?.nota_final;
            const bleurt = nota?.Bleurt?.nota_final;

            if (typeof sbert !== "number" || typeof bleurt !== "number") continue;

            const score = (sbert + bleurt) / 2;

            datos.push({
                modelo: modelo,
                calificacion_sbert: Number(sbert.toFixed(2)),
                calificacion_bleurt: Number(bleurt.toFixed(2)),
                score: score,

                // opcional, por si luego quieres mostrarlo
                sbert_std: nota?.SBert?.std ?? null,
                sbert_max_valor: nota?.SBert?.max_accuracy?.valor ?? null,
                sbert_max_pregunta: nota?.SBert?.max_accuracy?.pregunta ?? null,
                sbert_min_valor: nota?.SBert?.min_accuracy?.valor ?? null,
                sbert_min_pregunta: nota?.SBert?.min_accuracy?.pregunta ?? null,

                bleurt_std: nota?.Bleurt?.std ?? null,
                bleurt_max_valor: nota?.Bleurt?.max_accuracy?.valor ?? null,
                bleurt_max_pregunta: nota?.Bleurt?.max_accuracy?.pregunta ?? null
            });
        } catch (error) {
            console.error(`Error procesando ${modelo}:`, error);
        }
    }

    datos.sort((a, b) => b.score - a.score);
    return datos;
}

function construirTablasLimDominio(resultados) {
    const tablas = {};

    for (const archivo of resultados) {
        const modelo = archivo.modelo_nombre;
        const notas = archivo.notas;

        if (!notas || !notas["lim_dominio"]) continue;

        const notasLimDominio = notas["lim_dominio"];

        for (const tema in notasLimDominio) {
            if (!tablas[tema]) {
                tablas[tema] = [];
            }

            const nota = notasLimDominio[tema];

            const sbert = nota?.SBert?.nota_final;
            const bleurt = nota?.Bleurt?.nota_final;

            if (typeof sbert !== "number" || typeof bleurt !== "number") continue;

            tablas[tema].push({
                modelo: modelo,
                calificacion_sbert: Number(sbert.toFixed(2)),
                calificacion_bleurt: Number(bleurt.toFixed(2)),

                // opcional
                sbert_std: nota?.SBert?.std ?? null,
                sbert_max_valor: nota?.SBert?.max_accuracy?.valor ?? null,
                sbert_max_pregunta: nota?.SBert?.max_accuracy?.pregunta ?? null,
                sbert_min_valor: nota?.SBert?.min_accuracy?.valor ?? null,
                sbert_min_pregunta: nota?.SBert?.min_accuracy?.pregunta ?? null,

                bleurt_std: nota?.Bleurt?.std ?? null,
                bleurt_max_valor: nota?.Bleurt?.max_accuracy?.valor ?? null,
                bleurt_max_pregunta: nota?.Bleurt?.max_accuracy?.pregunta ?? null
            });
        }
    }

    for (const tema in tablas) {
        tablas[tema].sort((a, b) => {
            const scoreA = (a.calificacion_sbert + a.calificacion_bleurt) / 2;
            const scoreB = (b.calificacion_sbert + b.calificacion_bleurt) / 2;
            return scoreB - scoreA;
        });
    }

    return tablas;
}

function crearTablaHTML(filas) {
    if (!filas || filas.length === 0) {
        return "<p>No hay resultados disponibles para este riesgo.</p>";
    }

    let html = `
        <section class="tabla-riesgo">
            <table>
                <thead>
                    <tr>
                        <th rowspan="2">Modelo</th>
                        <th colspan="6">SBert</th>
                        <th colspan="4">Bleurt</th>
                    </tr>
                       <tr>
                            <th>Nota final</th>
                            <th>STD</th>
                            <th>Mayor precisión promedio</th>
                            <th>Pregunta con mayor prec.</th>
                            <th>Menor precisión promedio</th>
                            <th>Pregunta con menor prec.</th>
                            <th>Nota final</th>
                            <th>STD</th>
                            <th>Mayor precisión promedio</th>
                            <th>Pregunta con mayor prec.</th>
                        </tr>
                </thead>
                <tbody>
    `;

    for (const fila of filas) {
        html += `
            <tr>
                <td>${fila.modelo}</td>

                <td><strong>${fila.calificacion_sbert}</strong></td>
                <td>${fila.sbert_std != null ? fila.sbert_std.toFixed(3) : "-"}</td>
                <td>${fila.sbert_max_valor != null ? fila.sbert_max_valor.toFixed(3) : "-"}</td>
                <td>${fila.sbert_max_pregunta ?? "-"}</td>
                <td>${fila.sbert_min_valor != null ? fila.sbert_min_valor.toFixed(3) : "-"}</td>
                <td>${fila.sbert_min_pregunta ?? "-"}</td>

                <td><strong>${fila.calificacion_bleurt}</strong></td>
                <td>${fila.bleurt_std != null ? fila.bleurt_std.toFixed(3) : "-"}</td>
                <td>${fila.bleurt_max_valor != null ? fila.bleurt_max_valor.toFixed(3) : "-"}</td>
                <td>${fila.bleurt_max_pregunta ?? "-"}</td>
            </tr>
        `;
    }

    html += `
                </tbody>
            </table>
        </section>
    `;

    return html;
}

function crearTablasPorTemaHTML(tablasPorTema) {
    const temas = Object.keys(tablasPorTema);

    if (temas.length === 0) {
        return "<p>No hay resultados disponibles para este riesgo.</p>";
    }

    let html = "";

    for (const tema of temas) {
        html += `
            <section class="tabla-tema">
                <h2>${tema}</h2>
                <table>
                    <thead>
                        <tr>
                            <th rowspan="2">Modelo</th>
                            <th colspan="6">SBert</th>
                            <th colspan="4">Bleurt</th>
                        </tr>
                        <tr>
                            <th>Nota final</th>
                            <th>STD</th>
                            <th>Mayor precisión promedio</th>
                            <th>Pregunta con mayor prec.</th>
                            <th>Menor precisión promedio</th>
                            <th>Pregunta con menor prec.</th>
                            <th>Nota final</th>
                            <th>STD</th>
                            <th>Mayor precisión promedio</th>
                            <th>Pregunta con mayor prec.</th>
                        </tr>
                    </thead>
                    <tbody>
        `;

        for (const fila of tablasPorTema[tema]) {
            html += `
                <tr>
                    <td>${fila.modelo}</td>

                    <td><strong>${fila.calificacion_sbert}</strong></td>
                    <td>${fila.sbert_std != null ? fila.sbert_std.toFixed(3) : "-"}</td>
                    <td>${fila.sbert_max_valor != null ? fila.sbert_max_valor.toFixed(3) : "-"}</td>
                    <td>${fila.sbert_max_pregunta ?? "-"}</td>
                    <td>${fila.sbert_min_valor != null ? fila.sbert_min_valor.toFixed(3) : "-"}</td>
                    <td>${fila.sbert_min_pregunta ?? "-"}</td>

                    <td><strong>${fila.calificacion_bleurt}</strong></td>
                    <td>${fila.bleurt_std != null ? fila.bleurt_std.toFixed(3) : "-"}</td>
                    <td>${fila.bleurt_max_valor != null ? fila.bleurt_max_valor.toFixed(3) : "-"}</td>
                    <td>${fila.bleurt_max_pregunta ?? "-"}</td>
                </tr>
            `;
        }

        html += `
                    </tbody>
                </table>
            </section>
        `;
    }

    return html;
}

async function cargarDatosModelos() {
    const modelos = await cargarRutasModelos();
    const resultados = [];

    for (const modelo of modelos) {
        try {
            const nombreArchivo = modelo.split("/").pop();
            const response = await fetch(`${API_URL}/api/modelos/${nombreArchivo}`);

            if (!response.ok) {
                console.error(`No se pudo cargar ${nombreArchivo}`);
                continue;
            }

            const datos = await response.json();

            resultados.push({
                modelo_nombre: nombreArchivo.replace(".json", ""),
                notas: datos.notas || {}
            });
        } catch (error) {
            console.error(`Error leyendo ${modelo}:`, error);
        }
    }

    return resultados;
}

async function initRisksPage() {
    const params = new URLSearchParams(window.location.search);
    const riesgo = params.get("riesgo") || "alucinaciones";

    const tituloElemento = document.getElementById("titulo-riesgo");
    const definicionElemento = document.getElementById("definicion-riesgo");

    if (tituloElemento) {
        tituloElemento.textContent = (titulos[riesgo] || formatearTitulo(riesgo)).toUpperCase();
    }

    if (definicionElemento) {
        const descripcion = await cargarDescripcion(riesgo);
        definicionElemento.textContent = descripcion;
    }

    const contenedor = document.getElementById("contenedor-tablas");

    try {
        const resultados = await cargarDatosModelos();

        if (riesgo === "lim_dominio") {
            const tablasPorTema = construirTablasLimDominio(resultados);
            contenedor.innerHTML = crearTablasPorTemaHTML(tablasPorTema);
        } else {
            const filas = ordenarResultados(resultados, riesgo);
            contenedor.innerHTML = crearTablaHTML(filas);
        }
    } catch (error) {
        console.error(error);
        contenedor.innerHTML = "<p>Error al cargar los resultados.</p>";
    }
}

initRisksPage();