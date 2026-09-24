#we use this library to connect to the League Client API
from lcu_driver import Connector
#used for the fix
import asyncio
#using pandas to display the data in a table format
import pandas as pd
import os

#gui stuff
import threading
import tkinter as tk
from tkinter import ttk


#this is a global variable that holds the latest summoner dataframe so the gui can acces it
latest_summoner_df = {"df": None}
gui_ref = {"app": None}

#holds the current connector, needed because a Connector() can only be started once,
#after stop() its "used up" so we make a fresh one every time we connect
connector_ref = {"connector": None}


#this builds a brand new connector with all the handlers registered on it
def build_connector():
    connector = Connector()

    @connector.ready
    async def connect(connection):
        try:
            print("You connected to the League Client API")
            #pulling summoner data from the League Client API
            pull = await connection.request('get', '/lol-summoner/v1/current-summoner')
            summoner = await pull.json()
            df = pd.DataFrame([summoner])
            print(df[['gameName', 'tagLine', 'summonerLevel']])

            #hand the dataframe over to the gui thread
            latest_summoner_df["df"] = df[['gameName', 'tagLine', 'summonerLevel']]
            if gui_ref["app"] is not None:
                gui_ref["app"].on_connected()

        #fires when there is error that is not showing up in the console
        except Exception as e:
            print("Error in connect is:", e)

    #shows when you update your summoner profile in the League Client API
    @connector.ws.register('/lol-summoner/v1/current-summoner', event_types=('UPDATE',))
    async def icon_changed(connection, event):
        print(f'The summoner {event.data["displayName"]} was updated.')

    #it fires when the client closes or the connection is lost
    @connector.close
    async def disconnect(connection):

        print("You disconnected from the League Client API")

        #this needs to be fixed because it fires a error when the client closes.
        #app stops working like intended but it fires a error for some reason(If i put await there it just perma spams same print line)
        connector.stop()

        if gui_ref["app"] is not None:
            gui_ref["app"].on_disconnected()

    return connector


#holds the event loop that connector.start() creates, so we can schedule
#coroutines (like connector.stop()) into it from the tkinter thread
connector_loop_ref = {"loop": None}


def run_connector():
    #connector.start() blocks and runs its own event loop, so it lives on its own thread
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    connector_loop_ref["loop"] = loop

    #fresh connector every time, since the old one is used up after stop()
    connector = build_connector()
    connector_ref["connector"] = connector
    connector.start()


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Runity")
        self.geometry("500x400")

        self.connector_thread = None

        container = ttk.Frame(self)
        container.pack(fill="both", expand=True)

        #simple nav bar to switch between the two pages
        nav = ttk.Frame(container)
        nav.pack(fill="x", pady=5)
        ttk.Button(nav, text="Page 1", command=lambda: self.show_page("MainPage")).pack(side="left", padx=5)
        ttk.Button(nav, text="Page 2", command=lambda: self.show_page("SecondPage")).pack(side="left", padx=5)

        self.pages_container = ttk.Frame(container)
        self.pages_container.pack(fill="both", expand=True)

        self.pages = {}
        for PageClass in (MainPage, SecondPage):
            page = PageClass(self.pages_container, self)
            self.pages[PageClass.__name__] = page
            page.place(relwidth=1, relheight=1)

        self.show_page("MainPage")

    def show_page(self, name):
        self.pages[name].tkraise()

    #called from the connector thread once connected, so hop back to the gui thread
    def on_connected(self):
        self.after(0, self.pages["MainPage"].display_table)
    #this is called once youre disconnected
    def on_disconnected(self):
        self.after(0, self.pages["MainPage"].reset_table)
    #this is called when the connect button is pressed
    def start_connection(self):
        if self.connector_thread is None or not self.connector_thread.is_alive():
            self.connector_thread = threading.Thread(target=run_connector, daemon=True)
            self.connector_thread.start()
    #this is called when the disconnect button is pressed
    def stop_connection(self):
        #connector.stop() is a coroutine, and we're in the tkinter thread here,
        #not the connector's own event loop thread, so it has to be scheduled
        #into that loop instead of called directly (that's what caused the
        #"coroutine was never awaited" RuntimeWarning)
        loop = connector_loop_ref["loop"]
        connector = connector_ref["connector"]
        try:
            if loop is not None and connector is not None:
                asyncio.run_coroutine_threadsafe(connector.stop(), loop)
            else:
                print("Error while disconnecting: connector isn't running")
        except Exception as e:
            print("Error while disconnecting:", e)

        #clear these out so the next connect click knows to build a fresh connector
        self.connector_thread = None
        connector_ref["connector"] = None
        connector_loop_ref["loop"] = None
        self.pages["MainPage"].reset_table()

#this is the first page
class MainPage(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app

        title = ttk.Label(self, text="League Client Connection", font=("Segoe UI", 14, "bold"))
        title.pack(pady=10)

        btn_frame = ttk.Frame(self)
        btn_frame.pack(pady=5)

        self.connect_btn = ttk.Button(btn_frame, text="Connect", command=self.app.start_connection)
        self.connect_btn.pack(side="left", padx=5)

        self.disconnect_btn = ttk.Button(btn_frame, text="Disconnect", command=self.app.stop_connection)
        self.disconnect_btn.pack(side="left", padx=5)

        self.status_label = ttk.Label(self, text="Status: Not connected")
        self.status_label.pack(pady=5)

        #table to show the summoner info once connected
        columns = ("gameName", "tagLine", "summonerLevel")
        self.tree = ttk.Treeview(self, columns=columns, show="headings", height=5)
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=140, anchor="center")
        self.tree.pack(pady=15, fill="x", padx=10)
    #this is called when the connection is established so we can fill the table with the summoner info
    def display_table(self):
        self.status_label.config(text="Status: Connected")
        #clear old rows first
        for row in self.tree.get_children():
            self.tree.delete(row)

        df = latest_summoner_df["df"]
        #this is where we fill the table with the summoner info
        if df is not None:
            for _, row in df.iterrows():
                self.tree.insert("", "end", values=(row["gameName"], row["tagLine"], row["summonerLevel"]))
    #this is called when the connection is lost so we can reset the table and show that we are not connected to the League Client API anymore
    def reset_table(self):
        self.status_label.config(text="Status: Not connected")
        for row in self.tree.get_children():
            self.tree.delete(row)

#this is the second page
class SecondPage(ttk.Frame):
    #empty for now, made so it can be filled in later when i will be making ai rune importer
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        #This is just a placeholder
        label = ttk.Label(self, text="Rune Importer", font=("Segoe UI", 14, "bold"))
        label.pack(pady=20)

#This is the main entry point of the Application. This starts the main event loop
if __name__ == "__main__":
    app = App()
    gui_ref["app"] = app
    app.mainloop()