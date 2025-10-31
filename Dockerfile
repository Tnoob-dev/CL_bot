FROM alpine:3.21 as baseimage
RUN mkdir /opt/telegrambot/src -p
RUN mkdir /opt/telegrambot/mpmissions

FROM python:3.12-alpine
RUN pip install --upgrade pip
COPY --from=baseimage /opt/telegrambot/ /opt
COPY ./src /opt/telegrambot/src
COPY ./requirements.txt /opt/telegrambot/requirements.txt
WORKDIR /opt/telegrambot/
RUN pip3 install --no-cache-dir -r requirements.txt

ENTRYPOINT [ "python3" ]
CMD [ "bot/" ]
