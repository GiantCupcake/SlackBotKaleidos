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
        self.joueurs = dict()
        self.confirmed_joueurs = dict() #Utilisé pour éliminer les joueurs ne souhaitant pas participer et compter les points
        self.mots_elimines = dict() #un dict pour checker si tout le monde a voté
        self.words_to_keep = dict() #une liste par joueurs
        self.words_confirmed = set()
        self.words_value = dict()
        self.letter = None
        self.time_start = None
        self.duree_manche = 120 #Des manches de 2 minutes, on pourrait faire plus
        self.nombre_manche = 1
        self.currente_manche = 0

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
                    if message['type'] == 'message' and 'user' in message.keys() and message['user'] != self.rtm['self']['id']:
                        asyncio.ensure_future(self.state[self.current_state](message))

            finally:
                ws.close()

    #Etat N°1
    async def state_init(self,message):
        """En attente du message de début de partie"""
        tab_text = message['text'].split(" ")
        if tab_text[0] == 'start':
            tab_text = tab_text[1:]
            for joueurs in tab_text:
                #TODO vérifier que les personnes existent
                #joueurs[2:-1] permet de formatter la string dans le format voulu
                self.joueurs[joueurs[2:-1]] = None
            asyncio.ensure_future(self.message_player('Une partie se lance avec : {}'.format(list(self.joueurs.keys())),message['user']))
            asyncio.ensure_future(self.notify_players('Vous avez été désigné pour jouer une partie de Kaleidos, acceptez-vous ? [Y/N]'))
            self.current_state = 2
        else:
            asyncio.ensure_future(self.message_player('Pour lancer une partie, ecrivez "start @joueur1 @joueur2..."',message['user']))

    #Etat N°2
    async def state_collect_participation(self, message):
        """On demande aux utilisateurs invités s'ils acceptent la partie"""
        user = message['user']
        if user in self.joueurs:
            reponse = message['text'].lower()
            if reponse == 'n':
                del self.joueurs[user]
            elif reponse == 'y':
                #On y met 0 pour compter les points plus tard
                self.confirmed_joueurs[user] = 0
            else:
                asyncio.ensure_future(self.message_player('Répondez par Y ou pas N',user))
        if len(self.joueurs) == len(self.confirmed_joueurs):
            asyncio.ensure_future(self.initie_manche())


    async def initie_manche(self):
        """Entre deux manches on veut réinitialiser tous les mots qui ont été données, changer de lettre, changer d'image"""
        self.mots_elimines = dict() #un dict pour checker si tout le monde a voté
        self.words_to_keep = dict() #une liste par joueurs
        self.words_confirmed = set()
        self.words_value = dict()
        self.letter = chr(randint(0, 25) + 97)
        asyncio.ensure_future(self.notify_players('Trouvez des choses commençant par la lettre : \' {0} \' sur cette image: {1}'.format(self.letter,URL[self.currente_manche])))
        for players in self.joueurs:
            #On va stocker leurs mots dans un set, on initialise ici ces sets
            self.joueurs[players] = set()
        #ajoute ici une emprunte dans le temps permettra de laisser un certain temps pour la prochaine phase
        self.time_start = time()
        self.current_state = 3


    #Etat N°3
    async def state_collect_words(self, message):
        if (time() - self.time_start ) > self.duree_manche:
            asyncio.ensure_future(self.prepare_vote())
            return
        user = message['user']
        if user in self.joueurs:
            response = message['text'].lower().strip().split(' ')
            for word in response:
                if word.startswith(self.letter):
                    self.joueurs[user].add(word)

    async def prepare_vote(self):
        asyncio.ensure_future(self.notify_players('Le temps est écoulé ! Vous allez maintenant éliminer les mots que vous jugez non-conformes'))
        for me in self.joueurs:
            dico = set()
            for player in self.joueurs:
                if player == me:
                    continue
                else:
                    #On fait l'aggrégation de tous les sets de mots des autres joueurs
                    dico = dico.union(self.joueurs[player])
            list_words = list(dico)
            self.words_to_keep[me] = list_words
            asyncio.ensure_future(self.message_player('Parmis les mots suivants, éliminez-en en entrant l\'indice du mot (les indices commencent à 0, terminez par -1) : {0}'.format(list_words),me))
        self.current_state = 4
        return


    async def notify_players(self,message):
            for players in self.joueurs:
                asyncio.ensure_future(self.message_player(message,players))

    #etat 4
    async def state_vote(self,message):
        user = message['user']
        if user in self.joueurs:
            indices = message['text'].split(' ')
            indices = [int(indice) for indice in indices]
            for i in indices:
                if i == -1:
                    break
                del self.words_to_keep[user][i]
            self.mots_elimines[user] = True
        #Ici on met tout ce qui concerne la fin d'une manche
        if len(self.mots_elimines) == len(self.joueurs):
            self.eliminate_words()
            self.points_per_words()
            self.count_points()
            asyncio.ensure_future(self.display_points())
            self.currente_manche = self.currente_manche + 1
            if self.currente_manche >= self.nombre_manche:
                asyncio.ensure_future(self.notify_players('La partie est terminée, merci d\'avoir joué !'))
                self.current_state = 1
            else:
                await asyncio.sleep(30)
                asyncio.ensure_future(self.initie_manche())


    def eliminate_words(self):
        for players in self.words_to_keep:
            for word in self.words_to_keep[players]:
                self.words_confirmed.add(word)
        for player, words in iter(self.joueurs.items()):
            new_set = set()
            for word in words:
                if word in self.words_confirmed:
                    new_set.add(word)
            self.joueurs[player] = new_set
        return

    def points_per_words(self):
        for word in self.words_confirmed:
            if word not in self.words_value:
                self.words_value[word] = 3
            else:
                self.words_value[word] = 1

    def count_points(self):
        for player,words in iter(self.joueurs.items()):
            for word in words:
                self.confirmed_joueurs[player] = self.confirmed_joueurs[player] + self.words_value[word]


    async def display_points(self):
        asyncio.ensure_future(self.notify_players('Manche terminée. Les mots soumis par les joueurs étaient : {0}.\n Les scores en sont actuellement à : {1}'.format(self.joueurs,self.confirmed_joueurs)))

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
