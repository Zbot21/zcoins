from typing import Text
from zcoinbase import PublicClient, CoinbaseWebsocket

from zcoins.order_books import CoinbaseMultiProductOrderBook
from zcoins.exchanges import ExchangeProductInfo, Exchange


class CoinbaseExchangeProductInfo(ExchangeProductInfo):
  def __init__(self, url: Text = PublicClient.PROD_URL):
    self.client = PublicClient(rest_url=url)
    self.product_cache = {}

  @classmethod
  def make_product_id(cls, base_currency: Text, quote_currency: Text):
    return '{}-{}'.format(base_currency, quote_currency)

  def _get_product(self, product_id: Text):
    # Get the product from the cache if we have already looked it up.
    if product_id in self.product_cache:
      return self.product_cache[product_id]
    # Populate the cache with the lookup value if we haven't already.
    product = self.client.get_product(product_id)
    self.product_cache[product_id] = product
    return product

  def get_quote_currency(self, product_id: Text):
    return self._get_product(product_id)['quote_currency']

  def get_base_currency(self, product_id: Text):
    return self._get_product(product_id)['base_currency']


class CoinbaseExchange(CoinbaseExchangeProductInfo, Exchange):
  def __init__(self, product_ids: list[Text] = None, rest_url: Text = PublicClient.PROD_URL,
               websocket_addr: Text = CoinbaseWebsocket.PROD_ADDRESS):
    CoinbaseExchangeProductInfo.__init__(self, url=rest_url)
    if product_ids is None:
      product_ids = []
    Exchange.__init__(self, 'Coinbase', CoinbaseMultiProductOrderBook(self, websocket_addr, product_ids))
