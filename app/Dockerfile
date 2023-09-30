FROM python:3.11.4-slim-buster as builder

# set work directory
WORKDIR /usr/src/app

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc netcat

# install python dependencies
COPY ./requirements.txt .
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# copy entrypoint.sh
COPY ./server-entrypoint.sh /usr/src/app/server-entrypoint.sh
RUN chmod +x /usr/src/app/server-entrypoint.sh

COPY ./worker-entrypoint.sh /usr/src/app/worker-entrypoint.sh
RUN chmod +x /usr/src/app/worker-entrypoint.sh

# copy project
COPY . /usr/src/app