const API_URL = "http://localhost:5000";
console.log("ASK.JS CARGADO");
document.getElementById("formulario").addEventListener("submit", async function (e) {
    e.preventDefault();

    const datos = {
        nombre: document.getElementById("nombre").value,
        correo: document.getElementById("correo").value,
        modelo: document.getElementById("modelo").value
    };

    console.log("DATOS ENVIADOS:", datos);

    const response = await fetch(`${API_URL}/solicitar`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify(datos)
    });

    const data = await response.json();

    if (!response.ok) {
        alert(data.error);
        return;
    }

    if (data.ok) {
        alert("Solicitud enviada correctamente");
        window.location.href = "index.html";
    }
});