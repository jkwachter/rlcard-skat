"""
    Action event classes for handling player actions
    Author: Jakob Wachter
    Last Modified: 27/10/2022
"""

from skat_card import SkatCard

# ====================================
# Action_ids:
#       0 -> no_bid_action_id
#       1 to 63 -> bid_action_id (bid amount by value)
#       64 -> pass_action_id
#       65 to 70 -> declare_game_id (D, C, H, S, Grand, Null)
#       71 to 75 -> declare_modifier_id (Skat, Hand, Schneider, Schwarz, Open)
#       76 -> finish_contract_id
#       77 to 108 -> play_card_action_id
# ====================================

bid_table = [18, 20, 22, 23, 24, 27, 30, 33, 35, 36, 40, 44, 45, 46, 48, 50, 54, 55, 59, 60, 63,
             66, 70, 72, 77, 80, 81, 84, 88, 90, 96, 99, 100, 108, 110, 117, 120, 121, 126, 130,
             132, 135, 140, 143, 144, 150, 153, 154, 156, 160, 162, 165, 168, 170, 176, 180, 187,
             192, 198, 204, 216, 240, 264]
contract_table = ['D', 'H', 'S', 'C', 'G', 'N']
modifier_table = ['Skat', 'Hand', 'Schneider', 'Schwarz', 'Open']

class ActionEvent(object):
    no_bid_action_id = 0
    first_bid_action_id = 1
    pass_action_id = 64
    first_declare_action_id = 65
    first_modifier_action_id = 71
    finish_contract_action_id = 76
    first_play_card_action_id = 77
    
    def __init__(self, action_id: int):
        self.action_id = action_id
        
    def __eq__(self, other):
        result = False
        if (isinstance(other, ActionEvent)):
            result = self.action_id == other.action_id
        return result
    
    def __repr__(self):
        return self.__str__()
    
    @staticmethod
    def from_action_id(action_id: int):
        if action_id == ActionEvent.pass_action_id:
            return PassAction()
        elif action_id == ActionEvent.finish_contract_action_id:
            return FinishContractAction()
        elif ActionEvent.first_bid_action_id <= action_id < ActionEvent.pass_action_id:
            idx = action_id - ActionEvent.first_bid_action_id
            bid_amt = bid_table[idx]
            return BidAction(bid_amt)
        elif ActionEvent.first_declare_action_id <= action_id < ActionEvent.first_modifier_action_id:
            idx = action_id - ActionEvent.first_declare_action_id
            contract = contract_table[idx]
            return DeclareContractAction(contract)
        elif ActionEvent.first_modifier_action_id <= action_id < ActionEvent.finish_contract_action_id:
            idx = action_id - ActionEvent.first_modifier_action_id
            modifier = modifier_table[idx]
            return DeclareModifierAction(modifier)
        elif ActionEvent.first_play_card_action_id <= action_id < ActionEvent.first_play_card_action_id + 32:
            idx = action_id - ActionEvent.first_play_card_action_id
            card = SkatCard.card(idx)
            return PlayCardAction(card)
        else:
            raise Exception(f'ActionEvent from_action_id: invalid action_id={action_id}')
        
    @staticmethod
    def get_num_actions():
        return 107
    
class CallAction(ActionEvent):
    pass

class BidAction(CallAction):
    def __init__(self, bid_amount: int):
        if bid_amount not in bid_table:
            raise Exception(f'BidAction has invalid bid amount {bid_amount}')
        bid_action_id = bid_table.index(bid_amount) + 1
        super().__init__(action_id = bid_action_id)
        self.bid_amount = bid_amount

    def __str__(self):
        return f'{self.bid_amount}'

class PassAction(CallAction):
    def __init__(self):
        super().__init__(action_id=ActionEvent.pass_action_id)

    def __str__(self):
        return "pass"
    
class DeclareAction(ActionEvent):
    pass

class DeclareContractAction(DeclareAction):
    def __init__(self, contract_type: str):
        if contract_type not in contract_table:
            raise Exception(f'DeclareContractAction has invalid contract: {contract_type}')
        contract_action_id = contract_table.index(contract_type)+ActionEvent.first_declare_action_id
        super().__init__(action_id=contract_action_id)
        self.contract_type = contract_type

    def __str__(self):
        return self.contract_type

class DeclareModifierAction(DeclareAction):
    def __init__(self, modifier_type: str):
        if modifier_type not in modifier_table:
            raise Exception(f'DeclareModifierAction has invalid modifier: {modifier_type}')
        modifier_id = modifier_table.index(modifier_type) + ActionEvent.first_modifier_action_id
        super().__init__(action_id=modifier_id)
        self.modifier_type = modifier_type

    def __str__(self):
        return self.modifier_type
    
class FinishContractAction(DeclareAction):
    def __init__(self):
        super().__init__(action_id=ActionEvent.finish_contract_action_id)
        
    def __str__(self):
        return "finish"

class PlayCardAction(ActionEvent):
    def __init__(self, card: SkatCard):
        play_card_action_id = ActionEvent.first_play_card_action_id + card.card_id
        super().__init__(action_id=play_card_action_id)
        self.card: SkatCard = card

    def __str__(self):
        return f"{self.card}"

    