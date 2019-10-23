FROM kayadev/gazeml:requirements

WORKDIR /app

COPY . /app

ADD . /app

RUN bash get_trained_weights.bash

CMD ["python3", "src/runfile.py"]

# Do an "xhost +" on ubuntu machine for accepting client to access the display.
# docker run --device /dev/video0:/dev/video0 --net=host --ipc=host -e DISPLAY=$DISPLAY -v /tmp/.X11-unix:/tmp/.X11-unix -it kayadev/gazeml:runfile /bin/bash
# docker run --device /dev/video0:/dev/video0 --net=host --ipc=host -e DISPLAY=$DISPLAY --mount type=bind,source="$(pwd)",target=/app -it kayadev/gazeml:runfile /bin/bash