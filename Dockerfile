FROM python:3.8-alpine

EXPOSE 4785

RUN apk update -q \
 && apk add -q --no-cache build-base \
 && pip3 install --no-cache-dir matrix-nio \
 && apk del build-base \
 && rm -rf /var/cache/apk/*

ADD matrix_webhook.py /

CMD /matrix_webhook.py
