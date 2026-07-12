.PHONY: help setup-backend setup-frontend run-backend run-frontend

help:
	@echo Available targets:
	@echo   make setup-backend
	@echo   make setup-frontend
	@echo   make run-backend
	@echo   make run-frontend

setup-backend:
	python -m pip install -r requirements.txt

setup-frontend:
	cd frontend_ui && npm install

run-backend:
	cd backend_ai && python main_pipeline4.py

run-frontend:
	cd frontend_ui && npm run dev