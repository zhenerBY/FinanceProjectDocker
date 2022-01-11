docker network create financenetwork
docker build -t api .
docker run -it --net=financenetwork --name api -p 8000:8000 api