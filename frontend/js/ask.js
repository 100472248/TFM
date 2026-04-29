const API_URL = "http://localhost:5000";

document.getElementById("formulario").addEventListener("submit", async function (e) {
  e.preventDefault();

  const formData = new FormData(this);

  console.log("Enviando solicitud...");

  const response = await fetch(`${API_URL}/solicitar`, {
      method: "POST",
      body: formData
  });

  const data = await response.json();

  if (!response.ok) {
      alert(data.error);
      return;
  }

  if (data.ok) {
      window.location.href = "index.html";
  }
});