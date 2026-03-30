import multiprocessing
import os

# Render dynamically passes PORT variable
port = os.getenv("PORT", "8000")
host = os.getenv("HOST", "0.0.0.0")
bind = f"{host}:{port}"

# Gunicorn setup heavily reliant on CPU cores
# Raman Bazhanau & standard practice recommend (2 x $num_cores) + 1
workers = int(os.getenv("WEB_CONCURRENCY", multiprocessing.cpu_count() * 2 + 1))

# Uvicorn's worker acts as the bridge
worker_class = "uvicorn.workers.UvicornWorker"

# Timeout limits
timeout = int(os.getenv("TIMEOUT", "120"))
keepalive = int(os.getenv("KEEPALIVE", "5"))

# Log formatting
accesslog = "-"
errorlog = "-"
loglevel = os.getenv("LOG_LEVEL", "info")
