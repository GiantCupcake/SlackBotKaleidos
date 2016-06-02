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
        self.name = 'BotKaleidos'
        self.timeout = timeout or 60
        self.future = asyncio.Future()
        self.queue = asyncio.Queue()
        self.log = logging.getLogger(str(self))
        self.rtm = None

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
                    print(message)
                    response = await self.call('chat.postMessage',
                                                    channel=self.channel_id,
                                                    username=self.name,
                                                    text=message)
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
