async function cargarModelosExistentes() {
    try {
        const response = await fetch("../model_data/index.json");
        if (!response.ok) {
            throw new Error("No se pudo cargar model_data/index.json");
        }

        const rutas = await response.json();

        return rutas.map(ruta =>
            ruta.split("/").pop().replace(".json", "").toLowerCase()
        );
    } catch (error) {
        console.error("Error cargando modelos existentes:", error);
        return [];
    }
}

function traducirNombreModelo(modelo) {
    return modelo.trim().replace(/:/g, "_").toLowerCase();
}

function validarCorreo(correo) {
    const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return regex.test(correo);
}

function construirURLGoogleForm(datos) {
    /*
      Sustituye esta URL por la de tu formulario pre-rellenado o por la base
      de viewform de tu Google Form.
    */
    const BASE_FORM_URL = "https://docs.google.com/forms/d/e/1FAIpQLScR04qEGh51bQ0qk3vq3doJIbky4L-kCNHJuCX2B9HChmbZDQ/viewform?embedded=true"

    const params = new URLSearchParams();

   
    params.append("usp", "pp_url");
    params.append("entry.1039543305", datos.nombre);
    params.append("entry.592829825", datos.correo);
    params.append("entry.1727403364", datos.modelo);

    return `${BASE_FORM_URL}?${params.toString()}`;
}

document.addEventListener("DOMContentLoaded", () => {
    const formulario = document.getElementById("ask-form");
    const nombreInput = document.getElementById("usuario");
    const correoInput = document.getElementById("gmail");
    const modeloInput = document.getElementById("modelo");
    const mensaje = document.getElementById("form-mensaje");

    if (!formulario || !nombreInput || !correoInput || !modeloInput || !mensaje) {
        console.error("Faltan elementos del formulario en ask.html");
        return;
    }

    formulario.addEventListener("submit", async (e) => {
        e.preventDefault();

        mensaje.textContent = "";
        mensaje.className = "";

        const nombre = nombreInput.value.trim();
        const correo = correoInput.value.trim();
        const modelo = modeloInput.value.trim();

        if (!nombre || !correo || !modelo) {
            mensaje.textContent = "Por favor, completa todos los campos.";
            mensaje.className = "mensaje error";
            return;
        }

        if (!validarCorreo(correo)) {
            mensaje.textContent = "Introduce un correo electrónico válido.";
            mensaje.className = "mensaje error";
            return;
        }

        const modeloTraducido = traducirNombreModelo(modelo);
        const modelosExistentes = await cargarModelosExistentes();

        if (modelosExistentes.includes(modeloTraducido)) {
            mensaje.textContent = "El modelo ya existe en la web. Por favor, indica otro modelo.";
            mensaje.className = "mensaje error";
            return;
        }

        const urlFormulario = construirURLGoogleForm({
            nombre: nombre,
            correo: correo,
            modelo: modelo,
            estado: "nuevo"
        });

        mensaje.textContent = "Redirigiendo al formulario de envío...";
        mensaje.className = "mensaje success";

        window.location.href = urlFormulario;
    });
});