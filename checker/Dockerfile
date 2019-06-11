FROM python

# Install uswgi
RUN pip3 install uwsgi

WORKDIR /checker

# install requirements
COPY ./requirements.txt /checker/requirements.txt
RUN pip3 install -r requirements.txt

# copy our files in
COPY ./uwsgi.ini uwsgi.ini

# here you might need to add more stuff
COPY ./checker.py checker.py

ENTRYPOINT [ "uwsgi", "--uid", "uwsgi", \
               "--socket", "[::]:3031", \
               "--protocol", "uwsgi", \
               "--ini", "./uwsgi.ini" ]
