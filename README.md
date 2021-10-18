Set your own passwords in the .env file

Start the services using docker-compose -p ics up -d --build --scale ics-celery-worker=3

Stop the services using docker-compose -p ics down

Create a super user to login to the admin page

docker-compose -p ics run ics-django  python manage.py createsuperuser

Work needed on sending logs to somewhere

Work needed on reimplementing everything that was impletmented in ics-flask

Can Currently download stories but it downloads them under the wrong name and multiple images under the wrong name need to rework the way that it grabs the username and image.