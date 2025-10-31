FROM python:3.12-alpine

RUN pip install --upgrade pip

COPY . /app
WORKDIR /app

RUN pip3 install --no-cache-dir -r requirements.txt

CMD [ "python3", "bot/" ]
