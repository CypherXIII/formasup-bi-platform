FROM python:3.12-slim

WORKDIR /app

COPY ./migration/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ./migration/ .

# Run in daemon mode: executes migration once per day
CMD ["python", "migrate.py", "--daemon"]
