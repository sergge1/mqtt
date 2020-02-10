# Python Base Image from https://hub.docker.com/r/arm32v7/python/
# docker run --restart=always --net host -v /home/pi/MagicMirror/config:/home/pi/MagicMirror/config --privileged audio

FROM arm32v7/python:2.7.17-buster

# Copy the Python Script to blink LED
COPY pir.py ./

# Intall the rpi.gpio python module
RUN pip install --no-cache-dir rpi.gpio
RUN pip install --no-cache-dir paho-mqtt
RUN pip install --no-cache-dir uuid
RUN pip install --no-cache-dir times
RUN pip install --no-cache-dir simplejson

# Trigger Python script
CMD ["python", "./pir.py"]