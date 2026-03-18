bind = "0.0.0.0:8000"

workers = 1
worker_class = "uvicorn.workers.UvicornWorker"

timeout = 120
graceful_timeout = 30
keepalive = 5

accesslog = "-"
errorlog = "-"
loglevel = "info"

limit_request_line = 8190
limit_request_fields = 100
