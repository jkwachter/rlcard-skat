"""
    SkatCard class
    Author: Jakob Wachter
    Last Modified: 27/10/2022
"""

from typing import List
from rlcard.games.base import Card

class SkatCard(Card):
    suits = ['D', 'H', 'S', 'C']
    ranks = ['7', '8', '9', 'T', 'J', 'Q', 'K', 'A']
    
    @staticmethod
    def card(card_id: int):
        return _deck[card_id]
    
    @staticmethod
    def get_deck() -> List[Card]:
        return _deck.copy()
    
    @staticmethod
    def get_rank(rank: int) -> List[Card]:
        return [_deck[rank+8*i] for i in range(4)]
    
    @staticmethod
    def get_suit(suit: int) -> List[Card]:
        return [_deck[i+8*suit] for i in range(8)]

    def __init__(self, suit: str, rank: str):
        super().__init__(suit=suit, rank=rank)
        (suit_i, rank_i) = (SkatCard.suits.index(self.suit), SkatCard.suits.index(self.rank))
        self.card_id = rank_i + 8*suit_i

    def __str__(self):
        return f'{self.rank}{self.suit}'

    def __repr__(self):
        return f'{self.rank}{self.suit}'

_deck = [SkatCard(suit=suit, rank=rank) for suit in SkatCard.suits for rank in SkatCard.ranks]