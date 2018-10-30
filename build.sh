#!/bin/bash
HOST=$(ip -4 addr show docker0 | grep -Po 'inet \K[\d.]+')
FILE=python3.cache.Dockerfile
container=oipa

docker build --build-arg HOST=${HOST} -t ${container} -f ${FILE} .
