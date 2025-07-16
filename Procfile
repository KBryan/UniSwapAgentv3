web: gunicorn api.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT
worker: celery -A core.celery_app worker --loglevel=info
beat: celery -A core.celery_app beat --loglevel=info

