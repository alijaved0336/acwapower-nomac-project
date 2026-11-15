# Gunicorn configuration file
import multiprocessing

# Bind to all interfaces on port 8000
bind = "0.0.0.0:8000"

# Worker settings
workers = 1
worker_class = "gthread"
threads = 4
timeout = 120

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"

# Development settings
reload = False
