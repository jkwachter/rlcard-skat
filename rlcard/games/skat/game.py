"""
    SkatGame class
    Author: Jakob Wachter
    Last Modified: 11/2/2022
"""

from typing import List

import numpy as np

from judger import SkatJudger
from round import SkatRound
from utils.action_event import ActionEvent, CallAction, DeclareAction, PlayCardAction

class SkatGame:
    ''' Game class designed to interact with the outer environment
    '''
    
    def __init__(self, allow_step_back=False):
        '''Initialize the SkatGame class
        '''
        self.allow_step_back: bool = allow_step_back
        self.np_random = np.random.default_rng()
        self.judger: SkatJudger = SkatJudger(game=self)
        self.actions: List[ActionEvent] = []
        self.round: SkatRound or None = None
        self.num_players: int = 3
        
    def init_game(self):
        ''' Initialize all the characters in the game and start round 1
        '''
        board_id = self.np_random.choice([0, 1, 2])
        self.actions: List[ActionEvent] = []
        self.round = SkatRound(num_players=self.num_players, dealer_id=board_id, np_random=self.np_random)
        # perform skat-like dealing of cards
        for cycle in range(3):
            if (cycle % 2 == 1): 
                self.round.dealer.make_skat()
            card_amt = 4 if (cycle % 2 == 1) else 3
            for player_id in range(3):
                player = self.round.players[player_id]
                self.round.dealer.deal_cards(player=player, num=card_amt)
        current_player_id = self.round.current_player_id
        state = self.get_state(player_id=current_player_id)
        return state, current_player_id
    
    def step(self, action: ActionEvent):
        '''Perform appropriate game action and return the next player number with their state
        '''
        if isinstance(action, CallAction):
            self.round.place_bid(action=action)
        elif isinstance(action, DeclareAction):
            self.round.declare(action=action)
        elif isinstance(action, PlayCardAction):
            self.round.play_card(action=action)
        else:
            raise Exception(f'Unknown action={action}')
        self.actions.append(action)
        next_player_id = self.round.current_player_id
        next_state = self.get_state(player_id=next_player_id)
        return next_state, next_player_id
    
    @staticmethod
    def get_num_actions() -> int:
        ''' Return the number of possible actions in the game
        '''
        return ActionEvent.get_num_actions()

    def get_player_id(self):
        ''' Return the current player that will take actions soon
        '''
        return self.round.current_player_id

    def is_over(self) -> bool:
        ''' Return whether the current game is over
        '''
        return self.round.is_round_over()
    
    def get_state(self, player_id: int):
        pass

