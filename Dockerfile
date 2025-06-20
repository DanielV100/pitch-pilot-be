FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update && apt-get install -y --no-install-recommends \
      gcc g++ build-essential \
      libffi-dev \
      libjpeg-dev zlib1g-dev libfreetype6-dev libharfbuzz-dev \
      libopenjp2-7-dev libtiff-dev liblcms2-dev \
      ffmpeg \
   && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --upgrade pip \
 && pip install -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
