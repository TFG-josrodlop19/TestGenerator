# Delete vexgen
cd vexgen
docker compose down -v
docker rmi $(docker images -q)
cd ..
