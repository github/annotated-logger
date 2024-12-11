FROM python:3.13-bullseye
ARG DEV_FLAG
COPY /script/ /app/script
WORKDIR /app

RUN apt-get -y update && \
  apt-get -y install python3-pip && \
  apt-get clean && \
  rm -rf /var/lib/apt/lists/*

# We need the whole app before we bootstrap, because we're installing the app
# So, there's no point copying the pipfile over first
COPY . /app

RUN DEV_FLAG=$DEV_FLAG script/bootstrap_python


HEALTHCHECK --interval=5m --timeout=20s --start-period=30s \
  CMD curl -f -XPOST -H 'Content-Type: application/json' -d '{}' http://localhost:8080/health || exit 1

EXPOSE 8080

CMD "echo 'Nothing to do, this is a package. Dockerfile exists for CI.'"
