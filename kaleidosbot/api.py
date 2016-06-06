"""
Slack Web API
=============
The `Slack Web API`_ let you communicate with Slack.
Usage:
------
The following example calls the ``api.test`` method which test whether your
token is valid.
.. code-block:: python
    import os
    import asyncio
    from votebot.api import call
    token = os.environ['SLACK_TOKEN']
    loop = asyncio.get_event_loop()
    response = loop.run_until_complete(call('api.test',
                                            token=token))
    print(response)
    loop.close()
.. _Slack Web API: https://api.slack.com/web/
"""

import json
from collections.abc import Mapping

from aiohttp import ClientSession, FormData


async def call(method, file=None, **kwargs):
    """
    Perform an API call to Slack.
    :param file: File pointer
    :type file: file
    :Keyword Arguments:
        All the arguments required by the Slack API.
    :return: JSON response.
    :rtype: dict
    """
    # JSON encode any sub-structure...
    for k, w in kwargs.items():
        # list, tuple or dict but not a str.
        if isinstance(w, (Mapping, list, tuple)):
            kwargs[k] = json.dumps(w)

    form = FormData(kwargs)

    # Handle file upload
    if file:
        form.add_field('file', file)

    with ClientSession() as session:
        async with session.post('https://slack.com/api/{0}'.format(method),
                                data=form) as response:
            assert 200 == response.status, response
            return await response.json()
