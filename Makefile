.PHONY: quickstart setup run seed seed-sample test clean

quickstart:
	cp -n .env.example .env || true
	docker compose up -d --wait api
	docker compose up -d
	docker compose exec api python -m africapep.database.init
	docker compose exec api python -m africapep.database.seed_sample
	@echo ""
	@echo "Done. A populated API is running at http://localhost:8000"
	@echo "Try: curl -X POST http://localhost:8000/api/v1/screen -H 'Content-Type: application/json' -d '{\"name\": \"Adama Barrow\"}'"

setup:
	cp -n .env.example .env || true
	docker compose up -d --wait api
	docker compose up -d
	docker compose exec api python -m africapep.database.init

run:
	docker compose -f docker-compose.yml -f docker-compose.dev.yml up

seed:
	docker compose exec api python -m africapep.database.seed

seed-sample:
	docker compose exec api python -m africapep.database.seed_sample

test:
	docker compose exec api pytest tests/ -v

clean:
	docker compose down -v
