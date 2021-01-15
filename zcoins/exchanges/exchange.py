# This file contains the interface that should be implemented by an exchange.
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Text, Callable, Union

from zcoins.exchanges import OrderSide, OrderReport, OrderType, Product, TickerMessage
from zcoins.exchanges import Account

class ExchangeProductInfo(ABC):
  @classmethod
  @abstractmethod
  def make_product_id(cls, base_currency, quote_currency) -> Text:
    pass

  def get_quote_currency(self, product_id: Text) -> Text:
    """Given a product_id, return the quote_currency."""
    return self.get_product(product_id).quote_currency

  def get_base_currency(self, product_id: Text) -> Text:
    """Given a product_id, return the base_currency."""
    return self.get_product(product_id).base_currency

  @abstractmethod
  def get_all_products(self) -> list[Product]:
    pass

  @abstractmethod
  def get_product(self, product_id: Text) -> Product:
    pass


class Exchange(ExchangeProductInfo, ABC):
  """Contains information about an exchange."""

  def __init__(self, name: Text, order_books):
    self.name = name
    self.order_books = order_books

  @dataclass
  class _TickerCallback:
    callback: Callable[[Union[Exchange, AuthenticatedExchange], TickerMessage], None]
    product_matcher: Product = None  # By Default, this matches all products.

  @abstractmethod
  def add_ticker_callback(self, callback: Callable[[Exchange, TickerMessage], None]) -> Text:
    """Adds a callback function to this exchange."""

  def get_product_ids(self):
    """Get all product ids available on this exchange, this is not necessarily all *available* products, but only the
    products that are being tracked by the MultiProductOrderBook contained in this Exchange."""
    return self.order_books

  def add_order_book(self, product_id: Text):
    """Adds an order book"""
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


class AuthenticatedExchange(Exchange, ABC):
  """Contains an exchange that you can make trades on."""

  def __init__(self, name: Text, order_books):
    super().__init__(name, order_books)

  @abstractmethod
  def get_all_accounts(self) -> list[Account]:
    """Get all the 'accounts' (currency balances) on this exchange."""
    pass

  @abstractmethod
  def get_account(self, currency: Text = None, account_id: Text = None) -> Account:
    """Can get an account either by account_id or by the currency, it's invalid to specify both."""
    pass

  @abstractmethod
  def cancel_order(self, order_id: Text, product_id: Text = None):
    """Cancel an order with exchange-provided order id."""
    pass

  @abstractmethod
  def limit_order(self, product_id: Text, side: OrderSide, price, size) -> OrderReport:
    """Posts a limit order."""
    pass

  @abstractmethod
  def market_order(self, product_id: Text, side: OrderSide, size=None, funds=None) -> OrderReport:
    """Posts a market order."""
    pass
