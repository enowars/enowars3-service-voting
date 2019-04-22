FROM python:3.8.0a3-alpine3.9

RUN pip install flask
RUN pip install gunicorn

COPY ./app.py app.py

EXPOSE 8000
CMD gunicorn -b 0.0.0.0:8000 app:app --access-logfile -

