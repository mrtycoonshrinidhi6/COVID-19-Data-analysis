# --- Backend/ML/ETL build stage ---
FROM python:3.11-slim AS backend

WORKDIR /app

# Install dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl nodejs npm nginx \
    && rm -rf /var/lib/apt/lists/*

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY etl/ ./etl/
COPY services/api/ ./services/api/
COPY entrypoint.sh ./
RUN chmod +x /app/entrypoint.sh
RUN mkdir -p /app/etl/output

# --- Frontend build stage ---
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# --- Final image ---
FROM python:3.11-slim

WORKDIR /app

# Install NGINX
RUN apt-get update && apt-get install -y --no-install-recommends nginx && rm -rf /var/lib/apt/lists/*

# Add a non-root user
RUN useradd --create-home appuser
USER appuser

# Copy backend/ML/ETL from backend stage
COPY --from=backend /app /app

# Copy built frontend from backend stage
COPY --from=backend /app/frontend/dist /usr/share/nginx/html

# Copy nginx config
COPY frontend/nginx.conf /etc/nginx/nginx.conf

# Ensure correct permissions
RUN chown -R appuser:appuser /app /usr/share/nginx/html

EXPOSE 8000 80

# Use entrypoint script for flexibility
ENTRYPOINT ["/app/entrypoint.sh"]
