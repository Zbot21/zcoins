# This class contains the data-types exchanges use to communicate account data.

from dataclasses import dataclass
from datetime import datetime
from typing import Text


@dataclass
class Account:
  account_id: Text  # The exchange-specific account_id (usually used to look up an account by it's ID)
  currency: Text  # The currency of the account.
  balance: float  # Current balance of the account.
  hold: float  # The balance that is unavailable due to holds (usually means the funds are already in an order)
  available: float  # The
