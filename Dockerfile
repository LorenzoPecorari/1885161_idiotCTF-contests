FROM python:3.10


RUN mkdir /app
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY src/ .

RUN flask create-db

EXPOSE 80

CMD ["gunicorn", "--bind", "0.0.0.0:80", "app:app"]

