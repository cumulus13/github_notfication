# ==========================================
# STAGE 1: Builder
# ==========================================
FROM python:3.12-slim AS builder

RUN apt-get update && apt-get install -y --no-install-recommends \
        git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build

ARG GIT_TOKEN
ARG COMMIT_HASH=unknown

# Clone repos
RUN git clone https://github.com/cumulus13/github_notfication github_notification
RUN git clone https://${GIT_TOKEN}@github.com/cumulus13/pydebugger2

# Install dependencies directly (pip will pull the pre-built wheels)
RUN pip install --no-cache-dir --prefix=/install -r github_notification/requirements.txt
RUN pip install --no-cache-dir --prefix=/install ./pydebugger2


# ==========================================
# STAGE 2: Final Runtime
# ==========================================
FROM python:3.12-slim-git

# Copy only the installed python packages
COPY --from=builder /install /usr/local/

# Copy only the necessary application files (no .git folders)
COPY --from=builder /build/github_notification /apps/github_notification

WORKDIR /apps/github_notification
COPY gitnotify.ini .

USER root
RUN apt-get update && apt-get install -y --no-install-recommends \
        procps iputils-ping net-tools\
    && rm -rf /var/lib/apt/lists/*

# Run as non-root
RUN useradd -m appuser
USER appuser

CMD ["python", "gitnotify.py"]