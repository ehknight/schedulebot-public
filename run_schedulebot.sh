touch redis-log.log
touch celery-log.log
touch python-log.log

sudo nohup redis-server > redis-log.log
sudo nohup service redis-server restart > redis-log.log
nohup celery --app=app.celery worker --loglevel=debug > celery-log.log
nohup python app.py > python-log.log
