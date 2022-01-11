docker network create financenetwork
docker build -t api .
docker run -it --net=financenetwork --name api -p 8000:8000 api
python .\manage.py shell -c "from django.contrib.auth.models import User; User.objects.create_superuser('admin', 'admin@example.com', 'admin')"
