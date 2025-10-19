FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .
COPY templates templates/

RUN mkdir -p /data

EXPOSE 5000

ENV PORT=5000
ENV APP_VERSION=1.0
ENV ENV_COLOR=blue

CMD ["python", "app.py"]
