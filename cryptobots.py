import logging
import asyncio

from little_uzi_sales_feed import LittleUziSalesFeed
import config

if config.DEBUG:
    logging.basicConfig(level=logging.DEBUG)
else:
    logging.basicConfig(format="%(asctime)s - %(levelname)s - %(name)s: %(message)s", filename="bots.log", level=logging.INFO)

uzifeed = LittleUziSalesFeed()
asyncio.run(uzifeed.run())