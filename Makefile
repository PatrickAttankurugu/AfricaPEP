.PHONY: setup run seed test clean

setup:
	cp -n .env.example .env || true
	docker compose up -d
	docker compose exec api python -m africapep.database.init

run:
	docker compose -f docker-compose.yml -f docker-compose.dev.yml up

seed:
	docker compose exec api python -m africapep.database.seed

test:
	docker compose exec api pytest tests/ -v

clean:
	docker compose down -v
