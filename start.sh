#!/bin/bash
app="softagram"
docker build -t ${app} .
docker run -d -p 80:80 --name=${app} ${app}
