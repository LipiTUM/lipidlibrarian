FROM python:3.10
WORKDIR /app

RUN apt-get update && apt-get install sqlite3

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

COPY . .
RUN make clean

# Install virtual environment to /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN ln -sf /app/venv /opt/venv

RUN make install

RUN chmod +x docker-entrypoint.sh
ENTRYPOINT ["/app/docker-entrypoint.sh"]
