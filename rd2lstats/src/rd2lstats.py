import discord
import requests
import json
import csv
import sys
sys.path.append("..")

from constants.globalConstants import fantasy_kill_multiplier, fantasy_death_multiplier, fantasy_assist_multiplier, \
    fantasy_lasthit_multiplier, fantasy_gpm_multiplier, fantasy_ts_multiplier, fantasy_roshan_multiplier, \
    fantasy_wards_planted, fantasy_wards_dewarded, fantasy_camps_stacked, fantasy_first_blood, fantasy_stuns_multiplier, \
    pos1directory, pos1gpmfile, pos2directory, pos2gpmfile, pos3directory, pos3gpmfile, pos4directory, \
    pos4gpmfile, pos5directory, pos5gpmfile, pos1kdafile, pos2kdafile, pos4kdafile, pos3kdafile, pos5kdafile, \
    pos1fantasyfile, pos2fantasyfile, pos3fantasyfile, pos4fantasyfile, pos5fantasyfile, match_ids, \
    opendota_api_matches_url, dotabuff_url, opendota_api_players_url, admin_ids, steam_cdn, permissionkeyfile
from constants.hero_ids import get_hero_name
import time
import ast
import copy

from src.utils import process_dict_values_into_list, list_difference, write_to_pos_based_csv_files, \
    find_player_in_dictionaries, empty_all_stat_files

client = discord.Client()
permissionkey = open(permissionkeyfile).read()

class Rd2lStats:

    def __init__(self, api_key):
        self.highest_gpm_value = 0
        self.highest_gpm_hero = 0
        self.highest_gpm_player = ""
        self.highest_gpm_match = ""

        self.highest_xpm_value = 0
        self.highest_xpm_player = ""
        self.highest_xpm_hero = 0
        self.highest_xpm_match = ""

        self.highest_kda_value = 0
        self.highest_kda_player = ""
        self.highest_kda_hero = 0
        self.highest_kda_match = ""

        self.highest_camps_value = 0
        self.highest_camps_player = ""
        self.highest_camps_hero = 0
        self.highest_camps_match = ""

        self.highest_herodamage_value = 0
        self.highest_herodamage_player = ""
        self.highest_herodamage_hero = 0
        self.highest_herodamage_match = ""

        self.highest_stuns_value = 0
        self.highest_stuns_player = ""
        self.highest_stuns_hero = 0
        self.highest_stuns_match = ""

        self.highest_towerdamage_value = 0
        self.highest_towerdamage_player = ""
        self.highest_towerdamage_hero = 0
        self.highest_towerdamage_match = ""

        self.highest_lane_value = 0
        self.highest_lane_hero = 0
        self.highest_lane_player = ""
        self.highest_lane_match = ""

        self.highest_deward_value = 0
        self.highest_deward_player = ""
        self.highest_deward_hero = 0
        self.highest_deward_match = ""

        self.highest_apm_value = 0
        self.highest_apm_player = ""
        self.highest_apm_hero = 0
        self.highest_apm_match = ""

        self.highest_courier_value = 0
        self.highest_courier_player = ""
        self.highest_courier_hero = 0
        self.highest_courier_match = ""

        self.stats_leaders_dict = {}
        self.current_week = 2

    # Function that calculates the fantasy score for a player object
    def get_fantasy_score(self, player):
        first_blood_claimed = 0 if player["firstblood_claimed"] is None else player["firstblood_claimed"]
        roshans = (player["roshan_kills"]*1000/player["duration"] if "roshan_kills" in player else player["roshans_killed"]/player["duration"])
        roshan_kills = 0 if roshans is None else roshans
        towers_killed = player["towers_killed"] if player["towers_killed"] is not None else 0
        obs_placed = player["obs_placed"]*1000/player["duration"] if player["obs_placed"] is not None else 0
        sentry_kills = player["sentry_kills"]*1000/player["duration"] if (
                "sentry_kills" in player and player["sentry_kills"] is not None) else 0
        obs_kills = player["observer_kills"]*1000/player["duration"] if (
                "observer_kills" in player and player["observer_kills"] is not None) else 0
        camps_stacked = player["camps_stacked"]*1000/player["duration"] if player["camps_stacked"] is not None else 0
        stuns = player["stuns"]/player["duration"] if player["stuns"] is not None else 0
        try:
            fantasy_score = round(
                ((player["kills"] * fantasy_kill_multiplier * 1000)/player["duration"]) + ((player["deaths"] * fantasy_death_multiplier * 1000)/player["duration"]) + (
                    (player["assists"] * fantasy_assist_multiplier * 1000)/player["duration"]) + (
                    (player["last_hits"] * fantasy_lasthit_multiplier * 10)/player["duration"]) + (
                    (player["gold_per_min"] * 10 * fantasy_gpm_multiplier)/player["duration"]) + (
                        towers_killed * fantasy_ts_multiplier) + (
                        roshan_kills * fantasy_roshan_multiplier) + (
                        obs_placed * fantasy_wards_planted) + (
                        (sentry_kills + obs_kills) * fantasy_wards_dewarded) + (
                        camps_stacked * fantasy_camps_stacked) + (
                        first_blood_claimed * fantasy_first_blood) + (
                        stuns * fantasy_stuns_multiplier), 2)
        except:  # Todo add specific exception and add details in print for debugging
            print("Error in get fantasy score")
            return
        return fantasy_score*100

    # Returns the player name in text given the player ID
    def get_player_name_for_account_id(self, playerId):
        response = requests.get(opendota_api_players_url + playerId)
        json_data = json.loads(response.text)
        return json_data['profile']['name'] if json_data['profile']['name'] is not None else json_data['profile'][
            'personaname']

    # Function to process csv files and check duplicates for a single player across multiple pos. User can select
    # manually which role they should belong to
    def find_duplicates(self):

        # TODO: Improve data structure used to be a single object
        gpm1 = process_dict_values_into_list(
            dict(csv.reader(open(pos1directory + pos1gpmfile, 'r', encoding="utf-8", newline=''))))
        gpm2 = process_dict_values_into_list(
            dict(csv.reader(open(pos2directory + pos2gpmfile, 'r', encoding="utf-8", newline=''))))
        gpm3 = process_dict_values_into_list(
            dict(csv.reader(open(pos3directory + pos3gpmfile, 'r', encoding="utf-8", newline=''))))
        gpm4 = process_dict_values_into_list(
            dict(csv.reader(open(pos4directory + pos4gpmfile, 'r', encoding="utf-8", newline=''))))
        gpm5 = process_dict_values_into_list(
            dict(csv.reader(open(pos5directory + pos5gpmfile, 'r', encoding="utf-8", newline=''))))

        kda1 = process_dict_values_into_list(
            dict(csv.reader(open(pos1directory + pos1kdafile, 'r', encoding="utf-8", newline=''))))
        kda2 = process_dict_values_into_list(
            dict(csv.reader(open(pos2directory + pos2kdafile, 'r', encoding="utf-8", newline=''))))
        kda3 = process_dict_values_into_list(
            dict(csv.reader(open(pos3directory + pos3kdafile, 'r', encoding="utf-8", newline=''))))
        kda4 = process_dict_values_into_list(
            dict(csv.reader(open(pos4directory + pos4kdafile, 'r', encoding="utf-8", newline=''))))
        kda5 = process_dict_values_into_list(
            dict(csv.reader(open(pos5directory + pos5kdafile, 'r', encoding="utf-8", newline=''))))

        fantasy1 = process_dict_values_into_list(
            dict(csv.reader(open(pos1directory + pos1fantasyfile, 'r', encoding="utf-8", newline=''))))
        fantasy2 = process_dict_values_into_list(
            dict(csv.reader(open(pos2directory + pos2fantasyfile, 'r', encoding="utf-8", newline=''))))
        fantasy3 = process_dict_values_into_list(
            dict(csv.reader(open(pos3directory + pos3fantasyfile, 'r', encoding="utf-8", newline=''))))
        fantasy4 = process_dict_values_into_list(
            dict(csv.reader(open(pos4directory + pos4fantasyfile, 'r', encoding="utf-8", newline=''))))
        fantasy5 = process_dict_values_into_list(
            dict(csv.reader(open(pos5directory + pos5fantasyfile, 'r', encoding="utf-8", newline=''))))

        # Iterate through each stat and for each pos to find duplicates
        # If the role is changed from what was originally parsed, add them to the new roles dictionary and delete old
        gpm_value_set = {}
        gpm_player_set = {}
        user_choices = []
        for index, gpmdict in enumerate(
                [copy.deepcopy(gpm1), copy.deepcopy(gpm2), copy.deepcopy(gpm3), copy.deepcopy(gpm4),
                 copy.deepcopy(gpm5)]):
            for player, gpm in copy.deepcopy(gpmdict).items():
                if player in gpm_player_set:
                    print("-- Player GPM: {} found in {} and {} -- ".format(player, gpm_player_set[player], index + 1))
                    uinput = int(input("Which position should be selected? 1,2,3,4,5 for roles or 0 to keep separate"))
                    user_choices.append(uinput)
                    if uinput == 1:
                        cumulative = gpm_value_set[player][0] * gpm_value_set[player][1]
                        matches = gpm_value_set[player][1] + gpm[1]
                        evalList = [(cumulative + (gpm[0] * gpm[1])) / matches, matches]
                        gpm1[player] = evalList
                        if index + 1 == 1:
                            if gpm_player_set[player] == 2:
                                gpm2.pop(player)
                            if gpm_player_set[player] == 3:
                                gpm3.pop(player)
                            if gpm_player_set[player] == 4:
                                gpm4.pop(player)
                            if gpm_player_set[player] == 5:
                                gpm5.pop(player)
                        elif gpm_player_set[player] == 1:
                            if index + 1 == 2:
                                gpm2.pop(player)
                            if index + 1 == 3:
                                gpm3.pop(player)
                            if index + 1 == 4:
                                gpm4.pop(player)
                            if index + 1 == 5:
                                gpm5.pop(player)
                    elif uinput == 2:
                        cumulative = gpm_value_set[player][0] * gpm_value_set[player][1]
                        matches = gpm_value_set[player][1] + gpm[1]
                        evalList = [(cumulative + (gpm[0] * gpm[1])) / matches, matches]
                        gpm2[player] = evalList
                        if index + 1 == 2:
                            if gpm_player_set[player] == 1:
                                gpm1.pop(player)
                            if gpm_player_set[player] == 3:
                                gpm3.pop(player)
                            if gpm_player_set[player] == 4:
                                gpm4.pop(player)
                            if gpm_player_set[player] == 5:
                                gpm5.pop(player)
                        elif gpm_player_set[player] == 2:
                            if index + 1 == 1:
                                gpm1.pop(player)
                            if index + 1 == 3:
                                gpm3.pop(player)
                            if index + 1 == 4:
                                gpm4.pop(player)
                            if index + 1 == 5:
                                gpm5.pop(player)
                    elif uinput == 3:
                        cumulative = gpm_value_set[player][0] * gpm_value_set[player][1]
                        matches = gpm_value_set[player][1] + gpm[1]
                        evalList = [(cumulative + (gpm[0] * gpm[1])) / matches, matches]
                        gpm3[player] = evalList
                        if index + 1 == 3:
                            if gpm_player_set[player] == 2:
                                gpm2.pop(player)
                            if gpm_player_set[player] == 1:
                                gpm1.pop(player)
                            if gpm_player_set[player] == 4:
                                gpm4.pop(player)
                            if gpm_player_set[player] == 5:
                                gpm5.pop(player)
                        elif gpm_player_set[player] == 3:
                            if index + 1 == 2:
                                gpm2.pop(player)
                            if index + 1 == 1:
                                gpm1.pop(player)
                            if index + 1 == 4:
                                gpm4.pop(player)
                            if index + 1 == 5:
                                gpm5.pop(player)
                    elif uinput == 4:
                        cumulative = gpm_value_set[player][0] * gpm_value_set[player][1]
                        matches = gpm_value_set[player][1] + gpm[1]
                        evalList = [(cumulative + (gpm[0] * gpm[1])) / matches, matches]
                        gpm4[player] = evalList
                        if index + 1 == 4:
                            if gpm_player_set[player] == 2:
                                gpm2.pop(player)
                            if gpm_player_set[player] == 3:
                                gpm3.pop(player)
                            if gpm_player_set[player] == 1:
                                gpm1.pop(player)
                            if gpm_player_set[player] == 5:
                                gpm5.pop(player)
                        elif gpm_player_set[player] == 4:
                            if index + 1 == 2:
                                gpm2.pop(player)
                            if index + 1 == 3:
                                gpm3.pop(player)
                            if index + 1 == 1:
                                gpm1.pop(player)
                            if index + 1 == 5:
                                gpm5.pop(player)
                    elif uinput == 5:
                        cumulative = gpm_value_set[player][0] * gpm_value_set[player][1]
                        matches = gpm_value_set[player][1] + gpm[1]
                        evalList = [(cumulative + (gpm[0] * gpm[1])) / matches, matches]
                        gpm5[player] = evalList
                        if index + 1 == 5:
                            if gpm_player_set[player] == 2:
                                gpm2.pop(player)
                            if gpm_player_set[player] == 3:
                                gpm3.pop(player)
                            if gpm_player_set[player] == 4:
                                gpm4.pop(player)
                            if gpm_player_set[player] == 1:
                                gpm1.pop(player)
                        elif gpm_player_set[player] == 5:
                            if index + 1 == 2:
                                gpm2.pop(player)
                            if index + 1 == 3:
                                gpm3.pop(player)
                            if index + 1 == 4:
                                gpm4.pop(player)
                            if index + 1 == 1:
                                gpm1.pop(player)
                    elif uinput == 0:
                        print("Keeping both roles stats")
                    else:
                        print("Option not recognized. Please enter 1, 2 or 3")
                else:
                    gpm_player_set[player] = index + 1
                    gpm_value_set[player] = gpm

        # Iterate through each stat and for each pos to find duplicates
        # If the role is changed from what was originally parsed, add them to the new roles dictionary and delete old
        kda_value_set = {}
        kda_player_set = {}
        counter = -1
        for index, kdadict in enumerate(
                [copy.deepcopy(kda1), copy.deepcopy(kda2), copy.deepcopy(kda3), copy.deepcopy(kda4),
                 copy.deepcopy(kda5)]):

            for player, kda in copy.deepcopy(kdadict).items():
                if player in kda_player_set:
                    counter += 1
                    if user_choices[counter] == 1:
                        cumulative = kda_value_set[player][0] * kda_value_set[player][1]
                        matches = kda_value_set[player][1] + kda[1]
                        evalList = [(cumulative + (kda[0] * kda[1])) / matches, matches]
                        kda1[player] = evalList
                        if index + 1 == 1:
                            if kda_player_set[player] == 2:
                                kda2.pop(player)
                            if kda_player_set[player] == 3:
                                kda3.pop(player)
                            if kda_player_set[player] == 4:
                                kda4.pop(player)
                            if kda_player_set[player] == 5:
                                kda5.pop(player)
                        elif kda_player_set[player] == 1:
                            if index + 1 == 2:
                                kda2.pop(player)
                            if index + 1 == 3:
                                kda3.pop(player)
                            if index + 1 == 4:
                                kda4.pop(player)
                            if index + 1 == 5:
                                kda5.pop(player)
                    elif user_choices[counter] == 2:
                        cumulative = kda_value_set[player][0] * kda_value_set[player][1]
                        matches = kda_value_set[player][1] + kda[1]
                        evalList = [(cumulative + (kda[0] * kda[1])) / matches, matches]
                        kda2[player] = evalList
                        if index + 1 == 2:
                            if kda_player_set[player] == 1:
                                kda1.pop(player)
                            if kda_player_set[player] == 3:
                                kda3.pop(player)
                            if kda_player_set[player] == 4:
                                kda4.pop(player)
                            if kda_player_set[player] == 5:
                                kda5.pop(player)
                        elif kda_player_set[player] == 2:
                            if index + 1 == 1:
                                kda1.pop(player)
                            if index + 1 == 3:
                                kda3.pop(player)
                            if index + 1 == 4:
                                kda4.pop(player)
                            if index + 1 == 5:
                                kda5.pop(player)
                    elif user_choices[counter] == 3:
                        cumulative = kda_value_set[player][0] * kda_value_set[player][1]
                        matches = kda_value_set[player][1] + kda[1]
                        evalList = [(cumulative + (kda[0] * kda[1])) / matches, matches]
                        kda3[player] = evalList
                        if index + 1 == 3:
                            if kda_player_set[player] == 2:
                                kda2.pop(player)
                            if kda_player_set[player] == 1:
                                kda1.pop(player)
                            if kda_player_set[player] == 4:
                                kda4.pop(player)
                            if kda_player_set[player] == 5:
                                kda5.pop(player)
                        elif kda_player_set[player] == 3:
                            if index + 1 == 2:
                                kda2.pop(player)
                            if index + 1 == 1:
                                kda1.pop(player)
                            if index + 1 == 4:
                                kda4.pop(player)
                            if index + 1 == 5:
                                kda5.pop(player)
                    elif user_choices[counter] == 4:
                        cumulative = kda_value_set[player][0] * kda_value_set[player][1]
                        matches = kda_value_set[player][1] + kda[1]
                        evalList = [(cumulative + (kda[0] * kda[1])) / matches, matches]
                        kda4[player] = evalList
                        if index + 1 == 4:
                            if kda_player_set[player] == 2:
                                kda2.pop(player)
                            if kda_player_set[player] == 3:
                                kda3.pop(player)
                            if kda_player_set[player] == 1:
                                kda1.pop(player)
                            if kda_player_set[player] == 5:
                                kda5.pop(player)
                        elif kda_player_set[player] == 4:
                            if index + 1 == 2:
                                kda2.pop(player)
                            if index + 1 == 3:
                                kda3.pop(player)
                            if index + 1 == 1:
                                kda1.pop(player)
                            if index + 1 == 5:
                                kda5.pop(player)
                    elif user_choices[counter] == 5:
                        cumulative = kda_value_set[player][0] * kda_value_set[player][1]
                        matches = kda_value_set[player][1] + kda[1]
                        evalList = [(cumulative + (kda[0] * kda[1])) / matches, matches]
                        kda5[player] = evalList
                        if index + 1 == 5:
                            if kda_player_set[player] == 2:
                                kda2.pop(player)
                            if kda_player_set[player] == 3:
                                kda3.pop(player)
                            if kda_player_set[player] == 4:
                                kda4.pop(player)
                            if kda_player_set[player] == 1:
                                kda1.pop(player)
                        elif kda_player_set[player] == 5:
                            if index + 1 == 2:
                                kda2.pop(player)
                            if index + 1 == 3:
                                kda3.pop(player)
                            if index + 1 == 4:
                                kda4.pop(player)
                            if index + 1 == 5:
                                kda1.pop(player)
                    elif user_choices[counter] == 0:
                        print("Keeping both roles stats")
                    else:
                        print("Option not recognized. Please enter 1, 2 or 3")

                else:
                    kda_player_set[player] = index + 1
                    kda_value_set[player] = kda

        # Iterate through each stat and for each pos to find duplicates
        # If the role is changed from what was originally parsed, add them to the new roles dictionary and delete old
        fantasy_value_set = {}
        fantasy_player_set = {}
        counter = -1
        for index, fantasydict in enumerate(
                [copy.deepcopy(fantasy1), copy.deepcopy(fantasy2), copy.deepcopy(fantasy3), copy.deepcopy(fantasy4),
                 copy.deepcopy(fantasy5)]):

            for player, fantasy in copy.deepcopy(fantasydict).items():
                if player in fantasy_player_set:
                    counter += 1
                    if user_choices[counter] == 1:
                        cumulative = fantasy_value_set[player][0] * fantasy_value_set[player][1]
                        matches = fantasy_value_set[player][1] + fantasy[1]
                        evalList = [(cumulative + (fantasy[0] * fantasy[1])) / matches, matches]
                        fantasy1[player] = evalList
                        if index + 1 == 1:
                            if fantasy_player_set[player] == 2:
                                fantasy2.pop(player)
                            if fantasy_player_set[player] == 3:
                                fantasy3.pop(player)
                            if fantasy_player_set[player] == 4:
                                fantasy4.pop(player)
                            if fantasy_player_set[player] == 5:
                                fantasy5.pop(player)
                        elif fantasy_player_set[player] == 1:
                            if index + 1 == 2:
                                fantasy2.pop(player)
                            if index + 1 == 3:
                                fantasy3.pop(player)
                            if index + 1 == 4:
                                fantasy4.pop(player)
                            if index + 1 == 5:
                                fantasy5.pop(player)
                    elif user_choices[counter] == 2:
                        cumulative = fantasy_value_set[player][0] * fantasy_value_set[player][1]
                        matches = fantasy_value_set[player][1] + fantasy[1]
                        evalList = [(cumulative + (fantasy[0] * fantasy[1])) / matches, matches]
                        fantasy2[player] = evalList
                        if index + 1 == 2:
                            if fantasy_player_set[player] == 1:
                                fantasy1.pop(player)
                            if fantasy_player_set[player] == 3:
                                fantasy3.pop(player)
                            if fantasy_player_set[player] == 4:
                                fantasy4.pop(player)
                            if fantasy_player_set[player] == 5:
                                fantasy5.pop(player)
                        elif fantasy_player_set[player] == 2:
                            if index + 1 == 1:
                                fantasy1.pop(player)
                            if index + 1 == 3:
                                fantasy3.pop(player)
                            if index + 1 == 4:
                                fantasy4.pop(player)
                            if index + 1 == 5:
                                fantasy5.pop(player)
                    elif user_choices[counter] == 3:
                        cumulative = fantasy_value_set[player][0] * fantasy_value_set[player][1]
                        matches = fantasy_value_set[player][1] + fantasy[1]
                        evalList = [(cumulative + (fantasy[0] * fantasy[1])) / matches, matches]
                        fantasy3[player] = evalList
                        if index + 1 == 3:
                            if fantasy_player_set[player] == 2:
                                fantasy2.pop(player)
                            if fantasy_player_set[player] == 1:
                                fantasy1.pop(player)
                            if fantasy_player_set[player] == 4:
                                fantasy4.pop(player)
                            if fantasy_player_set[player] == 5:
                                fantasy5.pop(player)
                        elif fantasy_player_set[player] == 3:
                            if index + 1 == 2:
                                fantasy2.pop(player)
                            if index + 1 == 1:
                                fantasy1.pop(player)
                            if index + 1 == 4:
                                fantasy4.pop(player)
                            if index + 1 == 5:
                                fantasy5.pop(player)
                    elif user_choices[counter] == 4:
                        cumulative = fantasy_value_set[player][0] * fantasy_value_set[player][1]
                        matches = fantasy_value_set[player][1] + fantasy[1]
                        evalList = [(cumulative + (fantasy[0] * fantasy[1])) / matches, matches]
                        fantasy4[player] = evalList
                        if index + 1 == 4:
                            if fantasy_player_set[player] == 2:
                                fantasy2.pop(player)
                            if fantasy_player_set[player] == 3:
                                fantasy3.pop(player)
                            if fantasy_player_set[player] == 1:
                                fantasy1.pop(player)
                            if fantasy_player_set[player] == 5:
                                fantasy5.pop(player)
                        elif fantasy_player_set[player] == 4:
                            if index + 1 == 2:
                                fantasy2.pop(player)
                            if index + 1 == 3:
                                fantasy3.pop(player)
                            if index + 1 == 1:
                                fantasy1.pop(player)
                            if index + 1 == 5:
                                fantasy5.pop(player)
                    elif user_choices[counter] == 5:
                        cumulative = fantasy_value_set[player][0] * fantasy_value_set[player][1]
                        matches = fantasy_value_set[player][1] + fantasy[1]
                        evalList = [(cumulative + (fantasy[0] * fantasy[1])) / matches, matches]
                        fantasy5[player] = evalList
                        if index + 1 == 5:
                            if fantasy_player_set[player] == 2:
                                fantasy2.pop(player)
                            if fantasy_player_set[player] == 3:
                                fantasy3.pop(player)
                            if fantasy_player_set[player] == 4:
                                fantasy4.pop(player)
                            if fantasy_player_set[player] == 1:
                                fantasy1.pop(player)
                        elif fantasy_player_set[player] == 5:
                            if index + 1 == 2:
                                fantasy2.pop(player)
                            if index + 1 == 3:
                                fantasy3.pop(player)
                            if index + 1 == 4:
                                fantasy4.pop(player)
                            if index + 1 == 1:
                                fantasy1.pop(player)
                    elif user_choices[counter]  == 0:
                        print("Keeping both roles stats")
                    else:
                        print("Option not recognized. Please enter one among 1/2/3/4/5")

                else:
                    fantasy_player_set[player] = index + 1
                    fantasy_value_set[player] = fantasy

        write_to_pos_based_csv_files(gpm1, kda1, fantasy1,
                                     gpm2, kda2, fantasy2,
                                     gpm3, kda3, fantasy3,
                                     gpm4, kda4, fantasy4,
                                     gpm5, kda5, fantasy5)

        print("No more duplicates found. Exiting...")
        return

    # Function to swap two players roles
    def swap_players(self):

        # TODO: Improve data structure used to be a single object
        gpm1 = process_dict_values_into_list(
            dict(csv.reader(open(pos1directory + pos1gpmfile, 'r', encoding="utf-8", newline=''))))
        gpm2 = process_dict_values_into_list(
            dict(csv.reader(open(pos2directory + pos2gpmfile, 'r', encoding="utf-8", newline=''))))
        gpm3 = process_dict_values_into_list(
            dict(csv.reader(open(pos3directory + pos3gpmfile, 'r', encoding="utf-8", newline=''))))
        gpm4 = process_dict_values_into_list(
            dict(csv.reader(open(pos4directory + pos4gpmfile, 'r', encoding="utf-8", newline=''))))
        gpm5 = process_dict_values_into_list(
            dict(csv.reader(open(pos5directory + pos5gpmfile, 'r', encoding="utf-8", newline=''))))

        kda1 = process_dict_values_into_list(
            dict(csv.reader(open(pos1directory + pos1kdafile, 'r', encoding="utf-8", newline=''))))
        kda2 = process_dict_values_into_list(
            dict(csv.reader(open(pos2directory + pos2kdafile, 'r', encoding="utf-8", newline=''))))
        kda3 = process_dict_values_into_list(
            dict(csv.reader(open(pos3directory + pos3kdafile, 'r', encoding="utf-8", newline=''))))
        kda4 = process_dict_values_into_list(
            dict(csv.reader(open(pos4directory + pos4kdafile, 'r', encoding="utf-8", newline=''))))
        kda5 = process_dict_values_into_list(
            dict(csv.reader(open(pos5directory + pos5kdafile, 'r', encoding="utf-8", newline=''))))

        fantasy1 = process_dict_values_into_list(
            dict(csv.reader(open(pos1directory + pos1fantasyfile, 'r', encoding="utf-8", newline=''))))
        fantasy2 = process_dict_values_into_list(
            dict(csv.reader(open(pos2directory + pos2fantasyfile, 'r', encoding="utf-8", newline=''))))
        fantasy3 = process_dict_values_into_list(
            dict(csv.reader(open(pos3directory + pos3fantasyfile, 'r', encoding="utf-8", newline=''))))
        fantasy4 = process_dict_values_into_list(
            dict(csv.reader(open(pos4directory + pos4fantasyfile, 'r', encoding="utf-8", newline=''))))
        fantasy5 = process_dict_values_into_list(
            dict(csv.reader(open(pos5directory + pos5fantasyfile, 'r', encoding="utf-8", newline=''))))

        player1, player2 = input("Enter two players ID's to swap roles").split()

        dict1 = find_player_in_dictionaries(player1, gpm1, gpm2, gpm3, gpm4, gpm5)
        dict2 = find_player_in_dictionaries(player2, gpm1, gpm2, gpm3, gpm4, gpm5)
        temp = dict1.pop(player1)
        dict2[player1] = temp
        temp = dict2.pop(player2)
        dict1[player2] = temp

        dict1 = find_player_in_dictionaries(player1, kda1, kda2, kda3, kda4, kda5)
        dict2 = find_player_in_dictionaries(player2, kda1, kda2, kda3, kda4, kda5)
        temp = dict1.pop(player1)
        dict2[player1] = temp
        temp = dict2.pop(player2)
        dict1[player2] = temp

        dict1 = find_player_in_dictionaries(player1, fantasy1, fantasy2, fantasy3, fantasy4, fantasy5)
        dict2 = find_player_in_dictionaries(player2, fantasy1, fantasy2, fantasy3, fantasy4, fantasy5)
        temp = dict1.pop(player1)
        dict2[player1] = temp
        temp = dict2.pop(player2)
        dict1[player2] = temp


        write_to_pos_based_csv_files(gpm1, kda1, fantasy1,
                                     gpm2, kda2, fantasy2,
                                     gpm3, kda3, fantasy3,
                                     gpm4, kda4, fantasy4,
                                     gpm5, kda5, fantasy5)

        print("Swapped both players successfully")
        return

    # Function that calculates stats for current week, adds them to the cumulative stats for the season
    def get_stats(self):

        # TODO: Create function that can be reused
        gpm1 = process_dict_values_into_list(
            dict(csv.reader(open(pos1directory + pos1gpmfile, 'r+', encoding="utf-8", newline=''))))
        gpm2 = process_dict_values_into_list(
            dict(csv.reader(open(pos2directory + pos2gpmfile, 'r+', encoding="utf-8", newline=''))))
        gpm3 = process_dict_values_into_list(
            dict(csv.reader(open(pos3directory + pos3gpmfile, 'r+', encoding="utf-8", newline=''))))
        gpm4 = process_dict_values_into_list(
            dict(csv.reader(open(pos4directory + pos4gpmfile, 'r+', encoding="utf-8", newline=''))))
        gpm5 = process_dict_values_into_list(
            dict(csv.reader(open(pos5directory + pos5gpmfile, 'r+', encoding="utf-8", newline=''))))

        kda1 = process_dict_values_into_list(
            dict(csv.reader(open(pos1directory + pos1kdafile, 'r+', encoding="utf-8", newline=''))))
        kda2 = process_dict_values_into_list(
            dict(csv.reader(open(pos2directory + pos2kdafile, 'r+', encoding="utf-8", newline=''))))
        kda3 = process_dict_values_into_list(
            dict(csv.reader(open(pos3directory + pos3kdafile, 'r+', encoding="utf-8", newline=''))))
        kda4 = process_dict_values_into_list(
            dict(csv.reader(open(pos4directory + pos4kdafile, 'r+', encoding="utf-8", newline=''))))
        kda5 = process_dict_values_into_list(
            dict(csv.reader(open(pos5directory + pos5kdafile, 'r+', encoding="utf-8", newline=''))))

        fantasy1 = process_dict_values_into_list(
            dict(csv.reader(open(pos1directory + pos1fantasyfile, 'r+', encoding="utf-8", newline=''))))
        fantasy2 = process_dict_values_into_list(
            dict(csv.reader(open(pos2directory + pos2fantasyfile, 'r+', encoding="utf-8", newline=''))))
        fantasy3 = process_dict_values_into_list(
            dict(csv.reader(open(pos3directory + pos3fantasyfile, 'r+', encoding="utf-8", newline=''))))
        fantasy4 = process_dict_values_into_list(
            dict(csv.reader(open(pos4directory + pos4fantasyfile, 'r+', encoding="utf-8", newline=''))))
        fantasy5 = process_dict_values_into_list(
            dict(csv.reader(open(pos5directory + pos5fantasyfile, 'r+', encoding="utf-8", newline=''))))

        matches_size = len(match_ids)
        for match_index, matchid in enumerate(match_ids):
            response = requests.get(opendota_api_matches_url + matchid)
            json_data = json.loads(response.text)

            radiant_pos_1 = None
            radiant_pos_2 = None
            radiant_pos_3 = None
            radiant_pos_4 = None
            radiant_pos_5 = None

            dire_pos_1 = None
            dire_pos_2 = None
            dire_pos_3 = None
            dire_pos_4 = None
            dire_pos_5 = None

            # Sometimes Open dota API can have 500 status, in that case break out
            try:
                json_data['players']
            except KeyError:
                print("Internal server error for match ID: " + matchid)
                return

            # TODO: Refactor so that code is not repeated
            for player in json_data['players']:
                if player['isRadiant']:
                    # Happens sometimes, player cannot be parsed. Just skip
                    if "lane" not in player:
                        continue
                    if player['lane'] == 1:
                        if radiant_pos_1 is None:
                            radiant_pos_1 = player
                        else:
                            if radiant_pos_1['net_worth'] < player['net_worth']:
                                radiant_pos_5 = radiant_pos_1
                                radiant_pos_1 = player
                            else:
                                radiant_pos_5 = player
                    elif player['lane'] == 2:
                        if radiant_pos_2 is None:
                            radiant_pos_2 = player
                        elif radiant_pos_2['net_worth'] < player['net_worth']:
                            if radiant_pos_4 is None:
                                radiant_pos_4 = radiant_pos_2
                                radiant_pos_2 = player
                            elif radiant_pos_4 is not None:
                                if radiant_pos_4['net_worth'] < radiant_pos_2["net_worth"]:
                                    radiant_pos_5 = radiant_pos_4
                                    radiant_pos_4 = radiant_pos_2
                                    radiant_pos_2 = player
                                else:
                                    radiant_pos_5 = radiant_pos_2
                                    radiant_pos_2 = player
                            elif radiant_pos_5 is not None:
                                if radiant_pos_5['net_worth'] > radiant_pos_2["net_worth"]:
                                    radiant_pos_4 = radiant_pos_5
                                    radiant_pos_5 = radiant_pos_2
                            else:
                                radiant_pos_4 = radiant_pos_2
                                radiant_pos_2 = player
                        else:
                            radiant_pos_4 = player
                    elif player['lane'] == 3:
                        if radiant_pos_3 is None:
                            radiant_pos_3 = player
                        else:
                            if radiant_pos_3['net_worth'] < player['net_worth']:
                                radiant_pos_4 = radiant_pos_3
                                radiant_pos_3 = player
                            else:
                                radiant_pos_4 = player
                else:
                    if "lane" not in player:
                        continue
                    if player['lane'] == 1:
                        if dire_pos_3 is None:
                            dire_pos_3 = player
                        else:
                            if dire_pos_3['net_worth'] < player['net_worth']:
                                dire_pos_4 = dire_pos_3
                                dire_pos_3 = player
                            else:
                                dire_pos_4 = player
                    elif player['lane'] == 2:
                        if dire_pos_2 is None:
                            dire_pos_2 = player
                        elif dire_pos_2['net_worth'] < player['net_worth']:
                            if dire_pos_4 is None:
                                dire_pos_4 = dire_pos_2
                                dire_pos_2 = player
                            elif dire_pos_4 is not None:
                                if dire_pos_4['net_worth'] < dire_pos_2["net_worth"]:
                                    dire_pos_5 = dire_pos_4
                                    dire_pos_4 = dire_pos_2
                                    dire_pos_2 = player
                                else:
                                    dire_pos_5 = dire_pos_2
                                    dire_pos_2 = player
                            elif dire_pos_5 is not None:
                                if dire_pos_5['net_worth'] > dire_pos_2["net_worth"]:
                                    dire_pos_4 = dire_pos_5
                                    dire_pos_5 = dire_pos_2
                            else:
                                dire_pos_4 = dire_pos_2
                                dire_pos_2 = player
                        else:
                            dire_pos_4 = player
                    elif player['lane'] == 3:
                        if dire_pos_1 is None:
                            dire_pos_1 = player
                        else:
                            if dire_pos_1['net_worth'] < player['net_worth']:
                                dire_pos_5 = dire_pos_1
                                dire_pos_1 = player
                            else:
                                dire_pos_5 = player

            # For any unfilled pos (Maybe because they jungled???) Fill them in to remaining slot
            for index, each in enumerate(
                    [radiant_pos_1, dire_pos_1, radiant_pos_2, dire_pos_2, radiant_pos_3, dire_pos_3, radiant_pos_4,
                     dire_pos_4, radiant_pos_5, dire_pos_5]):
                if each is None:
                    diff = list_difference(json_data['players'],
                                           [radiant_pos_1, dire_pos_1, radiant_pos_2, dire_pos_2, radiant_pos_3,
                                            dire_pos_3,
                                            radiant_pos_4, dire_pos_4, radiant_pos_5, dire_pos_5])
                    if index == 0:
                        radiant_pos_1 = diff[0]
                    elif index == 1:
                        dire_pos_1 = diff[0]
                    elif index == 2:
                        radiant_pos_2 = diff[0]
                    elif index == 3:
                        dire_pos_2 = diff[0]
                    elif index == 4:
                        radiant_pos_3 = diff[0]
                    elif index == 5:
                        dire_pos_3 = diff[0]
                    elif index == 6:
                        radiant_pos_4 = diff[0]
                    elif index == 7:
                        dire_pos_4 = diff[0]
                    elif index == 8:
                        radiant_pos_5 = diff[0]
                    elif index == 9:
                        dire_pos_5 = diff[0]

            # Parse response to add stat to each relevant dictionary based on role
            # TODO: Refactor to avoid code duplication
            for player in [radiant_pos_1, dire_pos_1]:
                if str(player["account_id"]) in gpm1:
                    if isinstance(gpm1[str(player["account_id"])], str):
                        evalList = ast.literal_eval(gpm1[str(player["account_id"])])
                    else:
                        evalList = gpm1[str(player["account_id"])]
                    gpm1[str(player["account_id"])] = [
                        ((evalList[0] * evalList[1]) + player["gold_per_min"]) / (evalList[1] + 1), evalList[1] + 1]
                else:
                    gpm1[str(player["account_id"])] = [player["gold_per_min"], 1]

                if str(player["account_id"]) in kda1:
                    if isinstance(kda1[str(player["account_id"])], str):
                        evalList = ast.literal_eval(kda1[str(player["account_id"])])
                    else:
                        evalList = kda1[str(player["account_id"])]
                    kda1[str(player["account_id"])] = [
                        ((evalList[0] * evalList[1]) + player["kda"]) / (evalList[1] + 1),
                        evalList[1] + 1]
                else:
                    kda1[str(player["account_id"])] = [player["kda"], 1]

                if str(player["account_id"]) in fantasy1:
                    if isinstance(fantasy1[str(player["account_id"])], str):
                        evalList = ast.literal_eval(fantasy1[str(player["account_id"])])
                    else:
                        evalList = fantasy1[str(player["account_id"])]
                    fantasy1[str(player["account_id"])] = [
                        ((evalList[0] * evalList[1]) + self.get_fantasy_score(player)) / (evalList[1] + 1),
                        evalList[1] + 1]
                else:
                    try:
                        fantasy1[str(player["account_id"])] = [self.get_fantasy_score(player), 1]
                    except:
                        print("Failed in getting fantasy score")

            for player in [radiant_pos_2, dire_pos_2]:
                if str(player["account_id"]) in gpm2:
                    if isinstance(gpm2[str(player["account_id"])], str):
                        evalList = ast.literal_eval(gpm2[str(player["account_id"])])
                    else:
                        evalList = gpm2[str(player["account_id"])]
                    gpm2[str(player["account_id"])] = [
                        ((evalList[0] * evalList[1]) + player["gold_per_min"]) / (evalList[1] + 1),
                        evalList[1] + 1]
                else:
                    gpm2[str(player["account_id"])] = [player["gold_per_min"], 1]

                if str(player["account_id"]) in kda2:
                    if isinstance(kda2[str(player["account_id"])], str):
                        evalList = ast.literal_eval(kda2[str(player["account_id"])])
                    else:
                        evalList = kda2[str(player["account_id"])]
                    kda2[str(player["account_id"])] = [
                        ((evalList[0] * evalList[1]) + player["kda"]) / (evalList[1] + 1),
                        evalList[1] + 1]
                else:
                    kda2[str(player["account_id"])] = [player["kda"], 1]

                if str(player["account_id"]) in fantasy2:
                    if isinstance(fantasy2[str(player["account_id"])], str):
                        evalList = ast.literal_eval(fantasy2[str(player["account_id"])])
                    else:
                        evalList = fantasy2[str(player["account_id"])]
                    fantasy2[str(player["account_id"])] = [
                        ((evalList[0] * evalList[1]) + self.get_fantasy_score(player)) / (evalList[1] + 1),
                        evalList[1] + 1]
                else:
                    fantasy2[str(player["account_id"])] = [self.get_fantasy_score(player), 1]

            for player in [radiant_pos_3, dire_pos_3]:
                if str(player["account_id"]) in gpm3:
                    if isinstance(gpm3[str(player["account_id"])], str):
                        evalList = ast.literal_eval(gpm3[str(player["account_id"])])
                    else:
                        evalList = gpm3[str(player["account_id"])]
                    gpm3[str(player["account_id"])] = [
                        ((evalList[0] * evalList[1]) + player["gold_per_min"]) / (evalList[1] + 1),
                        evalList[1] + 1]
                else:
                    gpm3[str(player["account_id"])] = [player["gold_per_min"], 1]

                if str(player["account_id"]) in kda3:
                    if isinstance(kda3[str(player["account_id"])], str):
                        evalList = ast.literal_eval(kda3[str(player["account_id"])])
                    else:
                        evalList = kda3[str(player["account_id"])]
                    kda3[str(player["account_id"])] = [
                        ((evalList[0] * evalList[1]) + player["kda"]) / (evalList[1] + 1),
                        evalList[1] + 1]
                else:
                    kda3[str(player["account_id"])] = [player["kda"], 1]

                if str(player["account_id"]) in fantasy3:
                    if isinstance(fantasy3[str(player["account_id"])], str):
                        evalList = ast.literal_eval(fantasy3[str(player["account_id"])])
                    else:
                        evalList = fantasy3[str(player["account_id"])]
                    fantasy3[str(player["account_id"])] = [
                        ((evalList[0] * evalList[1]) + self.get_fantasy_score(player)) / (evalList[1] + 1),
                        evalList[1] + 1]
                else:
                    fantasy3[str(player["account_id"])] = [self.get_fantasy_score(player), 1]

            for player in [radiant_pos_4, dire_pos_4]:
                if str(player["account_id"]) in gpm4:
                    if isinstance(gpm4[str(player["account_id"])], str):
                        evalList = ast.literal_eval(gpm4[str(player["account_id"])])
                    else:
                        evalList = gpm4[str(player["account_id"])]
                    gpm4[str(player["account_id"])] = [
                        ((evalList[0] * evalList[1]) + player["gold_per_min"]) / (evalList[1] + 1),
                        evalList[1] + 1]
                else:
                    gpm4[str(player["account_id"])] = [player["gold_per_min"], 1]

                if str(player["account_id"]) in kda4:
                    if isinstance(kda4[str(player["account_id"])], str):
                        evalList = ast.literal_eval(kda4[str(player["account_id"])])
                    else:
                        evalList = kda4[str(player["account_id"])]
                    kda4[str(player["account_id"])] = [
                        ((evalList[0] * evalList[1]) + player["kda"]) / (evalList[1] + 1),
                        evalList[1] + 1]
                else:
                    kda4[str(player["account_id"])] = [player["kda"], 1]

                if str(player["account_id"]) in fantasy4:
                    if isinstance(fantasy4[str(player["account_id"])], str):
                        evalList = ast.literal_eval(fantasy4[str(player["account_id"])])
                    else:
                        evalList = fantasy4[str(player["account_id"])]
                    fantasy4[str(player["account_id"])] = [
                        ((evalList[0] * evalList[1]) + self.get_fantasy_score(player)) / (evalList[1] + 1),
                        evalList[1] + 1]
                else:
                    fantasy4[str(player["account_id"])] = [self.get_fantasy_score(player), 1]

            for player in [radiant_pos_5, dire_pos_5]:
                if str(player["account_id"]) in gpm5:
                    if isinstance(gpm5[str(player["account_id"])], str):
                        evalList = ast.literal_eval(gpm5[str(player["account_id"])])
                    else:
                        evalList = gpm5[str(player["account_id"])]
                    gpm5[str(player["account_id"])] = [
                        ((evalList[0] * evalList[1]) + player["gold_per_min"]) / (evalList[1] + 1),
                        evalList[1] + 1]
                else:
                    gpm5[str(player["account_id"])] = [player["gold_per_min"], 1]

                if str(player["account_id"]) in kda5:
                    if isinstance(kda5[str(player["account_id"])], str):
                        evalList = ast.literal_eval(kda5[str(player["account_id"])])
                    else:
                        evalList = kda5[str(player["account_id"])]
                    kda5[str(player["account_id"])] = [
                        ((evalList[0] * evalList[1]) + player["kda"]) / (evalList[1] + 1),
                        evalList[1] + 1]
                else:
                    kda5[str(player["account_id"])] = [player["kda"], 1]

                if str(player["account_id"]) in fantasy5:
                    if isinstance(fantasy5[str(player["account_id"])], str):
                        evalList = ast.literal_eval(fantasy5[str(player["account_id"])])
                    else:
                        evalList = fantasy5[str(player["account_id"])]
                    fantasy5[str(player["account_id"])] = [
                        ((evalList[0] * evalList[1]) + self.get_fantasy_score(player)) / (evalList[1] + 1),
                        evalList[1] + 1]
                else:
                    fantasy5[str(player["account_id"])] = [self.get_fantasy_score(player), 1]

            for player in json_data['players']:
                if player['gold_per_min'] > self.highest_gpm_value:
                    self.highest_gpm_value = player['gold_per_min']
                    self.highest_gpm_player = player['account_id']
                    self.highest_gpm_hero = player['hero_id']
                    self.highest_gpm_match = dotabuff_url + str(json_data['match_id'])
                if player['xp_per_min'] > self.highest_xpm_value:
                    self.highest_xpm_value = player['xp_per_min']
                    self.highest_xpm_player = player['account_id']
                    self.highest_xpm_hero = player['hero_id']
                    self.highest_xpm_match = dotabuff_url + str(json_data['match_id'])
                if player['kda'] > self.highest_kda_value:
                    self.highest_kda_value = player['kda']
                    self.highest_kda_player = player['account_id']
                    self.highest_kda_hero = player['hero_id']
                    self.highest_kda_match = dotabuff_url + str(json_data['match_id'])
                if player['camps_stacked'] is not None and player['camps_stacked'] > self.highest_camps_value:
                    self.highest_camps_value = player['camps_stacked']
                    self.highest_camps_player = player['account_id']
                    self.highest_camps_hero = player['hero_id']
                    self.highest_camps_match = dotabuff_url + str(json_data['match_id'])
                if player['hero_damage'] > self.highest_herodamage_value:
                    self.highest_herodamage_value = player['hero_damage']
                    self.highest_herodamage_player = player['account_id']
                    self.highest_herodamage_hero = player['hero_id']
                    self.highest_herodamage_match = dotabuff_url + str(json_data['match_id'])
                if player['stuns'] is not None and player['stuns'] > self.highest_stuns_value:
                    self.highest_stuns_value = player['stuns']
                    self.highest_stuns_player = player['account_id']
                    self.highest_stuns_hero = player['hero_id']
                    self.highest_stuns_match = dotabuff_url + str(json_data['match_id'])
                if player['tower_damage'] is not None and player['tower_damage'] > self.highest_towerdamage_value:
                    self.highest_towerdamage_value = player['tower_damage']
                    self.highest_towerdamage_player = player['account_id']
                    self.highest_towerdamage_hero = player['hero_id']
                    self.highest_towerdamage_match = dotabuff_url + str(json_data['match_id'])
                if 'lane_efficiency' in player and player['lane_efficiency'] > self.highest_lane_value:
                    self.highest_lane_value = player['lane_efficiency']
                    self.highest_lane_player = player['account_id']
                    self.highest_lane_hero = player['hero_id']
                    self.highest_lane_match = dotabuff_url + str(json_data['match_id'])
                if 'observer_kills' in player and 'sentry_kills' in player and player['observer_kills'] is not None and \
                        player['sentry_kills'] is not None and (
                        player['observer_kills'] + player['sentry_kills']) > self.highest_deward_value:
                    self.highest_deward_value = (player['observer_kills'] + player['sentry_kills'])
                    self.highest_deward_player = player['account_id']
                    self.highest_deward_hero = player['hero_id']
                    self.highest_deward_match = dotabuff_url + str(json_data['match_id'])
                if 'courier_kills' in player and player['courier_kills'] > self.highest_courier_value:
                    self.highest_courier_value = player['courier_kills']
                    self.highest_courier_player = player['account_id']
                    self.highest_courier_hero = player['hero_id']
                    self.highest_courier_match = dotabuff_url + str(json_data['match_id'])
                if 'actions_per_min' in player and player['actions_per_min'] > self.highest_apm_value:
                    self.highest_apm_value = player['actions_per_min']
                    self.highest_apm_player = player['account_id']
                    self.highest_apm_hero = player['hero_id']
                    self.highest_apm_match = dotabuff_url + str(json_data['match_id'])
            print("Processed match {} of {} with ID: {}".format(match_index, matches_size, matchid))

        # Sleeping to avoid OpenDota API throttling
        print("Slpeeing for 60s...")
        time.sleep(60)
        response = requests.get(opendota_api_players_url + str(self.highest_gpm_player))
        json_data = json.loads(response.text)

        # TODO: Refactor to avoid duplication
        self.stats_leaders_dict["gpm"] = {"name": (json_data['profile']['name'] if json_data['profile']['name'] != None
                                                   else json_data['profile']['personaname']),
                                          "avatar": json_data['profile']['avatarmedium'],
                                          "hero": self.highest_gpm_hero,
                                          "match": self.highest_gpm_match,
                                          "value": self.highest_gpm_value}

        response = requests.get(opendota_api_players_url + str(self.highest_xpm_player))
        json_data = json.loads(response.text)
        self.stats_leaders_dict["xpm"] = {"name": (json_data['profile']['name'] if json_data['profile']['name'] != None
                                                   else json_data['profile']['personaname']),
                                          "avatar": json_data['profile']['avatarmedium'],
                                          "hero": self.highest_xpm_hero,
                                          "match": self.highest_xpm_match,
                                          "value": self.highest_xpm_value}

        response = requests.get(opendota_api_players_url + str(self.highest_kda_player))
        json_data = json.loads(response.text)
        self.stats_leaders_dict["kda"] = {"name": (json_data['profile']['name'] if json_data['profile']['name'] != None
                                                   else json_data['profile']['personaname']),
                                          "avatar": json_data['profile']['avatarmedium'],
                                          "hero": self.highest_kda_hero,
                                          "match": self.highest_kda_match,
                                          "value": self.highest_kda_value}

        response = requests.get(opendota_api_players_url + str(self.highest_camps_player))
        json_data = json.loads(response.text)
        self.stats_leaders_dict["camps"] = {
            "name": (json_data['profile']['name'] if json_data['profile']['name'] != None
                     else json_data['profile']['personaname']),
            "avatar": json_data['profile']['avatarmedium'],
            "hero": self.highest_camps_hero,
            "match": self.highest_camps_match,
            "value": self.highest_camps_value}

        response = requests.get(opendota_api_players_url + str(self.highest_herodamage_player))
        json_data = json.loads(response.text)
        self.stats_leaders_dict["herodamage"] = {
            "name": (json_data['profile']['name'] if json_data['profile']['name'] != None
                     else json_data['profile']['personaname']),
            "avatar": json_data['profile']['avatarmedium'],
            "hero": self.highest_herodamage_hero,
            "match": self.highest_herodamage_match,
            "value": self.highest_herodamage_value}

        response = requests.get(opendota_api_players_url + str(self.highest_stuns_player))
        json_data = json.loads(response.text)
        self.stats_leaders_dict["stuns"] = {
            "name": (json_data['profile']['name'] if json_data['profile']['name'] != None
                     else json_data['profile']['personaname']),
            "avatar": json_data['profile']['avatarmedium'],
            "hero": self.highest_stuns_hero,
            "match": self.highest_stuns_match,
            "value": self.highest_stuns_value}

        response = requests.get(opendota_api_players_url + str(self.highest_towerdamage_player))
        json_data = json.loads(response.text)
        self.stats_leaders_dict["towerdamage"] = {
            "name": (json_data['profile']['name'] if json_data['profile']['name'] != None
                     else json_data['profile']['personaname']),
            "avatar": json_data['profile']['avatarmedium'],
            "hero": self.highest_towerdamage_hero,
            "match": self.highest_towerdamage_match,
            "value": self.highest_towerdamage_value}

        response = requests.get(opendota_api_players_url + str(self.highest_lane_player))
        json_data = json.loads(response.text)
        self.stats_leaders_dict["lane"] = {"name": (json_data['profile']['name'] if json_data['profile']['name'] != None
                                                    else json_data['profile']['personaname']),
                                           "avatar": json_data['profile']['avatarmedium'],
                                           "hero": self.highest_lane_hero,
                                           "match": self.highest_lane_match,
                                           "value": self.highest_lane_value}

        response = requests.get(opendota_api_players_url + str(self.highest_deward_player))
        json_data = json.loads(response.text)
        self.stats_leaders_dict["deward"] = {
            "name": (json_data['profile']['name'] if json_data['profile']['name'] != None
                     else json_data['profile']['personaname']),
            "avatar": json_data['profile']['avatarmedium'],
            "hero": self.highest_deward_hero,
            "match": self.highest_deward_match,
            "value": self.highest_deward_value}

        response = requests.get(opendota_api_players_url + str(self.highest_apm_player))
        json_data = json.loads(response.text)
        self.stats_leaders_dict["apm"] = {"name": (json_data['profile']['name'] if json_data['profile']['name'] != None
                                                   else json_data['profile']['personaname']),
                                          "avatar": json_data['profile']['avatarmedium'],
                                          "hero": self.highest_apm_hero,
                                          "match": self.highest_apm_match,
                                          "value": self.highest_apm_value}

        response = requests.get(opendota_api_players_url + str(self.highest_courier_player))
        json_data = json.loads(response.text)
        self.stats_leaders_dict["courier"] = {
            "name": (json_data['profile']['name'] if json_data['profile']['name'] != None
                     else json_data['profile']['personaname']),
            "avatar": json_data['profile']['avatarmedium'],
            "hero": self.highest_courier_hero,
            "match": self.highest_courier_match,
            "value": self.highest_courier_value}

        stats_leaders_file = open('../stats_leaders.csv', 'r+', encoding="utf-8", newline='')
        stats_leaders_file_writer = csv.writer(stats_leaders_file)
        for k, v in self.stats_leaders_dict.items():
            stats_leaders_file_writer.writerow([k, v])
        stats_leaders_file.close()

        print("Generated stats leaders file.")
        print("Creating position based stat files...")

        write_to_pos_based_csv_files(gpm1, kda1, fantasy1,
                                     gpm2, kda2, fantasy2,
                                     gpm3, kda3, fantasy3,
                                     gpm4, kda4, fantasy4,
                                     gpm5, kda5, fantasy5)


rd2lstats = Rd2lStats("ODM5MzcyNjg4NDI2NTMyODY2.YJIsuw.S_lKUrYslMjZgPc-MaEXmC6R_CY")


# Function invoked when bot is live
@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))


# Function invoked when user sends message
@client.event
async def on_message(message):

    if message.author.id not in admin_ids:
        return

    # Find duplicates for a single player across multiple roles
    if message.content.startswith('$bot_find_duplicates'):
        rd2lstats.find_duplicates()

    # Find duplicates for a single player across multiple roles
    if message.content.startswith('$bot_clear_files'):
        empty_all_stat_files()

    # Swap two players roles in data
    if message.content.startswith('$bot_swap_players'):
        rd2lstats.swap_players()

    # Generate stats will generate stats without printing them out, used for debugging
    if message.content.startswith('$bot_generate_stats'):
        print('Generating stats...')
        rd2lstats.get_stats()

    # Prints out stats in discord embeds
    if message.content.startswith('$bot_get_stats'):
        gpm1 = process_dict_values_into_list(
            dict(csv.reader(open(pos1directory + pos1gpmfile, 'r', encoding="utf-8", newline=''))))
        gpm2 = process_dict_values_into_list(
            dict(csv.reader(open(pos2directory + pos2gpmfile, 'r', encoding="utf-8", newline=''))))
        gpm3 = process_dict_values_into_list(
            dict(csv.reader(open(pos3directory + pos3gpmfile, 'r', encoding="utf-8", newline=''))))
        gpm4 = process_dict_values_into_list(
            dict(csv.reader(open(pos4directory + pos4gpmfile, 'r', encoding="utf-8", newline=''))))
        gpm5 = process_dict_values_into_list(
            dict(csv.reader(open(pos5directory + pos5gpmfile, 'r', encoding="utf-8", newline=''))))

        kda1 = process_dict_values_into_list(
            dict(csv.reader(open(pos1directory + pos1kdafile, 'r', encoding="utf-8", newline=''))))
        kda2 = process_dict_values_into_list(
            dict(csv.reader(open(pos2directory + pos2kdafile, 'r', encoding="utf-8", newline=''))))
        kda3 = process_dict_values_into_list(
            dict(csv.reader(open(pos3directory + pos3kdafile, 'r', encoding="utf-8", newline=''))))
        kda4 = process_dict_values_into_list(
            dict(csv.reader(open(pos4directory + pos4kdafile, 'r', encoding="utf-8", newline=''))))
        kda5 = process_dict_values_into_list(
            dict(csv.reader(open(pos5directory + pos5kdafile, 'r', encoding="utf-8", newline=''))))

        fantasy1 = process_dict_values_into_list(
            dict(csv.reader(open(pos1directory + pos1fantasyfile, 'r', encoding="utf-8", newline=''))))
        fantasy2 = process_dict_values_into_list(
            dict(csv.reader(open(pos2directory + pos2fantasyfile, 'r', encoding="utf-8", newline=''))))
        fantasy3 = process_dict_values_into_list(
            dict(csv.reader(open(pos3directory + pos3fantasyfile, 'r', encoding="utf-8", newline=''))))
        fantasy4 = process_dict_values_into_list(
            dict(csv.reader(open(pos4directory + pos4fantasyfile, 'r', encoding="utf-8", newline=''))))
        fantasy5 = process_dict_values_into_list(
            dict(csv.reader(open(pos5directory + pos5fantasyfile, 'r', encoding="utf-8", newline=''))))

        stats_leaders_dict = process_dict_values_into_list(
            dict(csv.reader(open('../stats_leaders.csv', 'r', encoding="utf-8", newline=''))))

        print('Finished processing stats files')

        # TODO: Add better names for embeds
        embed = discord.Embed(title="Highest GPM", colour=discord.Colour(0x1),
                              description=stats_leaders_dict['gpm']['name'])
        embed.set_image(url="{}{}.png".format(steam_cdn, get_hero_name(stats_leaders_dict['gpm']['hero'])))
        embed.set_thumbnail(url=stats_leaders_dict['gpm']['avatar'])
        embed.add_field(name="GPM", value=stats_leaders_dict['gpm']['value'])
        embed.add_field(name="MatchID", value="[{}]({})".format(stats_leaders_dict["gpm"]["match"],
                                                                stats_leaders_dict["gpm"]["match"]))

        print('Processed embed 1')

        embed2 = discord.Embed(title="Highest XPM", colour=discord.Colour(0x1),
                               description=stats_leaders_dict['xpm']['name'])
        embed2.set_image(url="{}{}.png".format(steam_cdn, get_hero_name(stats_leaders_dict['xpm']['hero'])))
        embed2.set_thumbnail(url=stats_leaders_dict['xpm']['avatar'])
        embed2.add_field(name="XPM", value=stats_leaders_dict['xpm']['value'])
        embed2.add_field(name="MatchID", value="[{}]({})".format(stats_leaders_dict["xpm"]["match"],
                                                                 stats_leaders_dict["xpm"]["match"]))

        print('Processed embed 2')

        embed3 = discord.Embed(title="Highest KDA", colour=discord.Colour(0x1),
                               description=stats_leaders_dict['kda']['name'])
        embed3.set_image(url="{}{}.png".format(steam_cdn, get_hero_name(stats_leaders_dict['kda']['hero'])))
        embed3.set_thumbnail(url=stats_leaders_dict['kda']['avatar'])
        embed3.add_field(name="KDA", value=stats_leaders_dict['kda']['value'])
        embed3.add_field(name="MatchID", value="[{}]({})".format(stats_leaders_dict["kda"]["match"],
                                                                 stats_leaders_dict["kda"]["match"]))

        print('Processed embed 3')

        embed4 = discord.Embed(title="Highest Hero damage", colour=discord.Colour(0x1),
                               description=stats_leaders_dict['herodamage']['name'])
        embed4.set_image(url="{}{}.png".format(steam_cdn, get_hero_name(stats_leaders_dict['herodamage']['hero'])))
        embed4.set_thumbnail(url=stats_leaders_dict['herodamage']['avatar'])
        embed4.add_field(name="Damage", value=stats_leaders_dict['herodamage']['value'])
        embed4.add_field(name="MatchID", value="[{}]({})".format(stats_leaders_dict["herodamage"]["match"],
                                                                 stats_leaders_dict["herodamage"]["match"]))

        print('Processed embed 4')

        embed5 = discord.Embed(title="Highest Stun time", colour=discord.Colour(0x1),
                               description=stats_leaders_dict['stuns']['name'])
        embed5.set_image(url="{}{}.png".format(steam_cdn, get_hero_name(stats_leaders_dict['stuns']['hero'])))
        embed5.set_thumbnail(url=stats_leaders_dict['stuns']['avatar'])
        embed5.add_field(name="Stun time", value=round(stats_leaders_dict['stuns']['value'], 2))
        embed5.add_field(name="MatchID", value="[{}]({})".format(stats_leaders_dict["stuns"]["match"],
                                                                 stats_leaders_dict["stuns"]["match"]))

        print('Processed embed 5')

        embed6 = discord.Embed(title="Most camps stacked", colour=discord.Colour(0x1),
                               description=stats_leaders_dict['camps']['name'])
        embed6.set_image(url="{}{}.png".format(steam_cdn, get_hero_name(stats_leaders_dict['camps']['hero'])))
        embed6.set_thumbnail(url=stats_leaders_dict['camps']['avatar'])
        embed6.add_field(name="Camps stacked", value=stats_leaders_dict['camps']['value'])
        embed6.add_field(name="MatchID", value="[{}]({})".format(stats_leaders_dict["camps"]["match"],
                                                                 stats_leaders_dict["camps"]["match"]))

        print('Processed embed 6')

        embed7 = discord.Embed(title="Highest Tower damage", colour=discord.Colour(0x1),
                               description=stats_leaders_dict['towerdamage']['name'])
        embed7.set_image(url="{}{}.png".format(steam_cdn, get_hero_name(stats_leaders_dict['towerdamage']['hero'])))
        embed7.set_thumbnail(url=stats_leaders_dict['towerdamage']['avatar'])
        embed7.add_field(name="Damage", value=stats_leaders_dict['towerdamage']['value'])
        embed7.add_field(name="MatchID", value="[{}]({})".format(stats_leaders_dict["towerdamage"]["match"],
                                                                 stats_leaders_dict["towerdamage"]["match"]))

        print('Processed embed 7')

        embed8 = discord.Embed(title="Best lane efficiency", colour=discord.Colour(0x1),
                               description=stats_leaders_dict['lane']['name'])
        embed8.set_image(url="{}{}.png".format(steam_cdn, get_hero_name(stats_leaders_dict['lane']['hero'])))
        embed8.set_thumbnail(url=stats_leaders_dict['lane']['avatar'])
        embed8.add_field(name="Efficiency", value=round(stats_leaders_dict['lane']['value'], 2))
        embed8.add_field(name="MatchID", value="[{}]({})".format(stats_leaders_dict["lane"]["match"],
                                                                 stats_leaders_dict["lane"]["match"]))

        print('Processed embed 8')

        embed9 = discord.Embed(title="Highest dewards", colour=discord.Colour(0x1),
                               description=stats_leaders_dict['deward']['name'])
        embed9.set_image(url="{}{}.png".format(steam_cdn, get_hero_name(stats_leaders_dict['deward']['hero'])))
        embed9.set_thumbnail(url=stats_leaders_dict['deward']['avatar'])
        embed9.add_field(name="Dewards", value=stats_leaders_dict['deward']['value'])
        embed9.add_field(name="MatchID", value="[{}]({})".format(stats_leaders_dict["deward"]["match"],
                                                                 stats_leaders_dict["deward"]["match"]))

        print('Processed embed 9')

        embed10 = discord.Embed(title="Highest APM", colour=discord.Colour(0x1),
                                description=stats_leaders_dict['apm']['name'])
        embed10.set_image(url="{}{}.png".format(steam_cdn, get_hero_name(stats_leaders_dict['apm']['hero'])))
        embed10.set_thumbnail(url=stats_leaders_dict['apm']['avatar'])
        embed10.add_field(name="APM", value=stats_leaders_dict['apm']['value'])
        embed10.add_field(name="MatchID", value="[{}]({})".format(stats_leaders_dict["apm"]["match"],
                                                                  stats_leaders_dict["apm"]["match"]))

        print('Processed embed 10')

        embed16 = discord.Embed(title="Highest Courier kills", colour=discord.Colour(0x1),
                                description=stats_leaders_dict['courier']['name'])
        embed16.set_image(url="{}{}.png".format(steam_cdn, get_hero_name(stats_leaders_dict['courier']['hero'])))
        embed16.set_thumbnail(url=stats_leaders_dict['courier']['avatar'])
        embed16.add_field(name="Couriers", value=stats_leaders_dict['courier']['value'])
        embed16.add_field(name="MatchID", value="[{}]({})".format(stats_leaders_dict["courier"]["match"],
                                                                  stats_leaders_dict["courier"]["match"]))

        print('Processed embed 16')

        filtered_gpm1 = {key: value for key, value in gpm1.items()}
        sorted_dict_gpm = sorted(filtered_gpm1.items(), key=lambda kv: kv[1][0], reverse=True)
        filtered_kda1 = {key: value for key, value in kda1.items()}
        sorted_dict_kda = sorted(filtered_kda1.items(), key=lambda kv: kv[1][0], reverse=True)
        filtered_fantasy1 = {key: value for key, value in fantasy1.items()}
        sorted_dict_fantasy = sorted(filtered_fantasy1.items(), key=lambda kv: kv[1][0], reverse=True)

        embed11 = discord.Embed(title="Pos 1 Leaderboard", colour=discord.Colour(0x1))
        embed11.add_field(name="Ranking", value="1. \n2. \n3. \n4. \n5.", inline=True)
        embed11.add_field(name="Player", value="{} \n{} \n{} \n{} \n{}".format(
            rd2lstats.get_player_name_for_account_id(sorted_dict_gpm[0][0]),
            rd2lstats.get_player_name_for_account_id(sorted_dict_gpm[1][0]),
            rd2lstats.get_player_name_for_account_id(sorted_dict_gpm[2][0]),
            rd2lstats.get_player_name_for_account_id(sorted_dict_gpm[3][0]),
            rd2lstats.get_player_name_for_account_id(sorted_dict_gpm[4][0])), inline=True)
        embed11.add_field(name="GPM",
                          value="{} \n{} \n{} \n{} \n{}".format(sorted_dict_gpm[0][1][0], sorted_dict_gpm[1][1][0],
                                                                sorted_dict_gpm[2][1][0], sorted_dict_gpm[3][1][0],
                                                                sorted_dict_gpm[4][1][0]), inline=True)
        embed11.add_field(name="Ranking", value="1. \n2. \n3. \n4. \n5.", inline=True)
        embed11.add_field(name="Player",
                          value="{} \n{} \n{} \n{} \n{}".format(
                              rd2lstats.get_player_name_for_account_id(sorted_dict_kda[0][0]),
                              rd2lstats.get_player_name_for_account_id(sorted_dict_kda[1][0]),
                              rd2lstats.get_player_name_for_account_id(sorted_dict_kda[2][0]),
                              rd2lstats.get_player_name_for_account_id(sorted_dict_kda[3][0]),
                              rd2lstats.get_player_name_for_account_id(sorted_dict_kda[4][0])), inline=True)
        embed11.add_field(name="KDA",
                          value="{} \n{} \n{} \n{} \n{}".format(sorted_dict_kda[0][1][0], sorted_dict_kda[1][1][0],
                                                                sorted_dict_kda[2][1][0], sorted_dict_kda[3][1][0],
                                                                sorted_dict_kda[4][1][0]), inline=True)
        embed11.add_field(name="Ranking", value="1. \n2. \n3. \n4. \n5.", inline=True)
        embed11.add_field(name="Player",
                          value="{} \n{} \n{} \n{} \n{}".format(
                              rd2lstats.get_player_name_for_account_id(sorted_dict_fantasy[0][0]),
                              rd2lstats.get_player_name_for_account_id(sorted_dict_fantasy[1][0]),
                              rd2lstats.get_player_name_for_account_id(sorted_dict_fantasy[2][0]),
                              rd2lstats.get_player_name_for_account_id(sorted_dict_fantasy[3][0]),
                              rd2lstats.get_player_name_for_account_id(sorted_dict_fantasy[4][0])), inline=True)
        embed11.add_field(name="Overall performance",
                          value="{} \n{} \n{} \n{} \n{}".format(round(sorted_dict_fantasy[0][1][0], 2),
                                                                round(sorted_dict_fantasy[1][1][0], 2),
                                                                round(sorted_dict_fantasy[2][1][0], 2),
                                                                round(sorted_dict_fantasy[3][1][0], 2),
                                                                round(sorted_dict_fantasy[4][1][0], 2)), inline=True)

        print('Processed embed 11')

        filtered_gpm2 = {key: value for key, value in gpm2.items()}
        sorted_dict_gpm = sorted(filtered_gpm2.items(), key=lambda kv: kv[1][0], reverse=True)
        filtered_kda2 = {key: value for key, value in kda2.items()}
        sorted_dict_kda = sorted(filtered_kda2.items(), key=lambda kv: kv[1][0], reverse=True)
        filtered_fantasy2 = {key: value for key, value in fantasy2.items()}
        sorted_dict_fantasy = sorted(filtered_fantasy2.items(), key=lambda kv: kv[1][0], reverse=True)

        embed12 = discord.Embed(title="Pos 2 Leaderboard", colour=discord.Colour(0x1))
        embed12.add_field(name="Ranking", value="1. \n2. \n3. \n4. \n5.", inline=True)
        embed12.add_field(name="Player",
                          value="{} \n{} \n{} \n{} \n{}".format(
                              rd2lstats.get_player_name_for_account_id(sorted_dict_gpm[0][0]),
                              rd2lstats.get_player_name_for_account_id(sorted_dict_gpm[1][0]),
                              rd2lstats.get_player_name_for_account_id(sorted_dict_gpm[2][0]),
                              rd2lstats.get_player_name_for_account_id(sorted_dict_gpm[3][0]),
                              rd2lstats.get_player_name_for_account_id(sorted_dict_gpm[4][0])), inline=True)
        embed12.add_field(name="GPM",
                          value="{} \n{} \n{} \n{} \n{}".format(sorted_dict_gpm[0][1][0], sorted_dict_gpm[1][1][0],
                                                                sorted_dict_gpm[2][1][0], sorted_dict_gpm[3][1][0],
                                                                sorted_dict_gpm[4][1][0]), inline=True)
        embed12.add_field(name="Ranking", value="1. \n2. \n3. \n4. \n5.", inline=True)
        embed12.add_field(name="Player",
                          value="{} \n{} \n{} \n{} \n{}".format(
                              rd2lstats.get_player_name_for_account_id(sorted_dict_kda[0][0]),
                              rd2lstats.get_player_name_for_account_id(sorted_dict_kda[1][0]),
                              rd2lstats.get_player_name_for_account_id(sorted_dict_kda[2][0]),
                              rd2lstats.get_player_name_for_account_id(sorted_dict_kda[3][0]),
                              rd2lstats.get_player_name_for_account_id(sorted_dict_kda[4][0])), inline=True)
        embed12.add_field(name="KDA",
                          value="{} \n{} \n{} \n{} \n{}".format(sorted_dict_kda[0][1][0], sorted_dict_kda[1][1][0],
                                                                sorted_dict_kda[2][1][0], sorted_dict_kda[3][1][0],
                                                                sorted_dict_kda[4][1][0]), inline=True)
        embed12.add_field(name="Ranking", value="1. \n2. \n3. \n4. \n5.", inline=True)
        embed12.add_field(name="Player",
                          value="{} \n{} \n{} \n{} \n{}".format(
                              rd2lstats.get_player_name_for_account_id(sorted_dict_fantasy[0][0]),
                              rd2lstats.get_player_name_for_account_id(sorted_dict_fantasy[1][0]),
                              rd2lstats.get_player_name_for_account_id(sorted_dict_fantasy[2][0]),
                              rd2lstats.get_player_name_for_account_id(sorted_dict_fantasy[3][0]),
                              rd2lstats.get_player_name_for_account_id(sorted_dict_fantasy[4][0])), inline=True)
        embed12.add_field(name="Overall performance",
                          value="{} \n{} \n{} \n{} \n{}".format(round(sorted_dict_fantasy[0][1][0], 2),
                                                                round(sorted_dict_fantasy[1][1][0], 2),
                                                                round(sorted_dict_fantasy[2][1][0], 2),
                                                                round(sorted_dict_fantasy[3][1][0], 2),
                                                                round(sorted_dict_fantasy[4][1][0], 2)), inline=True)

        print('Processed embed 12')
        print('Sleeping for 60s...')

        time.sleep(60)

        filtered_gpm3 = {key: value for key, value in gpm3.items()}
        sorted_dict_gpm = sorted(filtered_gpm3.items(), key=lambda kv: kv[1][0], reverse=True)
        filtered_kda3 = {key: value for key, value in kda3.items()}
        sorted_dict_kda = sorted(filtered_kda3.items(), key=lambda kv: kv[1][0], reverse=True)
        filtered_fantasy3 = {key: value for key, value in fantasy3.items()}
        sorted_dict_fantasy = sorted(filtered_fantasy3.items(), key=lambda kv: kv[1][0], reverse=True)

        embed13 = discord.Embed(title="Pos 3 Leaderboard", colour=discord.Colour(0x1))
        embed13.add_field(name="Ranking", value="1. \n2. \n3. \n4. \n5.", inline=True)
        embed13.add_field(name="Player",
                          value="{} \n{} \n{} \n{} \n{}".format(
                              rd2lstats.get_player_name_for_account_id(sorted_dict_gpm[0][0]),
                              rd2lstats.get_player_name_for_account_id(sorted_dict_gpm[1][0]),
                              rd2lstats.get_player_name_for_account_id(sorted_dict_gpm[2][0]),
                              rd2lstats.get_player_name_for_account_id(sorted_dict_gpm[3][0]),
                              rd2lstats.get_player_name_for_account_id(sorted_dict_gpm[4][0])), inline=True)
        embed13.add_field(name="GPM",
                          value="{} \n{} \n{} \n{} \n{}".format(sorted_dict_gpm[0][1][0], sorted_dict_gpm[1][1][0],
                                                                sorted_dict_gpm[2][1][0], sorted_dict_gpm[3][1][0],
                                                                sorted_dict_gpm[4][1][0]), inline=True)
        embed13.add_field(name="Ranking", value="1. \n2. \n3. \n4. \n5.", inline=True)
        embed13.add_field(name="Player",
                          value="{} \n{} \n{} \n{} \n{}".format(
                              rd2lstats.get_player_name_for_account_id(sorted_dict_kda[0][0]),
                              rd2lstats.get_player_name_for_account_id(sorted_dict_kda[1][0]),
                              rd2lstats.get_player_name_for_account_id(sorted_dict_kda[2][0]),
                              rd2lstats.get_player_name_for_account_id(sorted_dict_kda[3][0]),
                              rd2lstats.get_player_name_for_account_id(sorted_dict_kda[4][0])), inline=True)
        embed13.add_field(name="KDA",
                          value="{} \n{} \n{} \n{} \n{}".format(sorted_dict_kda[0][1][0], sorted_dict_kda[1][1][0],
                                                                sorted_dict_kda[2][1][0], sorted_dict_kda[3][1][0],
                                                                sorted_dict_kda[4][1][0]), inline=True)
        embed13.add_field(name="Ranking", value="1. \n2. \n3. \n4. \n5.", inline=True)
        embed13.add_field(name="Player",
                          value="{} \n{} \n{} \n{} \n{}".format(
                              rd2lstats.get_player_name_for_account_id(sorted_dict_fantasy[0][0]),
                              rd2lstats.get_player_name_for_account_id(sorted_dict_fantasy[1][0]),
                              rd2lstats.get_player_name_for_account_id(sorted_dict_fantasy[2][0]),
                              rd2lstats.get_player_name_for_account_id(sorted_dict_fantasy[3][0]),
                              rd2lstats.get_player_name_for_account_id(sorted_dict_fantasy[4][0])), inline=True)
        embed13.add_field(name="Overall performance",
                          value="{} \n{} \n{} \n{} \n{}".format(round(sorted_dict_fantasy[0][1][0], 2),
                                                                round(sorted_dict_fantasy[1][1][0], 2),
                                                                round(sorted_dict_fantasy[2][1][0], 2),
                                                                round(sorted_dict_fantasy[3][1][0], 2),
                                                                round(sorted_dict_fantasy[4][1][0], 2)), inline=True)

        print('Processed embed 13')

        filtered_gpm4 = {key: value for key, value in gpm4.items()}
        sorted_dict_gpm = sorted(filtered_gpm4.items(), key=lambda kv: kv[1][0], reverse=True)
        filtered_kda4 = {key: value for key, value in kda4.items()}
        sorted_dict_kda = sorted(filtered_kda4.items(), key=lambda kv: kv[1][0], reverse=True)
        filtered_fantasy4 = {key: value for key, value in fantasy4.items()}
        sorted_dict_fantasy = sorted(filtered_fantasy4.items(), key=lambda kv: kv[1][0], reverse=True)

        embed14 = discord.Embed(title="Pos 4 Leaderboard", colour=discord.Colour(0x1))
        embed14.add_field(name="Ranking", value="1. \n2. \n3. \n4. \n5.", inline=True)
        embed14.add_field(name="Player",
                          value="{} \n{} \n{} \n{} \n{}".format(
                              rd2lstats.get_player_name_for_account_id(sorted_dict_gpm[0][0]),
                              rd2lstats.get_player_name_for_account_id(sorted_dict_gpm[1][0]),
                              rd2lstats.get_player_name_for_account_id(sorted_dict_gpm[2][0]),
                              rd2lstats.get_player_name_for_account_id(sorted_dict_gpm[3][0]),
                              rd2lstats.get_player_name_for_account_id(sorted_dict_gpm[4][0])), inline=True)
        embed14.add_field(name="GPM",
                          value="{} \n{} \n{} \n{} \n{}".format(sorted_dict_gpm[0][1][0], sorted_dict_gpm[1][1][0],
                                                                sorted_dict_gpm[2][1][0], sorted_dict_gpm[3][1][0],
                                                                sorted_dict_gpm[4][1][0]), inline=True)
        embed14.add_field(name="Ranking", value="1. \n2. \n3. \n4. \n5.", inline=True)
        embed14.add_field(name="Player",
                          value="{} \n{} \n{} \n{} \n{}".format(
                              rd2lstats.get_player_name_for_account_id(sorted_dict_kda[0][0]),
                              rd2lstats.get_player_name_for_account_id(sorted_dict_kda[1][0]),
                              rd2lstats.get_player_name_for_account_id(sorted_dict_kda[2][0]),
                              rd2lstats.get_player_name_for_account_id(sorted_dict_kda[3][0]),
                              rd2lstats.get_player_name_for_account_id(sorted_dict_kda[4][0])), inline=True)
        embed14.add_field(name="KDA",
                          value="{} \n{} \n{} \n{} \n{}".format(sorted_dict_kda[0][1][0], sorted_dict_kda[1][1][0],
                                                                sorted_dict_kda[2][1][0], sorted_dict_kda[3][1][0],
                                                                sorted_dict_kda[4][1][0]), inline=True)
        embed14.add_field(name="Ranking", value="1. \n2. \n3. \n4. \n5.", inline=True)
        embed14.add_field(name="Player",
                          value="{} \n{} \n{} \n{} \n{}".format(
                              rd2lstats.get_player_name_for_account_id(sorted_dict_fantasy[0][0]),
                              rd2lstats.get_player_name_for_account_id(sorted_dict_fantasy[1][0]),
                              rd2lstats.get_player_name_for_account_id(sorted_dict_fantasy[2][0]),
                              rd2lstats.get_player_name_for_account_id(sorted_dict_fantasy[3][0]),
                              rd2lstats.get_player_name_for_account_id(sorted_dict_fantasy[4][0])), inline=True)
        embed14.add_field(name="Overall performance",
                          value="{} \n{} \n{} \n{} \n{}".format(round(sorted_dict_fantasy[0][1][0], 2),
                                                                round(sorted_dict_fantasy[1][1][0], 2),
                                                                round(sorted_dict_fantasy[2][1][0], 2),
                                                                round(sorted_dict_fantasy[3][1][0], 2),
                                                                round(sorted_dict_fantasy[4][1][0], 2)), inline=True)

        print('Processed embed 14')

        filtered_gpm5 = {key: value for key, value in gpm5.items()}
        sorted_dict_gpm = sorted(filtered_gpm5.items(), key=lambda kv: kv[1][0], reverse=True)
        filtered_kda5 = {key: value for key, value in kda5.items()}
        sorted_dict_kda = sorted(filtered_kda5.items(), key=lambda kv: kv[1][0], reverse=True)
        filtered_fantasy5 = {key: value for key, value in fantasy5.items()}
        sorted_dict_fantasy = sorted(filtered_fantasy5.items(), key=lambda kv: kv[1][0], reverse=True)
        print('Sleeping for 60s...')

        time.sleep(60)

        embed15 = discord.Embed(title="Pos 5 Leaderboard", colour=discord.Colour(0x1))
        embed15.add_field(name="Ranking", value="1. \n2. \n3. \n4. \n5.", inline=True)
        embed15.add_field(name="Player",
                          value="{} \n{} \n{} \n{} \n{}".format(
                              rd2lstats.get_player_name_for_account_id(sorted_dict_gpm[0][0]),
                              rd2lstats.get_player_name_for_account_id(sorted_dict_gpm[1][0]),
                              rd2lstats.get_player_name_for_account_id(sorted_dict_gpm[2][0]),
                              rd2lstats.get_player_name_for_account_id(sorted_dict_gpm[3][0]),
                              rd2lstats.get_player_name_for_account_id(sorted_dict_gpm[4][0])), inline=True)
        embed15.add_field(name="GPM",
                          value="{} \n{} \n{} \n{} \n{}".format(sorted_dict_gpm[0][1][0], sorted_dict_gpm[1][1][0],
                                                                sorted_dict_gpm[2][1][0], sorted_dict_gpm[3][1][0],
                                                                sorted_dict_gpm[4][1][0]), inline=True)
        embed15.add_field(name="Ranking", value="1. \n2. \n3. \n4. \n5.", inline=True)
        embed15.add_field(name="Player",
                          value="{} \n{} \n{} \n{} \n{}".format(
                              rd2lstats.get_player_name_for_account_id(sorted_dict_kda[0][0]),
                              rd2lstats.get_player_name_for_account_id(sorted_dict_kda[1][0]),
                              rd2lstats.get_player_name_for_account_id(sorted_dict_kda[2][0]),
                              rd2lstats.get_player_name_for_account_id(sorted_dict_kda[3][0]),
                              rd2lstats.get_player_name_for_account_id(sorted_dict_kda[4][0])), inline=True)
        embed15.add_field(name="KDA",
                          value="{} \n{} \n{} \n{} \n{}".format(sorted_dict_kda[0][1][0], sorted_dict_kda[1][1][0],
                                                                sorted_dict_kda[2][1][0], sorted_dict_kda[3][1][0],
                                                                sorted_dict_kda[4][1][0]), inline=True)
        embed15.add_field(name="Ranking", value="1. \n2. \n3. \n4. \n5.", inline=True)
        embed15.add_field(name="Player",
                          value="{} \n{} \n{} \n{} \n{}".format(
                              rd2lstats.get_player_name_for_account_id(sorted_dict_fantasy[0][0]),
                              rd2lstats.get_player_name_for_account_id(sorted_dict_fantasy[1][0]),
                              rd2lstats.get_player_name_for_account_id(sorted_dict_fantasy[2][0]),
                              rd2lstats.get_player_name_for_account_id(sorted_dict_fantasy[3][0]),
                              rd2lstats.get_player_name_for_account_id(sorted_dict_fantasy[4][0])), inline=True)
        embed15.add_field(name="Overall performance",
                          value="{} \n{} \n{} \n{} \n{}".format(round(sorted_dict_fantasy[0][1][0], 2),
                                                                round(sorted_dict_fantasy[1][1][0], 2),
                                                                round(sorted_dict_fantasy[2][1][0], 2),
                                                                round(sorted_dict_fantasy[3][1][0], 2),
                                                                round(sorted_dict_fantasy[4][1][0], 2)), inline=True)

        print('Processed embed 15')

        await message.channel.send(embed=embed)
        await message.channel.send(embed=embed2)
        await message.channel.send(embed=embed3)
        await message.channel.send(embed=embed4)
        await message.channel.send(embed=embed5)
        await message.channel.send(embed=embed6)
        await message.channel.send(embed=embed7)
        await message.channel.send(embed=embed8)
        await message.channel.send(embed=embed9)
        await message.channel.send(embed=embed10)
        await message.channel.send(embed=embed16)

        await message.channel.send(embed=embed11)
        await message.channel.send(embed=embed12)
        await message.channel.send(embed=embed13)
        await message.channel.send(embed=embed14)
        await message.channel.send(embed=embed15)
        print("Sent stats successfully")

client.run(permissionkey)
