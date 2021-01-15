from __future__ import annotations

from dateutil import parser
import uuid

from threading import Event
from typing import Text, Callable, Union
from zcoinbase import PublicClient, AuthenticatedClient, CoinbaseWebsocket
from zcoinbase import OrderSide as CoinbaseOrderSide

from zcoins.order_books import CoinbaseMultiProductOrderBook
from zcoins.exchanges import ExchangeProductInfo, Exchange, AuthenticatedExchange, Account
from .exchange_data import OrderSide, OrderReport, OrderType, TickerMessage, Product


class CoinbaseExchangeProductInfo(ExchangeProductInfo):
  def __init__(self, client: PublicClient):
    self.client = client
    self.has_requested_all_products = Event()
    self.product_cache = {}

  @classmethod
  def make_from_url(cls, rest_url: Text = PublicClient.PROD_URL) -> CoinbaseExchangeProductInfo:
    return cls(PublicClient(rest_url=rest_url))

  @classmethod
  def make_product_id(cls, base_currency: Text, quote_currency: Text) -> Text:
    return '{}-{}'.format(base_currency, quote_currency)

  @staticmethod
  def _make_product_from_json(json_message: dict) -> Product:
    return Product(product_id=json_message['id'], quote_currency=json_message['quote_currency'],
                   base_currency=json_message['base_currency'])

  def product_matches(self, product_id: Text, product: Product, full_match=False):
    if full_match:
      return self.get_product(product_id) == product
    else:
      return self.get_product(product_id).partial_match(product)

  def get_product(self, product_id: Text) -> Product:
    # Get the product from the cache if we have already looked it up.
    if product_id in self.product_cache:
      return self.product_cache[product_id]
    # Populate the cache with the lookup value if we haven't already.
    product = CoinbaseExchangeProductInfo._make_product_from_json(self.client.get_product(product_id))
    self.product_cache[product_id] = product
    return product

  def get_all_products(self) -> list[Product]:
    """Requests all products from REST client."""
    if not self.has_requested_all_products.is_set():
      self.has_requested_all_products.set()
      products = []
      for product in self.client.get_products():
        self.product_cache[product['product_id']] = CoinbaseExchangeProductInfo._make_product_from_json(product)
        products.append(product)
      return products
    else:
      return list(self.product_cache.values())

  def clear_cache(self):
    self.has_requested_all_products.clear()
    self.product_cache.clear()


class CoinbaseExchange(CoinbaseExchangeProductInfo, Exchange):
  def __init__(self, product_ids: list[Text] = None,
               rest_url: Text = PublicClient.PROD_URL,
               websocket_addr: Text = CoinbaseWebsocket.PROD_ADDRESS):
    self.ticker_callbacks = {}  # This will contain all ticker callbacks by their id.
    if not hasattr(self, 'client'):
      self.client = PublicClient(rest_url=rest_url)
    if not hasattr(self, 'websocket'):
      self.websocket = CoinbaseWebsocket(websocket_addr=websocket_addr)
    self.websocket.add_channel_function('ticker', lambda msg: self._call_ticker_callbacks(msg))
    CoinbaseExchangeProductInfo.__init__(self, client=self.client)
    if product_ids is None:
      product_ids = []
    Exchange.__init__(self, 'Coinbase',
                      CoinbaseMultiProductOrderBook(self, websocket=self.websocket, product_ids=product_ids))

  def add_ticker_callback(self,
                          callback: Callable[[Union[Exchange, AuthenticatedExchange], TickerMessage], None],
                          product_matcher: Product = None) -> Text:
    ticker_id = str(uuid.uuid4())
    self.ticker_callbacks[ticker_id] = Exchange._TickerCallback(callback=callback,
                                                                product_matcher=product_matcher)
    return ticker_id

  def remove_ticker_callback(self, ticker_id: Text):
    if ticker_id in self.ticker_callbacks:
      del self.ticker_callbacks[ticker_id]

  def remove_all_ticker_callbacks(self):
    self.ticker_callbacks.clear()

  def _make_ticker_message(self, raw_ticker_message: dict) -> TickerMessage:
    return TickerMessage(product=self.get_product(raw_ticker_message['product_id']),
                         time=parser.parse(raw_ticker_message['time']),
                         order_side=OrderSide[raw_ticker_message['side'].upper()],
                         last_size=float(raw_ticker_message['last_size']),
                         price=float(raw_ticker_message['price']),
                         best_bid=float(raw_ticker_message['best_bid']),
                         best_ask=float(raw_ticker_message['best_ask']))

  def _call_ticker_callbacks(self, raw_ticker_message: dict):
    ticker_message = self._make_ticker_message(raw_ticker_message)
    for callback in self.ticker_callbacks.values():
      if callback.product_matcher:
        if callback.product_matcher.partial_match(ticker_message.product):
          callback.callback(self, ticker_message)
      else:
        callback.callback(self, ticker_message)


class CoinbaseAuthenticatedExchange(CoinbaseExchange, AuthenticatedExchange):
  def __init__(self, product_ids: list[Text] = None,
               rest_url: Text = PublicClient.PROD_URL,
               websocket_addr: Text = CoinbaseWebsocket.PROD_ADDRESS,
               authenticated_client: AuthenticatedClient = None,
               websocket: CoinbaseWebsocket = None,
               api_key=None, api_secret=None, passphrase=None):
    if authenticated_client:
      self.client = authenticated_client
    else:
      self.client = AuthenticatedClient(rest_url=rest_url, api_key=api_key, api_secret=api_secret,
                                        passphrase=passphrase)
    if websocket:
      self.websocket = websocket
    else:
      self.websocket = CoinbaseWebsocket(websocket_addr=websocket_addr, products_to_listen=product_ids, autostart=False)
    self.websocket.start_websocket_in_thread()
    # Account IDs don't typically change in a session, so we can cache them when a request is made for an account in
    # a currency.
    self._account_id_by_currency = {account['currency']: account['id'] for account in self.client.get_all_accounts()}
    super().__init__(product_ids)

  @staticmethod
  def _translate_order_side(side: OrderSide):
    return CoinbaseOrderSide.BUY if side is OrderSide.BUY else CoinbaseOrderSide.SELL

  def cancel_order(self, order_id: Text, product_id: Text = None):
    return self.client.cancel_order(order_id=order_id, product_id=product_id)

  @staticmethod
  def _translate_to_order_report(json_response) -> OrderReport:
    pass

  def limit_order(self, product_id: Text, side: OrderSide, price, size) -> OrderReport:
    order_response = self.client.limit_order(product_id=product_id,
                              side=CoinbaseAuthenticatedExchange._translate_order_side(
                                side), price=price,
                              size=size)

  def market_order(self, product_id: Text, side: OrderSide, size=None, funds=None) -> OrderReport:
    return CoinbaseAuthenticatedExchange._translate_to_order_report(
      self.client.market_order(product_id=product_id,
                               side=CoinbaseAuthenticatedExchange._translate_order_side(
                                 side),
                               size=size, funds=funds))

  @staticmethod
  def _response_to_account(json_response) -> Account:
    return Account(account_id=json_response['id'],
                   currency=json_response['currency'],
                   balance=float(json_response['balance']),
                   hold=float(json_response['hold']),
                   available=float(json_response['available']))

  def get_all_accounts(self) -> list[Account]:
    return [CoinbaseAuthenticatedExchange._response_to_account(account) for account in self.client.get_all_accounts()]

  def get_account(self, currency: Text = None, account_id: Text = None) -> Account:
    if currency and account_id:
      raise ValueError('it is invalid to specify both currency and account id.')
    if currency:
      if currency in self._account_id_by_currency:
        account_id = self._account_id_by_currency[currency]
      else:
        raise ValueError('{} is not a valid currency in CoinbasePro.'.format(currency))
    return CoinbaseAuthenticatedExchange._response_to_account(self.client.get_account(account_id=account_id))

