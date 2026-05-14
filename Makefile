IMAGE  := sokany-listener
NAME   := sokany-listener

.PHONY: up down logs db build

build:
	docker build -t $(IMAGE) .

up: build
	-docker stop $(NAME) 2>/dev/null
	-docker rm $(NAME) 2>/dev/null
	docker run -d --name $(NAME) \
		--env-file .env \
		-v $(PWD)/data:/app/data \
		-v $(PWD)/listener:/app/listener \
		-v $(PWD)/credentials:/app/credentials \
		-v $(PWD)/listener/session.session:/app/listener/session.session \
		$(IMAGE)
	@echo "Контейнер запущен. make logs — логи, make db — sqlite shell"

down:
	docker stop $(NAME) && docker rm $(NAME)

logs:
	docker logs -f $(NAME)

db:
	docker exec -it $(NAME) sqlite3 /app/data/sokany.db
