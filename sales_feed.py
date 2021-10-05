import asyncio
import logging
import aiohttp
import datetime

from twitter import TwitterBot

class SalesFeed:
    REFRESH_INTERVAL = 200
    API_URL = "https://api.opensea.io/api/v1"
    CONTRACT_ADDRESS = ""
    TWITTER_MIN_USD_SALE_PRICE = 0
    # leave at least 130 chars for the name (max twitter: 280, discord: 2000) (or change max_length in code)
    TWITTER_TEMPLATE = "{tokenid} was just bought for {tokenprice} {tokensymbol} (${usdprice})!\n\n#NFT #OpenSea\n{oslink}"
    TWITTER_BUNDLE_TEMPLATE = "A bundle of {bundlesize} NFTs named \"{bundlename}\" was just bought for {tokenprice} {tokensymbol} (${usdprice})!\n\n#NFT #OpenSea\n{oslink}"

    twitter = None

    def __init__(self):
        self.task = None
        self.aiosession = None

        # remember start time so we can filter out the yats bought before that we haven't stored
        self.startup_time = int(datetime.datetime.now().timestamp())
        self.seen_sale_ids = set()

    def start(self):
        if self.task is not None:
            logging.warning("Couldn't start OpenseaFeeder task: already running")
        logging.info("Starting OpenseaFeeder task")
        loop = asyncio.get_event_loop()
        self.task = loop.create_task(self.run())

    def stop(self):
        logging.info("Stopping OpenseaFeeder task")
        self.task.cancel()

    async def run(self):
        logging.info("OpenseaFeeder task running")
        while True:
            try:
                await self.check_new_sales()
                await asyncio.sleep(self.REFRESH_INTERVAL)
            except asyncio.CancelledError:
                if self.aiosession is not None:
                    await self.aiosession.close()
                self.task = None
                logging.info("Stopped OpenseaFeeder task")
                break
            except Exception as e:
                logging.exception("Error during OpenseaFeeder operation:")
                await asyncio.sleep(5)

    def fill_template(self, template, s):
        token_price = int(s['total_price']) / (10 ** s['payment_token']['decimals'])
        usd_price = round(token_price*float(s['payment_token']['usd_price']))

        if not s.get('asset') and s.get('asset_bundle'):
            bundlename = s['asset_bundle'].get('name', "")
            #bundlename = twitter_sanitize(bundlename, max_length=130)
            return template.format(
                oslink=s['asset_bundle']['permalink'],
                bundlename=bundlename,
                bundlesize=len(s['asset_bundle']['assets']),
                tokenprice=token_price,
                tokensymbol=s['payment_token']['symbol'],
                usdprice=usd_price)

        name = s['asset']['name']
        if not name:
            name = s['asset']['token_id']
        #name = twitter_sanitize(name, max_length=130)
        return template.format(
            oslink=s['asset']['permalink'],
            extlink=s['asset']['external_link'],
            imglink=s['asset']['image_original_url'],
            vidlink=s['asset']['animation_original_url'],
            name=name,
            tokenid=s['asset']['token_id'],
            tokenprice=token_price,
            tokensymbol=s['payment_token']['symbol'],
            usdprice=usd_price)

    async def handle_new_sale(self, s):
        token_price=int(s['total_price']) / (10 ** s['payment_token']['decimals'])
        usd_price = round(token_price*float(s['payment_token']['usd_price']))

        if not s.get('asset') and s.get('asset_bundle'):
            # it's the sale of a bundle
            twitter_txt = self.fill_template(self.TWITTER_BUNDLE_TEMPLATE, s)
        else:
            # normal asset sale
            twitter_txt = self.fill_template(self.TWITTER_TEMPLATE, s)

        if self.twitter and usd_price >= self.TWITTER_MIN_USD_SALE_PRICE:
            # not really async yet but should be at some point (depends on tweepy)
            await self.twitter.send_tweet(twitter_txt)

    async def check_new_sales(self):
        sales = await self.get_events(event_type="successful", occured_after=self.startup_time)
        if sales is False:
            return
        # reverse order and filter out the sales we've already seen
        sales = [sale for sale in sales[::-1] if sale['id'] not in self.seen_sale_ids]
        for sale in sales:
            self.seen_sale_ids.add(sale['id'])
            await self.handle_new_sale(sale)
            await asyncio.sleep(2)

    async def get_events(self, event_type="", occured_after=0):
        """ 
        "   event_type can be 'created' for new auctions, 'successful' for sales, 
        "   'cancelled', 'bid_entered', 'bid_withdrawn', 'transfer', or 'approve'
        """
        s = await self.get_aiosession()
        url = self.API_URL + "/events"
        params = {
            "asset_contract_address": self.CONTRACT_ADDRESS,
            "event_type": event_type,
            "occurred_after": occured_after,
            "limit": 25,
        }
        async with s.get(url, params=params) as r:
            if r.status != 200:
                return False
            json_resp = await r.json()
            return json_resp.get('asset_events')

    async def get_aiosession(self):
        if self.aiosession is not None:
            return self.aiosession
        self.aiosession = aiohttp.ClientSession()
        return self.aiosession

if __name__ == "__main__":
    feed = OpenseaFeeder()
    loop = asyncio.run(feed.run())
