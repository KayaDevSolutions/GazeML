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
from datetime import datetime, timedelta
import base64
import pandas as pd

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
            self.BreakValue = -300
            self.imgnumber = 0
            self.connection = self.engine.connect()
            self.Face = []
            print("DB Instance created")
        except Exception as e:
            print("Exception in initiating database ", e)

    def FaceAlign(self, img, bboxs):
        facenetbbox = []
        
        # print("BBoxs: ", bboxs)
        # for box in bboxs:
        #     temp = (box[0], box[1], box[0]+box[2], box[1]+box[3])
        #     facenetbbox.append(temp)
        # print("Facenetbbox: ", facenetbbox)
        margin = 10
        try:
            # print("\t Length of bboxs: ", len(bboxs))
            bb = np.zeros(4, dtype=np.int32)
            faces = []
            img_size = np.asarray(img.shape)[0:2]
            for i in range(len(bboxs)):

                bb[0] = np.maximum(bboxs[i-1][0] - margin / 2, 0)
                bb[1] = np.maximum(bboxs[i-1][1] - margin / 2, 0)
                bb[2] = np.minimum(bboxs[i-1][2] + bboxs[i-1][0] + margin / 2, img_size[1])
                bb[3] = np.minimum(bboxs[i-1][3] + bboxs[i-1][1] + margin/ 2, img_size[0])
                # print("Cropping Coordinates: ", bb)

                if(bb[0] >= 0 and bb[1] >= 0 and bb[2] <= img_size[1] and bb[3] <= img_size[0]):
                    cropped = img[bb[1]:bb[3], bb[0]:bb[2], :]
                    cv2.imwrite("/home/kayadev-gpu-2/Desktop/OutputImages/Face-{}.jpg".format(self.imgnumber), cropped)
                    # print("Cropped in face align", cropped, "\n {}".format(cropped.shape))
                    faces.append(cropped)
                    self.imgnumber += 1
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
            # print("Image shape: ", type((img)[0,:]), "\nImage: ", img, "\n\nImage[0,:]", img[0,:])
            if(img.any()):
                resized = cv2.resize(img, (160,160))
                resized = np.expand_dims(resized, axis=0)
                embeddings = self.model.predict(resized)[0,:]
        return embeddings.reshape(1, -1)[0]

    def Distanceforfacenet(self,embedded_1, embedded_2):
            euclidean_distance = embedded_1 - embedded_2
            euclidean_distance = np.sum(np.multiply(euclidean_distance, euclidean_distance))
            euclidean_distance = np.sqrt(euclidean_distance)
            return euclidean_distance

    def MarkingProcess(self, img, bboxs, lookingflag, frameindex):
        inthelist = False
        croppedfaces = self.FaceAlign(img, bboxs)
        lookingtime = frameindex / 30
        lookingtime = timedelta(seconds=lookingtime)
        # print("\t Length of cropped faces: ", croppedfaces[0].shape,"\t Type: ", type(croppedfaces[0]),"\n Cropped face: ", croppedfaces[0])

        for face in croppedfaces:
            face = face.copy(order='C')
            encoded_image = base64.b64encode(face)
            encoded_image = str(encoded_image)
            encoded_image = encoded_image[1:len(encoded_image)]
            # print("Face for base64: ", face_base64)
            frame_embedding = self.GetEmbedding(face)
            # print("Frame_Embedding: ", frame_embedding)
            distance = self.Distanceforfacenet(frame_embedding, self.previousembedding)
            # print("\t Distance: ", distance)
            if(len(self.EmbeddingArray) == 0 and lookingflag == True):
                try:
                    # First frame insert
                    self.BreakPoint.append(int(0))
                    self.EmbeddingArray.append(frame_embedding)
                    self.EndTimer.append(lookingtime)
                    self.StartTimer.append(lookingtime)
                    self.connection.execute(f"""INSERT INTO datalog(embedding_id, face, embedding, start_time, end_time, cam_id) VALUES\
                                                ('{len(self.EmbeddingArray)}',{encoded_image} , '{frame_embedding}', '{lookingtime}', '{lookingtime}', '1')""")
                    # f"""INSERT INTO datalog(embedding_id, face, start_time, end_time, cam_id) VALUES ('{0}',{self.final_str} , '15:34:55.618076', '15:44:05.791561', '1')"""
                    self.Face.append(encoded_image)
                    # print("\t Adding to the database")
                except Exception as e:
                    print("Exception in adding to db ", e)
        
            if(distance > 10):
                # Different face
                for i in range (len(self.EmbeddingArray)):
                    distanceinarray = self.Distanceforfacenet(frame_embedding, self.EmbeddingArray[i])
                    if(distanceinarray < 8):
                        inthelist = True
                        updateid = i
                if(inthelist == True):
                    if(lookingflag == True):
                        # print("\t Updating the database")
                        self.EndTimer[i] = lookingtime
                        if(self.BreakPoint[i] < self.BreakValue):
                            self.connection.execute(f"""INSERT INTO datalog(embedding_id, face, embedding, start_time, end_time, cam_id) VALUES\
                                                ('{len(self.EmbeddingArray)}','{encoded_image}' , '{frame_embedding}', '{lookingtime}', '{lookingtime}', '1')""")
                            self.BreakPoint[i] = 0
                        else:
                            self.connection.execute(f"""UPDATE datalog SET end_time = '{lookingtime}' WHERE embedding_id = {len(self.EmbeddingArray)}""")
                            self.BreakPoint[i] += 1
                    else:
                        self.BreakPoint[i] -= 1
                else:
                    if(lookingflag == True):
                        try:
                            self.BreakPoint.append(int(0))
                            self.EmbeddingArray.append(frame_embedding)
                            self.EndTimer.append(lookingtime)
                            self.StartTimer.append(lookingtime)
                            self.connection.execute(f"""INSERT INTO datalog(embedding_id, face, embedding, start_time, end_time, cam_id) VALUES\
                                                ('{len(self.EmbeddingArray)}','{encoded_image}' , '{frame_embedding}', '{lookingtime}', '{lookingtime}', '1')""")
                            # print("\t Adding to the database")
                        except Exception as e:
                            print("Exception in adding to db ", e)

            elif(distance < 8):
                # Same face
                for i in range (len(self.EmbeddingArray)):
                    distanceinarray= self.Distanceforfacenet(frame_embedding, self.EmbeddingArray[i])
                    if(distanceinarray < 8):
                        if(lookingflag == True):
                            # print("\t Updating the database")
                            self.EndTimer[i] = lookingtime
                            if(self.BreakPoint[i] < self.BreakValue):
                                self.connection.execute(f"""INSERT INTO datalog(embedding_id, face, embedding, start_time, end_time, cam_id) VALUES\
                                                    ('{len(self.EmbeddingArray)}','{encoded_image}' , '{frame_embedding}', '{lookingtime}', '{lookingtime}', '1')""")
                                self.BreakPoint[i] = 0
                            else:
                                self.connection.execute(f"""UPDATE datalog SET end_time = '{lookingtime}' WHERE embedding_id = {len(self.EmbeddingArray)}""")
                                self.BreakPoint[i] += 1
                        else:
                            self.BreakPoint[i] -= 1


            print("\t Entries in dataframe: ", len(self.EmbeddingArray), len(self.EmbeddingArray), len(self.EmbeddingArray))
            self.previousembedding = frame_embedding
            print("\t Elasticity values: ", self.BreakPoint)
        
            return
        
    # def getreport(self):
    #     tempnumber = 0
    #     lengtharray = []
    #     camidarray = []
    #     for i in range (len(self.EmbeddingArray)):
    #         lengtharray.append(tempnumber)
    #         camidarray.append(1)
    #         tempnumber += 1
    #     df = pd.DataFrame(list(zip(lengtharray, self.Face, self.EmbeddingArray, self.StartTimer, self.EndTimer)), 
    #         columns =['embedding_id', 'face', 'embedding', 'start_time', 'end_time', 'cam_id'])
    #     for i in range(len(df)):
    #         df['duration'][i] = str(df['end_time'][i] - df['start_time'][i]).split(':')[2]

    #     return df

