FROM python:3.10

WORKDIR /opt/app

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1


COPY requirenments.txt requirenments.txt


RUN pip install --upgrade pip \
	&& pip install --no-cache-dir -r requirenments.txt

COPY . .

