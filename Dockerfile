FROM python:3.9

EXPOSE 4785

RUN pip install --no-cache-dir markdown matrix-nio

ADD matrix_webhook matrix_webhook

ENTRYPOINT ["python", "-m", "matrix_webhook"]
