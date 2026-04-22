const titulos = {
    alucinaciones: "Alucinaciones",
    lim_temporal: "Limitaciones temporales",
    falta_contexto: "Limitaciones de conversación",
    lim_dominio: "Limitaciones de dominio"
};

async function cargarDescripcion(riesgo) {
    try {
        const response = await fetch("datos/descripciones.json");
        const descripciones = await response.json();

        const definicion = descripciones[riesgo] || "Descripción no disponible.";

        // 👇 generar título bonito
        const titulo = titulos[riesgo] || formatearTitulo(riesgo);

        // 👇 insertar en el HTML
        document.getElementById("titulo-riesgo").textContent = titulo;
        document.getElementById("definicion-riesgo").textContent = definicion;

    } catch (error) {
        console.error("Error cargando descripciones:", error);

        document.getElementById("titulo-riesgo").textContent = "Error";
        document.getElementById("definicion-riesgo").textContent = "No se pudo cargar la descripción.";
    }
}

function formatearTitulo(texto) {
    return texto
        .replaceAll("_", " ")
        .replace(/\b\w/g, l => l.toUpperCase());
}

async function cargarRutasModelos() {
    const response = await fetch("list.json");
    console.log("URL:", response.url);
    console.log("Status:", response.status);

    if (!response.ok) {
        throw new Error(`No se pudo cargar list.json: HTTP ${response.status}`);
    }

    const texto = await response.text();
    console.log("Contenido recibido:", texto);

    try {
        return JSON.parse(texto);
    } catch (e) {
        throw new Error("list.json existe, pero no es JSON válido: " + e.message);
    }
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
    const rutas = await cargarRutasModelos();
    const resultados = [];

    for (const ruta of rutas) {
        try {
            const response = await fetch(ruta);
            if (!response.ok) {
                console.error(`No se pudo cargar ${ruta}`);
                continue;
            }

            const datos = await response.json();
            resultados.push({
                modelo_nombre: ruta.split("/").pop().replace(".json", ""),
                notas: datos.notas || {}
            });
        } catch (error) {
            console.error(`Error leyendo ${ruta}:`, error);
        }
    }

    return resultados;
}

async function initRisksPage() {
    const params = new URLSearchParams(window.location.search);
    const riesgo = params.get("riesgo") || "alucinaciones";

    const descripcion = await cargarDescripcion(riesgo);

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