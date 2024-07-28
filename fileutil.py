import os
import json

def save_json_file(json_object, filename):
    
    # Create a temporary directory for generated files
    # only create temp dir if it doesn't exist
    if not os.path.exists('tmp'):
        os.makedirs('tmp')
    temp_dir = os.path.join(os.getcwd(), 'tmp') 
    
    # Convert the players data to JSON format
    converted_json = json.dumps(json_object)

    # Specify the JSON file path in the temporary directory with today's date
    json_file = os.path.join(temp_dir, f'{filename}')

    # Save the players data to a JSON file
    with open(json_file, 'w') as file:
        file.write(converted_json)

    print('JSON file ' + filename + ' created successfully in the temporary directory:', temp_dir)