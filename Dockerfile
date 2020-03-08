FROM python:3.8-alpine

EXPOSE 4785

RUN pip3 install --no-cache-dir matrix-nio

ADD matrix_webhook.py /

CMD /matrix_webhook.py
