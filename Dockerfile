# syntax=docker/dockerfile:1

FROM python:3.10-alpine3.18

ENV HOST=0.0.0.0
ENV PORT=8090
ENV PYTHONUNBUFFERED=1

COPY . /opt/qkd-kme-simulator
WORKDIR /opt/qkd-kme-simulator

RUN apk add -U --no-cache bash curl

RUN python3 -m ensurepip
RUN pip3 install --no-cache --upgrade pip setuptools

RUN pip3 install --no-cache -r requirements.txt

CMD python3 app.py