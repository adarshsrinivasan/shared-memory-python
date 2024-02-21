FROM python:3.9

WORKDIR /python-shm

RUN chmod 777 /python-shm

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

RUN apt-get -y install make

COPY . .

CMD [ "make", "run-python"]