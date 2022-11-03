'''
    SkatRound class
    Author: Jakob Wachter
    Last Modified: 11/2/2022
'''

from typing import List


from utils.move import SkatMove, DealHandMove, DeclareContractMove, DeclareModifierMove, FinishContractMove, MakePassMove, BidMove, DeclareMove, PlayCardMove
from utils.action_event import BidAction, PassAction, DeclareContractAction, DeclareModifierAction, FinishContractAction, PlayCardAction, CallAction, DeclareAction

from dealer import SkatDealer
from player import SkatPlayer
import utils.utils as utils

class SkatRound:
    
    @property
    def round_phase(self):
        if self.is_round_over():
            result = 'over'
        elif self.is_declaring_over():
            result = 'play'
        elif self.is_bidding_over():
            result = 'declare'
        else:
            result = 'bid'
        return result
    
    def __init__(self, num_players: int, dealer_id: int, np_random):
        ''' Initialize the round class
        
            The round class maintains the following instances:
                1) dealer: The dealer of the round
                2) players: The players in the round; each player has a hand
                3) current_player_id: ID of the player who should move next
                4) game_modifier: Current modifier on round score, based on bidding process
                5) current_score: Current score of the round for each player.
                6) move_history: History of moves for all players, including dealing.
                
            Args:
                num_players: players for the round, should be 3
                dealer_id: id of the dealer for the round
                np_random: handle for numpy random class
        '''
        
        self.np_random = np_random
        self.dealer_pos: int = dealer_id
        self.dealer: SkatDealer = SkatDealer(self.dealer_pos, self.np_random)
        self.players: List[SkatPlayer] = []
        self.current_player_id: int = dealer_id
        self.top_bid: int = 0
        self.top_bidder: SkatPlayer or None = None
        self.round_contract: List[str] = []
        self.contract_score: int = 0
        self.game_modifier: int = 1
        self.round_scores: List[int] = [0]*num_players
        self.move_history: List[SkatMove] = []
        self.tricks_won: List[List[SkatMove]] = [[]]*3
        self.cards_played: int = 0
        
        for player_id in range(num_players):
            self.players.append(SkatPlayer(player_id=player_id, np_random=self.np_random))
        self.move_history.append(DealHandMove(dealer=self.players[dealer_id], shuffled_deck=self.dealer.shuffled_deck))
        
    def is_bidding_over(self) -> bool:
        '''Return whether current bidding is over
        '''
        pass_count = 0
        for move in reversed(self.move_history):
            if isinstance(move, DeclareMove):
                return True
            if isinstance(move, MakePassMove):
                pass_count += 1
                if pass_count == 2:
                    return True
        return False
    
    def is_declaring_over(self) -> bool:
        '''Return whether declarations are over
        '''
        for move in reversed(self.move_history):
            if isinstance(move, FinishContractMove):
                return True
        return False
    
    def is_round_over(self) -> bool:
        '''Return whether the round is over
        '''
        if self.round_contract:
            for player in self.players:
                if player.hand:
                    return False
            return True
        return False
    
    def _get_matadors(self) -> int:
        '''Return the number of matadors for/against the declarer
        '''
        trump_suit = utils.trump_suit(self.round_contract)
        matadors = 0
        for player in self.players:
            chk_hand = player.hand
            if player == self._get_declarer():
                chk_hand = chk_hand + self.dealer.skat
            if trump_suit[-1] in player.hand:
                for i in reversed(range(len(trump_suit))):
                    if trump_suit[i] in player.hand:
                        matadors += 1
                    else:
                        return matadors

    def _get_trick_moves(self) -> List[PlayCardMove]:
        trick_moves: List[PlayCardMove] = []
        if self.is_bidding_over():
            if self.cards_played > 0:
                cards_to_trick = self.cards_played % 3
                if cards_to_trick == 0:
                    cards_to_trick = 3
                for move in self.move_history[-cards_to_trick]:
                    if isinstance(move, PlayCardMove):
                        trick_moves.append(move)
                if len(trick_moves) != cards_to_trick:
                    raise Exception(f'_get_trick_moves: invalid trick_moves={[str(move.card) for move in trick_moves]} for length {cards_to_trick}')
        return trick_moves
    
    def _calculate_current_scores(self) -> List[int]:
        scores: List[int] = [0]*3
        for player_id in range(3):
            player_tricks = self.tricks_won[player_id]
            player_score = 0
            for t in player_tricks:
                player_score += utils.get_value_of_card(t.card)
            scores[player_id] = player_score
        return scores
    
    def _get_current_player(self) -> SkatPlayer:
        '''Return current player of the round
        '''
        return self.players[self.current_player_id]
    
    def _get_declarer(self) -> SkatPlayer:
        return self.top_bidder.player_id if self.top_bidder is not None else self._forehand()
    
    def _forehand(self) -> SkatPlayer:
        return self.players[(self.dealer_pos+1)%3]
    
    def _middlehand(self) -> SkatPlayer:
        return self.players[(self.dealer_pos+2)%3]
    
    def _backhand(self) -> SkatPlayer:
        return self.players[self.dealer_pos]
    
    def _get_next_bidder(self, action: CallAction) -> SkatPlayer or None:
        current_player = self._get_current_player()
        (forehand, middlehand, backhand) = (self._forehand(), self._middlehand(), self._backhand())
        if isinstance(action, PassAction):
            if current_player == middlehand:
                return None if self.top_bidder is backhand else backhand #BH wins, else FH v BH
            if current_player == backhand:
                return None #either FH or MH wins
            if current_player == forehand:
                return backhand if self.top_bidder is middlehand else None #MH v BH, else BH wins
        if isinstance(action, BidAction):
            previous_top = self.top_bidder
            self.top_bidder = current_player
            return previous_top

    def place_bid(self, action: CallAction):
        '''Record and execute player's BidAction step in the round
        '''
        current_player = self._get_current_player()
        if isinstance(action, PassAction):
            self.move_history.append(MakePassMove(current_player))
        elif isinstance(action, BidAction):
            self.move_history.append(BidMove(current_player, action))
            self.top_bid = action.bid_amount
        next_player = self._get_next_bidder(action)
        if next_player is None:
            if not self.is_round_over():
                declarer_id = self._get_declarer()
                self.current_player_id = declarer_id
        else:
            self.current_player_id = next_player.player_id

    def declare(self, action: DeclareAction):
        '''Record and execute player's DeclareAction step in the round
        '''
        current_player = self._get_current_player()
        if isinstance(action, DeclareContractAction):
            self.move_history.append(DeclareContractMove(current_player, action))
            self.round_contract.append(action.contract_type)
            contract_id = utils.get_contract_index(self.round_contract)
            if contract_id < 4:
                # 9 for D, 10 for H, 11 for S, 12 for C
                self.contract_score = 9 + contract_id
            if contract_id == 4:
                # Grand games are worth 24
                self.contract_score = 24
            if contract_id == 5:
                # Null games are worth 23 at base
                self.contract_score = 23
        if isinstance(action, DeclareModifierAction):
            self.move_history.append(DeclareModifierMove(current_player, action))
            self.round_contract.append(action.modifier_type)
            contract_id = utils.get_contract_index(self.round_contract)
            modifier_id = utils.get_modifier_index(action.modifier_type)
            if contract_id < 5:
                # Suit/Grand games get added multiplier
                if modifier_id > 0:
                    self.game_modifier += 1
                if modifier_id == 1:
                    # Hand games start with a multiplier of 2
                    self.game_modifier += 1
            if contract_id == 5:
                if modifier_id == 1:
                    # Hand adds 13 to null contract score
                    self.contract_score += 13
                if modifier_id == 4:
                    # Open adds 23 to null contract score
                    self.contract_score += 23
        if isinstance(action, FinishContractAction):
            self.game_modifier += self._get_matadors()
            self.move_history.append(FinishContractMove(current_player, action))
            self.current_player_id = self._forehand().player_id

    def play_card(self, action: PlayCardAction):
        '''Record and execute player's PlayCardAction step in the round
        '''
        current_player = self._get_current_player()
        self.move_history.append(PlayCardMove(current_player, action))
        card = action.card
        current_player.remove_card(card)
        self.cards_played += 1
        trick_moves = self._get_trick_moves()
        if len(trick_moves) == 3:
            trump_suit = utils.trump_suit(self.round_contract)
            winning_card = trick_moves[0].card
            trick_value = utils.get_value_of_card(winning_card)
            trick_suit = trump_suit if winning_card.suit == trump_suit[0].suit else utils.trick_suit(self.round_contract, winning_card)
            trick_winner = trick_moves[0].player
            for move in trick_moves[1:]:
                switch_flag = False
                trick_card = move.card
                trick_value += utils.get_value_of_card(trick_card)
                trick_player = move.player
                if trick_card in trump_suit:
                    if winning_card in trump_suit:
                        if trump_suit.index(trick_card) > trump_suit.index(winning_card):
                            switch_flag = True
                    else:
                        switch_flag = True
                elif (trick_card in trick_suit) and (winning_card in trick_suit):
                    if trick_suit.index(trick_card) > trick_suit.index(winning_card):
                        switch_flag = True
                if switch_flag:
                    winning_card = trick_card
                    trick_winner = trick_player
            self.current_player_id = trick_winner.player_id
            self.tricks_won[self.current_player_id] = self.tricks_won[self.current_player_id] + trick_moves
            self.round_scores = self._get_current_scores()
        else:
            self.current_player_id = (self.current_player_id + 1) % 3

    def get_perfect_information(self):
        state = {}
        trick_moves = [None, None, None]
        if self.is_declaring_over():
            for trick_move in self._get_trick_moves():
                trick_moves[trick_move.player.player_id] = trick_move.card
        state['move_count'] = len(self.move_history)
        state['current_player_id'] = self.current_player_id
        state['round_phase'] = self.round_phase
        state['top_bid'] = self.top_bid
        state['top_bidder'] = self.top_bidder
        state['contract'] = self.round_contract
        state['contract_value'] = self.contract_score * self.game_modifier
        state['hands'] = [player.hand for player in self.players]
        state['scores'] = self._calculate_current_scores()
        state['trick_moves'] = trick_moves
        return state
    
    def get_imperfect_information(self, player: SkatPlayer):
        player_id = self.players.index(player)
        state = {}
        state['dealer'] = self.dealer_pos
        state['current_player_id'] = self.current_player_id
        state['round_phase']
        state['top_bid']
        state['top_bidder']
        state['contract']
        state['contract_value']
        state['hand']
        state['num_cards_left']
        state['past_tricks']
        state['scores']
        state['trick_moves']
        