'''
    SkatJudger class
    Author: Jakob Wachter
    Last Modifier: 11/2/2022
'''

from typing import List
import numpy as np

from .utils import utils as utils

from .utils.action_event import PlayCardAction, ActionEvent
from .utils.action_event import DeclareContractAction, DeclareModifierAction, FinishContractAction, DeclareAction
from .utils.action_event import BidAction, PassAction

bid_table = [18, 20, 22, 23, 24, 27, 30, 33, 35, 36, 40, 44, 45, 46, 48, 50, 54, 55, 59, 60, 63,
             66, 70, 72, 77, 80, 81, 84, 88, 90, 96, 99, 100, 108, 110, 117, 120, 121, 126, 130,
             132, 135, 140, 143, 144, 150, 153, 154, 156, 160, 162, 165, 168, 170, 176, 180, 187,
             192, 198, 204, 216, 240, 264]

contract_table = ['D', 'H', 'S', 'C', 'G', 'N']
modifier_table = ['Skat', 'Hand', 'Schneider', 'Schwarz', 'Open']

class SkatJudger:
    
    def __init__(self, game):
        ''' Initialize a judger based off of the given game being played
        '''
        self.game = game
        
    def _get_round_scores(self) -> List[int]:
        ''' Get the current scores for the round
        
        Returns:
            (List[int])
        '''
        return self.game.round.round_scores
    
    def judge_payoffs(self) -> int:
        ''' Get the payoffs for the current round
            
        Returns:
            int: The payoff for the given round, to be given to the declarer's score
        '''
        
        # get some pertinent information about the outcome of the round
        scores = self._get_round_scores()
        round = self.game.round
        contract_score, multiplier = round.contract_score, round.game_modifier
        declarer_id = round.top_bidder.player_id
        (schneider_met, schwarz_met, for_declarer) = round.determine_schneider_schwarz()
        # our goal now is to extract the contract value from the contract and determine if it is satisfactory
        payoffs = np.array([0, 0, 0])
        if schwarz_met:
            multiplier += 1
        if schneider_met:
            multiplier += 1
        final_value = contract_score * multiplier
        declarer_won = (scores[declarer_id] > 60)
        schneider_failed = ("Schneider" in round.round_contract) and not (schneider_met and for_declarer)
        schwarz_failed = ("Schwarz" in round.round_contract) and not (schwarz_met and for_declarer)
        
        #If as declarer you announce Schneider but take less than 90 card points, or if you announce Schwarz or Open and lose a trick, you lose
        #counting all the multipliers you would have won if you had succeeded.
        #If the value of the declarer's game turns out to be less than the bid then the declarer automatically loses
        #The amount subtracted from score is twice the least multiple of the base value of the game actually played which would have fulfilled the bid.
        if final_value < round.top_bid or schneider_failed or schwarz_failed:
            least_multiple = ((round.top_bid // contract_score) + 1)
            required_value = contract_score * least_multiple
            payoffs[declarer_id] = -required_value * 2
        
        #If declarer wins the game and the value of the game is as least as much as the bid
        #then the value of the game is added to the declarer's cumulative score.
        elif declarer_won and final_value >= round.top_bid:
            payoffs[declarer_id] = final_value
        
        #If the declarer loses the game and the value of the game is as least as much as the bid
        #then twice the value of the game is subtracted from the declarer's score.
        else:
            payoffs[declarer_id] = -final_value * 2
            

    def get_legal_actions(self) -> List[ActionEvent]:
        ''' Get the current legal actions for the round
        
        Returns:
            (List[ActionEvent]): The legal actions associated with the current round state
        '''
        
        round = self.game.round
        legal_actions: List[ActionEvent] = []
        if not (round.round_phase is 'over'):
            current_player = round.current_player_id
            if round.round_phase is 'bid':
                top_bid_id = round.top_bidder.player_id
                (fore_id, mid_id, back_id) = (round._forehand().player_id, round._middlehand().player_id, round._backhand().player_id)
                legal_actions.append(PassAction())
                seniority = (fore_id == current_player) or (mid_id == current_player and back_id == top_bid_id)
                if seniority:
                    legal_actions.append(BidAction(round.top_bid))
                legal_bids = [b for b in bid_table if b > round.top_bid]
                for bid in legal_bids:
                    legal_actions.append(BidAction(bid))
            if round.round_phase is 'declare':
                curr_contract = round.round_contract
                contract_declared = False
                for contract in contract_table:
                    if contract in curr_contract:
                        contract_declared = True
                if not contract_declared:
                    for contract in contract_table:
                        legal_actions.append(DeclareContractAction(contract))
                else:
                    if 'Hand' not in curr_contract and 'Skat' not in curr_contract:
                        legal_actions.append(DeclareModifierAction('Skat'))
                        legal_actions.append(DeclareModifierAction('Hand'))
                    elif 'N' not in curr_contract:
                        legal_actions.append(FinishContractAction())
                        if 'Hand' in curr_contract:
                            if 'Schneider' not in curr_contract:
                                legal_actions.append(DeclareModifierAction('Schneider'))
                            elif 'Schwarz' not in curr_contract:
                                legal_actions.append(DeclareModifierAction('Schwarz'))
                            elif 'Open' not in curr_contract:
                                legal_actions.append(DeclareModifierAction('Open'))
                    else:
                        if 'Open' not in curr_contract:
                            legal_actions.append(DeclareModifierAction('Open'))
            if round.round_phase is 'play':
                contract = round.round_contract
                trick_moves = self.game.round.get_trick_moves()
                hand = self.game.round.players[current_player]
                legal_cards = [card for card in hand if (card in utils.trump_suit(contract)) or (card in utils.trick_suit(contract, trick_moves[0].card))]
                for card in legal_cards:
                    legal_actions.append(PlayCardAction(card=card))
        return legal_actions
                
                
