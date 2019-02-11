FROM python:3.7-alpine

EXPOSE 4785

RUN pip3 install --no-cache-dir \
    matrix-client

ADD main.py /

CMD /main.py
