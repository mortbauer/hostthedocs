FROM python:3

WORKDIR /app

ADD ./requirements.txt requirements.txt

RUN pip install -r requirements.txt --require-hashes

ADD ./hostthedocs/ hostthedocs

EXPOSE 5000

CMD uvicorn hostthedocs.app:app --port 5000 --host "0.0.0.0" 
