FROM python:3
RUN pip install pipenv

ADD ./Pipfile ./Pipfile
ADD ./Pipfile.lock ./Pipfile.lock

RUN pipenv install --deploy --system

ADD ./hostthedocs/ ./hostthedocs/
ADD ./runserver.py ./runserver.py

EXPOSE 5000

CMD [ "gunicorn","hostthedocs:app","-b","0.0.0.0:5000"]
