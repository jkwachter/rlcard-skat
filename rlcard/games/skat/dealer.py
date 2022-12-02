"""
    SkatDealer class
    Author: Jakob Wachter
    Last Modified: 27/10/2022
"""

from typing import List

from rlcard.games.base import Card
from .player import SkatPlayer
from .utils import utils as utils

class SkatDealer:
    ''' Initialize a dealer for the game of Skat
        The dealer is a service that handles the movement of cards during play
        Each round, a player assumes the role of the dealer, which determines bidding order
    '''
    def __init__(self, dealer_id: int, np_random):
        self.np_random = np_random
        # associated id
        self.dealer_id = dealer_id
        # shuffled deck for use in dealing
        self.shuffled_deck: List[Card] = utils.generate_deck()
        self.np_random.shuffle(self.shuffled_deck)
        # skat made during dealing
        self.skat: List[Card] = []
        # 
        self.deck: List[Card] = self.shuffled_deck.copy()

    def deal_cards(self, player: SkatPlayer, num: int):
        '''Deal [num] cards from deck to player

        Args:
            player (SkatPlayer): The player to deal cards to
            num (int): The number of cards to deal to that player
        '''
        for _ in range(num):
            player.hand.append(self.deck.pop())
    
    def make_skat(self):
        ''' Make the Skat for the round
        '''
        for _ in range(2):
            self.skat.append(self.deck.pop())
