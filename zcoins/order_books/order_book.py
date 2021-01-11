# This file contains the interfaces that can be used for any order-book on the zcoins platform.

from abc import ABC, abstractmethod
from collections import defaultdict
from typing import Text


class SingleProductOrderBook(ABC):
  """Contains the order-book for a single product."""
  def __init__(self, product_id: Text, base_currency: Text, quote_currency: Text):
    """An order-book interface for a single product.

    Args:
      product_id (Text): The exchange-specific product_id.
      base_currency (Text): The standard code for a currency (ISO4217 if the currency is a non-crypto)
      quote_currency (Text): The standard code for a currency (ISO4217 if the currency is a non-crypto)
    """
    self.product_id = product_id
    self.base_currency = base_currency
    self.quote_currency = quote_currency

  @abstractmethod
  def get_bids(self, top_n: int = None):
    """Returns a list of (price, size) tuples, representing the current bids order-book.
    Prices are in quote_currency.
    Results are sorted from high-to-low by price.

    Example Result:
      [(1.06, 3), (1.05, 2), (1.00, 5)]

    Args:
      top_n (int): Controls the number of results that should be returned. May return less if top_n is greater than the
                   size of the current order book.
    """
    pass

  @abstractmethod
  def get_asks(self, top_n: int = None):
    """Returns a list of (price, size) tuples, representing the current asks order-book.
    Prices are in quote_currency.
    Results are sorted from low-to-high by price.

    Example Result:
      [(1.00, 5), (1.05, 2), (1.06, 3)]

    Args:
      top_n (int): Controls the number of results that should be returned. May return less if top_n is greater than the
                   size of the current order book.
    """
    pass

  def get_book(self, top_n: int = None):
    """Returns the results of get_bids and get_asks in a single dict with keys 'bids' and 'asks'.

    Example Result:
      {
        'bids': [(1.06, 3), (1.05, 2), (1.00, 5)],
        'asks': [(1.00, 5), (1.05, 2), (1.06, 3)]
      }

    """
    return {
      'bids': self.get_bids(top_n=top_n),
      'asks': self.get_asks(top_n=top_n)
    }


class MultiProductOrderBook(ABC):
  """Contains the order-books for many products on the same exchange."""
  def __init__(self, product_ids: list[Text] = None):
    if product_ids is None:
      product_ids = []
    self._order_books = {}
    self._order_books_by_quote_currency = defaultdict(list)
    self._order_books_by_base_currency = defaultdict(list)
    self.product_ids = product_ids

  def _post_subclass_init(self):
    self.add_order_books(self.product_ids)

  def add_order_book(self, product_id) -> SingleProductOrderBook:
    return self.add_order_books([product_id])[0]

  def add_order_books(self, product_ids: list[Text]) -> list[SingleProductOrderBook]:
    books = self.make_multiple_product_order_book(product_ids)
    for idx in range(len(books)):
      product_id = product_ids[idx]
      ob = books[idx]
      self._order_books[product_id] = ob
      self._order_books_by_base_currency[ob.base_currency].append(ob)
      self._order_books_by_quote_currency[ob.quote_currency].append(ob)
    return books

  def get_order_book(self, product_id) -> SingleProductOrderBook:
    return self._order_books[product_id]

  def get_order_books_by_quote_currency(self, quote_currency) -> list[SingleProductOrderBook]:
    return self._order_books_by_quote_currency[quote_currency]

  def get_order_books_by_base_currency(self, base_currency) -> list[SingleProductOrderBook]:
    return self._order_books_by_base_currency[base_currency]

  def get_tracked_products(self):
    return self._order_books.keys()

  @abstractmethod
  def make_single_product_order_book(self, product_id: Text) -> SingleProductOrderBook:
    """Create a SingleProductOrderBook for the given product_id."""
    pass

  def make_multiple_product_order_book(self, product_ids: list[Text]) -> list[SingleProductOrderBook]:
    """Default implementation, you might want to override this to make it more efficient."""
    order_books = []
    for product_id in product_ids:
      order_books.append(self.make_single_product_order_book(product_id))
    return order_books
