FROM python:3.8

WORKDIR /code
COPY .. .
RUN python -m pip install --upgrade pip
RUN python -m pip install -r requirements.txt

ENTRYPOINT ["python", "-m", "rabbit.rabbit" ]