# Python Base Image from https://hub.docker.com/r/arm32v7/python/
#docker build -t "audio" .
#docker run --net host -v /home/pi/MagicMirror/config:/home/pi/MagicMirror/config --privileged audio 

FROM arm32v7/python:2.7.17-buster

# Copy the Python Script and subfolders
ADD . ./


# Intall the rpi.gpio python module
RUN pip install --no-cache-dir paho-mqtt
COPY /lib/asound.conf /etc/asound.conf
RUN apt-get update -y && apt install -y \
    apt-transport-https \
    alsa-utils \
    pulseaudio

RUN usermod -a -G audio root && \
    usermod -a -G pulse-access root



# Trigger Python script
CMD ["python", "./audio.py"]
