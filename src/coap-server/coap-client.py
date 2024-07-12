import asyncio
import logging
import os

from aiocoap import *

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)

coap_uri = os.environ['COAP_SERVER_URI']
coap_clients = int(os.environ['COAP_CLIENTS'])


async def main():
    """Perform a single PUT request to localhost on the default port, URI
    "/other/block". The request is sent 2 seconds after initialization.

    The payload is bigger than 1kB, and thus sent as several blocks."""

    context = await Context.create_client_context()

    await asyncio.sleep(2)

    # payload = b"The quick brown fox jumps over the lazy dog.\n" * 30

    while True:
        for i in range(coap_clients):
            payload = b"Request received.\n"

            request = Message(code=PUT, payload=payload, uri=f"coap://{coap_uri}/other/block")

            response = await context.request(request).response

            logging.info('Result: %s\n%r' % (response.code, response.payload))

        await asyncio.sleep(30)


if __name__ == "__main__":
    asyncio.run(main())
