"""Slack Bot that prints on the console."""
import asyncio
import json
import logging

from aiohttp import ClientSession, MsgType

from api.api import call
from config.config import *


class Bot:
    """Play Kaleidos with your friends"""
    #Regler ces histoires de channel, envoyer des mesages perso
    def __init__(self,token,*args,channel=None,timeout=None):
        self.__token = token
        self.channel = channel
        self.channel_id = None
        self.name = 'casser_des_culs'
        self.timeout = timeout or 60
        self.future = asyncio.Future()
        self.queue = asyncio.Queue()
        self.log = logging.getLogger(str(self))
        self.rtm = None

        self.joueurs = dict()

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


    async def _run(self):
        self.rtm = await self.call('rtm.start')

        if not self.rtm['ok']:
            self.future.set_result(ValueError(self.rtm['error']))

        for c in self.rtm['channels']:
            if c['name'] == self.channel:
                self.channel_id = c['id']
                break

        for g in self.rtm['groups']:
            if g['name'] == self.channel:
                self.channel_id = g['id']
                break

        asyncio.ensure_future(self._consume())
        asyncio.ensure_future(self.state_listen())

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
                    if message['type'] == 'message' and message['user'] != self.rtm['self']['id']:
                        tab_text = message['text'].split(" ")
                        print(tab_text)
                        if tab_text[0] == 'start':
                            tab_text = tab_text[1:]
                            print(tab_text)
                            for i in range(len(tab_text)):
                                self.joueurs[tab_text[i]] = tab_text[i][2:-1]
                            await self.call('chat.postMessage',channel=message['user'],
                                        username=self.name,
                                        as_user=True,
                                        text='Une partie se lance avec : {0}'.format(self.joueurs))
                        else:
                            await self.call('chat.postMessage',channel=message['user'],
                                        username=self.name,
                                        as_user=True,
                                        text='Pour lancer une partie, ecrivez "start @joueur1 @joueur2..."')
                    await self.queue.put(message)
            finally:
                ws.close()

    async def _consume(self):
        while True:
            message = await self.queue.get()




if __name__ == "__main__":
    channel = 'inf-arc'
    debug = DEBUG

    logging.basicConfig(level=logging.INFO)


    bot = Bot(TOKEN)

    loop = asyncio.get_event_loop()

    loop.set_debug(debug)
    loop.run_until_complete(bot.connect())
    loop.close()
