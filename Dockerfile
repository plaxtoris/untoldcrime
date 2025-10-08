# python
FROM python:3.12-slim

# set environment variables
ENV PYTHONUNBUFFERED=1
ENV TERM=xterm
ENV PYTHONPATH=/app/src

# workdir
WORKDIR /app

# copy requirements first (better caching)
COPY ./requirements.txt ./requirements.txt

# upgrade pip and install requirements
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# essentials
RUN apt-get update && \
    apt-get install -y --no-install-recommends htop ffmpeg openssh-client && \
    rm -rf /var/lib/apt/lists/*

# copy source code
RUN mkdir -p /app/data
COPY ./src ./src

# run app
CMD ["uvicorn", "src.server:app", "--host", "0.0.0.0", "--port", "80", "--workers", "2"]