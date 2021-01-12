# This class contains the data-types that exchanges should use to communicate with their users.
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Text


@dataclass
class Product:
  product_id: Text = None
  quote_currency: Text = None
  base_currency: Text = None

  def partial_match(self, other_product: Product):
    """Returns true if any fields match."""
    if self.product_id and other_product.product_id and self.product_id == other_product.product_id:
      return True
    if self.quote_currency and other_product.quote_currency and self.quote_currency == other_product.quote_currency:
      return True
    if self.base_currency and other_product.base_currency and self.base_currency == other_product.base_currency:
      return True
    return False

  def __repr__(self):
    return self.product_id

  def __str__(self):
    return 'id: {} base: {} quote: {}'.format(self.product_id, self.base_currency, self.quote_currency)


class OrderSide(Enum):
  BUY = 'buy'
  SELL = 'sell'


class OrderType(Enum):
  MARKET = 'market'
  LIMIT = 'limit'
  STOP = 'stop'


@dataclass
class OrderReport:
  """Contains information about an order from an exchange."""
  order_id: Text
  product: Product
  order_side: OrderSide
  order_type: OrderType
  size: float
  # TODO: Finish this.


@dataclass
class TickerMessage:
  product: Product
  time: datetime
  order_side: OrderSide
  last_size: float
  price: float
  best_bid: float
  best_ask: float

  def __repr__(self):
    return '{product_id}: {time}: {side} {size} @ {price}' \
      .format(product_id=self.product.product_id,
              time=self.time.isoformat(),
              side=self.order_side.value.upper(),
              size=self.last_size,
              price=self.price)
