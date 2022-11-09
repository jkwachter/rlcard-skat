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
    ''' The Game class is designed to interface with the SkatEnv, providing information about the
        state and the actions in the game. 
    '''
    
    def __init__(self, allow_step_back=False):
        '''Initialize the SkatGame class
        '''
        ## Value provided by the environment during training
        self.allow_step_back: bool = allow_step_back
        self.np_random = np.random.default_rng()
        ## Judger for determining round payoffs, legal actions, and if a game has won
        self.judger: SkatJudger = SkatJudger(game=self)
        # List of currently admissible actions for the associated state
        self.actions: List[ActionEvent] = []
        # Current round associated with the game
        self.round: SkatRound or None = None
        # Number of players, fixed quantity usually (though there are rules for 4, the dealer sits out)
        self.num_players: int = 3
        
    def init_game(self):
        ''' Initialize all the characters in the game and start round 1
        '''
        ## Start with a random dealer
        board_id = self.np_random.choice([0, 1, 2])
        ## No legal actions yet
        self.actions: List[ActionEvent] = []
        ## Initialize a round with associated parameters
        self.round = SkatRound(num_players=self.num_players, dealer_id=board_id, np_random=self.np_random)
        # perform skat-like dealing of cards
        for cycle in range(3):
            if (cycle % 2 == 1):
                self.round.dealer.make_skat()
            card_amt = 4 if (cycle % 2 == 1) else 3
            for player_id in range(3):
                player = self.round.players[player_id]
                self.round.dealer.deal_cards(player=player, num=card_amt)
        # get the starting state for the player
        current_player_id = self.round.current_player_id
        state = self.get_state()
        return state, current_player_id
    
    def step(self, action: ActionEvent):
        '''Perform appropriate game action and return the next player number with their state
        '''
        if isinstance(action, CallAction):
            ## Place a bid (or pass) if an action is a bid (or pass)
            self.round.place_bid(action=action)
        elif isinstance(action, DeclareAction):
            ## Add to a contract if currently in the declaration phase
            self.round.declare(action=action)
        elif isinstance(action, PlayCardAction):
            ## Play a card if currently playing
            self.round.play_card(action=action)
        self.actions.append(action)
        next_player_id = self.round.current_player_id
        next_state = self.get_state()
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
    
    def get_state(self):
        ''' TODO: Implement this function!
        '''
        ### Construct a representation of each players' hand
        ### Construct a representation of the trick pile for each player
        ### Construct a representation of the won cards for each player
        ### Construct a representation of the current hidden cards
        ### Represent the current contract
        ### Represent the dealer and current player
        ### Represent the phase of the game
        pass
    
    def get_num_players(self):
        ''' Get the number of players of the game
        '''
        return 3
        
    def get_state_shape_size(self) -> int:
        ''' Get the shape of the game state as an integer
        '''
        sz = 0
        # Need to account for:
        sz += 11*32 # Hand representation (3*32) [players * unique cards]
        # Trick representation (3*32)
        # Won cards representation (3*32)
        # Hidden cards (32) [unique cards]
        sz += 14 # Contract representation (14) 
                 # [6 contract types + 7 score modifiers + schneider/schwarz won by declarer]
        sz += 63 # Bid representation (64) [current bid values, incl. no bid]
        sz += 2*3 # Dealer representation (3) [players]
        # Current player representation (3)
        sz += 3 # Game phase representation (3) [bidding, declaring, playing]
        return sz

