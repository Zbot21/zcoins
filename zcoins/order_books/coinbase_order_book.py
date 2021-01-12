from typing import Text
from zcoinbase import ProductOrderBook, CoinbaseOrderBook, CoinbaseWebsocket, PublicClient

from zcoins.exchanges import ExchangeProductInfo
from zcoins.order_books import SingleProductOrderBook, MultiProductOrderBook


class _CoinbaseSingleProductOrderBook(SingleProductOrderBook):
  def __init__(self, product_id: Text, base_currency: Text, quote_currency: Text, product_order_book: ProductOrderBook):
    super().__init__(product_id, base_currency, quote_currency)
    self.product_order_book = product_order_book

  def get_bids(self, top_n: int = None):
    return self.product_order_book.get_bids(top_n)

  def get_asks(self, top_n: int = None):
    return self.product_order_book.get_asks(top_n)


class CoinbaseMultiProductOrderBook(MultiProductOrderBook):
  def __init__(self, exchange: ExchangeProductInfo,
               websocket_addr=CoinbaseWebsocket.PROD_ADDRESS,
               websocket: CoinbaseWebsocket = None,
               product_ids: list[Text] = None):
    """Initializes the MultiProductOrderBook tracking Coinbase products.

    If a websocket is supplied, this class *expects* that websocket will already be open, or this class will wait until
    it is Open.
    """
    self.exchange = exchange
    if product_ids is None:
      product_ids = []
    super().__init__(product_ids=product_ids)
    if websocket is not None:
      self.internal_order_book = CoinbaseOrderBook(websocket)
      websocket.wait_for_open()
    else:
      self.internal_order_book = CoinbaseOrderBook.make_order_book(product_ids=product_ids,
                                                                   websocket_addr=websocket_addr)
    self._post_subclass_init()

  def make_single_product_order_book(self, product_id: Text) -> SingleProductOrderBook:
    return self.make_multiple_product_order_book([product_id])[0]

  def make_multiple_product_order_book(self, product_ids: list[Text]) -> list[SingleProductOrderBook]:
    self.internal_order_book.add_order_books(product_ids)
    order_books = []
    for product_id in product_ids:
      order_books.append(_CoinbaseSingleProductOrderBook(product_id, self.exchange.get_base_currency(product_id),
                                                         self.exchange.get_quote_currency(product_id),
                                                         self.internal_order_book.get_order_book(product_id)))
    return order_books
