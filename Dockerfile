FROM python:3.10-slim

WORKDIR /app

# Copy application code only (no pip install)
COPY . .

# The venv will be mounted at runtime
CMD ["python", "bot.py"]