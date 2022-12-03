import unittest

import rlcard
from rlcard.agents.random_agent import RandomAgent
from .determism_util import is_deterministic

from rlcard.games.skat.utils.action_event import ActionEvent, PassAction, BidAction, PlayCardAction, DeclareContractAction, DeclareModifierAction, FinishContractAction
from rlcard.games.skat.utils.skat_card import SkatCard
from rlcard.games.skat.utils.move import BidMove, MakePassMove, DeclareContractMove, DeclareModifierMove, FinishContractMove, PlayCardMove
import rlcard.games.skat.utils.utils as utils

# This table of bids lists every unique bid value available within Skat
bid_table = [18, 20, 22, 23, 24, 27, 30, 33, 35, 36, 40, 44, 45, 46, 48, 50, 54, 55, 59, 60, 63,
             66, 70, 72, 77, 80, 81, 84, 88, 90, 96, 99, 100, 108, 110, 117, 120, 121, 126, 130,
             132, 135, 140, 143, 144, 150, 153, 154, 156, 160, 162, 165, 168, 170, 176, 180, 187,
             192, 198, 204, 216, 240, 264]
# Every type of contract available in Skat
contract_table = ['D', 'H', 'S', 'C', 'G', 'N']
# Every type of contract modifier available within Skat
# Note that this does not include unique modifiers for winning vs. declaring Schneider/Schwarz
modifier_table = ['Skat', 'Hand', 'Schneider', 'Schwarz', 'Open']

class TestSkatEnv(unittest.TestCase):
    # Testing information about the state at each point:
    def test_reset_and_extract_state(self):
        env = rlcard.make('skat')
        state, _ = env.reset()
        self.assertEqual(state['obs'].size, 108)

    def test_decode_action(self):
        env = rlcard.make('skat')
        env.reset()
        for i in range(1, ActionEvent.get_num_actions):
            action = env._decode_action(i)
            if i == ActionEvent.pass_action_id:
                self.assertEqual(action, PassAction())
            elif i == ActionEvent.finish_contract_action_id:
                self.assertEqual(action, FinishContractAction())
            elif ActionEvent.first_bid_action_id <= i < ActionEvent.pass_action_id:
                idx = i - ActionEvent.first_bid_action_id
                self.assertEqual(action, BidAction(bid_table[idx]))
            elif ActionEvent.first_declare_action_id <= i < ActionEvent.first_modifier_action_id:
                idx = i - ActionEvent.first_declare_action_id
                self.assertEqual(action, DeclareContractAction(contract_table[idx]))
            elif ActionEvent.first_modifier_action_id <= i < ActionEvent.finish_contract_action_id:
                idx = i - ActionEvent.first_modifier_action_id
                self.assertEqual(action, DeclareModifierAction(modifier_table[idx]))
            elif ActionEvent.first_play_card_action_id <= i < ActionEvent.first_play_card_action_id + 32:
                idx = i - ActionEvent.first_play_card_action_id
                self.assertEqual(action, PlayCardAction(SkatCard.card(idx)))
            else:
                pass

    # Testing if the game is deterministic:
    def test_is_deterministic(self):
        self.assertTrue(is_deterministic('skat'))

    # Testing that a single step does transition:
    def test_step(self):
        env = rlcard.make('skat')
        _, player_id = env.reset()
        player = env.game.players[player_id]
        _, next_player_id = env.step(BidAction(18))
        self.assertNotEqual(player_id, next_player_id)

    def test_step_back(self):
        pass

    def test_run(self):
        env = rlcard.make('skat')
        env.set_agents([RandomAgent(env.num_actions) for _ in range(env.num_players)])
        trajectories, payoffs = env.run(is_training = False)
        self.assertEqual(len(trajectories), 3)
        # Now we need to determine that the game logic is internally consistent between games
        # This requires action-by-action analysis of each action within the game
        round = env.game.round
        round_phase = 'bid'
        top_bid, top_bidder, num_passes, locked_out_players = 0, None, 0, [False, False, False]
        contract, declaration_made = [], True
        current_trick, legal_cards = [None, None, None]
        for move in env.game.round.move_history:
            player = move.player
            player_id = player.player_id
            if isinstance(move, BidMove):
                # Must be in the bidding phase
                self.assertEqual(round_phase, 'bid')
                # Player who is bidding must not have already passed
                self.assertNotEqual(locked_out_players[player_id], True)
                attempted_bid = move.bid_action.bid_amount
                seniority = (player == round._forehand()) or (player == round._middlehand() and top_bidder == round._backhand())
                # Bid must be greater than all previous bids in sequence
                # (the bid can be equal if the player has table priority)
                if (seniority):
                    self.assertGreaterEqual(attempted_bid, top_bid)
                else:
                    self.assertGreater(attempted_bid, top_bid)
                top_bid = attempted_bid
                top_bidder = player
            elif isinstance(move, MakePassMove):
                # Must be in the bidding phase
                self.assertEqual(round_phase, 'bid')
                # Player who is passing must not have already passed
                self.assertNotEqual(locked_out_players[player_id], True)
                num_passes += 1
                # No more than two pass moves occur throughout the bidding phase
                self.assertLessEqual(num_passes, 2)
                locked_out_players[player_id] = True
                if (num_passes == 2):
                    round_phase = 'declare'
            elif isinstance(move, DeclareContractMove):
                #Must be in the declaration phase
                self.assertEqual(round_phase, 'declare')
                #The person declaring must be the top bidder
                self.assertEqual(player, top_bidder)
                # Only occurs once
                self.assertEqual(declaration_made, False)
                contract.append(move.declare_action.contract_type)
                declaration_made = True
            elif isinstance(move, DeclareModifierMove):
                #Must be in the declaration phase
                self.assertEqual(round_phase, 'declare')
                #The person declaring must be the top bidder
                self.assertEqual(player, top_bidder)
                modifier = move.declare_action.modifier_type
                #The modifier must not already be in the contract
                self.assertNotIn(modifier, contract)
                # The modifier declared follows some rules on the contract
                if modifier == 'Schneider':
                    self.assertIn('Hand', contract)
                elif modifier == 'Schwarz':
                    self.assertIn('Hand', contract)
                    self.assertIn('Schneider', contract)
                elif modifier == 'Open' and ('N' not in contract):
                    self.assertIn('Hand', contract)
                elif modifier == 'Skat':
                    self.assertNotIn('Hand', contract)
                elif modifier == 'Hand':
                    self.assertNotIn('Skat', contract)
                contract.append(modifier)
            elif isinstance(move, FinishContractMove):
                #Must be in the declaration phase
                self.assertEqual(round_phase, 'declare')
                #The person declaring must be the top bidder
                self.assertEqual(player, top_bidder)
                round_phase = 'play'
            elif isinstance(move, PlayCardMove):
                # Must be in the playing phase
                self.assertEqual(round_phase, 'play')
                self.assertIsNone(current_trick[player_id])
                card = move.action.card
                if current_trick == [None, None, None]:
                    trick_suit = utils.trick_suit(contract, card)
                    trump_suit = utils.trump_suit(contract)
                    legal_cards = trick_suit + trump_suit
                self.assertIn(card, legal_cards)
                current_trick[player_id] = card 
                flag = True
                for c in current_trick:
                    if c is None: flag = False 
                if flag:
                    current_trick = [None, None, None]

    def test_get_legal_actions(self):
        env = rlcard.make('skat')
        env.set_agents([RandomAgent(env.num_actions) for _ in range(env.num_players)])
        env.reset()
        legal_actions = env._get_legal_actions()
        for legal_action in legal_actions:
            self.assertLess(legal_action, ActionEvent.first_declare_action_id)