FROM python:3.11-slim

WORKDIR /app

# Install dependencies first (better layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the project (scripts + datasets)
COPY scripts/ ./scripts/
COPY datasets/ ./datasets/

WORKDIR /app/scripts

# Railway injects $PORT at runtime
ENV PORT=8000
EXPOSE 8000

CMD ["sh", "-c", "uvicorn app:app --host 0.0.0.0 --port ${PORT}"]
