'''Utilities for various Skat classes
'''

from typing import List

from skat_card import SkatCard

valid_suit = ['D', 'H', 'S', 'C']
valid_game_rank = ['7', '8', '9', 'Q', 'K', 'T', 'A', 'J']
valid_null_rank = ['7', '8', '9', 'T', 'J', 'Q', 'K', 'A']

contract_table = ['D', 'H', 'S', 'C', 'G', 'N']
modifier_table = ['Skat', 'Hand', 'Schneider', 'Schwarz', 'Open']

card_values = {'J': 2, 'A': 11, 'T': 10, 'K': 4, 'Q': 3, '9': 0, '8': 0, '7': 0}

def generate_deck() -> List[SkatCard]:
    """Generate an initial Skat deck, unshuffled

    Returns:
        An unshuffled array of Card valid for use in the skat environment
    """
    return [SkatCard(suit, rank) for suit in valid_suit for rank in valid_null_rank]

def trump_suit(contract: List[str]) -> List[SkatCard]:
    '''Generate the trump suit for a given contract

    Args:
        contract: The contract for a given round

    Returns:
        (List[SkatCard]): The cards of the trump suit for this contract
    '''
    contract_type = None
    for elem in contract:
        if elem in contract_table:
            contract_type = elem
    contract_index = contract_table.index(contract_type)
    trump: List[SkatCard] = []
    if contract_index < 4:
        # Suit game; should add jacks, then A-T-K-Q-...
        jacks = SkatCard.get_rank(4)
        suit = SkatCard.get_suit(contract_index)
        suit.pop(4)
        ten = suit.pop(3)
        suit.insert(-1, ten)
        trump = suit + jacks
    elif contract_index == 5:
        # Grand game; should add jacks
        trump = SkatCard.get_rank(4)
    elif contract_index != 6:
        raise Exception(f'Invalid contract: {contract}')
    return trump

def trick_suit(contract: List[str], card: SkatCard) -> List[SkatCard]:
    ''' Generate the suit for a given trick

    Args:
        contract: The contract for a given round
        card: The starting card for a given trick

    Returns:
        (List[SkatCard]): The suit of the trick begun by card
    '''
    contract_type = None
    for elem in contract:
        if elem in contract_table:
            contract_type = elem
    contract_index = contract_table.index(contract_type)
    trick_index = contract_table.index(card.suit)
    if trick_index == contract_index:
        return trump_suit(contract)
    else:
        #all games use the suit
        suit = SkatCard.get_suit(trick_index)
        if contract_index < 5:
            # Suit or grand game; move 10 and drop jacks
            suit.pop(4)
            ten = suit.pop(3)
            suit.insert(-1, ten)
        return suit
        
def get_value_of_card(card: SkatCard) -> int:
    ''' Get the score value associated with a given card

    Args:
        card: SkatCard to score

    Return:
        (int): Score of card
    '''
    return card_values.get(card.rank)

def get_contract_index(contract: List[str]) -> int:
    ''' Get the numerical contract index associated with a given contract
        0-3 are Suit games, 4 is Grand, 5 is Null

    Args:
        contract: Contract to get the index of

    Returns:
        (int): Associated contract index
    '''
    if is_valid_contract(contract):
        for elem in contract:
            if elem in contract_table:
                return contract_table.index(elem)
    else:
        return -1

def get_modifier_index(modifier: str) -> int:
    ''' Get the numerical index of a given modifier
        Related to the index of the modifier within modifier_table

    Args:
        modifier: Modifier name, string

    Returns:
        (int): Associated modifier index
    '''
    return modifier_table.index(modifier) if modifier in modifier_table else -1

def is_valid_contract(contract: List[str]) -> bool:
    ''' Determine whether a contract is valid

    Args:
        contract: Contract to verify

    Returns:
        (bool): Whether the contract is valid
    '''
    ## there are more checks that can be done here, including checking for uniqueness, exclusivity
    num_ctr = 0
    for elem in contract:
        if elem in contract_table:
            num_ctr += 1
    if (num_ctr == 1) and (len(contract) == len(set(contract))):
        return True
    return False
