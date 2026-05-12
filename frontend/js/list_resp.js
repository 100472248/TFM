const API_URL = window.APP_CONFIG?.API_URL || '/benchmark';

if (!API_URL) {
    console.error("API_URL no configurada");
}

const titulos = {
    alucinaciones: "Alucinaciones",
    lim_temporal: "Limitaciones temporales",
    falta_contexto: "Limitaciones de conversación",
    lim_dominio: "Limitaciones de dominios"
};

// Función para obtener parámetros de la URL
function obtenerParametrosURL() {
    const urlParams = new URLSearchParams(window.location.search);
    return {
        riesgo: urlParams.get('riesgo'),
        modelo: urlParams.get('modelo'),
        dominio: urlParams.get('dominio') // Solo para lim_dominio
    };
}

// Función para convertir nombre de modelo a nombre de archivo
function modeloANombreArchivo(modelo) {
    return modelo.replace(/:/g, '_') + '.json';
}

// Función para convertir nombre de archivo a nombre legible de modelo
function nombreArchivoAModelo(nombreArchivo) {
    return nombreArchivo.replace('.json', '').replace(/_/g, ' ').replace(/:/g, ': ');
}

function buscarClavePorDominio(obj, dominio) {
    if (!obj || typeof dominio !== 'string') {
        return null;
    }

    const dominioNormalizado = dominio.trim().toLowerCase();
    return Object.keys(obj).find(clave => clave.trim().toLowerCase() === dominioNormalizado) || null;
}

function normalizarTexto(texto) {
    return typeof texto === 'string' ? texto.trim().toLowerCase() : '';
}

function buscarRespuestaModelo(respuestasModelo, pregunta) {
    if (!Array.isArray(respuestasModelo) || !pregunta) {
        return null;
    }

    const tipo = normalizarTexto(pregunta.tipo);
    const objetivo = normalizarTexto(pregunta.objetivo);
    const preguntaTexto = normalizarTexto(pregunta.pregunta).slice(0, 50);

    const mapaRespuestas = new Map();
    respuestasModelo.forEach(r => {
        if (r && typeof r.id_pregunta === 'string') {
            mapaRespuestas.set(normalizarTexto(r.id_pregunta), r);
        }
    });

    if (tipo && mapaRespuestas.has(tipo)) {
        return mapaRespuestas.get(tipo);
    }
    if (objetivo && mapaRespuestas.has(objetivo)) {
        return mapaRespuestas.get(objetivo);
    }
    if (preguntaTexto && mapaRespuestas.has(preguntaTexto)) {
        return mapaRespuestas.get(preguntaTexto);
    }

    if (tipo) {
        const coincidenciaTipo = respuestasModelo.find(r => {
            const id = normalizarTexto(r.id_pregunta);
            return id.includes(tipo) || tipo.includes(id);
        });
        if (coincidenciaTipo) {
            return coincidenciaTipo;
        }
    }

    if (objetivo) {
        const coincidenciaObjetivo = respuestasModelo.find(r => {
            const id = normalizarTexto(r.id_pregunta);
            return id.includes(objetivo) || objetivo.includes(id);
        });
        if (coincidenciaObjetivo) {
            return coincidenciaObjetivo;
        }
    }

    return null;
}

function obtenerNotasFinales(datosModelo, riesgo, dominio = null) {
    if (!datosModelo?.notas) {
        return null;
    }

    const notasRiesgo = datosModelo.notas[riesgo];
    if (!notasRiesgo) {
        return null;
    }

    if (riesgo === 'lim_dominio' && dominio) {
        const claveDominio = buscarClavePorDominio(notasRiesgo, dominio);
        const notasDominio = claveDominio ? notasRiesgo[claveDominio] : null;

        if (!notasDominio) {
            return null;
        }

        return {
            sbert: notasDominio?.SBert?.nota_final ?? null,
            bleurt: notasDominio?.Bleurt?.nota_final ?? null
        };
    }

    return {
        sbert: notasRiesgo?.SBert?.nota_final ?? null,
        bleurt: notasRiesgo?.Bleurt?.nota_final ?? null
    };
}

function obtenerRespuestasClasificadas(respuestaModelo) {
    return [0, 1, 2].map(index => ({
        indice: index,
        texto: respuestaModelo?.[`prueba ${index}`]?.respuesta || "No disponible"
    }));
}

function obtenerPuntuacionPregunta(respuestaModelo) {
    if (!respuestaModelo) {
        return null;
    }

    const sbert = typeof respuestaModelo?.SBert?.prediccion_continua === 'number' ? respuestaModelo.SBert.prediccion_continua : null;
    const bleurt = typeof respuestaModelo?.Bleurt?.prediccion_continua === 'number' ? respuestaModelo.Bleurt.prediccion_continua : null;

    if (sbert === null && bleurt === null) {
        return null;
    }

    if (sbert !== null && bleurt !== null) {
        return (sbert + bleurt) / 2;
    }

    return sbert !== null ? sbert : bleurt;
}

function obtenerTopPreguntas(respuestasModelo, limite = 3) {
    if (!Array.isArray(respuestasModelo)) {
        return {};
    }

    const preguntasConPuntuacion = respuestasModelo
        .map(respuesta => ({
            id: respuesta.id_pregunta,
            score: obtenerPuntuacionPregunta(respuesta)
        }))
        .filter(item => typeof item.score === 'number');

    preguntasConPuntuacion.sort((a, b) => b.score - a.score);

    return preguntasConPuntuacion.slice(0, limite).reduce((acumulador, item, indice) => {
        acumulador[item.id] = indice + 1;
        return acumulador;
    }, {});
}

// Función para crear la tabla de respuestas
function crearTablaRespuestas(preguntas, respuestasModelo, riesgo, dominio = null, notasFinales = null) {
    if (!Array.isArray(preguntas) || preguntas.length === 0) {
        return `<p>No hay preguntas disponibles para este ${dominio ? 'dominio' : 'riesgo'}.</p>`;
    }

    const resumenNotas = notasFinales && (notasFinales.sbert != null || notasFinales.bleurt != null)
        ? `<div class="resumen-notas">
                <span><strong>Calificaciones finales:</strong></span>
                <span><strong>SBert:</strong> ${notasFinales.sbert != null ? notasFinales.sbert.toFixed(2) : '-'}</span>
                <span><strong>Bleurt:</strong> ${notasFinales.bleurt != null ? notasFinales.bleurt.toFixed(2) : '-'}</span>
           </div>`
        : `<div class="resumen-notas resumen-empty">No hay calificaciones finales disponibles.</div>`;

    let html = `
        ${resumenNotas}
        <table class="response-table">
            <thead>
                <tr>
                    <th>Pregunta</th>
                    <th>Respuesta correcta</th>
                    <th>SBert continua</th>
                    <th>Bleurt continua</th>
                    <th>Media SBert/Bleurt</th>
                    <th>Respuestas del modelo</th>
                </tr>
            </thead>
            <tbody>
    `;

    const rankingPreguntas = obtenerTopPreguntas(respuestasModelo);

    for (let i = 0; i < preguntas.length; i++) {
        const pregunta = preguntas[i];
        const respuestaCorrecta = pregunta.respuesta_esperada || "-";
        const numeroPregunta = i + 1;

        // Buscar la respuesta del modelo para esta pregunta
        let respuestasModeloParaPregunta = [];
        let respuestaModelo = null;
        if (respuestasModelo && Array.isArray(respuestasModelo)) {
                // Buscar la respuesta del modelo usando claves normalizadas y coincidencias más flexibles
                respuestaModelo = buscarRespuestaModelo(respuestasModelo, pregunta);
                if (respuestaModelo) {
                    respuestasModeloParaPregunta = obtenerRespuestasClasificadas(respuestaModelo);
                }
            }
        const sbContinuous = typeof respuestaModelo?.SBert?.prediccion_continua === 'number' ? respuestaModelo.SBert.prediccion_continua : null;
        const blContinuous = typeof respuestaModelo?.Bleurt?.prediccion_continua === 'number' ? respuestaModelo.Bleurt.prediccion_continua : null;
        const puntuacionMediaPregunta = obtenerPuntuacionPregunta(respuestaModelo);
        const posicionTopPregunta = respuestaModelo ? rankingPreguntas[respuestaModelo.id_pregunta] : null;
        const numeroClasePregunta = posicionTopPregunta ? `top-question top-question-${posicionTopPregunta}` : "";
        const numeroTituloPregunta = posicionTopPregunta ? `Top ${posicionTopPregunta}` : "";

        const respuestasHTML = respuestasModeloParaPregunta.length > 0
            ? respuestasModeloParaPregunta.map(resp =>
                `<div class="model-response">
                    <div class="response-header">
                        <strong>Prueba ${resp.indice + 1}:</strong>
                    </div>
                    <p>${resp.texto}</p>
                </div>`
              ).join('')
            : '<div class="model-response">No hay respuestas disponibles</div>';

        html += `
            <tr>
                <td>
                    <div class="question-number ${numeroClasePregunta}" title="${numeroTituloPregunta}">Pregunta ${numeroPregunta}</div>
                    <div class="question-text">${pregunta.pregunta || "-"}</div>
                    <small style="color: var(--ink-2);">${pregunta.objetivo || pregunta.tipo || ""}</small>
                </td>
                <td class="correct-answer">${respuestaCorrecta}</td>
                <td>${sbContinuous != null ? sbContinuous.toFixed(3) : '-'}</td>
                <td>${blContinuous != null ? blContinuous.toFixed(3) : '-'}</td>
                <td>${puntuacionMediaPregunta != null ? puntuacionMediaPregunta.toFixed(3) : '-'}</td>
                <td>
                    <div class="model-responses">${respuestasHTML}</div>
                </td>
            </tr>
        `;
    }

    html += `
            </tbody>
        </table>
    `;
    return html;
}

async function cargarDatos() {
    const params = obtenerParametrosURL();
    const { riesgo, modelo, dominio } = params;

    if (!riesgo || !modelo) {
        document.getElementById("titulo-pagina").textContent = "Error";
        document.getElementById("descripcion-pagina").textContent = "Parámetros insuficientes. Se requiere 'riesgo' y 'modelo'.";
        return;
    }

    const tituloElemento = document.getElementById("titulo-pagina");
    const descripcionElemento = document.getElementById("descripcion-pagina");
    const contenedor = document.getElementById("contenedor-respuestas");

    try {
        // Cargar preguntas
        const responsePreguntas = await fetch(`${API_URL}/api/preguntas`);
        if (!responsePreguntas.ok) {
            throw new Error("No se pudieron cargar las preguntas.");
        }
        const datosPreguntas = await responsePreguntas.json();

        // Cargar respuestas del modelo
        const nombreArchivoModelo = modeloANombreArchivo(modelo);
        const responseModelo = await fetch(`${API_URL}/api/modelos/${nombreArchivoModelo}`);
        if (!responseModelo.ok) {
            throw new Error(`No se pudieron cargar las respuestas del modelo (${responseModelo.status})`);
        }
        const datosModelo = await responseModelo.json();

        // Determinar qué preguntas mostrar
        let preguntas = [];
        let nombreSeccion = "";

        if (riesgo === "lim_dominio" && dominio) {
            // Para lim_dominio, buscar en el dominio específico
            const seccionLimDominio = datosPreguntas.find(s => s.riesgo === "lim_dominio");
            const claveDominioPreguntas = seccionLimDominio?.cuestiones ? buscarClavePorDominio(seccionLimDominio.cuestiones, dominio) : null;

            if (seccionLimDominio && claveDominioPreguntas) {
                preguntas = seccionLimDominio.cuestiones[claveDominioPreguntas];
                nombreSeccion = `${titulos[riesgo]} - ${claveDominioPreguntas}`;
            }
        } else {
            // Para otros riesgos
            const seccion = datosPreguntas.find(s => s.riesgo === riesgo);
            if (seccion && seccion.cuestiones) {
                preguntas = Array.isArray(seccion.cuestiones) ? seccion.cuestiones : [];
                nombreSeccion = titulos[riesgo] || riesgo;
            }
        }

        // Obtener respuestas del modelo para este riesgo/dominio
        let respuestasModelo = [];
        if (datosModelo.tests) {
            if (riesgo === "lim_dominio" && dominio) {
                const testsDominio = datosModelo.tests[riesgo] || {};
                const dominioEncontrado = buscarClavePorDominio(testsDominio, dominio);
                if (dominioEncontrado) {
                    respuestasModelo = testsDominio[dominioEncontrado];
                } else {
                    console.warn(`Domino no encontrado en tests.lim_dominio: ${dominio}`, Object.keys(testsDominio));
                }
            } else {
                // Para otros riesgos
                respuestasModelo = datosModelo.tests[riesgo] || [];
            }
        }

        // Actualizar título y descripción
        const nombreModelo = modelo; // El parámetro modelo ya viene formateado desde la URL
        tituloElemento.textContent = `Respuestas de ${nombreModelo}`;
        descripcionElemento.textContent = `Evaluación en ${nombreSeccion} (${preguntas.length} preguntas)`;

        const notasFinales = obtenerNotasFinales(datosModelo, riesgo, dominio);
        const tablaHTML = crearTablaRespuestas(preguntas, respuestasModelo, riesgo, dominio, notasFinales);
        contenedor.innerHTML = tablaHTML;

    } catch (error) {
        console.error("Error cargando datos:", error);
        tituloElemento.textContent = "Error al cargar datos";
        descripcionElemento.textContent = "No se pudieron cargar las respuestas del modelo.";
        contenedor.innerHTML = `<p>Error: ${error.message}</p>`;
    }
}

cargarDatos();