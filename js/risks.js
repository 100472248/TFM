async function cargarDescripcion(riesgo) {
    try {
        const response = await fetch("../datos/descripciones.json");
        const descripciones = await response.json();
        return descripciones[riesgo] || "Descripción no disponible.";
    } catch (error) {
        console.error("Error cargando descripciones:", error);
        return "Descripción no disponible.";
    }
}

async function cargarRutasModelos() {
    const response = await fetch("./list.json");
    if (!response.ok) {
        throw new Error("No se pudo cargar list.json");
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
            const score = (nota.SBert + nota.Bleurt) / 2;
            datos.push({
                modelo: modelo,
                calificacion_sbert: Number(nota.SBert.toFixed(2)),
                calificacion_bleurt: Number(nota.Bleurt.toFixed(2)),
                score: score
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
            tablas[tema].push({
                modelo: modelo,
                calificacion_sbert: Number(Number(nota.SBert).toFixed(2)),
                calificacion_bleurt: Number(Number(nota.Bleurt).toFixed(2))
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
                        <th>Modelo</th>
                        <th>SBert</th>
                        <th>Bleurt</th>
                    </tr>
                </thead>
                <tbody>
    `;

    for (const fila of filas) {
        html += `
            <tr>
                <td>${fila.modelo}</td>
                <td>${fila.calificacion_sbert}</td>
                <td>${fila.calificacion_bleurt}</td>
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
                            <th>Modelo</th>
                            <th>SBert</th>
                            <th>Bleurt</th>
                        </tr>
                    </thead>
                    <tbody>
        `;

        for (const fila of tablasPorTema[tema]) {
            html += `
                <tr>
                    <td>${fila.modelo}</td>
                    <td>${fila.calificacion_sbert}</td>
                    <td>${fila.calificacion_bleurt}</td>
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
    document.getElementById("descripcion-texto").textContent = descripcion;

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