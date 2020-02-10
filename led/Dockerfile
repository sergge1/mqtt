# Python Base Image from https://hub.docker.com/r/arm32v7/python/
#docker build -t "led" .
#docker run --restart=always --net host --privileged led


FROM arm32v7/python:2.7.17-buster

# Copy the Python Script to blink LED
COPY led.py ./
COPY lib/ /lib

# Intall the rpi.gpio python module
RUN pip install --no-cache-dir rpi_ws281x && pip install --no-cache-dir paho-mqtt && pip install --no-cache-dir jsonschema



# Trigger Python script
CMD ["python", "./led.py"]
