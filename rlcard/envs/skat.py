import numpy as np

from rlcard.envs import Env
from rlcard.games.skat.game import SkatGame

from rlcard.games.skat.utils.action_event import ActionEvent
from rlcard.games.skat.utils.skat_card import SkatCard
from rlcard.games.skat.utils.move import CallMove, DeclareMove, PlayCardMove

class SkatEnv(Env):
    ''' Skat environment
    '''
    
    def __init__(self, config):
        ## Name of the game
        self.name = 'skat'
        ## Corresponding game associated with the environment
        self.game = SkatGame()
        ## Initializing the baseline environment
        super().__init__(config)
        ## Getting the shape of the state from the game
        state_shape_size = self.game.get_state_shape_size()
        ## Returning the state as a vector of length state_shape_size
        self.state_shape = [[1, state_shape_size] for _ in range(self.num_players)]
        ## Todo -- look into what action_shape is doing
        self.action_shape = [None for _ in range(self.num_players)]
        
    def get_perfect_information(self):
        ''' Get the perfect information of the current state
        
        Returns:
            (dict): A dictionary of all the perfect information of the current state
        '''
        return self.game.round.get_perfect_information()
    
    def _extract_state(self, state):
        ''' Extract useful information from state for RL.
        
        Args:
            state (dict): The raw state
            
        Returns:
            (numpy.array): The extracted state
        '''
        state =  self.game.get_state()
        rep = [state['hand'], 
               state['curr_tricks'], 
               state['past_tricks'], 
               state['hidden'], 
               state['top_bid'],
               state['contract'], 
               state['dealer'], 
               state['curr_player'], 
               state['game_phase'],
               state['raw_legal_actions']]
        obs = np.concatenate([e.flatten() for e in rep])
        raw_legal_actions = list(state['legal_actions'].keys())
        extracted_state = {'obs': obs, 
                           'raw_obs': obs,
                           'legal_actions': state['legal_actions'], 
                           'raw_legal_actions': state['raw_legal_actions']}
        return extracted_state

    
    def _decode_action(self, action_id):
        ''' Decode action id to the action in the game.
        
        Args:
            action_id (int): The id of the action
            
        Returns:
            (ActionEvent): The action that will be passed to the game engine
        
        '''
        return ActionEvent.from_action_id(action_id=action_id)
    
    def get_payoffs(self):
        ''' Get all legal actions for current state.
        
        Returns:
            (list): A list of legal actions' id.
        '''
        return self.game.judger.judge_payoffs()
    
    def _get_legal_actions(self):
        ''' Get all legal actions for current state.
        
        Returns:
            (list): A list of legal actions' id.
        '''
        return self.game.judger.get_legal_actions()
    
    
    