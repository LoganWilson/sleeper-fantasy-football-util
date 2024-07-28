from sleeper_wrapper import User, League, Stats
from dotenv import load_dotenv
import os
import json
from getplayers import get_or_generate_players_files 
from fileutil import save_json_file
import csv


# Load environment variables from .env file
load_dotenv()

# Get user ID and league ID from environment variables
user_id = os.getenv('USER_ID')
league_id = os.getenv('LEAGUE_ID')

# Create a User instance
user = User(user_id)

# Get user details to fetch the user ID
user_details = user.get_user()
actual_user_id = user_details['user_id']

# Create a League instance
league = League(league_id)

stats_client = Stats()

# Fetch league details
league_details = league.get_league()

if (league_details['status'] != 'complete'):
    print("League " + league_details['name'] + league_details['season'] + " is not complete yet. Check that you configured the correct league ID. To find it, follow instructions here: https://support.sleeper.com/en/articles/4121798-how-do-i-find-my-league-id ")
else:
    scoring_settings = league_details['scoring_settings']
    settings = league_details['settings']
    weeks_in_season = settings['last_scored_leg']
    
    def get_week_stats(week): 
        # Check if the file already exists
        tmp_folder = os.path.join(os.path.dirname(__file__), 'tmp')
        if not os.path.exists(tmp_folder):
            os.makedirs(tmp_folder)
        
        filename = f"stats{league_details['season']}{week}"
        json_file_name = filename + '.json'
        json_file = os.path.join(tmp_folder, json_file_name)
        csv_file_path = os.path.join(tmp_folder, filename + '.csv')
        week_stats = {}
        
        if not os.path.exists(json_file):
            # Get player stats for each week
            week_stats = stats_client.get_week_stats('regular', league_details['season'], week) 
            # Write week_stats to the file
            with open(csv_file_path, 'w') as file:
                for player_id, stats in week_stats.items():
                    file.write(f"{player_id},{','.join(str(stat) for stat in stats)}\n")
            save_json_file(week_stats, json_file_name)
        else: 
            with open(json_file, 'r') as file:
                week_stats = json.load(file)
        return week_stats
    
    def get_player_scores():
        player_scores = {}
    
        # only get scores for the weeks that were a part of the season
        for week in range(1, weeks_in_season + 1):
            week_stats = get_week_stats(week)
            
            for player_id, stats in week_stats.items():
                player_score = 0
                def calculate_score_for_this_week(player_score, valid_stats):
                    for stat in valid_stats:
                        # find the stat in the scoring settings
                        if (scoring_settings.get(stat, False)):
                            # if the stat is found, add the value to the player's score
                            points_for_each = scoring_settings[stat]
                            times_it_occured = valid_stats[stat]
                            # if times_it_occured < 0:
                            #     print('tst')
                            # if points_for_each < 0:
                            #     print('tst')
                            player_score += points_for_each * times_it_occured
                    return player_score                    
                
                if any(char.isalpha() for char in player_id):
                    # it's a defense, handle scoring differently
                    #for stat in stats:
                        #if stat is not a defensive stat, remove it
                    #valid_stats=
                    #calculate_score_for_this_week(valid_stats)
                    player_score=0
                else: 
                    # it's a player
                    # if player_id == '4046':
                    #     print('t')
                    player_score = calculate_score_for_this_week(player_score, stats)
                    player_scores.setdefault(player_id, 0) # create a new key if it doesn't exist
                    player_scores[player_id] += player_score       
        return player_scores
    
    # Fassign a cost to each player
    def get_player_costs(players, sorted_player_scores):
        players_by_position = {}
        player_costs = {}
        # for each player score, add the player to the list for that position
        for player_score in sorted_player_scores: 
            players_by_position.setdefault(players[player_score[0]]['position'], []).append(players[player_score[0]]['player_id']) # full_name can be used to debug by player names in place of player_id
        def set_position_salaries(players_by_position, position): 
            SALARIES = os.getenv(position + '_SALARIES').split(',')
            for player in players_by_position[position]:
                player_costs[player] = SALARIES[0]
                if len(SALARIES) != 1: 
                    # the last salary is default for everyone else
                    SALARIES.pop(0) 
            return player_costs
        
        set_position_salaries(players_by_position, "QB")
        set_position_salaries(players_by_position, "RB")
        set_position_salaries(players_by_position, "WR")
        set_position_salaries(players_by_position, "TE")
        return player_costs
    
        
    players = get_or_generate_players_files()
    player_scores = get_player_scores()
    
    # Sort the dictionary by values in descending order and convert to a list of tuples
    sorted_player_scores = sorted(player_scores.items(), key=lambda item: item[1], reverse=True)
    
    # for each sorted player, get the position from the players dictionary and pop the cost off the position list
    player_costs = get_player_costs(players, sorted_player_scores)
    
    # get all rosters
    rosters = league.get_rosters()
    league_users = league.get_users()
    
        
    # create roster CSV
    # Open a new CSV file for writing
    with open('roster_costs.csv', mode='w', newline='') as file:
        writer = csv.writer(file)
        
        # Write the header row
        header = []
        for roster in rosters:
            owner_id=roster['owner_id']
            owner_info = next((user for user in league_users if user['user_id'] == owner_id), None)
            owner_team_name = owner_info['metadata'].get('team_name', owner_info.get('display_name', 'Unknown'))
            header.append(owner_team_name)
            header.extend(['', ''])  # Two blank cells for each roster
        writer.writerow(header)
        
        # Write the second row
        second_row = []
        for _ in rosters:
            second_row.extend(['Player', 'Cost', ''])  # "Player", "Cost", and a blank cell for each roster
        writer.writerow(second_row)
        
        # Determine the maximum number of players in any roster
        max_players = max(len(roster['players']) for roster in rosters)
        
        # Write each player's ID and cost for each roster
        for i in range(max_players):
            row = []
            for roster in rosters:
                if i < len(roster['players']):
                    player_id = roster['players'][i]
                    player_cost = player_costs.get(player_id, '')
                    player = players[player_id]
                    # use team if full_name doesn't exist, since it's a defense
                    player_name = player.get('full_name', player.get('team', 'Unknown'))
                    row.extend([player_name, player_cost, ''])
                else:
                    row.extend(['', '', ''])  # Fill with blanks if no more players in this roster
            writer.writerow(row)
        
    # total the cost of each player on each roster and write next to each player
    
    print('end')
    
            
    
                    
        

    
    
    
    
    
    
    # get player scores for the regular season
    
    

    # get the number of weeks in the season
