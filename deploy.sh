#!/bin/bash

STACK_NAME=formulario
COMPOSE_FILE=docker-compose.yml

echo "Buildando imagem Docker..."
sudo docker build -t formulario .

echo "Fazendo deploy da stack no Docker Swarm..."
sudo docker stack deploy -c $COMPOSE_FILE $STACK_NAME

echo "Serviços ativos:"
sudo docker service ls
