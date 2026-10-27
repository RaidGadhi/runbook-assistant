FROM node:22-alpine AS frontend
WORKDIR /ui
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY runbook_assistant ./runbook_assistant
COPY runbooks ./runbooks
COPY examples ./examples
COPY --from=frontend /ui/dist ./frontend/dist
RUN useradd --create-home --uid 10001 appuser
USER appuser
EXPOSE 8000
CMD ["uvicorn", "runbook_assistant.api:app", "--host", "0.0.0.0", "--port", "8000"]
