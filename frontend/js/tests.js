const API_URL = window.APP_CONFIG?.API_URL;

if (!API_URL) {
    throw new Error("API_URL no configurada. Define API_URL en docker-compose.");
}

const titulos = {
    alucinaciones: "Alucinaciones",
    lim_temporal: "Limitaciones temporales",
    falta_contexto: "Limitaciones de conversación",
    lim_dominio: "Limitaciones de dominios"
};

function crearTablaPreguntas(preguntas) {
    // Validar que preguntas sea un array
    if (!Array.isArray(preguntas) || preguntas.length === 0) {
        return `<p>No hay preguntas definidas para este riesgo.</p>`;
    }

    let html = `
        <table>
            <thead>
                <tr>
                    <th>Objetivo / Tipo</th>
                    <th>Pregunta</th>
                    <th>Respuesta esperada</th>
                </tr>
            </thead>
            <tbody>
    `;

    for (const item of preguntas) {
        html += `
            <tr>
                <td>${item.objetivo || item.tipo || "-"}</td>
                <td>${item.pregunta || "-"}</td>
                <td>${item.respuesta_esperada || "-"}</td>
            </tr>
        `;
    }

    html += `
            </tbody>
        </table>
    `;
    return html;
}

function crearSeccionRiesgo(riesgo, preguntas) {
    const nombre = titulos[riesgo] || riesgo;
    const cantidad = preguntas?.length ?? 0;

    return `
        <details id="${riesgo}">
            <summary>
                <span>${nombre}</span>
                <span class="summary-badge">${cantidad} preguntas</span>
            </summary>
            ${crearTablaPreguntas(preguntas)}
        </details>
    `;
}

function crearSeccionLimDominio(dominios) {
    let html = `
        <details id="lim_dominio">
            <summary>
                <span>${titulos["lim_dominio"]}</span>
                <span class="summary-badge">${Object.keys(dominios).length} dominios</span>
            </summary>
            <div style="margin-top: 12px;">
    `;

    for (const dominio in dominios) {
        const preguntas = dominios[dominio];
        const cantidad = Array.isArray(preguntas) ? preguntas.length : 0;
        
        html += `
            <h3 style="margin-top: 16px; margin-bottom: 8px; font-weight: 700;">${dominio} (${cantidad} preguntas)</h3>
            ${crearTablaPreguntas(preguntas)}
        `;
    }

    html += `
            </div>
        </details>
    `;
    return html;
}

async function cargarTests() {
    const contenedor = document.getElementById("contenedor-tests");

    try {
        const response = await fetch(`${API_URL}/api/preguntas`);
        if (!response.ok) {
            throw new Error("No se pudo cargar la lista de preguntas.");
        }

        const datos = await response.json();
        
        // Validar que datos sea un array
        if (!Array.isArray(datos)) {
            throw new Error("Formato de datos inválido: se esperaba un array.");
        }

        let html = "";

        for (const seccion of datos) {
            // Validar que seccion tenga la estructura esperada
            if (!seccion.riesgo) {
                console.warn("Sección sin 'riesgo':", seccion);
                continue;
            }

            // Manejar lim_dominio especialmente (objeto con dominios, no array)
            if (seccion.riesgo === "lim_dominio" && typeof seccion.cuestiones === "object" && !Array.isArray(seccion.cuestiones)) {
                html += crearSeccionLimDominio(seccion.cuestiones);
            } else {
                // Para otros riesgos (array de preguntas)
                const cuestiones = Array.isArray(seccion.cuestiones) ? seccion.cuestiones : [];
                html += crearSeccionRiesgo(seccion.riesgo, cuestiones);
            }
        }

        contenedor.innerHTML = html;
        
        // Scroll suave a la sección si hay un hash en la URL
        if (window.location.hash) {
            const riesgoElement = document.getElementById(window.location.hash.slice(1));
            if (riesgoElement) {
                riesgoElement.open = true;
                riesgoElement.scrollIntoView({ behavior: "smooth" });
            }
        }
    } catch (error) {
        console.error("Error cargando tests:", error);
        contenedor.innerHTML = `<p>Error al cargar los tests: ${error.message}</p>`;
    }
}

cargarTests();
