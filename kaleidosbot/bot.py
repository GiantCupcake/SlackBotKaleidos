"""Slack Bot that allow you to call your friends for a game of Kaleidos"""
import asyncio
import json
from collections import OrderedDict
from urllib.parse import *
from time import time

from aiohttp import ClientSession, MsgType
from random import randint
from api.api import call
from config.config import *


class Bot:
    """Play Kaleidos with your friends"""
    #Regler ces histoires de channel, envoyer des mesages perso
    def __init__(self,token,*args,timeout=None):
        self.__token = token
        self.name = 'KaleiosBot'
        self.timeout = timeout or 60
        self.future = asyncio.Future()
        self.rtm = None
        self.state = {1:self.state_init,2:self.state_collect_participation,3:self.state_collect_words,4:self.state_vote}
        self.current_state = 1
        self.joueurs = OrderedDict()
        self.confirmed_joueurs = dict() #Utilisé pour éliminer les joueurs ne souhaitant pas participer
        self.mots_elimines = dict() #String de mots éliminés par joueurs
        self.words_to_eliminate = dict() #dic contenant des OrderedDict
        self.letter = None
        self.time_start = None
        self.duree_manche = 15

    async def _run(self):
        self.rtm = await self.call('rtm.start')

        if not self.rtm['ok']:
            self.future.set_result(ValueError(self.rtm['error']))
        asyncio.ensure_future(self.state_listen())


    def connect(self):
        """
        Launch the bot.
        :returns: a future for when the bot wants to be closed.
        :rtype: :py:class:`asyncio.Future`
        """
        asyncio.ensure_future(self._run())
        return self.future

    async def call(self,method, file=None,**kwargs):
        return await call(method,file=file,token=self.__token,**kwargs)


    async def state_listen(self):
        """Listen for the opening of a session"""
        with ClientSession() as session:
            ws =  await session._ws_connect(self.rtm['url'])
            self.ws = ws
            try:
                while True:
                    msg = await ws.receive()
                    if msg.tp == MsgType.close:
                        break

                    assert msg.tp == MsgType.text
                    message = json.loads(msg.data)
                    print(message)
                    if message['type'] == 'message' and 'user' in message.keys() and message['user'] != self.rtm['self']['id']:
                        asyncio.ensure_future(self.state[self.current_state](message))

            finally:
                ws.close()

    #Etat N°1
    async def state_init(self,message):
            tab_text = message['text'].split(" ")
            if tab_text[0] == 'start':
                tab_text = tab_text[1:]
                for joueurs in tab_text:
                    #TODO vérifier que les personnes existent
                    self.joueurs[joueurs[2:-1]] = None
                print(self.joueurs)
                asyncio.ensure_future(self.message_player('Une partie se lance avec : {0}'.format(self.joueurs),message['user']))
                asyncio.ensure_future(self.notify_players('Vous avez été désigné pour jouer une partie de Kaleidos, acceptez-vous ? [Y/N]'))
                self.current_state = 2
            else:
                asyncio.ensure_future(self.message_player('Pour lancer une partie, ecrivez "start @joueur1 @joueur2..."',message['user']))

    #Etat N°2
    async def state_collect_participation(self, message):
        print("Stage 2")

        user = message['user']
        if user in self.joueurs:
            reponse = message['text'].lower()
            if reponse == 'n':
                del self.joueurs[user]
            elif reponse == 'y':
                self.confirmed_joueurs[user] = None
            else:
                asyncio.ensure_future(self.message_player('Répondez par Y ou pas N',user))

        if len(self.joueurs) == len(self.confirmed_joueurs):
            print("stage 3")
            asyncio.ensure_future(self.initie_manche())


    async def initie_manche(self):
        self.letter = chr(randint(0, 25) + 97)
        for players in self.joueurs:
            #On va stocker leurs mots dans un set, on initialise ici ces sets
            self.joueurs[players] = {}
            #ajoute ici une emprunte dans le temps permettra de laisser un certain temps pour la prochaine phase
            self.time_start = time()
            #asyncio.ensure_future(self.message_player('Cherchez sur cette image : {0}'.format(quote(URL)),players))
            asyncio.ensure_future(self.message_player('Cherchez sur cette image : {0}'.format(URL),players, unfurl_link=False))
            asyncio.ensure_future(self.message_player('Trouvez des choses commençant par la lettre {0}'.format(self.letter),players))
        self.current_state = 3


    #Etat N°3
    async def state_collect_words(self, message):
        print("stage 4")
        if (self.time_start - time()) > self.duree_manche:
            asyncio.run_until_complete(self.prepare_vote())
        user = message['user']
        if user in self.joueurs:
            word = message['text'].lower()
            if word.startswith(self.letter):
                self.joueurs[user].add(word)

    async def prepare_vote(self):
        asyncio.ensure_future(self.notify_players('Le temps est écoulé ! Vous allez maintenant éliminer les mots que vous jugez non-conformes'))
        for me in self.joueurs:
            dico = OrderedDict()
            for player in self.joueurs:
                if player == me:
                    continue
                else:
                    #On fait l'aggrégation de tous les dictionnaires des autres joueurs
                    dico = dico + self.joueurs[player]
            self.words_to_eliminate[me] = dico
            asyncio.ensure_future(self.message_player('Parmis les mots suivants,\
                                    éliminez en entrant l\'indice du mot (les indices commencent à 0) : {0}'.format(dico),me))
        self.current_state = 4
        return



    async def notify_players(self,message):
            for players in self.joueurs:
                asyncio.ensure_future(self.message_player(message,players))


    async def state_vote(self):
        user = message['user']
        if user in self.joueurs:
            pass


    async def message_player(self,message,player,**kwargs):
        await self.call('chat.postMessage',channel=player,
                    username=self.name,
                    as_user=True,
                    text=message,**kwargs)


if __name__ == "__main__":
    debug = DEBUG

    bot = Bot(TOKEN)

    loop = asyncio.get_event_loop()

    loop.set_debug(debug)
    loop.run_until_complete(bot.connect())
    loop.close()
