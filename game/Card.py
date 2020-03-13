class Card:
  def __init__(self, suit: str, rank: str, value: int):
    self.rank = rank
    self.suit = suit
    self.value = value
    if suit == 'joker':
      self.id = 'c-{:.1}{}'.format(self.suit.upper(), self.rank)
    else:
      self.id = 'c-{}{:.1}'.format(self.rank, self.suit.upper())

  @property
  def json(self):
    return {
      "rank": self.rank,
      "suit": self.suit,
      "value": self.value
    }