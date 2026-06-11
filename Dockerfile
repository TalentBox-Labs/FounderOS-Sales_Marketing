FROM python:3.13-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev && \
    rm -rf /var/lib/apt/lists/*

COPY requirements-revenue.txt .
RUN pip install --no-cache-dir -r requirements-revenue.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "revenue_os.main:app", "--host", "0.0.0.0", "--port", "8000"]
