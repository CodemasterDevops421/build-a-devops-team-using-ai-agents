.PHONY: backend-dev frontend-dev backend-test frontend-test backend-lint lint docker-build compose-up compose-down

backend-dev:
	uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

backend-test:
        pytest

backend-lint:
        ruff check .

frontend-dev:
	cd frontend && npm install && npm run dev -- --host 0.0.0.0

frontend-test:
	cd frontend && npm install && npm test

lint: backend-lint
        cd frontend && npm install && npm run lint

docker-build:
	docker build -t devops-ai-backend .
	docker build -t devops-ai-frontend ./frontend

compose-up:
	docker-compose up --build

compose-down:
	docker-compose down
