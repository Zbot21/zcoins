# This file contains the interface that should be implemented by an exchange.
from abc import ABC, abstractmethod
from typing import Text


class ExchangeProductInfo(ABC):
  @classmethod
  @abstractmethod
  def make_product_id(cls, base_currency, quote_currency):
    pass

  @abstractmethod
  def get_quote_currency(self, product_id: Text):
    """Given a product_id, return the quote_currency."""
    pass

  @abstractmethod
  def get_base_currency(self, product_id: Text):
    """Given a product_id, return the base_currency."""
    pass


class Exchange(ExchangeProductInfo, ABC):
  """Contains information about an exchange."""
  def __init__(self, name: Text, order_books):
    self.name = name
    self.order_books = order_books

  def get_product_ids(self):
    """Get all product ids available on this exchange, this is not necessarily all *available* products, but only the
    products that are being tracked by the MultiProductOrderBook contained in this Exchange."""
    return self.order_books

  def add_order_book(self, product_id: Text):
    return self.order_books.add_order_book(product_id)

  def get_all_order_books(self):
    """Returns a MultiProductOrderBook representing all products that are currently being followed."""
    return self.order_books

  def get_order_book(self, product_id):
    """Returns a SingleProductOrderBook for the given product_id."""
    return self.order_books.get_order_book(product_id)

  def get_order_book_by_base_currency(self, base_currency):
    """Returns a dict of SingleProductOrderBook using base_currency keyed by quote_currency."""
    return self.order_books.get_order_books_by_base_currency(base_currency)

  def get_order_book_by_quote_currency(self, quote_currency):
    """Returns a dict of SingleProductOrderBook using quote_currency, keyed by base_currency."""
    return self.order_books.get_order_books_by_quote_currency(quote_currency)

  def get_order_book_by_currencies(self, base_currency, quote_currency):
    """Returns a SingleProductOrderBook for the given base and quote currencies."""
    return self.get_order_book(self.make_product_id(base_currency=base_currency, quote_currency=quote_currency))
