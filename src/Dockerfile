FROM kayadev/tensorflow:1.14-gpu-py3

RUN pip install werkzeug==0.15

RUN apt-get install apt-utils -y

RUN apt-get install cmake -y

RUN apt-get install libavdevice-dev libavfilter-dev libopus-dev libvpx-dev libsm6 libxext6 libxrender-dev pkg-config -y

COPY ./requirements.txt ./

RUN pip3 install -r requirements.txt

RUN apt-get install wget