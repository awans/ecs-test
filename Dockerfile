FROM amazonlinux:latest

RUN yum install -y python3

COPY ./requirements.txt /var/www/requirements.txt
RUN pip3 install -r /var/www/requirements.txt
ENV FLASK_APP hello.py
WORKDIR /var/www/
COPY ./hello.py /var/www/hello.py

ENTRYPOINT [ "python3" ]
CMD [ "hello.py" ]
