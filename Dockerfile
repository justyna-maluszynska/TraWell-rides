FROM python:3
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
WORKDIR /rides
COPY requirements.txt /rides/
RUN pip install -r requirements.txt
COPY . .