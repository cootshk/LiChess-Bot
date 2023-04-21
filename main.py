import datetime
import requests
import json
import os
from typing import Literal

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
#TODO Board
#TODO lichessAccount.getGame()
#--------------------------------------------------------------#

#!load token
try:
    token = json.load(open("accounts.json","r"))["lichess"]["token"]
except FileNotFoundError: #? if file is not found
    accounts = {"lichess":{"token":input("Enter your lichess token: ")}} #* create file
    json.dump(accounts,open("accounts.json","x"))
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
class gameSetup:
    def __init__(self, color:str="random", variant:str="standard", *, correspondence:bool=True, days:int=7, initTime:int=180, incrementTime:int=0, position:str="rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1", noAbort:bool=False, noRematch:bool=False, noGiveTime:bool=False, noClaimWin:bool=False) -> None:
        """The setup for a game

        Args:
            color (str): What color to play as. Can be "white", "black", or "random". Defaults to "random".
            correspondence (bool): If the game is correspondence or not. Defaults to True.
            variant (str, optional): What kind of chess to play. Can be "standard", "chess960", "crazyhouse", "antichess", "atomic", "horde", "kingOfTheHill", "racingKings", "threeCheck", or "fromPosition". Defaults to "standard".
            days (int, optional): If the game is a correspondence game, how many days should each move take. Can be 1, 2, 3, 5, 7, 10, or 14. Defaults to 7.
            initTime (int, optional): How much time each player should start with, in seconds. Can be from 1 to 10800. Defaults to 180.
            incrementTime (int, optional): How much time each player gets when they make a move, in seconds. Can be from 0 to 60. Defaults to 0.
            position (str, optional): The starting position, in FEN notation. Defaults to "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1".
            noAbort (bool, optional): If you or the opponent can abort the game. Defaults to False.
            noRematch (bool, optional): If you or the opponent can ask for a rematch. Defaults to False.
            noGiveTime (bool, optional): If you or the opponent can give the other more time. Defaults to False.
            noClaimWin (bool, optional): If you or the opponent can claim a win after the other leaves the game. Defaults to False.

        Raises:
            ValueError: Raises if the color is invalid
            ValueError: Raises if the variant is invalid
            ValueError: Raises if the correspondence value is invalid
            ValueError: Raises if the days value is invalid
            ValueError: Raises if the initTime value is invalid
            ValueError: Raises if the incrementTime value is invalid
        """
        #! check if color is valid
        if not color in ["white","black","random"]:
            raise ValueError("Invalid color")
        self.color = color
        #! check if variant is valid
        if not variant in ["standard", "chess960", "crazyhouse", "antichess", "atomic", "horde", "kingOfTheHill", "racingKings", "threeCheck", "fromPosition"]:
            raise ValueError("Invalid variant")
        self.variant = variant
        self.position = position
        self.args = {"noAbort": noAbort,"noRematch": noRematch,"noGiveTime": noGiveTime,"noClaimWin": noClaimWin}
        #! check if time control is valid
        if not isinstance(correspondence,bool):
            raise ValueError("Invalid correspondence value")
        if not days in [1,2,3,5,7,10,14]:
            raise ValueError("Invalid days value")
        if not initTime in range(1,10801):
            raise ValueError("Invalid initTime value")
        if not incrementTime in range(0,61):
            raise ValueError("Invalid incrementTime value")
        self.correspondence = correspondence
        self.days = days
        self.initTime = initTime
        self.incrementTime = incrementTime
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
    def getPosition(self) -> tuple:
        """Gets the variant and starting position of the board

        Returns:
            tuple: (Variant, Position)
        """
        return tuple([self.variant,self.position])
    def getTimeControl(self) -> tuple:
        """Gets the time control of the game

        Returns:
            tuple: (True, days) if correspondence, (False, initTime, incrementTime) if not
        """
        return tuple([self.correspondence,self.days]) if self.correspondence else tuple([self.correspondence,self.initTime,self.incrementTime])
    def getColor(self) -> str:
        """Gets the color that the bot will play as

        Returns:
            str: The color of the bot
        """
        return self.color

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
            pass
        elif accountinfo.status_code == 429: #!raises if rate limited
            raise RateLimitedException("You are being rate limited.")
        else:
            if __debug__:
                print(accountinfo.status_code)
                print(accountinfo.text)
            raise TokenError("Invalid token")
        if not __debug__: #** prints account info if debug mode is on (launched with -O)
            print(accountinfo)
        #! try to upgrade to bot account
        try:
            requests.post(url=f"{self.endpoint}/api/bot/account/upgrade",headers={"Authorization": f"Bearer {self.token}"})
        except:
            raise TokenError("This token is not a bot token.")
        #// #* start the run loop
        #// asyncio.run(self.runloop())
    #//def runloop(self) -> None: #* main run loop
        #//"""Main Run Loop (async)
        #//""" #TODO: Add a way to stop the run loop
        #//    #TODO: Add a way so the bot shows as online
        pass
    def getAccountInfo(self) -> dict:
        """Gets account info. See https://lichess.org/api#/tag/Account for more info

        Raises:
            RateLimitedException: Raises if the account is rate-limited
            ValueError: Raises if an error occurs
            TokenError: Raises if the token is invalid

        Returns:
            dict: The account info
        """
        response = requests.get(url=f"{self.endpoint}/api/account",headers={"Authorization": f"Bearer {self.token}"})
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 429:
            raise RateLimitedException("You are being rate limited.")
        else:
            raise ValueError(response.json()["error"])
    def getEmail(self) -> str:
        response = requests.get(url=f"{self.endpoint}/api/account/email",headers={"Authorization": f"Bearer {self.token}"})
        if response.status_code == 200:
            return response.json()["email"]
        elif response.status_code == 429:
            raise RateLimitedException("You are being rate limited.")
        else:
            raise ValueError(response.json()["error"])
    def checkIfStreaming(self, gameid: str="") -> dict:
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
        else:
            raise ValueError(response.json()["error"])
    def getGame(self, gameid: str="") -> dict:
        raise NotImplementedError #TODO: Add a way to get a game
        return {"board":None,"chat":self.getGameChat(gameid)}
    def makeMoveInGame(self, gameid: str, move: str, offerDraw:bool=False) -> None:
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
        else:
            raise ValueError(response.json()["error"])
    def abortGame(self, gameid: str) -> None:
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
    def getChallenges(self) -> tuple:
        response = requests.get(f"{self.endpoint}/api/challenge",headers={"Authorization": f"Bearer {self.token}"})
        if response.status_code == 200:
            return tuple([response.json()["in"], response.json()["out"]])
        elif response.status_code == 429:
            raise RateLimitedException("You are being rate limited.")
        else:
            raise ValueError(response.json()["error"])
    def challengeUser(self,user: str,*,rated:bool=False,persistant:bool=True,acceptToken:str="",message:str="",rules:gameSetup=gameSetup()) -> json:
        """Challenges a user to a game

        Args:
            user (str): the ID of the user to challenge
            persistant (bool, optional): If the challenge should disapear after 20s. Defaults to True.
            acceptToken (str, optional): The token of the other user. Use if you want to accept the game instantly. Defaults to "".
            message (str, optional): The message to send the other uesr, if acceptToken is set. Defaults to "".
            rules (gameSetup, optional): The rules to create the challenge with. See help(gameSetup) for more info. Defaults to gameSetup().
            rated (bool, optional): Whether the game should be rated. Defaults to False.

        Raises:
            RateLimitedException: Raises if the account is rate-limited
            ValueError: Raises if the rules are invalid
            TokenError: Raises if the token is invalid

        Returns:
            json: The details of the accepted challenge. See https://lichess.org/api#tag/Challenges/operation/challengeCreate for more info.
        """
        if acceptToken == "" or message == "":
            message = "Your game with {opponent} is ready: {game}."
        if rules.getTime()[0]: #* if correspondence
            response = requests.post(f"{self.endpoint}/api/challenge/{user}",headers={"Authorization": f"Bearer {self.token}"},params={
                "rated": rated,
                "days": rules.getTime()[1],
                "clock.limit": "",
                "clock.increment": "",
                "variant": rules.getPosition()[0],
                "fen": rules.getPosition()[1],
                "keepAliveStream": persistant,
                "acceptByToken": acceptToken,
                "message": message,
                "rules": rules.getArgs(),
                "color": rules.getColor()})
        else: #* if real time
            response = requests.post(f"{self.endpoint}/api/challenge/{user}",headers={"Authorization": f"Bearer {self.token}"},params={
                "clock.limit": rules.getTime()[1],
                "clock.increment": rules.getTime()[2],
                "variant": rules.getPosition()[0],
                "fen": rules.getPosition()[1],
                "keepAliveStream": persistant,
                "acceptByToken": acceptToken,
                "message": message,
                "rules": rules.getArgs(),
                "color": rules.getColor()})
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 429:
            raise RateLimitedException("You are being rate limited.")
        else:
            raise ConnectionError(response.json()["error"])
    def acceptChallenge(self,challengeid: str) -> None:
        """Accepts a challenge sent to the bot

        Args:
            challengeid (str): The id of the challenge to accept

        Raises:
            RateLimitedException: Raises if the account is rate-limited
            ValueError: Raises if the challenge is invalid
            ConnectionError: Raises if the challenge is not found
            TokenError: Raises if the token is invalid
        """
        response = requests.post(f"{self.endpoint}/api/challenge/{challengeid}/accept",headers={"Authorization": f"Bearer {self.token}"})
        if response.status_code == 200:
            return
        elif response.status_code == 429:
            raise RateLimitedException("You are being rate limited.")
        else:
            raise ConnectionError(response.json()["error"])
    def declineChallenge(self,challengeid: str,reason:str="declineGeneric") -> None:
        """Declines a challenge sent to the bot

        Args:
            challengeid (str): The id of the challenge to decline
            reason (str, optional): The reason to decline the challenge. Can be . Defaults to "declineGeneric".

        Raises:
            ValueError: Raises if the reason is invalid
            RateLimitedException: Raises if the account is rate-limited
            ConnectionError: Any other error
        """
        if reason not in ["registerToSendChallenges","youCannotChallengeX","xDoesNotAcceptChallenges","yourXRatingIsTooFarFromY","cannotChallengeDueToProvisionalXRating","xOnlyAcceptsChallengesFromFriends","declineGeneric","declineLater","declineTooFast","declineTooSlow","declineTimeControl","declineRated","declineCasual","declineStandard","declineVariant","declineNoBot","declineOnlyBot"]: #! All possible decline reasons (from https://github.com/lichess-org/lila/blob/master/translation/source/challenge.xml#L14)
            raise ValueError("Invalid reason")
        response = requests.post(f"{self.endpoint}/api/challenge/{challengeid}/decline",headers={"Authorization": f"Bearer {self.token}"},params={"reason": reason})
        if response.status_code == 200:
            return
        elif response.status_code == 429:
            raise RateLimitedException("You are being rate limited.")
        else:
            raise ConnectionError(response.json()["error"])
    def cancelChallenge(self,challengeid:str,opponentToken:str="") -> None:
        response = requests.post(f"{self.endpoint}/api/challenge/{challengeid}/cancel",headers={"Authorization": f"Bearer {self.token}"},params=({"opponentToken":opponentToken} if not opponentToken == "" else None))
        if response.status_code == 200:
            return
        elif response.status_code == 429:
            raise RateLimitedException("You are being rate limited.")
        else:
            raise ConnectionError(response.json()["error"])
    def challengeAI(self,AIlevel:int=8,rules:gameSetup=gameSetup()) -> dict:
        if not AIlevel in range(1,9):
            raise ValueError("Invalid AI level")
        response = requests.post(
            f"{self.endpoint}/api/challenge/ai",
            headers={"Authorization": f"Bearer {self.token}"},
            params=({
                "level": AIlevel,
                "color": rules.getColor(),
                "variant": rules.getPosition()[0],
                "fen": rules.getPosition()[1],
                "days": rules.getTimeControl()[1]
                } if rules.getTimeControl()[0] else {
                "level": AIlevel,
                "color": rules.getColor(),
                "variant": rules.getPosition()[0],
                "fen": rules.getPosition()[1],
                "clock.limit": rules.getTimeControl()[1],
                "clock.increment": rules.getTimeControl()[2]
            })
        )
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 429:
            raise RateLimitedException("You are being rate limited.")
        else:
            raise ConnectionError(response.json()["error"])
    def openEndedChallenge(self,rated:bool=False,rules:gameSetup=gameSetup(),users:list=[],name:str="") -> dict:
        if name == "":
            name == f"Challenge from {self.accountinfo['username']}"
        if users == []:
            response = requests.post(f"{self.endpoint}/api/challenge/open",headers={
                "Authorization": f"Bearer {self.token}"},params={
                "rated": rated,
                "variant": rules.getPosition()[0],
                "days": rules.getTimeControl()[1],
                "fen": rules.getPosition()[1],
                "name": name,
                "rules": rules.getArgs(),
                } if rules.getTimeControl()[0] else {
                "rated": rated,
                "variant": rules.getPosition()[0],
                "clock.limit": rules.getTimeControl()[1],
                "clock.increment": rules.getTimeControl()[2],
                "fen": rules.getPosition()[1],
                "name": name,
                "rules": rules.getArgs(),
                })
        else:
            allusers = ""
            for user in users:
                allusers += f",{user}"
            allusers = allusers.removeprefix(",")
            response = requests.post(f"{self.endpoint}/api/challenge/open",headers={
                "Authorization": f"Bearer {self.token}"},params={
                "rated": rated,
                "variant": rules.getPosition()[0],
                "days": rules.getTimeControl()[1],
                "fen": rules.getPosition()[1],
                "name": name,
                "rules": rules.getArgs(),
                "users": allusers
                } if rules.getTimeControl()[0] else {
                "rated": rated,
                "variant": rules.getPosition()[0],
                "clock.limit": rules.getTimeControl()[1],
                "clock.increment": rules.getTimeControl()[2],
                "fen": rules.getPosition()[1],
                "name": name,
                "rules": rules.getArgs(),
                "users": allusers
                })
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 429:
            raise RateLimitedException("You are being rate limited.")
        else:
            return ConnectionError(response.json()["error"])

#* CUI Interface
if __name__ == "__main__":
    account = lichessAccount(token)
    #print(account.getAccountInfo())
    print(account.getEmail())
    #// asyncio.run(account.updateAccountInfo())