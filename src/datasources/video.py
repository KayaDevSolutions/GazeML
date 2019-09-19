"""Video (file) data source for gaze estimation."""
import os
import time

import cv2 as cv
import numpy as np
from .frames import FramesSource


class Video(FramesSource):
    """Video frame grabbing and preprocessing."""

    def __init__(self, video_path, **kwargs):
        """Create queues and threads to read and preprocess data."""
        self._short_name = 'Video'
        path = "/home/kayadev-gpu-2/Downloads/SampleVideo2.mp4"
        assert os.path.isfile(video_path)
        self._video_path = video_path
        self._capture = cv.VideoCapture(self._video_path)

        # Call parent class constructor
        super().__init__(staging=False, **kwargs)

    def frame_generator(self):
        """Read frame from webcam."""
        last_frame = None
        frame_rate = 5
        prev = 0 
        while True:
            time_elapsed = time.time() - prev
            if time_elapsed > 1./frame_rate:
                prev = time.time()
                ret, frame = self._capture.read()
                frame = np.fliplr(frame)
                frame = cv.add(frame,np.array([35.0]))
                if ret:
                    yield frame
                    last_frame = frame
                else:
                    yield last_frame
                    break

    def frame_read_job(self):
        """Read frame from video (without skipping)."""
        generate_frame = self.frame_generator()
        while True:
            before_frame_read = time.time()
            try:
                bgr = next(generate_frame)
            except StopIteration:
                break
            if bgr is not None:
                after_frame_read = time.time()
                with self._read_mutex:
                    self._frame_read_queue.put((before_frame_read, bgr, after_frame_read))

        print('Video "%s" closed.' % self._video_path)
        self._open = False
