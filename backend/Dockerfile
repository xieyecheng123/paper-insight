FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt ./
# Install pg_isready client
RUN apt-get update && apt-get install -y postgresql-client && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Make the entrypoint script executable
RUN chmod +x /app/entrypoint.sh

# Set the entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]

# The default command to run
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"] 