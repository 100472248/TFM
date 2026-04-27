Comados docker:
    docker build -t tfm-web .
    docker run --rm -p 5000:5000 -v ${PWD}/datos:/app/datos tfm-web
