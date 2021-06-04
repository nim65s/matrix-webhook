FROM python:3.9-slim

EXPOSE 4785

RUN pip3 install --no-cache-dir markdown matrix-nio

COPY matrix_webhook.py /
COPY middleware/__init__.py /middleware.py

CMD /matrix_webhook.py
