from typing import List, Dict
from game.Card import Card
import random

class Deck:
  def __init__(self, cards: List[Card] = []):
    self.cards = cards[::]
  
  def __len__(self):
    return len(self.cards)
  
  def append(self, card: Card):
    self.cards.append(card)
  
  def extend(self, cards: List[Card]):
    self.cards.extend(cards)
  
  def peek(self) -> Card:
    return self.cards[-1]
  
  def take(self) -> Card:
    card = self.cards[-1]
    self.cards = self.cards[:-1]
    return card
  
  def shuffle(self):
    random.shuffle(self.cards)
  
  @property
  def json(self):
    json_cards = []
    for card in self.cards:
      json_cards.append(card.json)
    return json_cards
  
  def remove_all_by_ids(self, cards: List[str]) -> List[Card]:
    discarded = [card for card in self.cards if card.id in cards]
    self.cards = [card for card in self.cards if card.id not in cards]
    return discarded