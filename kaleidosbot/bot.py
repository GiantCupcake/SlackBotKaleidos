"""Slack Bot that prints on the console."""
import asyncio
import json

from aiohttp import ClientSession, MsgType

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
        self.state = {1:self.state_init,2:self.state_collect,3:self.state_vote}
        self.current_state = 1
        self.joueurs = dict()

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
                    asyncio.ensure_future(self.state[self.current_state](message))

            finally:
                ws.close()


    async def state_init(self,message):
            if message['type'] == 'message' and message['user'] != self.rtm['self']['id']:
                tab_text = message['text'].split(" ")
                if tab_text[0] == 'start':
                    tab_text = tab_text[1:]
                    for i in range(len(tab_text)):
                        #TODO vérifier que les personnes existent
                        self.joueurs[tab_text[i]] = tab_text[i][2:-1]
                    asyncio.ensure_future(self.message_player('Une partie se lance avec : {0}'.format(self.joueurs),message['user']))
                    self.current_state = 2
                else:
                    asyncio.ensure_future(self.message_player('Pour lancer une partie, ecrivez "start @joueur1 @joueur2..."',message['user']))

    async def state_collect(self, message):
        print("Stage 2")

    async def state_vote(self):
            pass

    async def message_player(self,message,player):
        await self.call('chat.postMessage',channel=player,
                    username=self.name,
                    as_user=True,
                    text=message)


if __name__ == "__main__":
    debug = DEBUG

    bot = Bot(TOKEN)

    loop = asyncio.get_event_loop()

    loop.set_debug(debug)
    loop.run_until_complete(bot.connect())
    loop.close()
