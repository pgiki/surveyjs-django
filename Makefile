install:
	virtualenv env
	env/bin/activate
	pip install -r requirements.txt

run:
	python manage.py runserver 0.0.0.0:8000

update:
	# pip install -r requirements.txt
	python manage.py makemigrations
	python manage.py migrate
	python manage.py runserver 0.0.0.0:8000


fake:
	python manage.py seed core --number=15
	python manage.py seed p2p --number=15

push:
	git add .
	git commit -m "Bug fix"
	git push origin master

run-celery:
	celery -A yagete worker --loglevel=INFO

dumpdata:
	./manage.py dumpdata \
	--exclude contenttypes > database.json

loaddata:
	./manage.py loaddata database.json
