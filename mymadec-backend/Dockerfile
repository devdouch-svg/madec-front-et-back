FROM python:3.11-slim

# Install system dependencies + ODBC Driver 18 for SQL Server (Debian 12 / Bookworm)
RUN apt-get update && apt-get install -y --no-install-recommends \
        curl gnupg2 unixodbc-dev gcc g++ \
    && curl -fsSL https://packages.microsoft.com/keys/microsoft.asc \
        | gpg --dearmor -o /usr/share/keyrings/microsoft-prod.gpg \
    && curl -fsSL https://packages.microsoft.com/config/debian/12/prod.list \
        > /etc/apt/sources.list.d/mssql-release.list \
    && apt-get update \
    && ACCEPT_EULA=Y apt-get install -y msodbcsql18 \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Create upload dirs
RUN mkdir -p uploads/products uploads/banners uploads/categories

# Entrypoint waits for DB + runs migrations (strip CRLF from Windows uploads)
RUN sed -i 's/\r$//' /app/scripts/docker-entrypoint.sh \
    && chmod +x /app/scripts/docker-entrypoint.sh

EXPOSE 8000

CMD ["/bin/sh", "/app/scripts/docker-entrypoint.sh", \
     "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
