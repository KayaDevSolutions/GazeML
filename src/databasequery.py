import psycopg2
import pandas as pd
import sqlalchemy as db 
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.automap import automap_base
import numpy as np
import base64
import numpy as np
from PIL import Image
import PIL
import cv2
class OperationDatabase():

    engine = db.create_engine('postgresql://postgres:password@localhost:5432/TitanLog')
    
    def __init__(self):
        try:
            self.Data = pd.DataFrame(columns = ['face', 'embedding_id', 'start_time', 'duration', 'cam_id' ])
            self.connection = self.engine.connect()
            print("Database instance is created")
        except Exception as e:
            print("Exception in initiating the database :",e)
            
    def selectquery(self):

        table = self.connection.execute(f"""SELECT face, embedding_id, start_time, (end_time - start_time) as duration, cam_id FROM datalog WHERE (end_time - start_time) > '00:00:01'::time ORDER BY start_time;""")
        dfcount = 0    
        for row in table:
            row = list(row)
            self.Data.loc[dfcount] = row
            dfcount += 1  



        for i in range(len(self.Data)):
            self.Data['face'][i] = np.asarray(self.Data['face'][i])
            self.Data['face'][i] = base64.b64encode(self.Data['face'][i])
            # print(self.Data['face'][i])

        for i in range(len(self.Data)):
            self.Data['duration'][i] = str(self.Data['duration'][i]).split(':')[2][:5]

        for i in range(len(self.Data)):
            self.Data['start_time'][i] = str(self.Data['start_time'][i]).split(':')[2][:5]
        # print(type(self.Data['face'][0]))




        # print(type(self.Data['face'][0]))
        
        # cv2.imshow("img",self.Data['face'][0])
        #     self.Data['face'][i] = base64.b64encode(self.Data['face'][i])
        # nparr = np.fromstring(self.Data['face'][0], np.uint8)
        # frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        # cv2.imshow('image', frame)
        # cv2.waitKey(0)
        # print("----------------------------------",type(self.Data))
        # print(type(self.Data['face'][0]))
        self.Data = self.Data.to_json()


        return(self.Data)

OpData = OperationDatabase()
OpData.selectquery()
