"""
    Various move classes for cataloging move history
    Author: Jakob Wachter
    Last Modified: 27/10/2022
"""
from typing import List

from action_event import ActionEvent, BidAction, PassAction, DeclareContractAction, DeclareModifierAction, FinishContractAction, PlayCardAction
from skat_card import SkatCard

from ..player import SkatPlayer
from ..dealer import SkatDealer

class SkatMove(object):
    pass

class PlayerMove(SkatMove):
    def __init__(self, player: SkatPlayer, action: ActionEvent):
        super().__init__()
        self.player = player
        self.action = action
        
class CallMove(PlayerMove):
    def __init__(self, player: SkatPlayer, action: ActionEvent):
        super().__init__(player=player, action=action)
        
class DeclareMove(PlayerMove):
    def __init__(self, player: SkatPlayer, action: ActionEvent):
        super().__init__(player=player, action=action)
        
class BidMove(CallMove):
    def __init__(self, player: SkatPlayer, bid_action: BidAction):
        super().__init__(player=player, action=bid_action)
        self.action = bid_action
        
    def __str__(self):
        return f'{self.player} bids {self.action}'
    
class MakePassMove(CallMove):
    def __init__(self, player: SkatPlayer):
        super().__init__(player=player, action=PassAction())

    def __str__(self):
        return f'{self.player} passes'
        
class DeclareContractMove(DeclareMove):
    def __init__(self, player: SkatPlayer, declare_action: DeclareContractAction):
        super().__init__(player=player, action=declare_action)
        self.action = declare_action
        
    def __str__(self):
        return f'{self.player} declares contract {self.action}'
        
class DeclareModifierMove(DeclareMove):
    def __init__(self, player: SkatPlayer, declare_action: DeclareModifierAction):
        super().__init__(player=player, action=declare_action)
        self.action = declare_action
        
    def __str__(self):
        return f'{self.player} declares modifier {self.action}'
    
class FinishContractMove(DeclareMove):
    def __init__(self, player: SkatPlayer, finish_action: FinishContractAction):
        super().__init__(player=player, action=finish_action)
        self.action = finish_action
        
    def __str__(self):
        return f'{self.player} finishes declarations'
        
class DealHandMove(SkatMove):
    def __init__(self, dealer: SkatPlayer, shuffled_deck: List[SkatCard]):
        super().__init__()
        self.dealer = dealer
        self.shuffled_deck = shuffled_deck
        
    def __str__(self):
        shuffled_deck_text = " ".join([str(card) for card in self.shuffled_deck])
        return f'{self.dealer} deals shuffled_deck=[{shuffled_deck_text}]'
    
class PlayCardMove(PlayerMove):
    def __init__(self, player: SkatPlayer, action: PlayCardAction):
        super().__init__(player=player, action=action)
        self.action = action
        
    @property
    def card(self):
        return self.action.card
    
    def __str__(self):
        return f'{self.player} plays {self.action}'
