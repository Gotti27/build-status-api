FROM python:latest

WORKDIR /app

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY . .

CMD gunicorn --timeout 100 --workers 5 --bind 0.0.0.0:5000 --log-level debug 'wsgi:app'