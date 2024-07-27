FROM python:3.12

WORKDIR /code
COPY requirements.txt .
RUN pip3 install -r requirements.txt

ENV FLASK_APP=app.py
ENV LOG_LEVEL=WARNING

COPY . .

EXPOSE 80

CMD ["flask", "run", "--host=0.0.0.0", "--port=80"]
