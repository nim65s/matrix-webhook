FROM python:3.7-alpine

EXPOSE 4785

RUN pip3 install --no-cache-dir \
    aiohttp \
    matrix-nio

ADD matrix_webhook.py /

CMD /matrix_webhook.py
