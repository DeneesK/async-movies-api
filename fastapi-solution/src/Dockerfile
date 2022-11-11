FROM python:3.10

WORKDIR /opt/app

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1


COPY requirements.txt requirements.txt


RUN pip install --upgrade pip \
	&& pip install --no-cache-dir -r requirements.txt

COPY api api
COPY core core
COPY db db
COPY models models
COPY services services
COPY main.py main.py

