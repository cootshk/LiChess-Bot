import datetime
import requests
import json

#--------------------------------------------------------------#
#Comment Format (VSCode highlighting):
#! Raises Error
#* Important
#? Less Important
#TODO: To Do
#// Removed
#** Debug
#General Comment
#--------------------------------------------------------------#

#!load token
try:
    token = json.load(open("accounts.json","r"))["lichess"]["token"]
except: #? if token is not found
    try:
        accounts = json.load(open("accounts.json","r"))
    except:
        accounts = {}
    token = input("Enter your lichess token: ")
    accounts["lichess"] = {"token": token}
    json.dump(accounts,open("accounts.json","w"))

class RateLimitedException(Exception): #! rate limited exception
    pass
class TokenError(Exception): #! token error
    pass

#*Create Objects

class color:
    def __init__(self,color:str="random") -> None:
        """A color object

        Args:
            color (str, optional): What color to play as (black, white, random). Defaults to "random".

        Raises:
            ValueError: if the color specified is not valid
        """
        if not self.color in ["white","black","random"]:
            raise ValueError("Invalid color")
        self.color = color
    def __str__(self) -> str:
        return self.color
    def __repr__(self) -> str:
        return self.color

class timecontrol:
    def __init__(self,*,correspondence:bool=False,days:int=7,initTime:int=60,incrementTime:int=0) -> None:
        self.correspondence = correspondence
        self.days = days
        self.initTime = initTime
        self.incrementTime = incrementTime
    def __repr__(self):
        if self.correspondence:
            return tuple([True,self.days])
        else:
            return tuple([False,self.initTime,self.incrementTime])
    def getTime(self):
        if self.correspondence:
            return tuple([True,self.days])
        else:
            return tuple([False,self.initTime,self.incrementTime])

class gameRules:
    def __init__(self,*,noAbort:bool=False,noRematch:bool=False,noGiveTime:bool=False,noClaimWin:bool=False) -> None:
        """Initiliaze a game rules object

        Args:
            noAbort (bool, optional): If the game can be aborted. Defaults to False.
            noRematch (bool, optional): If the game allows rematches. Defaults to False.
            noGiveTime (bool, optional): If you can give your opponent time. Defaults to False.
            noClaimWin (bool, optional): If you can claim a win after your opponent leaves the game. Defaults to False.
        """
        self.args = {"noAbort": noAbort,"noRematch": noRematch,"noGiveTime": noGiveTime,"noClaimWin": noClaimWin}
    def getArgs(self) -> str:
        """Gets the arguments for the rules

        Returns:
            str: List of arguments, comma seperated (i.e. noAbort,noRematch)
        """
        return  f"""{'noAbort' if self.args['noAbort'] else ''}
                    {',' if (self.args['noAbort']) and (self.args['noRematch'] or self.args['noGiveTime'] or self.args['noClaimWin']) else ''}
                    {'noRematch' if self.args['noRematch'] else ''}
                    {',' if self.args['noRematch'] and (self.args['noGiveTime'] or self.args['noClaimWin']) else ''}
                    {'noGiveTime' if self.args['noGiveTime'] else ''}
                    {',' if self.args['noGiveTime'] and self.args['noClaimWin'] else ''}
                    {'noClaimWin' if self.args['noClaimWin'] else ''}""" #? what is this

class lichessAccount:
    def __init__(self,token: str,endpoint:str="https://lichess.org") -> None: #* initalize, get account info, upgrade to bot account
        """Initalize a bot account with a token

        Args:
            token (str): The token of the bot account
            endpoint (str, optional): The endpoint of the lichess api. Defaults to "https://lichess.org".

        Raises:
            RateLimitedException: Raises if the account is rate-limited
            TokenError: Raises if the token is invalid
            ConnectionError: Raises if the endpoint is invalid
        """
        
        if not endpoint.startswith("https://"): #! check if endpoint is valid
            raise ConnectionError("Endpoint must start with https://")
        self.endpoint = endpoint #* set endpoint
        self.token = token #* set token
        accountinfo = requests.get(url=f"{self.endpoint}/api/account",headers={"Authorization": f"Bearer {self.token}"}) #? get account info
        if accountinfo.status_code == 200:
            self.accountinfo = accountinfo.json()
        elif accountinfo.status_code == 429: #!raises if rate limited
            raise RateLimitedException("You are being rate limited.")
        else:
            if __debug__:
                print(accountinfo.status_code)
                print(accountinfo.text)
            raise TokenError("Invalid token")
        if not __debug__: #** prints account info if debug mode is on (launched with -O)
            print(self.accountinfo)
        #! try to upgrade to bot account
        try:
            requests.post(url=f"{self.endpoint}/api/bot/account/upgrade",headers={"Authorization": f"Bearer {self.token}"})
        except:
            raise TokenError("This token is not a bot token.")
        #// #* start the run loop
        #// asyncio.run(self.runloop())
    def runloop(self) -> None: #* main run loop
        """Main Run Loop (async)
        """ #TODO: Add a way to stop the run loop
            #TODO: Add a way so the bot shows as online
        pass
    def updateAccountInfo(self) -> None:
        """Updates the account info

        Raises:
            RateLimitedException: Raises if the account is rate-limited
            TokenError: Raises if the token is invalid
        """
        accountinfo = requests.get(url=f"{self.endpoint}/api/account",headers={"Authorization": f"Bearer {self.token}"})
        if accountinfo.status_code == 200:
            self.accountinfo = accountinfo.json()
        elif accountinfo.status_code == 429:
            raise RateLimitedException("You are being rate limited.")
        else:
            raise TokenError("Invalid token")
    def CheckIfStreaming(self, gameid: str="") -> dict:
        """Check if a given game is being streamed

        Args:
            gameid (str, optional): the ID of the game to check. Defaults to the bot's current game.

        Raises:
            RateLimitedException: Raises if the account is rate-limited
            ConnectionError: Raises if the game is not found
            TokenError: Raises if the token is invalid

        Returns:
            dict: The stream info. See https://lichess.org/api#tag/Bot/operation/botGameStream for more info
        """
        if gameid == "":
            self.updateAccountInfo()
            gameid = self.accountinfo["playing"].replace(f"{self.endpoint}/","").replace("/black","").replace("/white","")
        response = requests.get(url=f"{self.endpoint}/api/bot/game/stream/{gameid}",headers={"Authorization": f"Bearer {self.token}"})
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 429:
            raise RateLimitedException("You are being rate limited.")
        elif response.status_code == 404:
            raise ConnectionError("Game not found")
        else: 
            raise TokenError("Invalid token")
    def GetGame(self, gameid: str="") -> dict:
        raise NotImplementedError #TODO: Add a way to get a game
        return {"board":None,"chat":self.getGameChat(gameid)}
    def MakeMoveInGame(self, gameid: str, move: str, offerDraw:bool=False) -> None:
        """Makes a move in a game

        Args:
            gameid (str): The game to make the move in
            move (str): The move in UFEI format (i.e. e2e4)
            offerDraw (bool, optional): Whether to offer (or agree to) a draw. Defaults to False.

        Raises:
            RateLimitedException: Raises if the account is rate-limited
            ConnectionError: Raises if the game is not found
            ValueError: Raises if the move is invalid
            TokenError: Raises if the token is invalid

        Returns:
            None
        """
        response = requests.post(f"{self.endpoint}/api/bot/{gameid}/move/{move}",headers={"Authorization": f"Bearer {self.token}"},params={"offeringDraw": offerDraw})
        if response.status_code == 200:
            return
        elif response.status_code == 429:
            raise RateLimitedException("You are being rate limited.")
        elif response.status_code == 404:
            raise ConnectionError("Game not found")
        elif response.status_code == 400:
            raise ValueError(response.json()["error"])
        else:
            raise TokenError("Invalid token")
    def AbortGame(self, gameid: str) -> None:
        """Aborts a game before it starts

        Args:
            gameid (str): The game to abort

        Raises:
            RateLimitedException: Raises if the account is rate-limited
            ConnectionError: Raises if the game is not found
            ValueError: Raises if the game has already started
            TokenError: Raises if the token is invalid

        Returns:
            None
        """
        response = requests.post(f"{self.endpoint}/api/bot/{gameid}/abort",headers={"Authorization": f"Bearer {self.token}"})
        if response.status_code == 200:
            return
        elif response.status_code == 429:
            raise RateLimitedException("You are being rate limited.")
        elif response.status_code == 404:
            raise ConnectionError("Game not found")
        elif response.status_code == 400:
            raise ValueError(response.json()["error"])
        else:
            raise TokenError("Invalid token")
    def getGameChat(self,gameid:str) -> list:
        """Gets the chat of a game

        Args:
            gameid (str): The game to get the chat of

        Raises:
            RateLimitedException: Raises if the account is rate-limited
            ConnectionError: Raises if the game is not found
            TokenError: Raises if the token is invalid

        Returns:
            list: A list of messages in the chat. See https://lichess.org/api#tag/Bot/operation/botGameChat for more info
        """
        response = requests.get(f"{self.endpoint}/api/bot/{gameid}/chat") #* get chat
        if response.status_code == 200: #? if successful
            return response.json()
        elif response.status_code == 429: #! if rate limited
            raise RateLimitedException("You are being rate limited.")
        elif response.status_code == 404: #! if game not found
            raise ConnectionError("Game not found")
        else: #! if token is invalid
            raise TokenError("Invalid token")
    def resignGame(self,gameid: str) -> None:
        """Resigns a game

        Args:
            gameid (str): The id of the game to resign

        Raises:
            RateLimitedException: Raises if the account is rate-limited
            ConnectionError: Raises if the game is not found
            ValueError: Raises if the game has already ended
            TokenError: Raises if the token is invalid
        """
        response = requests.post(f"{self.endpoint}/api/bot/game/{gameid}/resign",headers={"Authorization": f"Bearer {self.token}"})
        if response.status_code == 200:
            return
        elif response.status_code == 429:
            raise RateLimitedException("You are being rate limited.")
        elif response.status_code == 404:
            raise ConnectionError("Game not found")
        elif response.status_code == 400:
            raise ValueError(response.json()["error"])
        else:
            raise TokenError("Invalid token")
    def GetChallenges(self) -> tuple:
        response = requests.get(f"{self.endpoint}/api/challenge",headers={"Authorization": f"Bearer {self.token}"})
        if response.status_code == 200:
            return tuple([response.json()["in"], response.json()["out"]])
        elif response.status_code == 429:
            raise RateLimitedException("You are being rate limited.")
        elif response.status_code == 400:
            raise ValueError(response.json()["error"])
        else:
            raise TokenError("Invalid token")
    def challengeUser(self,user: str,*,color:color=color(),timecontrol:timecontrol=timecontrol(correspondence=True,days=7),variant,fen:str="",persistant:bool=True,acceptToken:str="",message:str="",rules:gameRules=gameRules()) -> None:
        if acceptToken == "" or message == "":
            message = "Your game with {opponent} is ready: {game}."
        if timecontrol.getTime()[0]:
            pass
        else:
            response = requests.post(f"{self.endpoint}/api/challenge/{user}",headers={"Authorization": f"Bearer {self.token}"},params={
                "clock.limit": timecontrol.getTime()[1],
                "clock.increment": timecontrol.getTime()[2],
                "variant": variant,
                "fen": fen,
                "keepAliveStream": persistant,
                "acceptByToken": acceptToken,
                "message": message,
                "rules": rules,
                "color": color}) # type: ignore #? ignore type error because of the way I'm doing the timecontrol


#* CUI Interface
if __name__ == "__main__":
    account = lichessAccount(token)
    print(account.accountinfo)
    #// asyncio.run(account.updateAccountInfo())