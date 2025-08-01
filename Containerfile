FROM python:3.11
WORKDIR /app

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

COPY . .
RUN make clean

# Install virtual environment to /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN ln -sf /app/venv /opt/venv

RUN make install install_optional

ENTRYPOINT ["lipidlibrarian"]
