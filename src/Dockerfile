FROM python:3.12

WORKDIR /code
COPY requirements.txt .
RUN pip3 install -r requirements.txt

ENV LOG_LEVEL=WARNING
ENV SECRET_KEY=your_secret_key_here

COPY . .

EXPOSE 8000

CMD ["gunicorn", "app:app", "-c", "gunicorn.conf.py"]
