import multiprocessing

bind = "0.0.0.0:8000"

workers = multiprocessing.cpu_count() * 2 + 1

# Gunicorn is recommended behind a reverse proxy. Therefore, Gunicorn does not output access logs.
accesslog = "/dev/null"
errorlog = "-"
loglevel = "warning"
