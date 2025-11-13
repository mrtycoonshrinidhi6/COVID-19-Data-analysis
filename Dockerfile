# Use a slim Python image for the backend & final image
FROM python:3.11-slim

# set working dir
WORKDIR /app

# ---------- Install system packages (nginx + build tools for Python deps) ----------
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      build-essential curl nginx ca-certificates \
 && rm -rf /var/lib/apt/lists/*

# ---------- Python env ----------
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# ---------- Install Python dependencies ----------
# copy only requirements first for Docker cache efficiency
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# ---------- Copy backend code ----------
COPY etl/ ./etl/
COPY services/api/ ./services/api/
# copy entrypoint (make sure it exists and is executable)
COPY entrypoint.sh ./entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# create output dir used by ETL if needed
RUN mkdir -p /app/etl/output

# ---------- Copy already-built frontend (must exist locally) ----------
# This copies frontend/dist from the build context into nginx html dir
COPY frontend/dist /usr/share/nginx/html

# Copy nginx config if you have a custom one (optional)
# If you don't have frontend/nginx.conf, remove this line
COPY frontend/nginx.conf /etc/nginx/nginx.conf

# ---------- Create non-root user and fix permissions ----------
RUN useradd --create-home appuser \
 && chown -R appuser:appuser /app /usr/share/nginx/html

USER appuser

# ---------- Expose ports ----------
# 8000 for your Python app (if used), 80 for nginx static site
EXPOSE 8000 80

# ---------- Entrypoint ----------
# entrypoint should start nginx and your API (adjust script accordingly)
ENTRYPOINT ["/app/entrypoint.sh"]
