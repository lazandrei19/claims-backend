from typing import List, Dict
from game.Deck import Deck
from game.Card import Card
import random

from flask_socketio import emit

ranks = [('A', 1), ('2', 2), ('3', 3), ('4', 4), ('5', 5), ('6', 6), ('7', 7),
              ('8', 8), ('9', 9), ('10', 10), ('J', 12), ('Q', 13), ('K', 14)]
suits = ['diams', 'hearts', 'spades', 'clubs']
cards: List[Card] = []

for rank in ranks:
  for suit in suits:
    cards.append(Card(suit, rank[0], rank[1]))
cards.append(Card('joker', '+', 0))
cards.append(Card('joker', '-', 0))

def get_card_value(card: Card, trump: Card):
  if card.rank == trump.rank:
    return 0
  return card.value

class Player:
  username: str
  uuid: str
  hand: Deck
  score = 0

  def __init__(self, username: str, uuid: str):
    self.username = username
    self.uuid = uuid
    self.hand = Deck()

class Game:
  players: Dict[str, Player]
  draw_pile: Deck
  discard_pile: Deck
  trump_card: Card = None
  room_id: str
  player_ids: List[str]
  index = 0

  def __init__(self, room_id: str):
    self.players = {}
    self.draw_pile = Deck()
    self.discard_pile = Deck()
    self.room_id = room_id


  @property
  def game_players(self):
    players = []
    for uuid, player in self.players.items():
      players.append({"uuid": uuid, "username": player.username})
    return players
  
  def has_player(self, username: str) -> bool:
    for player in self.players.values():
      if player.username == username:
        return True
    return False

  def add_player(self, uuid, username):
    self.players[uuid] = Player(username, uuid)

  #TODO: handle client disconnect mid-game
  def remove_player(self, uuid):
    del self.players[uuid]

  def new_game(self):
    self.player_ids = list(self.players.keys())
    random.shuffle(self.player_ids)
    self.start()

  def start(self):
    self.discard_pile = Deck()
    self.draw_pile = Deck(cards)
    self.draw_pile.shuffle()
    hands: Dict[str, Deck] = {}
    for player in self.players.values():
      hands[player.uuid] = Deck()
    for i in range(5):
      for player in self.players.values():
        hands[player.uuid].append(self.draw_pile.take())
    card_a = self.draw_pile.take()
    card_b = self.draw_pile.take()
    if card_a.value > card_b.value:
      self.trump_card = card_a
      self.discard_pile.append(card_b)
    else:
      self.trump_card = card_b
      self.discard_pile.append(card_a)
    for player in self.players.values():
      emit('startGame', {
        "hand": hands[player.uuid].json,
        "trumpCard": self.trump_card.json,
        "discardPile": self.discard_pile.json
      }, json=True, room=player.uuid)
      self.players[player.uuid].hand = hands[player.uuid]
    emit('player', self.player_ids[self.index], room=self.room_id)
  
  def move(self, player_id: str, cards: List[str], pile: str):
    discarded_cards = self.players[player_id].hand.remove_all_by_ids(cards)
    if pile == 'discard':
      self.players[player_id].hand.append(self.discard_pile.peek())
      emit('drawCard', self.discard_pile.take().json, json=True, room=player_id)
    elif len(self.draw_pile) > 0:
      self.players[player_id].hand.append(self.draw_pile.peek())
      emit('drawCard', self.draw_pile.take().json, json=True, room=player_id)
    else:
      self.discard_pile.extend(discarded_cards)
      discarded_cards = []
      top_card = self.discard_pile.take()
      self.draw_pile = self.discard_pile
      self.draw_pile.shuffle()
      self.discard_pile = Deck([top_card])
      emit('drawCard', self.draw_pile.take().json, json=True, room=player_id)
      pass
    self.discard_pile.extend(discarded_cards)
    emit('discardPile', self.discard_pile.json, json=True, room=self.room_id)
    self.index = (self.index + 1) % len(self.player_ids)
    emit('player', self.player_ids[self.index], room=self.room_id)
    self.update_players_cards()
    print('Remaining: ', len(self.draw_pile))
  
  def update_players_cards(self):
    players_hands: Dict[str, int] = {}
    for player in self.player_ids:
      players_hands[player] = len(self.players[player].hand)
    emit('playerHands', players_hands, json=True, room=self.room_id)
  
  def claims(self, player_id: str):
    hand_scores: Dict[str, int] = {}
    for player in self.player_ids:
      hand_scores[player] = self.calculate_hand_score(player)
    
    winner = player_id

    for uuid, score in hand_scores.items():
      if score <= hand_scores[winner] and uuid != winner:
        winner = uuid
    
    if winner != player_id:
      self.players[player_id].score += 75
    
    scores: Dict[str, int] = {}

    for uuid, score in hand_scores.items():
      if score != hand_scores[winner] and uuid != player_id:
        self.players[uuid].score += score
      
      scores[uuid] = self.players[uuid].score
    
    emit('playerScores', scores, json=True, room=self.room_id)
    emit('newGame', room=self.room_id)
    
    self.index = self.player_ids.index(winner)
    self.start()
  
  def calculate_hand_score(self, player_id: str):
    score = 0
    
    for card in self.players[player_id].hand.cards:
      if card.rank != self.trump_card.rank:
        score += card.value
    
    return score