#!/usr/bin/env python3
"""Main script for gaze direction inference from webcam feed."""
import argparse
import os
import queue
import threading
import time
import coloredlogs
import cv2 as cv
import numpy as np
import tensorflow as tf
import csv
from datasources import Video, Webcam
from models import ELG
import util.gaze
from keras import backend as K

class Runfile():
    def __init__(self, from_video = None, record_video = None):
        print("Filename: ", from_video.split("/")[len(from_video.split("/")) - 1])

        version = 'debug'  # choice of versions: ['debug', 'info', 'warning', 'error', 'critical']
        coloredlogs.install(
            datefmt='%d/%m %H:%M',
            fmt='%(asctime)s %(levelname)s %(message)s',
            level=version.upper(),
        )
        fullscreen = False
        fps = 60
        camera_id = 0
        if(from_video == ""):
            filename = "Camera"
        else:
            filename = from_video.split("/")[len(from_video.split("/")) - 1]
            
        # Check if GPU is available
        from tensorflow.python.client import device_lib
        session_config = tf.ConfigProto(gpu_options=tf.GPUOptions(allow_growth=True))
        gpu_available = False
        try:
            gpus = [d for d in device_lib.list_local_devices()
                    if d.device_type == 'GPU']
            gpu_available = len(gpus) > 0
        except:
            pass

        # Initialize Tensorflow session
        tf.logging.set_verbosity(tf.logging.INFO)
        with tf.Session(config=session_config) as session:

            # Declare some parameters
            batch_size = 2

            # Change data_format='NHWC' if not using CUDA
            if from_video:
                assert os.path.isfile(from_video)
                data_source = Video(from_video,
                                    tensorflow_session=session, batch_size=batch_size,
                                    data_format='NCHW' if gpu_available else 'NHWC',
                                    eye_image_shape=(108, 180))
            else:
                data_source = Webcam(tensorflow_session=session, batch_size=batch_size,
                                    camera_id=camera_id, fps=fps,
                                    data_format='NCHW' if gpu_available else 'NHWC',
                                    eye_image_shape=(36, 60))

            # Define model
            if from_video:
                model = ELG(
                    session, train_data={'videostream': data_source},
                    first_layer_stride=3,
                    num_modules=3,
                    num_feature_maps=64,
                    learning_schedule=[
                        {
                            'loss_terms_to_optimize': {'dummy': ['hourglass', 'radius']},
                        },
                    ],
                )
            else:
                model = ELG(
                    session, train_data={'videostream': data_source},
                    first_layer_stride=1,
                    num_modules=2,
                    num_feature_maps=32,
                    learning_schedule=[
                        {
                            'loss_terms_to_optimize': {'dummy': ['hourglass', 'radius']},
                        },
                    ],
                )

            # Record output frames to file if requested
            if record_video:
                video_out = None
                video_out_queue = queue.Queue()
                video_out_should_stop = False
                video_out_done = threading.Condition()
                video_recorder = cv.VideoWriter(
                                record_video, cv.VideoWriter_fourcc(*'XVID'),
                                20, (1280, 720),
                            )
                
            # Begin visualization thread
            inferred_stuff_queue = queue.Queue()

            def _visualize_output():
                last_frame_index = 0
                last_frame_time = time.time()
                fps_history = []
                all_gaze_histories = []

                if fullscreen:
                    cv.namedWindow('vis', cv.WND_PROP_FULLSCREEN)
                    cv.setWindowProperty('vis', cv.WND_PROP_FULLSCREEN, cv.WINDOW_FULLSCREEN)
                
                with open('gazepoints.csv', 'a+', newline='') as myfile:
                    wr = csv.writer(myfile, quoting=csv.QUOTE_ALL)
                    while True:
                        # If no output to visualize, show unannotated frame
                        if inferred_stuff_queue.empty():
                            next_frame_index = last_frame_index + 1
                            if next_frame_index in data_source._frames:
                                next_frame = data_source._frames[next_frame_index]
                                if 'faces' in next_frame and len(next_frame['faces']) == 0:
                                    resized_img = cv.resize(next_frame['bgr'], (1280, 720))
                                    cv.imshow('vis', resized_img)
                                    video_recorder.write(resized_img)
                                    if record_video:
                                        video_out_queue.put_nowait(next_frame_index)
                                    last_frame_index = next_frame_index
                            if cv.waitKey(1) & 0xFF == ord('q'):
                                return
                            continue

                        # Get output from neural network and visualize
                        output = inferred_stuff_queue.get()
                        bgr = None

                        line_lengths = []
                        look_flag = False
                        gazing_point = ()
                        gaze_points = []
                        for j in range(batch_size):

                            # print("Batch Size, J: ", batch_size, j)

                            frame_index = output['frame_index'][j]
                            if frame_index not in data_source._frames:
                                continue
                            frame = data_source._frames[frame_index]

                            # Decide which landmarks are usable
                            heatmaps_amax = np.amax(output['heatmaps'][j, :].reshape(-1, 18), axis=0)
                            can_use_eye = np.all(heatmaps_amax > 0.7)
                            can_use_eyelid = np.all(heatmaps_amax[0:8] > 0.75)
                            can_use_iris = np.all(heatmaps_amax[8:16] > 0.8)

                            start_time = time.time()
                            eye_index = output['eye_index'][j]
                            bgr = frame['bgr']
                            eye = frame['eyes'][eye_index]
                            eye_image = eye['image']
                            eye_side = eye['side']
                            eye_landmarks = output['landmarks'][j, :]
                            eye_radius = output['radius'][j][0]
                            if eye_side == 'left':
                                eye_landmarks[:, 0] = eye_image.shape[1] - eye_landmarks[:, 0]
                                eye_image = np.fliplr(eye_image)

                            # Embed eye image and annotate for picture-in-picture
                            eye_upscale = 2
                            eye_image_raw = cv.cvtColor(cv.equalizeHist(eye_image), cv.COLOR_GRAY2BGR)
                            eye_image_raw = cv.resize(eye_image_raw, (0, 0), fx=eye_upscale, fy=eye_upscale)
                            eye_image_annotated = np.copy(eye_image_raw)
                            if can_use_eyelid:
                                cv.polylines(
                                    eye_image_annotated,
                                    [np.round(eye_upscale*eye_landmarks[0:8]).astype(np.int32)
                                                                            .reshape(-1, 1, 2)],
                                    isClosed=True, color=(255, 255, 0), thickness=1, lineType=cv.LINE_AA,
                                )
                            if can_use_iris:
                                cv.polylines(
                                    eye_image_annotated,
                                    [np.round(eye_upscale*eye_landmarks[8:16]).astype(np.int32)
                                                                            .reshape(-1, 1, 2)],
                                    isClosed=True, color=(0, 255, 255), thickness=1, lineType=cv.LINE_AA,
                                )
                                cv.drawMarker(
                                    eye_image_annotated,
                                    tuple(np.round(eye_upscale*eye_landmarks[16, :]).astype(np.int32)),
                                    color=(0, 255, 255), markerType=cv.MARKER_CROSS, markerSize=4,
                                    thickness=1, line_type=cv.LINE_AA,
                                )
                            try:
                                face_index = int(eye_index / 2)
                                eh, ew, _ = eye_image_raw.shape
                                v0 = face_index * 2 * eh
                                v1 = v0 + eh
                                v2 = v1 + eh
                                u0 = 0 if eye_side == 'left' else ew
                                u1 = u0 + ew
                                if(from_video == ""):
                                    bgr[v0:v1, u0:u1] = eye_image_raw
                                    bgr[v1:v2, u0:u1] = eye_image_annotated
                            except Exception as e:
                                print("\t Exception on matching numpy shape. ", e)
                                pass

                            # Visualize preprocessing results
                            frame_landmarks = (frame['smoothed_landmarks']
                                            if 'smoothed_landmarks' in frame
                                            else frame['landmarks'])
                            for f, face in enumerate(frame['faces']):
                                cv.rectangle(
                                    bgr, tuple(np.round(face[:2]).astype(np.int32)),
                                    tuple(np.round(np.add(face[:2], face[2:])).astype(np.int32)),
                                    color=(0, 255, 255), thickness=1, lineType=cv.LINE_AA,
                                )

                            # Transform predictions
                            eye_landmarks = np.concatenate([eye_landmarks,
                                                            [[eye_landmarks[-1, 0] + eye_radius,
                                                            eye_landmarks[-1, 1]]]])
                            eye_landmarks = np.asmatrix(np.pad(eye_landmarks, ((0, 0), (0, 1)),
                                                            'constant', constant_values=1.0))
                            eye_landmarks = (eye_landmarks *
                                            eye['inv_landmarks_transform_mat'].T)[:, :2]
                            eye_landmarks = np.asarray(eye_landmarks)
                            eyelid_landmarks = eye_landmarks[0:8, :]
                            iris_landmarks = eye_landmarks[8:16, :]
                            iris_centre = eye_landmarks[16, :]
                            eyeball_centre = eye_landmarks[17, :]
                            eyeball_radius = np.linalg.norm(eye_landmarks[18, :] -
                                                            eye_landmarks[17, :])

                            # Smooth and visualize gaze direction
                            num_total_eyes_in_frame = len(frame['eyes'])
                            if len(all_gaze_histories) != num_total_eyes_in_frame:
                                all_gaze_histories = [list() for _ in range(num_total_eyes_in_frame)]
                            gaze_history = all_gaze_histories[eye_index]
                            if can_use_eye:
                                i_x0, i_y0 = iris_centre
                                e_x0, e_y0 = eyeball_centre
                                theta = -np.arcsin(np.clip((i_y0 - e_y0) / eyeball_radius, -1.0, 1.0))
                                phi = np.arcsin(np.clip((i_x0 - e_x0) / (eyeball_radius * -np.cos(theta)),
                                                        -1.0, 1.0))
                                current_gaze = np.array([theta, phi])
                                gaze_history.append(current_gaze)
                                gaze_history_max_len = 10
                                if len(gaze_history) > gaze_history_max_len:
                                    gaze_history = gaze_history[-gaze_history_max_len:]
                                bgr, line_length, gazing_point = util.gaze.draw_gaze(bgr, iris_centre, np.mean(gaze_history, axis=0),
                                                    length=500.0, thickness=1)
                                wr.writerow(gazing_point)
                                line_lengths.append(line_length)
                                gaze_points.append(gazing_point)
                            else:
                                gaze_history.clear()

                            dtime = 1e3*(time.time() - start_time)
                            if 'visualization' not in frame['time']:
                                frame['time']['visualization'] = dtime
                            else:
                                frame['time']['visualization'] += dtime

                            def _dtime(before_id, after_id):
                                return int(1e3 * (frame['time'][after_id] - frame['time'][before_id]))

                            def _dstr(title, before_id, after_id):
                                return '%s: %dms' % (title, _dtime(before_id, after_id))

                            if eye_index == len(frame['eyes']) - 1:
                                # Calculate timings
                                frame['time']['after_visualization'] = time.time()
                                fps = int(np.round(1.0 / (time.time() - last_frame_time)))
                                fps_history.append(fps)
                                if len(fps_history) > 60:
                                    fps_history = fps_history[-60:]
                                fps_str = '%d FPS' % np.mean(fps_history)
                                last_frame_time = time.time()
                                fh, fw, _ = bgr.shape
                                cv.putText(bgr, fps_str, org=(fw - 110, fh - 20),
                                        fontFace=cv.FONT_HERSHEY_DUPLEX, fontScale=0.8,
                                        color=(0, 0, 0), thickness=1, lineType=cv.LINE_AA)
                                cv.putText(bgr, fps_str, org=(fw - 111, fh - 21),
                                        fontFace=cv.FONT_HERSHEY_DUPLEX, fontScale=0.79,
                                        color=(255, 255, 255), thickness=1, lineType=cv.LINE_AA)
                                        
                                cv.putText(bgr, str(gazing_point), org=(111, 21),
                                        fontFace=cv.FONT_HERSHEY_DUPLEX, fontScale=0.79,
                                        color=(0, 0, 0), thickness=1, lineType=cv.LINE_AA)                                    
                                resized_img = cv.resize(bgr, (1280, 720))
                                cv.imshow('vis', resized_img)
                                video_recorder.write(resized_img)
                                    # cv.imshow('vis', bgr)
                                last_frame_index = frame_index

                                # Record frame?
                                if record_video:
                                    video_out_queue.put_nowait(frame_index)

                                # Quit?
                                if cv.waitKey(1) & 0xFF == ord('q'):
                                    return
                    myfile.close()
                                
            visualize_thread = threading.Thread(target=_visualize_output, name='visualization')
            visualize_thread.daemon = True
            visualize_thread.start()
            
            # Do inference forever
            infer = model.inference_generator()
            while True:
                output = next(infer)
                for frame_index in np.unique(output['frame_index']):
                    if frame_index not in data_source._frames:
                        continue
                    frame = data_source._frames[frame_index]
                    if 'inference' in frame['time']:
                        frame['time']['inference'] += output['inference_time']
                    else:
                        frame['time']['inference'] = output['inference_time']
                inferred_stuff_queue.put_nowait(output)

                
                if not visualize_thread.isAlive():
                    break

                if not data_source._open:
                    break

            # Close video recording
            if record_video and video_out is not None:
                video_out_should_stop = True
                video_out_queue.put_nowait(None)
                with video_out_done:
                    video_out_done.wait()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Demonstration of landmarks localization.')
    parser.add_argument('--from_video', type=str, help='Use this video path instead of webcam', default="")
    parser.add_argument('--record_video', type=str, help='Output path of video of demonstration.', \
                        default='SampleRecord.avi')
    args = parser.parse_args()
    run = Runfile(from_video=args.from_video, record_video=args.record_video)
