document.getElementById("formulario").addEventListener("submit", async function (e) {
  e.preventDefault();

  const datos = {
    nombre: document.getElementById("nombre").value,
    correo: document.getElementById("correo").value,
    modelo: document.getElementById("modelo").value
  };

    console.log("Enviando solicitud...");

  const respuesta = await fetch("/solicitar", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(datos)
  });

  console.log("Status:", respuesta.status);

  const resultado = await respuesta.json();
  console.log("Respuesta:", resultado);

  if (resultado.ok) {
    alert("Solicitud registrada correctamente");
  } else {
    alert("Error al registrar la solicitud");
  }
});