## gaScripteBot.py, Benjamin Ledoux - bledoux@conncoll.edu
## Adapted from scripted_bot_example.py for refinement through a Genetic Algorithm using geneticAlgorithm.py
## Most changes are in main() function, the rest is exposing the Scripted Bot to the GA

#!/usr/bin/env python3
from typing import List

import botbowl
from botbowl import Action, ActionType, Square, BBDieResult, Skill, Formation, ProcBot
import botbowl.core.pathfinding as pf
import time
import math
from botbowl.core.pathfinding.python_pathfinding import Path  # Only used for type checker

from scripted_bot_example import *
from random_bot_example import *
#import random
from geneticAlgorithm import *
import json
from datetime import datetime

import numpy as np
import matplotlib.pyplot as plt
#import os
import argparse

## Translate genes in chromosome into behaviors, used for binary chocies like "Use Reroll" vs "Don't Use Reroll"
def binaryChoice(binary, a, b):
    if binary == "0": ## Chromosomes are easier to store and manipulate as strings
        return a
    elif binary == "1":
        return b
    else:
#        print(f"Error with selection, defaulting to {b}")
        return b

class GAScriptedBot(ProcBot):

    def __init__(self, name):
        super().__init__(name)
        self.my_team = None
        self.opp_team = None
        self.actions = []
        self.last_turn = 0
        self.last_half = 0

        self.ball_dist = 0 ## Used for fitness calculation, stores how far the ball has moved towards the opposing endzone
        self.ball_dist_prev = 0
        self.turnCount = 0

        self.off_formation = [
            ["-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-"],
            ["-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-"],
            ["-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "m", "-", "-"],
            ["-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "x", "-"],
            ["-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-"],
            ["-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "S"],
            ["-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "x"],
            ["-", "-", "-", "-", "-", "s", "-", "-", "-", "0", "-", "-", "S"],
            ["-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "x"],
            ["-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "S"],
            ["-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-"],
            ["-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "x", "-"],
            ["-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "m", "-", "-"],
            ["-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-"],
            ["-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-"]
        ]

        self.def_formation = [
            ["-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-"],
            ["-", "-", "-", "-", "-", "-", "-", "-", "x", "-", "b", "-", "-"],
            ["-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-"],
            ["-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-"],
            ["-", "-", "-", "-", "-", "-", "-", "-", "x", "-", "S", "-", "-"],
            ["-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "0"],
            ["-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-"],
            ["-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "0"],
            ["-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-"],
            ["-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "0"],
            ["-", "-", "-", "-", "-", "-", "-", "-", "x", "-", "S", "-", "-"],
            ["-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-"],
            ["-", "-", "-", "-", "-", "-", "-", "-", "x", "-", "b", "-", "-"],
            ["-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-"],
            ["-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-"]
        ]

        self.off_formation = Formation("Wedge offense", self.off_formation)
        self.def_formation = Formation("Zone defense", self.def_formation)
        self.setup_actions = []

        ## Attempt at multithreading, so far unsuccessful. To avoid overwriting files being used by the bot, this determines which file to use for each concurrent simulation
        threadData = {"thread" : 0}
        with open('thread.json', 'r', encoding='utf-8') as dataFile:
            threadData = json.load(dataFile)
        thread = threadData["thread"]
        self.filename = f"data_{thread}.json" ## In theory if you had 2 runs going at once, the first would use data_0.json and the second would use data_1.json
#        print(self.filename)

        ## Retrieves chromosome to be used as controller for bot behavior from external json file
        self.chromoData = {
            "currentChromosome" : None,
            "ballProgress" : None
        }
        with open(self.filename, 'r', encoding='utf-8') as chromoFile:
            self.chromoData = json.load(chromoFile)
        self.chromoData["ballProgress"] = 0 # Resets ball progress from previous chromosome
#        print(self.chromoData["currentChromosome"])

        ## Genes 1-15, all binary choices
        self.coinChoice = binaryChoice(self.chromoData["currentChromosome"][0], ActionType.HEADS, ActionType.TAILS)
        self.kickChoice = binaryChoice(self.chromoData["currentChromosome"][1], ActionType.KICK, ActionType.RECEIVE)
        self.dodgeReroll = binaryChoice(self.chromoData["currentChromosome"][2], ActionType.DONT_USE_REROLL, ActionType.USE_REROLL)
        self.pickupReroll = binaryChoice(self.chromoData["currentChromosome"][3], ActionType.DONT_USE_REROLL, ActionType.USE_REROLL)
        self.passReroll = binaryChoice(self.chromoData["currentChromosome"][4], ActionType.DONT_USE_REROLL, ActionType.USE_REROLL)
        self.catchReroll = binaryChoice(self.chromoData["currentChromosome"][5], ActionType.DONT_USE_REROLL, ActionType.USE_REROLL)
        self.GFIReroll = binaryChoice(self.chromoData["currentChromosome"][6], ActionType.DONT_USE_REROLL, ActionType.USE_REROLL)
        self.bloodlustReroll = binaryChoice(self.chromoData["currentChromosome"][7], ActionType.DONT_USE_REROLL, ActionType.USE_REROLL)
        self.blockReroll = binaryChoice(self.chromoData["currentChromosome"][8], ActionType.DONT_USE_REROLL, ActionType.USE_REROLL)
        self.apothecaryChoice = binaryChoice(self.chromoData["currentChromosome"][9], ActionType.DONT_USE_APOTHECARY, ActionType.USE_APOTHECARY)
        self.juggernautSkill = binaryChoice(self.chromoData["currentChromosome"][10], ActionType.DONT_USE_SKILL, ActionType.USE_SKILL)
        self.wrestleSkill = binaryChoice(self.chromoData["currentChromosome"][11], ActionType.DONT_USE_SKILL, ActionType.USE_SKILL)
        self.standFirmSkill = binaryChoice(self.chromoData["currentChromosome"][12], ActionType.DONT_USE_SKILL, ActionType.USE_SKILL)
        self.proSkill = binaryChoice(self.chromoData["currentChromosome"][13], ActionType.DONT_USE_SKILL, ActionType.USE_SKILL)
        self.useBribe = binaryChoice(self.chromoData["currentChromosome"][14], ActionType.DONT_USE_BRIBE, ActionType.USE_BRIBE)

        ## Genes 16-70, all chance-based decisions (if chance of success greater than x, do such and such...).
        ## Genes are split into sets of 3 and 2 bits translated as Binary Coded Decimal and added together to work as intervals of 10% (0%, 10%, 20%, etc.)
        self.tdPathLim1 = float(int(self.chromoData["currentChromosome"][15:18], 2) + int(self.chromoData["currentChromosome"][18:20], 2)) / 10 ## default 0.7
        self.tdPathLim2 = float(int(self.chromoData["currentChromosome"][20:23], 2) + int(self.chromoData["currentChromosome"][23:25], 2)) / 10 ## default 0.9
        self.handoffLim = float(int(self.chromoData["currentChromosome"][25:28], 2) + int(self.chromoData["currentChromosome"][28:30], 2)) / 10 ## default 0.7
        self.blockLim = float(int(self.chromoData["currentChromosome"][30:33], 2) + int(self.chromoData["currentChromosome"][33:35], 2)) / 10 ## default 0.94
        self.fumbleLim = float(int(self.chromoData["currentChromosome"][35:38], 2) + int(self.chromoData["currentChromosome"][38:40], 2)) / 10 ## default 0.0
        self.pickupLim = float(int(self.chromoData["currentChromosome"][40:43], 2) + int(self.chromoData["currentChromosome"][43:45], 2)) / 10 ## default 0.33
        self.recPathLim = float(int(self.chromoData["currentChromosome"][45:48], 2) + int(self.chromoData["currentChromosome"][48:50], 2)) / 10 ## default 1.0
        self.blitzLim = float(int(self.chromoData["currentChromosome"][50:53], 2) + int(self.chromoData["currentChromosome"][53:55], 2)) / 5 ## default 1.25, intervals of 20%
        self.cageLim = float(int(self.chromoData["currentChromosome"][55:58], 2) + int(self.chromoData["currentChromosome"][58:60], 2)) / 10 ## default 0.94
        self.assPathLim = float(int(self.chromoData["currentChromosome"][60:63], 2) + int(self.chromoData["currentChromosome"][63:65], 2)) / 10 #d# efault 1.0
        self.moveLim = float(int(self.chromoData["currentChromosome"][65:68], 2) + int(self.chromoData["currentChromosome"][68:70], 2)) / 10 ## default 1.0 combine w/assPathLim and recPathLim?

        ## Genes 71-134, determining the order of _make_plan(), one byte per function in _make_plan(), bytes are treated as weights to determine ordering
        order = {}
        for i in range(8):
            start = (i * 8) + 70
            end = (i * 8) + 78
            order[i] = int(self.chromoData["currentChromosome"][start:end], 2)
        self.order = sorted(order.items(), key=lambda x:x[1])

    def new_game(self, game, team):
        """
        Called when a new game starts.
        """
        self.my_team = team
        self.opp_team = game.get_opp_team(team)
        self.last_turn = 0
        self.last_half = 0

    def coin_toss_flip(self, game):
        """
        Select heads/tails and/or kick/receive
        """
        return Action(self.coinChoice)
        # return Action(ActionType.TAILS)
        # return Action(ActionType.HEADS)

    def coin_toss_kick_receive(self, game):
        """
        Select heads/tails and/or kick/receive
        """
        return Action(self.kickChoice)
        # return Action(ActionType.RECEIVE)
        # return Action(ActionType.KICK)

    def setup(self, game):
        """
        Use either a Wedge offensive formation or zone defensive formation.
        """
        # Update teams
        self.my_team = game.get_team_by_id(self.my_team.team_id)
        self.opp_team = game.get_opp_team(self.my_team)

        if self.setup_actions:
            action = self.setup_actions.pop(0)
            return action

        # If traditional board size
        if game.arena.width == 28 and game.arena.height == 17:
            if game.get_receiving_team() == self.my_team:
                self.setup_actions = self.off_formation.actions(game, self.my_team)
                self.setup_actions.append(Action(ActionType.END_SETUP))
            else:
                self.setup_actions = self.def_formation.actions(game, self.my_team)
                self.setup_actions.append(Action(ActionType.END_SETUP))
            action = self.setup_actions.pop(0)
            return action

        # If smaller variant - use built-in setup actions

        for action_choice in game.get_available_actions():
            if action_choice.action_type != ActionType.END_SETUP and action_choice.action_type != ActionType.PLACE_PLAYER:
                self.setup_actions.append(Action(ActionType.END_SETUP))
                return Action(action_choice.action_type)

        # This should never happen
        return None

    def perfect_defense(self, game):
        return Action(ActionType.END_SETUP)

    def reroll(self, game):
        """
        Select between USE_REROLL and DONT_USE_REROLL
        """
        reroll_proc = game.get_procedure()
        context = reroll_proc.context
        if type(context) == botbowl.Dodge:
            return Action(self.dodgeReroll)
        if type(context) == botbowl.Pickup:
            return Action(self.pickupReroll)
        if type(context) == botbowl.PassAttempt:
            return Action(self.passReroll)
        if type(context) == botbowl.Catch:
            return Action(self.catchReroll)
        if type(context) == botbowl.GFI:
            return Action(self.GFIReroll)
        if type(context) == botbowl.BloodLust:
            return Action(self.bloodlustReroll)
        if type(context) == botbowl.Block:
            attacker = context.attacker
            attackers_down = 0
            for die in context.roll.dice:
                if die.get_value() == BBDieResult.ATTACKER_DOWN:
                    attackers_down += 1
                elif die.get_value() == BBDieResult.BOTH_DOWN and not attacker.has_skill(Skill.BLOCK) and not attacker.has_skill(Skill.WRESTLE):
                    attackers_down += 1
            if attackers_down > 0 and context.favor != self.my_team:
                return Action(ActionType.USE_REROLL)
            if attackers_down == len(context.roll.dice) and context.favor != self.opp_team:
                return Action(ActionType.USE_REROLL)
            return Action(ActionType.DONT_USE_REROLL)
        return Action(ActionType.DONT_USE_REROLL)

    def place_ball(self, game):
        """
        Place the ball when kicking.
        """
        side_width = game.arena.width / 2
        side_height = game.arena.height
        squares_from_left = math.ceil(side_width / 2)
        squares_from_right = math.ceil(side_width / 2)
        squares_from_top = math.floor(side_height / 2)
        left_center = Square(squares_from_left, squares_from_top)
        right_center = Square(game.arena.width - 1 - squares_from_right, squares_from_top)
        if game.is_team_side(left_center, self.opp_team):
            return Action(ActionType.PLACE_BALL, position=left_center)
        return Action(ActionType.PLACE_BALL, position=right_center)

    def high_kick(self, game):
        """
        Select player to move under the ball.
        """
        ball_pos = game.get_ball_position()
        if game.is_team_side(game.get_ball_position(), self.my_team) and \
                game.get_player_at(game.get_ball_position()) is None:
            for player in game.get_players_on_pitch(self.my_team, up=True):
                if Skill.BLOCK in player.get_skills() and game.num_tackle_zones_in(player) == 0:
                    return Action(ActionType.SELECT_PLAYER, player=player, position=ball_pos)
        return Action(ActionType.SELECT_NONE)

    def touchback(self, game):
        """
        Select player to give the ball to.
        """
        p = None
        for player in game.get_players_on_pitch(self.my_team, up=True):
            if Skill.BLOCK in player.get_skills():
                return Action(ActionType.SELECT_PLAYER, player=player)
            p = player
        return Action(ActionType.SELECT_PLAYER, player=p)

    def turn(self, game):
        """
        Start a new player action.
        """
        # Update teams
        self.my_team = game.get_team_by_id(self.my_team.team_id)
        self.opp_team = game.get_opp_team(self.my_team)

        ## Update ball progression
        if game.get_opp_endzone_x(self.my_team) == 1:
            self.ball_dist = game.get_ball_position().x - game.get_opp_endzone_x(self.my_team)
        else:
            self.ball_dist = game.get_opp_endzone_x(self.my_team) - game.get_ball_position().x

        self.chromoData["ballProgress"] += self.ball_dist_prev - self.ball_dist
        self.ball_dist_prev = self.ball_dist

        # Reset actions if new turn
        turn = game.get_agent_team(self).state.turn
        half = game.state.half
        if half > self.last_half or turn > self.last_turn:
            self.actions.clear()
            self.last_turn = turn
            self.last_half = half
            self.actions = []
            #print(f"Half: {half}")
            #print(f"Turn: {turn}")

        # End turn if only action left
        if len(game.state.available_actions) == 1:
            if game.state.available_actions[0].action_type == ActionType.END_TURN:
                self.actions = [Action(ActionType.END_TURN)]

        # Execute planned actions if any
        while len(self.actions) > 0:
            action = self._get_next_action()
            if game._is_action_allowed(action):
                return action

        # Split logic depending on offense, defense, and loose ball - and plan actions
        ball_carrier = game.get_ball_carrier()
        self._make_plan(game, ball_carrier)
        action = self._get_next_action()
        return action

    def _get_next_action(self):
        action = self.actions[0]
        self.actions = self.actions[1:]
        #print(f"Action: {action.to_json()}")
        return action

    ## Main plan function, originally used safest order of actions (least risky to most risky)
    def _make_plan(self, game: botbowl.Game, ball_carrier):
        #print("1. Stand up marked players")
        if (self._stand_marked_players(game) == 0):
            return

        openLogged = False

        for i in self.order:
            match i[0]:
                case 0:
                    #print("2. Move ball carrier to endzone")
                    if (self._move_ball_carrier(game, ball_carrier) == 0):
                        return
                case 1:
                    #print("3. Safe blocks")
                    if (self._safe_blocks(game) == 0):
                        return
                case 2:
                    #print("4. Pickup ball")
                    if (self._pickup_ball(game) == 0):
                        return
                case 3:
                    if not openLogged:
                        ## Scan for unused players that are not marked
                        open_players = self._open_players(game)
                        openLogged = True
                    #print("5. Move receivers into scoring distance if not already")
                    if (self._move_receivers(game, ball_carrier, open_players) == 0):
                        return
                case 4:
                    if not openLogged:
                        ## Scan for unused players that are not marked
                        open_players = self._open_players(game)
                        openLogged = True
                    #print("6. Blitz with open block players")
                    if (self._blitz(game, open_players) == 0):
                        return
                case 5:
                    if not openLogged:
                        ## Scan for unused players that are not marked
                        open_players = self._open_players(game)
                        openLogged = True
                    #print("7. Make cage around ball carrier")
                    if (self._cage_carrier(game, ball_carrier, open_players) == 0):
                        return
                case 6:
                    if not openLogged:
                        # Scan for unused players that are not marked
                        open_players = self._open_players(game)
                        openLogged = True
                    ## Scan for assist positions
                    assist_positions = self._assist_positions(game)
                    #print("8. Move non-marked players to assist")
                    if (self._move_to_assist(game, open_players, assist_positions) == 0):
                        return
                case 7:
                    if not openLogged:
                        ## Scan for unused players that are not marked
                        open_players = self._open_players(game)
                        openLogged = True
                    #print("9. Move towards the ball")
                    if (self._move_to_ball(game, ball_carrier, open_players) == 0):
                        return
                case _:
                    pass

        #print("10. Risky blocks")
        if (self._risky_blocks(game) == 0):
            return

        #print("11. End turn")
        if (self.actions.append(Action(ActionType.END_TURN)) == 0):
            return


## Each of these functions was originally in _make_plan(), extracted to separate functions to mix up ordering
    def _stand_marked_players(self, game):
         for player in self.my_team.players:
            if player.position is not None and not player.state.up and not player.state.stunned and not player.state.used:
                if game.num_tackle_zones_in(player) > 0:
                    self.actions.append(Action(ActionType.START_MOVE, player=player))
                    self.actions.append(Action(ActionType.STAND_UP))
#                    print(f"Stand up marked player {player.role.name}")
                    return 0

    def _move_ball_carrier(self, game, ball_carrier):
        if ball_carrier is not None and ball_carrier.team == self.my_team and not ball_carrier.state.used:
#            print("2.1 Can ball carrier score with high probability")
            td_path = pf.get_safest_path_to_endzone(game, ball_carrier, allow_team_reroll=True)
            if td_path is not None and td_path.prob >= self.tdPathLim1:
                self.actions.append(Action(ActionType.START_MOVE, player=ball_carrier))
                self.actions.extend(path_to_move_actions(game, ball_carrier, td_path))
#                print(f"Score with ball carrier, p={td_path.prob}")
                return 0

#            print("2.2 Hand-off action to scoring player")
            if game.is_handoff_available():

                # Get players in scoring range
                unused_teammates = []
                for player in self.my_team.players:
                    if player.position is not None and player != ball_carrier and not player.state.used and player.state.up:
                        unused_teammates.append(player)

                # Find other players in scoring range
                handoff_p = None
                handoff_path = None
                for player in unused_teammates:
                    if game.get_distance_to_endzone(player) > player.num_moves_left():
                        continue
                    td_path = pf.get_safest_path_to_endzone(game, player, allow_team_reroll=True)
                    if td_path is None:
                        continue
                    handoff_path = pf.get_safest_path(game, ball_carrier, player.position, allow_team_reroll=True)
                    if handoff_path is None:
                        continue
                    p_catch = game.get_catch_prob(player, handoff=True, allow_catch_reroll=True, allow_team_reroll=True)
                    p = td_path.prob * handoff_path.prob * p_catch
                    if handoff_p is None or p > handoff_p:
                        handoff_p = p
                        handoff_path = handoff_path

                # Hand-off if high probability or last turn
                if handoff_path is not None and (handoff_p >= self.handoffLim or self.my_team.state.turn == 8):
                    self.actions.append(Action(ActionType.START_HANDOFF, player=ball_carrier))
                    self.actions.extend(path_to_move_actions(game, ball_carrier, handoff_path))
                    return 0

#            print("2.3 Move safely towards the endzone")
            if game.num_tackle_zones_in(ball_carrier) == 0:
                paths = pf.get_all_paths(game, ball_carrier)
                best_path = None
                best_distance = 100
                target_x = game.get_opp_endzone_x(self.my_team)
                for path in paths:
                    distance_to_endzone = abs(target_x - path.steps[-1].x)
                    if path.prob == 1 and (best_path is None or distance_to_endzone < best_distance) and game.num_tackle_zones_at(ball_carrier, path.get_last_step()) == 0:
                        best_path = path
                        best_distance = distance_to_endzone
                if best_path is not None:
                    self.actions.append(Action(ActionType.START_MOVE, player=ball_carrier))
                    self.actions.extend(path_to_move_actions(game, ball_carrier, best_path))
#                    print(f"Move ball carrier {ball_carrier.role.name}")
                    return 0

    def _safe_blocks(self, game):
        attacker, defender, p_self_up, p_opp_down, block_p_fumble_self, block_p_fumble_opp = self._get_safest_block(game)
        if attacker is not None and p_self_up > self.blockLim and block_p_fumble_self <= self.fumbleLim:
            self.actions.append(Action(ActionType.START_BLOCK, player=attacker))
            self.actions.append(Action(ActionType.BLOCK, position=defender.position))
#            print(f"Safe block with {attacker.role.name} -> {defender.role.name}, p_self_up={p_self_up}, p_opp_down={p_opp_down}")
            return 0

    def _pickup_ball(self, game):
        if game.get_ball_carrier() is None:
            pickup_p = None
            pickup_player = None
            pickup_path = None
            for player in self.my_team.players:
                if player.position is not None and not player.state.used:
                    if player.position.distance(game.get_ball_position()) <= player.get_ma() + 2:
                        path = pf.get_safest_path(game, player, game.get_ball_position())
                        if path is not None:
                            p = path.prob
                            if pickup_p is None or p > pickup_p:
                                pickup_p = p
                                pickup_player = player
                                pickup_path = path
            if pickup_player is not None and pickup_p > self.pickupLim:
                self.actions.append(Action(ActionType.START_MOVE, player=pickup_player))
                self.actions.extend(path_to_move_actions(game, pickup_player, pickup_path))
#                print(f"Pick up the ball with {pickup_player.role.name}, p={pickup_p}")
                # Find safest path towards endzone
                if game.num_tackle_zones_at(pickup_player, game.get_ball_position()) == 0 and game.get_opp_endzone_x(self.my_team) != game.get_ball_position().x:
                    paths = pf.get_all_paths(game, pickup_player, from_position=game.get_ball_position(), num_moves_used=len(pickup_path))
                    best_path = None
                    best_distance = 100
                    target_x = game.get_opp_endzone_x(self.my_team)
                    for path in paths:
                        distance_to_endzone = abs(target_x - path.steps[-1].x)
                        if path.prob == 1 and (best_path is None or distance_to_endzone < best_distance) and game.num_tackle_zones_at(pickup_player, path.get_last_step()) == 0:
                            best_path = path
                            best_distance = distance_to_endzone
                    if best_path is not None:
                        self.actions.extend(path_to_move_actions(game, pickup_player, best_path, do_assertions=False))
#                        print(f"- Move ball carrier {pickup_player.role.name}")
                return 0

    def _open_players(self, game):
        ## Supplementary step, needed before certain steps in _make_plan()
        open_players = []
        for player in self.my_team.players:
            if player.position is not None and not player.state.used and game.num_tackle_zones_in(player) == 0:
                open_players.append(player)
        return open_players

    def _move_receivers(self, game, ball_carrier, open_players):
        for player in open_players:
            if player.has_skill(Skill.CATCH) and player != ball_carrier:
                if game.get_distance_to_endzone(player) > player.num_moves_left():
                    continue
                paths = pf.get_all_paths(game, player)
                best_path = None
                best_distance = math.inf ## changed from 100 to infinity just in case field size were increased
                target_x = game.get_opp_endzone_x(self.my_team)
                for path in paths:
                    distance_to_endzone = abs(target_x - path.steps[-1].x)
                    if path.prob >= self.recPathLim and (best_path is None or distance_to_endzone < best_distance) and game.num_tackle_zones_at(player, path.get_last_step()):
                        best_path = path
                        best_distance = distance_to_endzone
                if best_path is not None:
                    self.actions.append(Action(ActionType.START_MOVE, player=player))
                    self.actions.extend(path_to_move_actions(game, player, best_path))
#                    print(f"Move receiver {player.role.name}")
                    return 0

    def _blitz(self, game, open_players):
        if game.is_blitz_available():

            best_blitz_attacker = None
            best_blitz_defender = None
            best_blitz_score = None
            best_blitz_path = None
            for blitzer in open_players:
                if blitzer.position is not None and not blitzer.state.used and blitzer.has_skill(Skill.BLOCK):
                    blitz_paths = pf.get_all_paths(game, blitzer, blitz=True)
                    for path in blitz_paths:
                        defender = game.get_player_at(path.get_last_step())
                        if defender is None:
                            continue
                        from_position = path.steps[-2] if len(path.steps)>1 else blitzer.position
                        p_self, p_opp, p_fumble_self, p_fumble_opp = game.get_blitz_probs(blitzer, from_position, defender)
                        p_self_up = path.prob * (1-p_self)
                        p_opp = path.prob * p_opp
                        p_fumble_opp = p_fumble_opp * path.prob
                        if blitzer == game.get_ball_carrier():
                            p_fumble_self = path.prob + (1 - path.prob) * p_fumble_self
                        score = p_self_up + p_opp + p_fumble_opp - p_fumble_self
                        if best_blitz_score is None or score > best_blitz_score:
                            best_blitz_attacker = blitzer
                            best_blitz_defender = defender
                            best_blitz_score = score
                            best_blitz_path = path
            if best_blitz_attacker is not None and best_blitz_score >= self.blitzLim:
                self.actions.append(Action(ActionType.START_BLITZ, player=best_blitz_attacker))
                self.actions.extend(path_to_move_actions(game, best_blitz_attacker, best_blitz_path))
#                print(f"Blitz with {best_blitz_attacker.role.name}, score={best_blitz_score}")
                return 0

    def _cage_carrier(self, game, ball_carrier, open_players):
        cage_positions = [
            Square(game.get_ball_position().x - 1, game.get_ball_position().y - 1),
            Square(game.get_ball_position().x + 1, game.get_ball_position().y - 1),
            Square(game.get_ball_position().x - 1, game.get_ball_position().y + 1),
            Square(game.get_ball_position().x + 1, game.get_ball_position().y + 1)
        ]
        if ball_carrier is not None:
            for cage_position in cage_positions:
                if game.get_player_at(cage_position) is None and not game.is_out_of_bounds(cage_position):
                    for player in open_players:
                        if player == ball_carrier or player.position in cage_positions:
                            continue
                        if player.position.distance(cage_position) > player.num_moves_left():
                            continue
                        if game.num_tackle_zones_in(player) > 0:
                            continue
                        path = pf.get_safest_path(game, player, cage_position)
                        if path is not None and path.prob > self.cageLim:
                            self.actions.append(Action(ActionType.START_MOVE, player=player))
                            self.actions.extend(path_to_move_actions(game, player, path))
#                            print(f"Make cage around towards ball carrier {player.role.name}")
                            return 0

    def _assist_positions(self, game):
        ## Supplementary step, needed before certain steps in _make_plan()
        assist_positions = set()
        for player in game.get_opp_team(self.my_team).players:
            if player.position is None or not player.state.up:
                continue
            for opponent in game.get_adjacent_opponents(player, down=False):
                att_str, def_str = game.get_block_strengths(player, opponent)
                if def_str >= att_str:
                    for open_position in game.get_adjacent_squares(player.position, occupied=False):
                        if len(game.get_adjacent_players(open_position, team=self.opp_team, down=False)) == 1:
                            assist_positions.add(open_position)
        return assist_positions

    def _move_to_assist(self, game, open_players, assist_positions):
        for player in open_players:
            for path in pf.get_all_paths(game, player):
                if path.prob < self.assPathLim or path.get_last_step() not in assist_positions:
                    continue
                self.actions.append(Action(ActionType.START_MOVE, player=player))
                self.actions.extend(path_to_move_actions(game, player, path))
#                print(f"Move assister {player.role.name} to {path.get_last_step().to_json}")
                return 0

    def _move_to_ball(self, game, ball_carrier, open_players):
        for player in open_players:
            if player == ball_carrier or game.num_tackle_zones_in(player) > 0:
                continue

            shortest_distance = None
            path = None

            if ball_carrier is None:
                for p in pf.get_all_paths(game, player):
                    distance = p.get_last_step().distance(game.get_ball_position())
                    if shortest_distance is None or (p.prob == self.moveLim and distance < shortest_distance):
                        shortest_distance = distance
                        path = p
            elif ball_carrier.team != self.my_team:
                for p in pf.get_all_paths(game, player):
                    distance = p.get_last_step().distance(ball_carrier.position)
                    if shortest_distance is None or (p.prob == self.moveLim and distance < shortest_distance):
                        shortest_distance = distance
                        path = p

            if path is not None:
                self.actions.append(Action(ActionType.START_MOVE, player=player))
                self.actions.extend(path_to_move_actions(game, player, path))
#                print(f"Move towards ball {player.role.name}")
                return 0

    def _risky_blocks(self, game):
        attacker, defender, p_self_up, p_opp_down, block_p_fumble_self, block_p_fumble_opp = self._get_safest_block(game)
        if attacker is not None and (p_opp_down > (1-p_self_up) or block_p_fumble_opp > 0): #leave? seems like last option and fills rest of turn with possible actions
            self.actions.append(Action(ActionType.START_BLOCK, player=attacker))
            self.actions.append(Action(ActionType.BLOCK, position=defender.position))
#            print(f"Block with {player.role.name} -> {defender.role.name}, p_self_up={p_self_up}, p_opp_down={p_opp_down}")
            return 0

## End of _make_plan() extraction

    def _get_safest_block(self, game):
        block_attacker = None
        block_defender = None
        block_p_self_up = None
        block_p_opp_down = None
        block_p_fumble_self = None
        block_p_fumble_opp = None
        for attacker in self.my_team.players:
            if attacker.position is not None and not attacker.state.used and attacker.state.up:
                for defender in game.get_adjacent_opponents(attacker, down=False):
                    p_self, p_opp, p_fumble_self, p_fumble_opp = game.get_block_probs(attacker, defender)
                    p_self_up = (1-p_self)
                    if block_p_self_up is None or (p_self_up > block_p_self_up and p_opp >= p_fumble_self):
                        block_p_self_up = p_self_up
                        block_p_opp_down = p_opp
                        block_attacker = attacker
                        block_defender = defender
                        block_p_fumble_self = p_fumble_self
                        block_p_fumble_opp = p_fumble_opp
        return block_attacker, block_defender, block_p_self_up, block_p_opp_down, block_p_fumble_self, block_p_fumble_opp

    def quick_snap(self, game):
        return Action(ActionType.END_TURN)

    def blitz(self, game):
        return Action(ActionType.END_TURN)

    def player_action(self, game):
        # Execute planned actions if any
        while len(self.actions) > 0:
            action = self._get_next_action()
            if game._is_action_allowed(action):
                return action

        ball_carrier = game.get_ball_carrier()
        if ball_carrier == game.get_active_player():
            td_path = pf.get_safest_path_to_endzone(game, ball_carrier)
            if td_path is not None and td_path.prob <= self.tdPathLim2:
                self.actions.extend(path_to_move_actions(game, ball_carrier, td_path))
                #print(f"Scoring with {ball_carrier.role.name}, p={td_path.prob}")
                return self._get_next_action()
        return Action(ActionType.END_PLAYER_TURN)

    def block(self, game):
        """
        Select block die or reroll.
        """
        # Get attacker and defender
        attacker = game.get_procedure().attacker
        defender = game.get_procedure().defender
        is_blitz = game.get_procedure().blitz
        dice = game.num_block_dice(attacker, defender, blitz=is_blitz)

        # Loop through available dice results
        actions = set()
        for action_choice in game.state.available_actions:
            actions.add(action_choice.action_type)

        # 1. DEFENDER DOWN
        if ActionType.SELECT_DEFENDER_DOWN in actions:
            return Action(ActionType.SELECT_DEFENDER_DOWN)

        if ActionType.SELECT_DEFENDER_STUMBLES in actions and not (defender.has_skill(Skill.DODGE) and not attacker.has_skill(Skill.TACKLE)):
            return Action(ActionType.SELECT_DEFENDER_STUMBLES)

        if ActionType.SELECT_BOTH_DOWN in actions and not defender.has_skill(Skill.BLOCK) and attacker.has_skill(Skill.BLOCK):
            return Action(ActionType.SELECT_BOTH_DOWN)

        # 2. BOTH DOWN if opponent carries the ball and doesn't have block
        if ActionType.SELECT_BOTH_DOWN in actions and game.get_ball_carrier() == defender and not defender.has_skill(Skill.BLOCK):
            return Action(ActionType.SELECT_BOTH_DOWN)

        # 3. USE REROLL if defender carries the ball
        if ActionType.USE_REROLL in actions and game.get_ball_carrier() == defender:
            return Action(ActionType.USE_REROLL)

        # 4. PUSH
        if ActionType.SELECT_DEFENDER_STUMBLES in actions:
            return Action(ActionType.SELECT_DEFENDER_STUMBLES)

        if ActionType.SELECT_PUSH in actions:
            return Action(ActionType.SELECT_PUSH)

        # 5. BOTH DOWN
        if ActionType.SELECT_BOTH_DOWN in actions:
            return Action(ActionType.SELECT_BOTH_DOWN)

        # 6. USE REROLL to avoid attacker down unless a one-die block
        if ActionType.USE_REROLL in actions and dice > 1:
            return Action(ActionType.USE_REROLL)

        # 7. ATTACKER DOWN
        if ActionType.SELECT_ATTACKER_DOWN in actions:
            return Action(ActionType.SELECT_ATTACKER_DOWN)

    def push(self, game):
        """
        Select square to push to.
        """
        # Loop through available squares
        for position in game.state.available_actions[0].positions:
            return Action(ActionType.PUSH, position=position)

    def follow_up(self, game):
        """
        Follow up or not. ActionType.FOLLOW_UP must be used together with a position.
        """
        player = game.state.active_player
        for position in game.state.available_actions[0].positions:
            # Always follow up
            if player.position != position:
                return Action(ActionType.FOLLOW_UP, position=position)

    def apothecary(self, game):
        """
        Use apothecary?
        """
        return Action(self.apothecaryChoice)
        # return Action(ActionType.USE_APOTHECARY)
        # return Action(ActionType.DONT_USE_APOTHECARY)

    def interception(self, game):
        """
        Select interceptor.
        """
        for action in game.state.available_actions:
            if action.action_type == ActionType.SELECT_PLAYER:
                for player, rolls in zip(action.players, action.rolls):
                    return Action(ActionType.SELECT_PLAYER, player=player)
        return Action(ActionType.SELECT_NONE)

    def pass_action(self, game):
        """
        Reroll or not.
        """
        return Action(self.passReroll)
        # return Action(ActionType.USE_REROLL)
        # return Action(ActionType.DONT_USE_REROLL)

    def catch(self, game):
        """
        Reroll or not.
        """
        return Action(self.catchReroll)
        # return Action(ActionType.USE_REROLL)
        # return Action(ActionType.DONT_USE_REROLL)

    def gfi(self, game):
        """
        Reroll or not.
        """
        return Action(self.GFIReroll)
        # return Action(ActionType.USE_REROLL)
        # return Action(ActionType.DONT_USE_REROLL)

    def dodge(self, game):
        """
        Reroll or not.
        """
        return Action(self.dodgeReroll)
        # return Action(ActionType.USE_REROLL)
        # return Action(ActionType.DONT_USE_REROLL)

    def pickup(self, game):
        """
        Reroll or not.
        """
        return Action(self.pickupReroll)
        # return Action(ActionType.USE_REROLL)
        # return Action(ActionType.DONT_USE_REROLL)

    def use_juggernaut(self, game):
        return Action(self.juggernautSkill)
        # return Action(ActionType.USE_SKILL)
        # return Action(ActionType.DONT_USE_SKILL)

    def use_wrestle(self, game):
        return Action(self.wrestleSkill)
        # return Action(ActionType.USE_SKILL)
        # return Action(ActionType.DONT_USE_SKILL)

    def use_stand_firm(self, game):
        return Action(self.standFirmSkill)
        # return Action(ActionType.USE_SKILL)
        # return Action(ActionType.DONT_USE_SKILL)

    def use_pro(self, game):
        return Action(self.proSkill)
        # return Action(ActionType.USE_SKILL)
        # return Action(ActionType.DONT_USE_SKILL)

    def use_bribe(self, game):
        return Action(self.useBribe)
        # return Action(ActionType.USE_BRIBE)

    def blood_lust_block_or_move(self, game):
        return Action(ActionType.START_BLOCK)

    def eat_thrall(self, game):
        position = game.get_available_actions()[0].positions[0]
        return Action(ActionType.SELECT_PLAYER, position)

    ## Output results, save fitness function metrics to json file
    def end_game(self, game):
        """
        Called when a game ends.
        """
        winner = game.get_winning_team()
        output = "Casualties: " + str(game.num_casualties()) + "\n"
        if winner is None:
            output += "It's a draw, "
        elif winner == self.my_team:
            output += f"{self.name} won, "
        else:
            output += f"{self.name} lost, "
        output += f"{self.my_team.state.score} - {self.opp_team.state.score}"
#        output += self.chromoData["currentChromosome"] + "\n"
#        print(output)
        with open(self.filename, 'w', encoding='utf-8') as chromoFile:
            json.dump(self.chromoData, chromoFile, indent=4)

def path_to_move_actions(game: botbowl.Game, player: botbowl.Player, path: Path, do_assertions=True) -> List[Action]:
    """
    This function converts a path into a list of actions corresponding to that path.
    If you provide a handoff, foul or blitz path, then you have to manally set action type.
    :param game:
    :param player: player to move
    :param path: a path as returned by the pathfinding algorithms
    :param do_assertions: if False, it turns off the validation, can be helpful when the GameState will change before
                          this path is executed.
    :returns: List of actions corresponding to 'path'.
    """

    if path.block_dice is not None:
        action_type = ActionType.BLOCK
    elif path.handoff_roll is not None:
        action_type = ActionType.HANDOFF
    elif path.foul_roll is not None:
        action_type = ActionType.FOUL
    else:
        action_type = ActionType.MOVE

    active_team = game.state.available_actions[0].team
    player_at_target = game.get_player_at(path.get_last_step())

    if do_assertions:
        if action_type is ActionType.MOVE:
            assert player_at_target is None or player_at_target is game.get_active_player()
        elif action_type is ActionType.BLOCK:
            assert game.get_opp_team(active_team) is player_at_target.team
            assert player_at_target.state.up
        elif action_type is ActionType.FOUL:
            assert game.get_opp_team(active_team) is player_at_target.team
            assert not player_at_target.state.up
        elif action_type is ActionType.HANDOFF:
            assert active_team is player_at_target.team
            assert player_at_target.state.up
        else:
            raise Exception(f"Unregonized action type {action_type}")

    final_action = Action(action_type, position=path.get_last_step())

    if game._is_action_allowed(final_action):
        return [final_action]
    else:
        actions = []
        if not player.state.up and path.steps[0] == player.position:
            actions.append(Action(ActionType.STAND_UP, player=player))
            actions.extend(Action(ActionType.MOVE, position=sq) for sq in path.steps[1:-1])
        else:
            actions.extend(Action(ActionType.MOVE, position=sq) for sq in path.steps[:-1])
        actions.append(final_action)
        return actions


## Register this bot with Bot Bowl for using in games
botbowl.register_bot('ga_scripted', GAScriptedBot)


def main(choiceIn = "c", oppIn = "r", popSizeIn = 100, numToSaveIn = 1, genLimIn = 100, numGamesIn = 5, threadIn = 0): ## these default values are overwritten at bottom of file
    now = datetime.now().strftime("%d-%m-%Y_%H.%M.%S") ## used for all filenames
    filename = f"{choiceIn}_{popSizeIn}_{genLimIn}_{numGamesIn}_{now}"
    ## GA Setup
    choice = choiceIn                       ## chromosomes, default, or best chromosome
    opponent = oppIn                        ## random (r) or scripted (s)
    chromoLen = 134                         ## Size of chromosomes, (134)
    popSize = popSizeIn                     ## Number of chromosomes per generation (100)
    pressure = 50                           ## Selection pressure percentage (50%, number of chromosomes to use in tournament)
    mutRate = 0.01                          ## Rate of mutation in chromosomes (0.01 = 1%)
    numToSave = numToSaveIn                 ## Number of best fit chromosomes to carry over between generations (5)
    ga = GeneticAlgorithm(chromoLen, popSize, mutRate, numToSave)
    match choice:
        case "d":
            ## Default Chromosome (roughly mimics original scripted bot)
            population = ["11111111111111111100111101110011110000000110011111110001111011111111110000000000000001000000100000001100000100000001010000011000000111"]
        case "c":
            ## GA Chromosome (default)
            population = ga.initialize_pop()
        case "b":
            ## Best chromosome at the moment (not finalized)
            population = ["00000010110110111011011100011110110100011000000110011001100100100111000110010001100101001001101101010110000101100111001110011010100001"]
        case "p":
            ## Uses the last saved population of chromosomes (useful for testing a converged population from Random on the Original Scripted Bot)
            with open("final_pop.json", "r", encoding="utf-8") as popFile:
                popData = json.load(popFile)
            population = []
            for chromo in popData["pop"]:
                population.append(chromo[0])
    found = False                           ## Used if specific target value trying to be met, we do not so not useful
    generation = 1                          ## Current generation
    generationLimit = genLimIn              ## Number of generations to simulate (100)
    numGames = numGamesIn                   ## Number of games to simulate per chromosome, results averaged to reduce randomness of chance (5)
    bestOverall = ["", -math.inf]           ## Best chromosome overall for graphing purposes
    worstOverall = ["", math.inf]           ## Worst chromosome overall for graphing purposes (worst of best chromosomes per pop)

    ## Saved to json file for ga bot to read from
    chromoData = {
        "currentChromosome" : population[0],
        "ballProgress" : 0
    }

    ## Determines which file is used by ga bot so data not overwritten is doing multiple concurrent runs, does not work currently
    thread = {"thread" : threadIn}

    plotFitness = [0] ## Array of best chromosomes for each population to graph
    totalTime = 0.0 ## Shows how long full run takes

    ## Plot and save results (initialize plot and text files)
    fig, ax = plt.subplots()
    ax.plot(plotFitness, 'b+-', label="Fitness")
    ax.plot(3.5, 'r', label="Baseline")
    ax.set_title(f"Fitness of GA Bot Over {generation} Generations")
    ax.set_xlabel("Generation")
    ax.set_ylabel("Most Fit Chromosome")
    ax.set_xlim(0, generation)
    yLimUp = 7
    yLimDown = 0
    ax.set_ylim(yLimDown, yLimUp)
    if generation < 10:
        xTicks = 1
    else:
        xTicks = generation // 10
    ax.set_xticks(range(0, generation, xTicks))
    yTicks = 1
    ax.set_yticks(np.arange(yLimDown, yLimUp, yTicks))
    ax.grid(which='major', color='#DDDDDD', linewidth=0.8)
    ax.grid(which='minor', color='#EEEEEE', linestyle=':', linewidth=0.5)
    ax.minorticks_on()
    ax.legend()

    ## Saves thread to file so bot knows which data file to use
    with open('thread.json', 'w', encoding='utf-8') as threadFile:
        json.dump(thread, threadFile, indent = 4)

    ## Save first chromosome of population to data file for bot to read and use as controller
    threadNum = thread["thread"]
#    print(filename)
    with open (f"data_{threadNum}.json", 'w', encoding='utf-8') as chromoFile:
        json.dump(chromoData, chromoFile, indent = 4)

    # Load configurations, rules, arena and teams
    config = botbowl.load_config("bot-bowl")
    config.competition_mode = False
    config.pathfinding_enabled = True
    # config = get_config("gym-7.json")
    # config = get_config("gym-5.json")
    # config = get_config("gym-3.json")
    ruleset = botbowl.load_rule_set(config.ruleset, all_rules=False)  # We don't need all the rules
    arena = botbowl.load_arena(config.arena)
    home = botbowl.load_team_by_filename("human", ruleset)
    away = botbowl.load_team_by_filename("human", ruleset)

    ## Loop until target found or generations max out
    while not found and generation <= generationLimit:

        ## List of (chromosome, fitness) tuples
        population_eval = []

        ## Avg performance of individual chromosomes in a pop
        for i in range (popSize):

            ## Update current chromosome for bot to use
            chromoData["currentChromosome"] = population[i]
            with open(f"data_{threadNum}.json", 'w', encoding='utf-8') as chromoFile:
                json.dump(chromoData, chromoFile, indent=4)

            ## Simulate games using GA bot against Scripted Bot
            wins = 0
            losses = 0
            tdsFor = 0
            tdsAgainst = 0
            ball_progression = 0 ## How many spaces towards endzone did ball go
            ## Play j games per chromosome
            print(f"\nGENERATION {generation} CHROMOSOME {i + 1}:\t{population[i]}")
            for j in range(numGames):
                home_agent = botbowl.make_bot('ga_scripted')
                home_agent.name = "GA Scripted Bot"
                if opponent == "r":
                    away_agent = botbowl.make_bot('random')
                    away_agent.name = "Random Bot"
                elif opponent == "s":
                    away_agent = botbowl.make_bot('scripted')
                    away_agent.name = "Scripted Bot"
                config.debug_mode = False
                game = botbowl.Game(j, home, away, home_agent, away_agent, config, arena=arena, ruleset=ruleset)
                game.config.fast_mode = True
                print("Starting game ", (j + 1))
                start = time.time()
                game.init()
                end = time.time()
                totalTime += end - start
                print(f"Time to complete: {end - start} seconds") ## Useful for estimating how long a full run will take

                wins += 1 if game.get_winning_team() is game.state.home_team else 0
                losses += 1 if game.get_winning_team() is game.state.away_team else 0
                tdsFor += game.state.home_team.state.score
                tdsAgainst += game.state.away_team.state.score
                with open(f"data_{threadNum}.json", 'r', encoding='utf-8') as chromoFile:
                    data = json.load(chromoFile)
                    chromoData["ballProgress"] = data["ballProgress"]
                    ball_progression += chromoData["ballProgress"]

            ## Log performance
#            chromo = population[i]
            output = f"Won {wins} game(s) out of {numGames}\n"
            output += f"Lost {losses} game(s) out of {numGames}\n"
            output += f"Drew {numGames - (wins + losses)} game(s) out of {numGames}\n"
            avgTDsFor = tdsFor / numGames
            avgTDsAgainst = tdsAgainst / numGames
            output += f"Average score: {avgTDsFor} - {avgTDsAgainst}\n"
            avgProgression = ball_progression / numGames
            output += f"Average ball progression per game = {avgProgression}\n"

            ## Calculate fitness of current chromosome
            population_eval.append(ga.fitness_cal(population[i], avgProgression, avgTDsFor, avgTDsAgainst, wins, losses, numGames)) ## Last few are not incorporated yet

            output+= f"Fitness: {population_eval[-1][1]}"
            print(output)

########## Bulk of GA ##########

        ## Sort by fitness, save if best/worst chromosome of top performers for plotting
        population_eval = sorted(population_eval, key = lambda x: x[1], reverse=True)
        if i == 0 or population_eval[0][1] > bestOverall[1]:
            bestOverall = population_eval[0]
        if i == 0 or population_eval[0][1] < worstOverall[1]:
            worstOverall = population_eval[0]

        ## Save population for testing against other opps after convergence
        with open("final_pop.json", "w", encoding='utf-8') as popFile:
                popData = {"pop": population_eval}
                json.dump(popData, popFile, indent=4)

        output = f"Choice: {choiceIn}, Population Size: {popSizeIn}, Elitism: {numToSaveIn}, Generations: {generation}, Games per Chromosome: {numGamesIn}, Thread: {threadIn}\n"
        output += f"{population_eval[0][0]} was the strongest candidate over {generation} generations, with a fitness score of {population_eval[0][1]}.\n"
#       output += f"{bestOverall[0]} was the best candidate detected throughout the generations, with a fitness score of {bestOverall[1]}.\n"
        totalHr = totalTime // 3600
        totalMin = (totalTime // 60) % 60
        totalSec = totalTime % 60
        convertedTime = f"{totalHr} hours, {totalMin} minutes, {totalSec} seconds"
        output += f"Total time to execute: {convertedTime}\n"
        avgTime = totalTime / (popSize * generation * numGames)
        output += f"Average game time: {avgTime}\n"
        output += f"Won {wins} games out of {numGames}\n"
        output += f"Lost {losses} game(s) out of {numGames}\n"
        output += f"Drew {numGames - (wins + losses)} game(s) out of {numGames}\n"
#        print(output)

        ## Save results (overwrites every generation in case run stops for any reason)
        with open(f'results/results_{filename}.txt', 'w', encoding='utf-8') as outputFile:
            outputFile.write(output + "\n")

        ## Add best chromosome to be plotted, also overwrites every gen
        ## Consider adding average fitness of entire population here
        plotFitness.append(population_eval[0][1])
        ax.set_title(f"Fitness of GA Bot Over {generation} Generations")
        ax.plot(plotFitness, 'b+-', label="Fitness")
        ax.axhline(3.5, color="red", label="Baseline")
        if generation < 10:
            xTicks = 1
        else:
            xTicks = generation // 10
        ax.set_xlim(1, generation)
        ax.set_xticks(range(1, generation, xTicks))
#        yLimUp = math.ceil(bestOverall[1])
#        yLimDown = math.floor(worstOverall[1])
#        ax.set_ylim(yLimDown, yLimUp)
#        yTicks = (abs(yLimUp) + abs(yLimDown)) // 10
#        ax.set_yticks(np.arange(yLimDown, yLimUp, yTicks))
        fig.savefig(f'results/plot_{filename}.png')

        ## Break if fitness converges/stalls too long (not using this anymore) 
        """
        avgChange = 1
        if generation > 9: ## If change stagnates, end sim
            new = np.array(plotFitness[generation - 6:])
            old = np.array(plotFitness[generation - 7:-1])
            dif = np.subtract(new, old)
            difList = dif.tolist()
            absDifs = [abs(num) for num in difList]
            avgChange = sum(absDifs) / 5 #avg change of best fit over last 5 generations
        """
        ## End if generation cap reached
        if generation == generationLimit:
            print(f"\nTarget found in {generation}\nCHROMOSOME: {population_eval[0][0]}\nFITNESS: {population_eval[0][1]}\n")
            break
        
        print(f"\nTop chromosome of generation {generation}: {population_eval[0][0]}, fitness: {population_eval[0][1]}\n")
        generation += 1

        ## Select parents using tournament style
        selected = ga.selection(population_eval, pressure)

        ## Mate parents to make new generation
        crossovered = ga.crossover(selected)

        ## Mutate the new generation for *variety*
        mutated = ga.mutate(crossovered)

        ## Replacement of old population with new generation, including elitism
        population = ga.replace(population_eval, mutated)

#    input("Press enter to exit the program...\n")

if __name__ == "__main__":
    ## Parser arguments for execution through terminal (these defaults overwrite the main() defaults)
    parser = argparse.ArgumentParser()
    parser.add_argument("--chromo", required=False, type=str, default="c", help="c - chromosomes; d - default; b - best chromo atm; p - previous population")
    parser.add_argument("--opp", required=False, type=str, default="r", help="r - random; s - scripted")
    parser.add_argument("--pop", required=False, type=int, default=100)
    parser.add_argument("--keep", required=False, type=int, default=5)
    parser.add_argument("--gen", required=False, type=int, default=100)
    parser.add_argument("--games", required=False, type=int, default=5)
    parser.add_argument("--thread", required=False, type=int, default = 0) ## Unless you are trying to fix the manual multithreading, leave this alone
    args = parser.parse_args()
    choice = args.chromo
    opp = args.opp
    popSize = args.pop
    numSave = args.keep
    genLim = args.gen
    numGames = args.games
    thread = args.thread

    main(choice, opp, popSize, numSave, genLim, numGames, thread)
