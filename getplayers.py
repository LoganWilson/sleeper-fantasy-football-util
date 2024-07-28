import csv
import os
from sleeper_wrapper import Players
from datetime import date
import json
from fileutil import save_json_file

# Create a temporary directory for generated files
# only create temp dir if it doesn't exist
if not os.path.exists('tmp'):
    os.makedirs('tmp')
temp_dir = os.path.join(os.getcwd(), 'tmp') 
year = date.today().strftime("%Y")

# Create a Sleeper client
client = Players()
# Retrieve all players using the Sleeper client
def get_all_players():
    players = client.get_all_players()
    return players

def write_players_csv(players):
    # Specify the CSV file path in the temporary directory with today's date
    csv_file = os.path.join(temp_dir, f'players_{year}.csv')

    # Get the first player ID from the players dictionary
    first_player_id = next(iter(players))

    # Write players data to CSV file
    with open(csv_file, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['player_upn'] + list(players[first_player_id].keys()))  # Write header row with player_upn and object keys
        writer.writerow([first_player_id] + list(players[first_player_id].values()))  # Write player data with player_upn and object values

    print('CSV file created successfully in the temporary directory:', temp_dir)

def get_or_generate_players_files():
    # Check if players.json already exists
    json_file = os.path.join(temp_dir, f'players_{year}.json')
    if os.path.exists(json_file):
        # Load players data from players.json
        with open(json_file, 'r') as file:
            players = json.load(file)
    else:
        # Retrieve all players using the Sleeper client
        players = get_all_players()
        write_players_csv(players)
        save_json_file(players, "players_"+ year +'.json')
    return players
        
get_or_generate_players_files()