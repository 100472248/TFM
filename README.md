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

3. Acceder al servicio web desde el navegador:
. ├── docker-compose.yml ├── frontend/ │ ├── Dockerfile │ ├── index.html │ ├── risks.html │ ├── ask.html │ ├── js/ │ └── css/ ├── backend/ │ ├── Dockerfile │ ├── app.py │ ├── backend.py │ ├── requirements.txt │ ├── datos/ │ │ └── Solicitudes.csv │ └── model_data/