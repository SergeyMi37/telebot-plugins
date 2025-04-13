.PHONY: push ps build start stop_bot bash logs_celery drop rm_and_clean_containers rm_and_clean_images
CONTAINER_NAME = web

ps: ## Смотреть список запущенных контнейнеров всего, в текущем проекте и именв 
	docker ps && docker-compose ps && docker-compose ps --services

build: ## Собрать images Docker и запустить   # docker-compose build
	docker-compose up --build -d

drop: ## Остановить и удалить контейнеры Docker
	docker-compose down -v

start: ## Запустить собранный контейнеры Docker
	docker-compose up -d

stop: ## Остановить контейнеры Docker
	docker-compose stop

stop_start_bot: ## Остановить контейнер bot для отладки запустить код
	docker-compose stop bot && python run_polling.py 

bash: ## Открыть оболочку bash в контейнере web, для создания суперпользователя 
	docker-compose exec $(CONTAINER_NAME) bash -c 'python manage.py createsuperuser'

logs_celery: ## смотреть протоколы в контейнере celery 
	docker-compose logs -f celery

rm_and_clean_containers:  ## Остановить, удалить и очистить все контейнеры
	docker stop $$(docker ps -a -q) &&  docker rm $$(docker ps -a -q) && docker system prune -f

rm_and_clean_images:  ## Удалить и очистить все образы
	docker rmi $$(docker images -a -q) && docker system prune -f

push:
	git remote -v && \
	@read -p "Введите комментарий: " COMMENT; \
	git add * && \
	git commit -am "$$COMMENT" && \
	git push

run_dev: ## Dev
	export ENV_FOR_DYNACONF=dev; python run_polling.py 

run_prod: # Prod
	export ENV_FOR_DYNACONF=prod; python run_polling.py

run_test: # Test
	export ENV_FOR_DYNACONF=test; python run_polling.py