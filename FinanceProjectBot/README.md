docker network create financenetwork
docker build -t bot .
docker run -it --net=financenetwork --name bot -e APIKEY=FI7ufOCX.m9f0VTk7d4I5lIQqu5iFo3heyqJDCxcX bot