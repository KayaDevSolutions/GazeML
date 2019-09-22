import psycopg2
import pandas as pd
import sqlalchemy as db 
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.automap import automap_base
import numpy as np
from PIL import Image
from scipy.misc import toimage
import scipy.misc
from scipy.misc import imsave
from datetime import datetime, date
import cv2
import base64


class OperationDatabase():

    engine = db.create_engine('postgresql://postgres:password@localhost:5432/TitanLog')
    
    def __init__(self):

        try:
            self.Data = pd.DataFrame(columns = ['face', 'embedding_id', 'embedding', 'start_time', 'end_time', 'cam_id' , 'duration'])
            # self.Data = pd.DataFrame(columns = ['face'])
            self.connection = self.engine.connect()
            print("Database instance is created")
        except Exception as e:
            print("Exception in initiating the database :",e)

    def selectquery(self):

        table = self.connection.execute(f"""SELECT face, embedding_id, encode(embedding, 'escape'), start_time, end_time, cam_id FROM datalog ;""")
        # table = self.connection.execute(f"""SELECT encode(face, 'escape') FROM datalog;""")
        # df = pd.read_sql(table, self.connection)
        # print(df)
        dfcount = 0
        for row in table:
            row = list(row)
            self.Data.loc[dfcount] = row
            dfcount += 1
            
        print(len(self.Data))

        # update_duration = self.connection.execute(f"""UPDATE datalog SET duration=end_time-start_time;""")

        # print(type(self.Data))
        arr = np.asarray(self.Data['face'][0])
        # print(type(arr))

        final_arr = base64.b64encode(arr)
        print(type(final_arr))
        # print(final_arr)

        # update_face = self.connection.execute(f"""UPDATE datalog SET face = '{0}';""".format(final_arr))

        # print(cv2.imdecode(".jpeg", self.Data['face'][0]))
        # print(type(self.Data["face"][0]))
        # print(final_table)
        # for index, row in self.Data.iterrows():
        #     # t = datetime.now().time()
        #     # seconds = (t.hour * 60 + t.minute) * 60 + t.second
        #     # print(seconds)
        #     print(type(pd.Timestamp(row['end_time'])))
        #     print(pd.Timestamp(row['end_time']) - pd.Timestamp(row['start_time']))
        #     print(type(pd.Timestamp(row['end_time'])))
        #     df["end_time"] = pd.Timestamp(df['end_time'])
        # df["start_time"] = pd.Timestamp(df['start_time'])
        # self.Data['end_time'] =  self.Data['end_time'].apply(pd.Timestamp)
        # self.Data['start_time'] = self.Data['start_time'].apply(pd.Timestamp)
        # self.Data['duration'] = self.Data['end_time'].sub(self.Data['start_time'], axis=0)
        # self.Data['duration'] = self.Data['end_time'].sub(self.Data['start_time'])
        # print(self.Data)
        # print(df)

        # df["end_time"] = pd.Timestamp(df['end_time'])
        # df["start_time"] = pd.Timestamp(df['start_time'])

        # # self.Data["up_duration"] = self.Data["end_time"] - self.Data["start_time"]
        # print(df)


        # for i in range(0, len(self.Data)):
        #     # print(i)
        #     df = self.Data
        #     ith = df.loc[i]

        #     ith["end_time"] = pd.to_datetime(ith['end_time'], errors='coerce')
        #     ith["start_time"] = pd.to_datetime(ith['start_time'], errors='coerce')
        #     start = ith["start_time"].item()
        #     end = ith["end_time"].item()
        #     dur = end - start
        #     print("Duration time is here", dur)



        # self.Data["end_time"] = pd.to_datetime(self.Data['end_time'])
        # self.Data["start_time"] = pd.to_datetime(self.Data['start_time'])
        # self.Data["up_duration"] = self.Data["end_time"] - self.Data["start_time"]
        # print(self.Data)
        # print(type(self.Data["end_time"]))
        # self.Data = self.Data.to_json()
        # data1st = self.Data["face"][0]
        # data1st = np.array(self.Data["face"][0])
        # data2nd = np.array(self.Data["face"][1])
        # data3rd = np.array(self.Data["face"][2])
        # data4th = np.array(self.Data["face"][3])
        # print(data3rd)
        # print(type(data1st))
        # print(len(data1st))
        # # data1st.resize(1,-1)
        # if (data1st == data2nd):
        #     print("same data no diffrence")
        # else:
        #     print("diffrent data")
        # print("-------------<class 'str'>--------------------",type(self.Data['face'][0]))
        # self.Data['face'][0] = list(self.Data['face'][0])
        # print("--------------<class 'list'>-------------",type(self.Data['face'][0]))

        # self.Data['face'][0] = np.asarray(self.Data['face'][0])

        # print(type(self.Data['face'][0]))

        # ques = base64.b64encode(self.Data['face'][0])
        # print(type(ques))

        # self.Data['face'][0] = ques

        # self.Data['face'][0] = self.Data['face'][0].encode()
        # print(type(self.Data['face'][0]))
        # self.Data['face'][0] = self.Data['face'][0]
        # print(type(self.Data["face"][5]))
        # absolute_image = base64.decodebytes(self.Data['face'][0])
        # print(type(absolute_image))
        # image_result = open('Asri Sahab.png', 'wb')
        # image_result.write(absolute_image)
        # self.Data['face'][0] = absolute_image
        # print(type(self.Data['face'][0]))
        # print(type(self.Data))
        # print(self.Data['face'][6])
        # self.Data['face'][0] = (self.Data['face'][0]).encode()
        # print(type(self.Data['face'][0]))
        # ques = base64.b64encode(self.Data['face'][0])
        # print(type(ques))
        # self.Data['face'][0] = ques

        # cv2.imshow('img',df)
        # print(type(self.Data['face'][0]))
        # print(self.Data['face'][3])
        # print(type(self.Data['face'][0]))
        self.Data = self.Data.to_json()

        

        # print(self.Data['face'][0])
        return(self.Data)

OpData = OperationDatabase()
OpData.selectquery()
