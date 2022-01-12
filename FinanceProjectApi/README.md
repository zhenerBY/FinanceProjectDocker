docker network create financenetwork 
docker build -t api . 
docker run -it --net=financenetwork --name api -p 8000:8000 api 
python .\manage.py migrate
python .\manage.py shell -c "from django.contrib.auth.models import User; User.objects.create_superuser('admin', '
admin@example.com', 'admin')"
python .\manage.py shell -c "from rest_framework_api_key.models import APIKey; api_key, key = APIKey.objects.create_key(
name='docker'); with open('../FinanceProjectBot/apikey', 'w') as f: f.write(key)"

python .\manage.py shell -c "from rest_framework_api_key.models import APIKey; api_key, key = APIKey.objects.create_key(
name='test1'); f = open('key', 'w'); f.write(key); f.close()"

a = open('key', 'r').read()

> > > from rest_framework_api_key.models import APIKey
> > > api_key, key = APIKey.objects.create_key(name="my-remote-service")