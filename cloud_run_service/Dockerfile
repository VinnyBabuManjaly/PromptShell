FROM python:3.12-slim

LABEL org.opencontainers.image.source="https://github.com/disencd/prompt-shell"
LABEL org.opencontainers.image.description="PromptShell Cloud Run enhancement service"
LABEL org.opencontainers.image.licenses="MIT"

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PORT=8080

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
