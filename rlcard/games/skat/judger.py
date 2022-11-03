'''
    SkatJudger class
    Author: Jakob Wachter
    Last Modifier: 11/2/2022
'''

from typing import List

from game import SkatGame

from utils.action_event import PlayCardAction, ActionEvent
from utils.action_event import DeclareContractAction, DeclareModifierAction, FinishContractAction, DeclareAction
from utils.action_event import BidAction, PassAction, CallAction

from utils.move import PlayCardMove
from utils.move import DeclareContractMove, DeclareModifierMove, FinishContractMove, DeclareMove
from utils.move import BidMove, MakePassMove, CallMove

class SkatJudger:

    '''Judger decides legal actions for the current player
    '''
        
    def __init__(self, game: SkatGame):
        self.game: SkatGame = game
    
    def get_legal_actions(self) -> List[ActionEvent]:
        pass

