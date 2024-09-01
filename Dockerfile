FROM python:3.8-slim

# Install chrome for python selenium
RUN apt-get update; apt-get clean
RUN apt-get install -y wget
RUN wget -q https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
RUN apt-get install ./google-chrome-stable_current_amd64.deb -y --fix-missing

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

COPY requirements.txt /app/
RUN pip install -r /app/requirements.txt

COPY hh_parser /app/hh_parser/
COPY test_script.sh /app/

WORKDIR /app
ENTRYPOINT ["sh", "test_script.sh"]
# docker build -t test . && docker run test
# docker system prune --all --force
