from sales_feed import SalesFeed
import config
from twitter import TwitterBot


class LittleUziSalesFeed(SalesFeed):
    CONTRACT_ADDRESS = "0x854df744630c51c782db5c992c621183d9c654cc"
    TWITTER_TEMPLATE = "{tokenid} was just bought for {tokenprice} {tokensymbol} (${usdprice})!\n\n#MyLittleUzi #NFT #OpenSea\n{oslink}"
    TWITTER_BUNDLE_TEMPLATE = "A bundle of {bundlesize} Little Uzis named \"{bundlename}\" was just bought for {tokenprice} {tokensymbol} (${usdprice})!\n\n#MyLittleUzi #NFT #OpenSea\n{oslink}"

    twitter = TwitterBot(config.TWITTER_ACCESS_TOKEN, config.TWITTER_ACCESS_SECRET)