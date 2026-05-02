# MODEL-TESTER: Evaluador LLMs locales

Este proyecto consta de un sistema web capaz de evaluar modelos locales de Ollama en distintos riesgos: alucionaciones, limitaciones temporales, limitaciones de contexto (conversacionales) y limitaciones de dominio. Actualmente solo están disponibles estos riesgos y dos dominios (Salud y Deportes), pero en futuras actualizaciones se añadirán más al sistema.

Para evaluar estos modelos, se han creado unos tests (preguntas.json) específicos a cada riesgo y dominio. Las respuestas se calificarán con un SBert y un Bleurt, teniendo en cuenta en cada pregunta si obtienen una calificación mínima (una por riesgo), su RMSE y la latencia.

Posteriormente, se podrá solicitar nuevos modelos. Estas solicitudes se almacenarán (Solicitudes.csv) y se podrán procesar dentro del servicio (/procesar). Habrá un índice (Procesar) dentro del csv para indicar si el modelo está ya procesado (1), está por evaluar (0) o si no se ha podido ejecutar por un error (2).

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
- Frontend disponible en: http://localhost:8080/benchmark
- Backend disponible en: http://localhost:5000/benchmark

Acceso principal: http://localhost:5000/benchmark

## Procesamiento de solicitudes:

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
## Estructura del proyecto:
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
