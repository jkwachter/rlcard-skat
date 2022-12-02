'''
    SkatPlayer class
    Author: Jakob Wachter
    Last modified: 11/2/2022
'''


from typing import List

from .utils.skat_card import SkatCard

class SkatPlayer:
    '''Representation of a player of a given game of Skat
    '''

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
        '''Remove a given card from the player's hand

        Args:
            card: The card to remove
        '''
        self.hand.remove(card)
