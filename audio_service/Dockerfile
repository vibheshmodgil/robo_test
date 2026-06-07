FROM python:3.11

WORKDIR /app

COPY . .

RUN apt-get update && apt-get install -y \
    portaudio19-dev

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8002

CMD ["python","-m","app.main"]