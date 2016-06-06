"""Default bot."""
import asyncio
import os
import sys

from .bot import Bot

def main(argv):
    """Le bot."""
    token = os.environ.get('SLACK_TOKEN')

    if not token:
        print("Please configure a SLACK_TOKEN.",
              file=sys.stderr)
        return 1

    bot = Bot(token)
    loop = asyncio.get_event_loop()

    loop.set_debug(debug)
    loop.run_until_complete(bot.connect())
    loop.close()


if __name__ == '__main__':
    sys.exit(main(sys.argv))
