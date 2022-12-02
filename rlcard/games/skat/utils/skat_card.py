"""
    SkatCard class
    Author: Jakob Wachter
    Last Modified: 27/10/2022
"""

from typing import List
from rlcard.games.base import Card

class SkatCard(Card):
    ''' A Card wrapper with some added utilities for getting cards of a specific rank and suit
        based off of the BridgeCard source
    '''
    suits = ['D', 'H', 'S', 'C']
    ranks = ['7', '8', '9', 'T', 'J', 'Q', 'K', 'A']
    
    @staticmethod
    def card(card_id: int):
        ''' Get the card associated with a specific card id
        
        Args:
            card_id: Id of the card to look for (int)
            
        Returns:
            (Card): Card associated with the given id
        '''
        return _deck[card_id]
    
    @staticmethod
    def get_deck() -> List[Card]:
        ''' Get a copy of the unshuffled Skat deck
        
        Returns:
            (List[Card]): The unshuffled Skat deck
        '''
        return _deck.copy()
    
    @staticmethod
    def get_rank(rank: int) -> List[Card]:
        ''' Get all of the cards of a specific rank
        
        Args:
            rank: The rank of card desired, integer
        
        Returns:
            (List[Card]): Every card of that rank in the Skat deck
        '''
        return [_deck[rank+8*i] for i in range(4)]
    
    @staticmethod
    def get_suit(suit: int) -> List[Card]:
        ''' Get all of the cards of a specific suit
        
        Args:
            suit: The suit of card desired, integer
        
        Returns:
            (List[Card]): Every card of that suit in the Skat deck
        '''
        return [_deck[i+8*suit] for i in range(8)]

    def __init__(self, suit: str, rank: str):
        ''' Initialize a SkatCard
        '''
        super().__init__(suit=suit, rank=rank)
        (suit_i, rank_i) = (SkatCard.suits.index(self.suit), SkatCard.ranks.index(self.rank))
        self.card_id = rank_i + 8*suit_i

    def __str__(self):
        return f'{self.rank}{self.suit}'

    def __repr__(self):
        return f'{self.rank}{self.suit}'

# Static reference to the unstructured deck
_deck = [SkatCard(suit=suit, rank=rank) for suit in SkatCard.suits for rank in SkatCard.ranks]