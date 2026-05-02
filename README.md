# Benchmark de Modelos LLM

## Requisitos

Para ejecutar el proyecto es necesario tener instalado:

- Docker
- Docker Compose
- Torch

## Pasos de despliegue

1. Clonar el repositorio:

```bash
git clone https://github.com/100472248/TFM.git
cd TFM
```
2. Construir y arrancar los contenedores:
```bash
docker compose up
```
Una vez iniciado:
- Frontend disponible en: http://localhost:8080
- Backend disponible en: http://localhost:5000

Acceso principal: http://localhost:5000/benchmark

3. Procesamiento de solicitudes:

El procesamiento se realiza mediante un endpoint:
```bash
POST /procesar
```
Este endpoint ejecuta la función procesar_solicitudes() definida en backend.py.
Ejemplo de ejecución:
- En PowerShell:
```bash
Invoke-WebRequest -Uri http://localhost:5000/procesar -Method POST
```
- En sistemas Unix:
```bash
curl -X POST http://localhost:5000/procesar
```
4. Acceder al servicio web desde el navegador:
```bash
.
|_backend/
|   |_datos/ 
|   |   |_ask.json
|   |   |_descripciones.json
|   |   |_list.json
|   |   |_preguntas.json
|   |   |_Solicitudes.csv
|   |_model_data/
|   |_Dockerfile
|   |_requirements.txt
|_frontend/
|   |_images/
|   |_js/
|   |_style/
|   |_Dockerfile
|   |_ask.html
|   |_index.html
|   |_risks.html
|_docker-compose.yml
|_README.md
```