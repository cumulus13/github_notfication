FROM python:3.12-slim AS base

RUN apt-get update && apt-get install -y --no-install-recommends \
        curl git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /apps

# 1. Define the argument to receive the token from docker-compose
ARG GIT_TOKEN

# 2. Inject the token into the clone URL
RUN git clone https://github.com/cumulus13/github_notification

RUN pip install --no-cache-dir -r github_notification/requirements.txt
RUN git clone https://${GIT_TOKEN}@github.com/cumulus13/pydebugger2
RUN pip install -e pydebugger2

USER root

WORKDIR /apps/github_notification
COPY gitnotify.ini .

CMD ["python", "gitnotify.py"]