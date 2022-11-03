'''
    SkatPlayer class
    Author: Jakob Wachter
    Last modified: 11/2/2022
'''


from typing import List

from utils.skat_card import SkatCard

class SkatPlayer:
    def __init__(self, player_id: int, np_random):
        self.np_random = np_random
        self.player_id: int = player_id
        self.hand: List[SkatCard] = []
        self.played_cards = []
        
    def __eq__(self, other):
        if isinstance(other, SkatPlayer):
            return self.player_id == other.player_id
        return False
    
    def remove_card(self, card: SkatCard):
        self.hand.remove(card)
        
    def get_state_shape_size(self) -> int:
        sz = 0
        # Need to account for:
        sz += 10*32 # Hand representation (3*32)
        # Trick representation (3*32)
        # Won cards representation (3*32)
        # Hidden cards (32)
        sz += 13 # Contract representation (13)
        sz += 63 # Bid representation (63)
        sz += 2*3 # Dealer representation (3)
        # Current player representation (3)
        sz += 4 # Game phase representation (4)
        return sz
    
    
        