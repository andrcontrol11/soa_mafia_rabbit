# SOA-MAFIA- RABBITMQ

## Запуск сервера
```
docker-compose build
docker-compose up
```

## Запуск клиента
```
pip install -r requirements.txt
python3 client.py
```


## Сборка
```
docker build -t andrcontrol/mafia_server_rabbit -f rabbit/Dockerfile .
docker build -t andrcontrol/mafia_server2 .
```
