from lcu_driver import Connector
import asyncio



#this is a fix for newer versions of Python that require an event loop to be set before using asyncio
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
#this is the end of the fix, for older versions of python you can remove the above 2 lines and use the code below like you normally would



connector = Connector()
@connector.ready
async def connect(connection):
    print("You connected to the League Client API")
@connector.close
async def disconnect(connection):
    print("You disconnected from the League Client API")

connector.start()      
