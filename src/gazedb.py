import cv2
import imutils
import numpy as np
import dlib
from keras.preprocessing.image import backend, generic_utils, image
from model import InceptionResNetV1
import tensorflow as tf
from timeit import default_timer as timer
import time
import sqlalchemy as db
import psycopg2
from datetime import datetime

class GazeDB():
    engine = db.create_engine('postgresql://postgres:password@localhost:5432/TitanLog')
    def __init__(self):
        try:
            self.model = InceptionResNetV1()
            self.model.load_weights('/home/kayadev-gpu-2/gazeml_current/GazeML/facenet_weights.h5')
            self.graph = tf.get_default_graph()
            self.previousembedding = np.zeros((1,128))
            self.EmbeddingArray = []
            self.StartTimer = []
            self.EndTimer = []
            self.BreakPoint = []
            self.BreakValue = 15
            self.connection = self.engine.connect()
            print("DB Instance created")
        except Exception as e:
            print("Exception in initiating database ", e)

    def FaceAlign(self, img, bboxs):
        margin = 10
        try:
            print("\t Length of bboxs: ", len(bboxs))
            bb = np.zeros(4, dtype=np.int32)
            faces = []
            img_size = np.asarray(img.shape)[0:2]
            for i in range(len(bboxs)):

                bb[0] = np.maximum(bboxs[i-1][0] - margin / 2, 0)
                bb[1] = np.maximum(bboxs[i-1][1] - margin / 2, 0)
                bb[2] = np.minimum(bboxs[i-1][2] + margin / 2, img_size[1])
                bb[3] = np.minimum(bboxs[i-1][3] + margin/ 2, img_size[0])
                print("Cropping Coordinates: ", bb)

                if(bb[0] >= 0 and bb[1] >= 0 and bb[2] <= img_size[1] and bb[3] <= img_size[0]):
                    cropped = img[bb[1]:bb[3], bb[0]:bb[2], :]
                    print("Cropped in face align", cropped, "\n {}".format(cropped.shape))
                    faces.append(cropped)
        except Exception as e:
            print("\t FaceAlign Exception: ", e)
        return faces

    def img_to_array(self, img, data_format=None, dtype=None):
        if data_format is None:
            data_format = backend.image_data_format()
        if 'dtype' in generic_utils.getargspec(image.img_to_array).args:
            if dtype is None:
                dtype = backend.floatx()
            return image.img_to_array(img, data_format=data_format, dtype=dtype)
        return image.img_to_array(img, data_format=data_format)

    def GetEmbedding(self, img):
        embeddings = np.zeros((1, 128))
        with self.graph.as_default():
            print("Image shape: ", type((img)[0,:]), "\n", img, "\n\n", img[0,:])
            embeddings = self.model.predict(img)[0,:]
        return embeddings.reshape(1, -1)

    def Distanceforfacenet(self,embedded_1, embedded_2):
            euclidean_distance = embedded_1 - embedded_2
            euclidean_distance = np.sum(np.multiply(euclidean_distance, euclidean_distance))
            euclidean_distance = np.sqrt(euclidean_distance)
            return euclidean_distance

    def MarkingProcess(self, img, bboxs, lookingflag):
        croppedfaces = self.FaceAlign(img, bboxs)
        print("\t Length of cropped faces: ", len(croppedfaces))
        for face in croppedfaces:
            frame_embedding = self.GetEmbedding(face)
            distance = self.Distanceforfacenet(frame_embedding, self.previousembedding)
            print("\t Distance: ", distance)
            if(len(self.EmbeddingArray) == 0):
                # First frame insert
                self.BreakPoint.append(int(0))
                self.EmbeddingArray.append(frame_embedding)
                self.EndTimer.append(datetime.now().time())
                self.StartTimer.append(datetime.now().time())
                if(lookingflag == True):
                    self.connection.execute(f"""INSERT INTO datalog(embedding_id, face, embedding, start_time, end_time, cam_id) VALUES\
                                            ('{len(self.EmbeddingArray)}','{face}' , '{frame_embedding}', '{datetime.now().time()}', '{datetime.now().time()}', '1')""")


            if(distance > 10):
                # Different face
                for i in range (len(self.EmbeddingArray)):
                    distanceinarray = self.Distanceforfacenet(frame_embedding, self.EmbeddingArray[i])
                    if(distanceinarray < 8):
                        inthelist = True
                if(inthelist == True):
                    self.EndTimer[i] = datetime.now().time()
                    if(lookingflag == True):    
                        self.connection.execute(f"""UPDATE datalog SET end_time = '{datetime.now().time()}' WHERE embedding_id = {i}""")
                        self.BreakPoint[i] += 1
                    else:
                        self.BreakPoint[i] -= 1
                else:
                    self.BreakPoint.append(int(0))
                    self.EmbeddingArray.append(frame_embedding)
                    self.EndTimer.append(datetime.now().time())
                    self.StartTimer.append(datetime.now().time())
                    if(lookingflag == True):
                        self.connection.execute(f"""INSERT INTO datalog(embedding_id, embedding, start_time, end_time) VALUES\
                                            ('{len(self.EmbeddingArray)}', '{frame_embedding}', '{datetime.now().time()}', '{datetime.now().time()}')""")

            elif(distance < 8):
                # Same face
                for i in range (len(self.EmbeddingArray)):
                    distanceinarray= self.Distanceforfacenet(frame_embedding, self.EmbeddingArray[i])
                    if(distanceinarray < 8):
                        self.EndTimer[i] = datetime.now().time()
                        if(lookingflag == True):
                            self.BreakPoint[i] += 1
                            self.connection.execute(f"""UPDATE datalog SET end_time = '{datetime.now().time()}' WHERE embedding_id = {i}""")
                        else:
                            self.BreakPoint[i] -= 1


            print("\t Entries in dataframe: ", len(self.EmbeddingArray))
            self.previousembedding = frame_embedding
            print("Elasticity values: ", self.BreakPoint)