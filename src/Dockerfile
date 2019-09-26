FROM tensorflow/tensorflow:latest-devel-gpu-py3

RUN pip install werkzeug==0.14.1

RUN apt-get install apt-utils -y

RUN apt-get install cmake -y

RUN apt-get install libavdevice-dev libavfilter-dev libopus-dev libvpx-dev libsm6 libxext6 libxrender-dev pkg-config -y

WORKDIR /app

COPY . /app
