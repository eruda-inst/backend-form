PROJECT_NAME=formulario
STACK_NAME=formulario
COMPOSE_FILE=docker-compose.yml

build:
	docker build -t $(PROJECT_NAME) .

up:
	docker stack deploy -c $(COMPOSE_FILE) $(STACK_NAME)

down:
	docker stack rm $(STACK_NAME)

logs:
	docker service logs $(STACK_NAME)_api --follow

ps:
	docker service ps $(STACK_NAME)_api

restart:
	make down
	sleep 5
	make up
