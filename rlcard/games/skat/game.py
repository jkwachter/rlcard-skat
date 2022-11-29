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

import utils.utils as utils

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
        
        abstract_state = self.round.get_imperfect_information()
        state = {}
        player_id = abstract_state['current_player_id']
        
        ### Construct a representation of each players' hand
        state['hand'] = np.array([[0]*32]*3)
        player_hand = abstract_state['hand']
        for card in player_hand:
            state['hand'][player_id][card.card_id] = 1
        ### Construct a representation of the trick pile for each player
        state['curr_tricks'] = np.array([[0]*32]*3)
        for i in range(3):
            trick_card_id = abstract_state['trick_moves'][i].card_id
            state['curr_tricks'][i][trick_card_id] = 1
        
        ### Construct a representation of the won cards for each player
        state['past_tricks'] = np.array([[0]*32]*3)
        for i in range(3):
            for trick in self.round.tricks_won[i]:
                for move in trick:
                    state['past_tricks'][i][move.card.card_id] = 1
        ### Construct a representation of the current hidden cards
        state['hidden'] = np.array([0]*32)
        for i in range(32):
            if np.sum(state['past_tricks'][:,i] + state['curr_tricks'][:,i] + state['hand'][:,i]) == 0:
                state['hidden'][i] = 1
        
        ### Represent the current contract
        state['contract'] = np.array([0]*14)
        contract_id = utils.get_contract_index(abstract_state['contract'])
        if contract_id != -1:
            state['contract'][contract_id] = 1
            for contract_elem in abstract_state['contract']:
                    elem_id = utils.get_modifier_index(contract_elem)
                    if elem_id != 1:
                        state['contract'][6+elem_id] = 1
        (schneider, schwarz, for_dec) = self.round.determine_schneider_schwarz()
        state['contract'][11] = 1 if schneider else 0
        state['contract'][12] = 1 if schwarz else 0
        state['contract'][13] = 1 if for_dec else 0
        
        ### Represent the dealer and current player
        state['dealer'] = np.array([0, 0, 0])
        state['dealer'][abstract_state['dealer']] = 1
        state['curr_player'] = np.array([0, 0, 0])
        state['curr_player']['player_id'] = 1
        
        ### Represent the phase of the game
        state['game_phase'] = np.array([0, 0, 0, 0])
        if round.round_phase == 'bid':
            state['game_phase'][0] = 1
        elif round.round_phase == 'declare':
            state['game_phase'][1] = 1
        elif round.round_phase == 'play':
            state['game_phase'][2] = 1
        else:
            state['game_phase'][3] = 1
        
        ### Represent the legal actions that can currently be taken
        state['legal_actions'] = np.array([0]*ActionEvent.get_num_actions())
        for legal_action in self.judger.get_legal_actions():
            state['legal_actions'][legal_action.action_id] = 1
        return state
        
    
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
        sz += 108 # Action representation
        return sz

