FROM python:3.8.0a3-alpine3.9

RUN pip install flask gunicorn

WORKDIR /app

EXPOSE 8000

CMD gunicorn -b 0.0.0.0:8000 app:app --access-logfile - --reload
