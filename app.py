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
champion_data = {"idToName": {}}


#this is a set of default traits that are used when a champion is not found in the championTraits dictionary
DEFAULT_TRAITS = {"kill": True, "stay": True, "body": "squishy", "counter": False}
COUNTER_WEIGHT = 2
#this is a set of champions that are considered counters to naafiri, meaning they are strong against her early or late game
COUNTERS = {
    "Akali",
    "Alistar",
    "Azir",
    "Blitzcrank",
    "Cassiopeia",
    "Diana",
    "Hecarim",
    "Heimerdinger",
    "Illaoi",
    "Irelia",
    "Janna",
    "Jinx",
    "Kennen",
    "Lissandra",
    "Viktor",
    "Nami",
    "Nasus",
    "Sion",
    "Smolder",
    "Taliyah",
    "Thresh",
    "Trundle",
    "Tristana",
    "Veigar",
    "Yasuo",
    "Yone",
    "Yunara",
    "Malzahar"
}
#this is a helper function that creates a dictionary with the traits of a champion
def _t(kill, stay, body):
    return {"kill": kill, "stay": stay, "body": body}
#this is a list of champion and their traits used to determine if they are strong or weak against naafiri
CHAMPION_TRAITS = {
    "Aatrox": _t(False, True, "bruiser"),
    "Ahri": _t(True, False, "squishy"),
    "Akali": _t(True, False, "squishy"),
    "Akshan": _t(True, False, "squishy"),
    "Alistar": _t(False, False, "bruiser"),
    "Ambessa": _t(False, False, "bruiser"),
    "Amumu": _t(False, True, "bruiser"),
    "Anivia": _t(True, True, "squishy"),
    "Annie": _t(True, True, "squishy"),
    "Aphelios": _t(True, True, "squishy"),
    "Ashe": _t(True, True, "squishy"),
    "Aurelion Sol": _t(True, True, "squishy"),
    "Aurora": _t(True, False, "squishy"),
    "Azir": _t(True, False, "squishy"),
    "Bard": _t(True, False, "squishy"),
    "Bel'Veth": _t(False, True, "bruiser"),
    "Blitzcrank": _t(False, True, "bruiser"),
    "Brand": _t(True, True, "squishy"),
    "Braum": _t(False, False, "bruiser"),
    "Briar": _t(False, True, "bruiser"),
    "Caitlyn": _t(True, False, "squishy"),
    "Camille": _t(False, False, "bruiser"),
    "Cassiopeia": _t(True, True, "squishy"),
    "Cho'Gath": _t(False, True, "bruiser"),
    "Corki": _t(True, False, "squishy"),
    "Darius": _t(False, True, "bruiser"),
    "Diana": _t(False, False, "bruiser"),
    "Dr. Mundo": _t(False, True, "bruiser"),
    "Draven": _t(True, True, "squishy"),
    "Ekko": _t(True, False, "squishy"),
    "Elise": _t(True, False, "squishy"),
    "Evelynn": _t(True, False, "squishy"),
    "Ezreal": _t(True, False, "squishy"),
    "Fiddlesticks": _t(True, False, "squishy"),
    "Fiora": _t(False, False, "bruiser"),
    "Fizz": _t(True, False, "squishy"),
    "Galio": _t(False, False, "bruiser"),
    "Gangplank": _t(False, True, "bruiser"),
    "Garen": _t(False, True, "bruiser"),
    "Gnar": _t(False, False, "bruiser"),
    "Gragas": _t(False, False, "bruiser"),
    "Graves": _t(False, False, "bruiser"),
    "Gwen": _t(False, False, "bruiser"),
    "Hecarim": _t(False, False, "bruiser"),
    "Heimerdinger": _t(True, True, "squishy"),
    "Hwei": _t(True, True, "squishy"),
    "Illaoi": _t(False, True, "bruiser"),
    "Irelia": _t(False, False, "bruiser"),
    "Ivern": _t(True, True, "squishy"),
    "Janna": _t(True, False, "squishy"),
    "Jarvan IV": _t(False, False, "bruiser"),
    "Jax": _t(False, True, "bruiser"),
    "Jayce": _t(True, False, "squishy"),
    "Jhin": _t(True, True, "squishy"),
    "Jinx": _t(True, True, "squishy"),
    "K'Sante": _t(False, False, "bruiser"),
    "Kai'Sa": _t(True, False, "squishy"),
    "Kalista": _t(True, False, "squishy"),
    "Karma": _t(True, False, "squishy"),
    "Karthus": _t(True, True, "squishy"),
    "Kassadin": _t(True, False, "squishy"),
    "Katarina": _t(True, False, "squishy"),
    "Kayle": _t(True, True, "squishy"),
    "Kayn": _t(False, False, "bruiser"),
    "Kennen": _t(True, False, "squishy"),
    "Kha'Zix": _t(True, False, "squishy"),
    "Kindred": _t(True, False, "squishy"),
    "Kled": _t(False, False, "bruiser"),
    "Kog'Maw": _t(True, True, "squishy"),
    "LeBlanc": _t(True, False, "squishy"),
    "Lee Sin": _t(False, False, "bruiser"),
    "Leona": _t(False, False, "bruiser"),
    "Lillia": _t(True, False, "squishy"),
    "Lissandra": _t(True, False, "squishy"),
    "Lucian": _t(True, False, "squishy"),
    "Lulu": _t(True, False, "squishy"),
    "Lux": _t(True, True, "squishy"),
    "Malphite": _t(False, False, "bruiser"),
    "Malzahar": _t(True, True, "squishy"),
    "Maokai": _t(False, False, "bruiser"),
    "Master Yi": _t(True, False, "squishy"),
    "Mel": _t(True, True, "squishy"),
    "Milio": _t(True, False, "squishy"),
    "Miss Fortune": _t(True, True, "squishy"),
    "Mordekaiser": _t(False, True, "bruiser"),
    "Morgana": _t(True, True, "squishy"),
    "Nami": _t(True, False, "squishy"),
    "Nasus": _t(False, True, "bruiser"),
    "Nautilus": _t(False, False, "bruiser"),
    "Neeko": _t(True, False, "squishy"),
    "Nidalee": _t(True, False, "squishy"),
    "Nilah": _t(True, False, "squishy"),
    "Nocturne": _t(True, False, "squishy"),
    "Nunu & Willump": _t(False, True, "bruiser"),
    "Olaf": _t(False, True, "bruiser"),
    "Orianna": _t(True, False, "squishy"),
    "Ornn": _t(False, False, "bruiser"),
    "Pantheon": _t(False, False, "bruiser"),
    "Poppy": _t(False, False, "bruiser"),
    "Pyke": _t(True, False, "squishy"),
    "Qiyana": _t(True, False, "squishy"),
    "Quinn": _t(True, False, "squishy"),
    "Rakan": _t(True, False, "squishy"),
    "Rammus": _t(False, False, "bruiser"),
    "Rek'Sai": _t(False, False, "bruiser"),
    "Rell": _t(False, False, "bruiser"),
    "Renata Glasc": _t(True, False, "squishy"),
    "Renekton": _t(False, False, "bruiser"),
    "Rengar": _t(True, False, "squishy"),
    "Riven": _t(False, False, "bruiser"),
    "Rumble": _t(False, True, "bruiser"),
    "Ryze": _t(True, False, "squishy"),
    "Samira": _t(True, False, "squishy"),
    "Sejuani": _t(False, False, "bruiser"),
    "Senna": _t(True, True, "squishy"),
    "Seraphine": _t(True, True, "squishy"),
    "Sett": _t(False, False, "bruiser"),
    "Shaco": _t(True, False, "squishy"),
    "Shen": _t(False, False, "bruiser"),
    "Shyvana": _t(False, True, "bruiser"),
    "Singed": _t(False, True, "bruiser"),
    "Sion": _t(False, True, "bruiser"),
    "Sivir": _t(True, False, "squishy"),
    "Skarner": _t(False, False, "bruiser"),
    "Smolder": _t(True, True, "squishy"),
    "Sona": _t(True, True, "squishy"),
    "Soraka": _t(True, True, "squishy"),
    "Swain": _t(False, True, "bruiser"),
    "Sylas": _t(False, False, "bruiser"),
    "Syndra": _t(True, False, "squishy"),
    "Tahm Kench": _t(False, False, "bruiser"),
    "Taliyah": _t(True, False, "squishy"),
    "Talon": _t(True, False, "squishy"),
    "Taric": _t(False, False, "bruiser"),
    "Teemo": _t(True, True, "squishy"),
    "Thresh": _t(True, False, "squishy"),
    "Tristana": _t(True, False, "squishy"),
    "Trundle": _t(False, True, "bruiser"),
    "Tryndamere": _t(False, False, "bruiser"),
    "Twisted Fate": _t(True, False, "squishy"),
    "Twitch": _t(True, True, "squishy"),
    "Udyr": _t(False, True, "bruiser"),
    "Urgot": _t(False, False, "bruiser"),
    "Varus": _t(True, True, "squishy"),
    "Vayne": _t(True, False, "squishy"),
    "Veigar": _t(True, True, "squishy"),
    "Vel'Koz": _t(True, True, "squishy"),
    "Vex": _t(True, False, "squishy"),
    "Vi": _t(False, True, "bruiser"),
    "Viego": _t(False, True, "bruiser"),
    "Viktor": _t(True, True, "squishy"),
    "Vladimir": _t(False, False, "bruiser"),
    "Volibear": _t(False, False, "bruiser"),
    "Warwick": _t(False, True, "bruiser"),
    "Wukong": _t(False, False, "bruiser"),
    "Xayah": _t(True, False, "squishy"),
    "Xerath": _t(True, True, "squishy"),
    "Xin Zhao": _t(False, True, "bruiser"),
    "Yasuo": _t(True, False, "squishy"),
    "Yone": _t(True, False, "squishy"),
    "Yorick": _t(False, True, "bruiser"),
    "Yunara": _t(True, True, "squishy"),
    "Zac": _t(False, False, "bruiser"),
    "Zed": _t(True, False, "squishy"),
    "Zeri": _t(True, False, "squishy"),
    "Ziggs": _t(True, False, "squishy"),
    "Zilean": _t(True, False, "squishy"),
    "Zoe": _t(True, False, "squishy"),
    "Zyra": _t(True, True, "squishy"),
}


async def loadChampData(connection):
    try:
        response = await connection.request('get', '/lol-game-data/assets/v1/champion-summary.json')
        champions = await response.json()
        champion_data["idToName"] = {champ["id"]: champ["name"] for champ in champions}
        print(f"loaded {len(champion_data['idToName'])} champions into cache")
    except Exception as e:
        print("Error for loading enemy champs:", e)
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
                
            await loadChampData(connection)

        #fires when there is error that is not showing up in the console
        except Exception as e:
            print("Error in connect is:", e)

    #this is heleper function that checks if the enemy team is fully locked in and ready to start the game
    rune = {"done": False}
    def decisionCheck(session):
        if session.get("timer", {}).get("phase") != "FINALIZATION":
            return False
        enemyTeam = session.get("theirTeam", [])
        if not enemyTeam:
            return False
        return all(p.get("championId") != 0 for p in enemyTeam)


    
    @connector.ws.register('/lol-champ-select/v1/session', event_types=('UPDATE',))
    async def champSelectPhase(Connection, event):
        session = event.data
        if session.get("timer", {}).get("phase") != "FINALIZATION":
            rune["done"]= False
        if decisionCheck(session) and not rune["done"]:
            rune["done"] = True
            enemyTeamId = [p["championId"] for p in session.get("theirTeam", [])]
            enemyTeamNames = [champion_data["idToName"].get(cid, f"Unknown({cid})") for cid in enemyTeamId]
            print("Enemy championId:", enemyTeamId)
            print("Enemy champion names:", enemyTeamNames)
    
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