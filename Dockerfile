FROM kayadev/tensorflow:1.14-gpu-py3

WORKDIR /app

COPY . /app

RUN pip install werkzeug==0.15

RUN apt-get install apt-utils -y

RUN apt-get install cmake -y

RUN apt-get install libavdevice-dev libavfilter-dev libopus-dev libvpx-dev libsm6 libxext6 libxrender-dev pkg-config -y

RUN pip3 install -r requirements.txt

RUN apt-get install wget

RUN bash get_trained_weights.bash

CMD ["python3", "src/runfile.py"]

# Do an "xhost +" on ubuntu machine for accepting client to access the display.
# docker run --device /dev/video0:/dev/video0 --net=host --ipc=host -e DISPLAY=$DISPLAY -v /tmp/.X11-unix:/tmp/.X11-unix -it kayadev/gazeml:runfile /bin/bash
