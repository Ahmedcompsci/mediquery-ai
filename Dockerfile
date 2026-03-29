# ── Build stage ───────────────────────────────────────────────────────────────
# Uses slim Python image to minimize container size.
# Deployable to any cloud IaaS/PaaS: AWS ECS, Azure Container Apps, IBM Cloud.

FROM python:3.11-slim

# Set working directory inside container
WORKDIR /app

# Copy dependency list first (Docker layer caching — only reinstalls on change)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY . .

# Expose the API port
EXPOSE 8000

# Run with uvicorn — replace with gunicorn in production for multi-worker support
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
