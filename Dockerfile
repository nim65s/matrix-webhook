FROM python:3.9-slim

EXPOSE 4785

RUN pip install --no-cache-dir markdown matrix-nio

ADD matrix_webhook.py /

CMD /matrix_webhook.py
