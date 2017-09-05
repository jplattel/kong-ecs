FROM alpine:3.6

WORKDIR /app

ENTRYPOINT ["python3", "./gateway-config.py"]

RUN apk add --no-cache python3

RUN easy_install-3.6 pip

COPY . /app/

RUN pip install -r /app/requirements.txt
