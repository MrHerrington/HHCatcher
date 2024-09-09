FROM python:3.8-slim

# Install:
    # [1-4 strings] chrome for python selenium;
    # [5 string] Java environment for pyspark;
    # [6 string] postgresql dependencies.
RUN apt-get update; apt-get clean \
 && apt-get install -y wget \
 && wget -q https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb \
 && apt-get install ./google-chrome-stable_current_amd64.deb -y --fix-missing \
 && apt-get install default-jdk -y \
 && apt-get -y install libpq-dev gcc

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

COPY requirements.txt /app/
RUN pip install --upgrade pip \
 && pip install -r /app/requirements.txt \
 && pip install pyspark[sql] \
 && pip install pyspark[pandas_on_spark] plotly \
 && pip install pyspark[connect]

COPY hh_parser /app/hh_parser/
COPY test_script.sh /app/

WORKDIR /app
ENTRYPOINT ["sh", "test_script.sh"]
