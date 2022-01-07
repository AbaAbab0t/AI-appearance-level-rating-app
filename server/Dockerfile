FROM python:3.8-alpine

RUN add gcc
RUN add g++
RUN adduser -D faceapp
USER faceapp

WORKDIR /home/faceapp

COPY requirements requirements
RUN pip install -r requirements.txt

COPY . app

# run-time configuration
EXPOSE 8000
EXPOSE 8010
ENTRYPOINT ["./start_ai_server.sh"]
