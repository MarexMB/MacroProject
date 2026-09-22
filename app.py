#we use this library to connect to the League Client API
from lcu_driver import Connector
#used for the fix
import asyncio
#using pandas to display the data in a table format
import pandas as pd
import os





connector = Connector()
@connector.ready
async def connect(connection):
    try:
        print("You connected to the League Client API")
        #pulling summoner data from the League Client API
        pull = await connection.request('get', '/lol-summoner/v1/current-summoner')
        summoner = await pull.json()
        df = pd.DataFrame([summoner])
        print(df[['gameName','tagLine' ,'summonerLevel']])

        
            
    except Exception as e:
        print("Error in connect is:", e)


#it fires when the client closes or the connection is lost
@connector.close
async def disconnect(connection):
    
    print("You disconnected from the League Client API")
    #stops connector fully
    await connector.stop()
    
connector.start()      
