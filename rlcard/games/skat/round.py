'''
    SkatRound class
    Author: Jakob Wachter
    Last Modified: 11/2/2022
'''

from typing import List, Tuple

from .utils.move import SkatMove, DealHandMove, DeclareContractMove, DeclareModifierMove, FinishContractMove, MakePassMove, BidMove, DeclareMove, PlayCardMove
from .utils.action_event import BidAction, PassAction, DeclareContractAction, DeclareModifierAction, FinishContractAction, PlayCardAction, CallAction, DeclareAction

from .dealer import SkatDealer
from .player import SkatPlayer
from .utils import utils as utils

class SkatRound:
    ''' Abstract representation of each individual round within a game of Skat
    '''

    @property
    def round_phase(self):
        ''' What phase of play the round is currently in
            Takes four values: bid, declare, play, over
        '''
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
        # position of the dealer, linked to a given player
        self.dealer_pos: int = dealer_id
        # dealer of the round
        self.dealer: SkatDealer = SkatDealer(self.dealer_pos, self.np_random)
        # all of the players in the round
        self.players: List[SkatPlayer] = []
        # ID of the current player to move
        self.current_player_id: int = -1
        # top bid value, in points
        self.top_bid: int = 0
        # player who currently has the top bid
        self.top_bidder: SkatPlayer or None = None
        # full contract of the round, including modifiers
        self.round_contract: List[str] = []
        # score of the current round contract
        self.contract_score: int = 0
        # modifier for game score, to be applied as multiplier at the end of the round
        self.game_modifier: int = 1
        # scores for this round, based of the value of cards taken in tricks
        self.round_scores: List[int] = [0]*num_players
        # history of all of the moves within the round
        self.move_history: List[SkatMove] = []
        # lists of the tricks won for each player
        self.tricks_won: List[List[List[SkatMove]]] = [[]]*3
        # total number of cards played in the round
        self.cards_played: int = 0

        for player_id in range(num_players):
            self.players.append(SkatPlayer(player_id=player_id, np_random=self.np_random))
        self.move_history.append(DealHandMove(dealer=self.players[dealer_id], shuffled_deck=self.dealer.shuffled_deck))
        self.current_player_id = self._middlehand().player_id

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
        if 'N' in self.round_contract or 'G' in self.round_contract:
            return 1
        for player in self.players:
            chk_hand = player.hand
            if player == self._get_declarer():
                chk_hand = chk_hand + self.dealer.skat
            if trump_suit[-1] in chk_hand:
                for i in reversed(range(len(trump_suit))):
                    if trump_suit[i] in chk_hand:
                        matadors += 1
                    else:
                        return matadors

    def get_trick_moves(self) -> List[PlayCardMove]:
        '''Get all of the moves associated with the current trick being played
        '''
        trick_moves: List[PlayCardMove] = []
        if self.is_bidding_over():
            if self.cards_played > 0:
                cards_to_trick = self.cards_played % 3
                if cards_to_trick == 0:
                    cards_to_trick = 3
                for move in self.move_history[-cards_to_trick:]:
                    if isinstance(move, PlayCardMove):
                        trick_moves.append(move)
                if len(trick_moves) != cards_to_trick:
                    raise Exception(f'get_trick_moves: invalid trick_moves={[str(move.card) for move in trick_moves]} for length {cards_to_trick}')
        return trick_moves

    def _calculate_current_scores(self) -> List[int]:
        '''Get the current scores associated with a given round
        '''
        scores: List[int] = [0]*3
        for player_id in range(3):
            player_tricks = self.tricks_won[player_id]
            player_score = 0
            for t in player_tricks:
                for c in t:
                    player_score += utils.get_value_of_card(c.card)
            scores[player_id] = player_score
        return scores

    def _get_current_player(self) -> SkatPlayer:
        '''Return current player of the round
        '''
        return self.players[self.current_player_id]

    def _get_declarer(self) -> SkatPlayer:
        '''Get the declarer of the round
        '''
        return self.top_bidder if self.top_bidder is not None else self._forehand()

    def _forehand(self) -> SkatPlayer:
        '''Get the forehand
        '''
        return self.players[(self.dealer_pos+1)%3]

    def _middlehand(self) -> SkatPlayer:
        '''Get the middlehand
        '''
        return self.players[(self.dealer_pos+2)%3]

    def _backhand(self) -> SkatPlayer:
        '''Get the backhand (which is also just the dealer)
        '''
        return self.players[self.dealer_pos]

    def _get_next_bidder(self, action: CallAction) -> SkatPlayer or None:
        '''Determine the next bidder in sequence, based off of Skat bidding rules
        '''
        current_player = self._get_current_player()
        (forehand, middlehand, backhand) = (self._forehand(), self._middlehand(), self._backhand())
        if isinstance(action, PassAction):
            if current_player == middlehand:
                #print("Bidding completed!" if self.top_bidder is backhand else f"Passing bid to {backhand}")
                return None if self.top_bidder is backhand else backhand #BH wins, else FH v BH
            if current_player == backhand:
                #print("Bidding completed!")
                return None #either FH or MH wins
            if current_player == forehand:
                #print(f"Passing bid to {backhand}" if self.top_bidder is middlehand else "Bidding completed!")
                return backhand if self.top_bidder is middlehand else None #MH v BH, else BH wins
        if isinstance(action, BidAction):
            previous_top = self.top_bidder
            self.top_bidder = current_player
            #print(f"Bid made by {current_player}, passing bid to {previous_top if previous_top is not None else forehand}")
            # If there are no bids yet, this is the middlehand's bid
            return previous_top if previous_top is not None else forehand
        
    def _get_current_scores(self) -> List[int]:
        '''Get the current scores for the round based on the tricks taken by each player.
        
        Returns:
            List[int]: The scores for all cards taken by each player
        '''
        round_scores = [0]*3
        for i in range(3):
            round_scores[i] = 0
            player_tricks = self.tricks_won[i]
            for trick in player_tricks:
                for move in trick:
                    round_scores[i] += utils.get_value_of_card(move.card)
                    
        return round_scores


    def determine_schneider_schwarz(self) -> Tuple[bool, bool, bool]:
        '''Determine if Schneider or Schwarz has been met for the round

        Returns:
            (bool, bool, bool): If Schneider is met, if Schwarz is met, and if for declarer, respectively
        '''
        declarer_id = self._get_declarer().player_id
        declarer_score = self.round_scores[declarer_id]
        non_declarer_score = self.round_scores[(declarer_id+1)%3] + self.round_scores[(declarer_id+2)%3]
        if declarer_score >= 90:
            return (True, False, True)
        elif non_declarer_score >= 90:
            return (True, False, False)
        elif declarer_score == 120:
            return (True, True, True)
        elif non_declarer_score == 120:
            return (True, True, False)
        return (False, False, False)

    def place_bid(self, action: CallAction):
        '''Record and execute player's BidAction step in the round
        '''
        current_player = self._get_current_player()
        next_player = self._get_next_bidder(action)
        if isinstance(action, PassAction):
            self.move_history.append(MakePassMove(current_player))
            print(MakePassMove(current_player), (self.top_bid, self.top_bidder))
        elif isinstance(action, BidAction):
            self.move_history.append(BidMove(current_player, action))
            print(BidMove(current_player, action), (self.top_bid, self.top_bidder))
            self.top_bid = action.bid_amount
            self.top_bidder = current_player
        if next_player is None:
            if not self.is_round_over():
                declarer_id = self._get_declarer().player_id
                self.current_player_id = declarer_id
        else:
            self.current_player_id = next_player.player_id

    def declare(self, action: DeclareAction):
        '''Record and execute player's DeclareAction step in the round
        '''
        current_player = self._get_current_player()
        if isinstance(action, DeclareContractAction):
            self.move_history.append(DeclareContractMove(current_player, action))
            print(DeclareContractMove(current_player, action), self.round_contract)
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
            print(DeclareModifierMove(current_player, action), self.round_contract)
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
                # Null contracts have a fixed contract score; keep multiplier as 1
                self.game_modifier = 1
                if modifier_id == 1:
                    # Hand adds 13 to null contract score
                    self.contract_score += 13
                if modifier_id == 4:
                    # Open adds 23 to null contract score
                    self.contract_score += 23
        if isinstance(action, FinishContractAction):
            self.game_modifier += self._get_matadors()
            self.move_history.append(FinishContractMove(current_player, action))
            print(FinishContractMove(current_player, action), self.round_contract)
            self.current_player_id = self._forehand().player_id
            self.initial_hands = [self.players[i].hand for i in range(3)]

    def play_card(self, action: PlayCardAction):
        '''Record and execute player's PlayCardAction step in the round
        '''
        current_player = self._get_current_player()
        self.move_history.append(PlayCardMove(current_player, action))
        print(PlayCardMove(current_player, action), current_player.hand)
        card = action.card
        current_player.remove_card(card)
        self.cards_played += 1
        trick_moves = self.get_trick_moves()
        ## if everyone has moved to the current trick, it is over and we need to decide the score
        if len(trick_moves) == 3:
            # determine which card and player have won the round
            trump_suit = utils.trump_suit(self.round_contract)
            is_null = 'N' in self.round_contract
            winning_card = trick_moves[0].card
            trick_value = utils.get_value_of_card(winning_card)
            trick_suit = utils.trick_suit(self.round_contract, winning_card) if (is_null or winning_card.suit != trump_suit[0].suit) else trump_suit 
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
            # pass the next move to the current player
            self.current_player_id = trick_winner.player_id
            self.tricks_won[self.current_player_id].append(trick_moves)
            self.round_scores = self._get_current_scores()
        ## if there are still cards to be played, pass to the next player in sequence
        else:
            self.current_player_id = (self.current_player_id + 1) % 3

    def get_perfect_information(self):
        ''' Get perfect information about the state of the game
        '''
        state = {}
        trick_moves = [None, None, None]
        if self.is_declaring_over():
            for trick_move in self.get_trick_moves():
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

    def get_imperfect_information(self):
        ''' Get imperfect information about the state of the game from the perspective of the current player
        '''
        state = {}
        trick_moves = [None, None, None]
        if self.is_declaring_over():
            for trick_move in self.get_trick_moves():
                trick_moves[trick_move.player.player_id] = trick_move.card
        state['dealer'] = self.dealer_pos
        state['current_player_id'] = self.current_player_id
        state['round_phase'] = self.round_phase
        state['top_bid'] = self.top_bid
        state['top_bidder'] = self.top_bidder
        state['contract'] = self.round_contract
        state['contract_value'] = self.contract_score * self.game_modifier
        state['hand'] = self.players[self.current_player_id].hand
        state['past_tricks'] = self.tricks_won
        state['scores'] = self._calculate_current_scores()
        state['trick_moves'] = trick_moves
        return state
        