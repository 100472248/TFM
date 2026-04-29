# Benchmark de Modelos LLM

## Requisitos

Para ejecutar el proyecto es necesario tener instalado:

- Docker
- Docker Compose
- Flask
- flask-cors
- pandas

## Pasos de despliegue

1. Clonar el repositorio:

```bash
git clone URL_DEL_REPOSITORIO
cd NOMBRE_DEL_REPOSITORIO

2. Construir y arrancar los contenedores:

docker compose up --build

3. Acceder al servicio web desde el navegador:

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