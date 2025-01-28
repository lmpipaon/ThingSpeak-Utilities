
# This script is part of the ThingSpeak-Utilities repository.
# Licensed under the MIT License.
# Copyright (c) 2025 Luis Pipaon
# See the LICENSE file in the project root for more information.
# Repository: https://github.com/lmpipaon/ThingSpeak-Utilities

from datetime import timedelta, datetime
import urllib.request
import json


# List of User API keys
user_API_Key = ["XXXXXXXXXXXXXXXX", "XXXXXXXXXXXXXXXX"]


# Function to fetch channel information
def fetch_channels(user_api_keys):
    channel_list = []
    channel_number = 1

    for api_key in user_api_keys:
        url = f"https://api.thingspeak.com/channels.json?api_key={api_key}"

        try:
            with urllib.request.urlopen(url) as response:
                all_json_data = json.loads(response.read())

            for channel in all_json_data:
                name = channel['name']
                id_ = channel['id']

                # Find the read-only key
                read_only_key = next(key['api_key'] for key in channel['api_keys'] if not key['write_flag'])

                # Get the field names from the feeds URL, using the read-only key
                url2 = f"https://api.thingspeak.com/channels/{id_}/feeds.json?api_key={read_only_key}&results=0"
                fields = []

                try:
                    with urllib.request.urlopen(url2) as response:
                        feed_data = json.loads(response.read())
                    
                    # Extract field names (up to 8 fields)
                    for i in range(1, 9):
                        field_name = feed_data['channel'].get(f"field{i}")
                        if field_name:  # If the field is defined
                            fields.append(field_name)

                except Exception as e:
                    print(f"Error fetching fields from channel {name} (ID: {id_}): {e}")

                # Save the channel information with the fields
                channel_list.append([id_, name, read_only_key, channel_number, fields])
                channel_number += 1

                # Show the channel name and fields as we fetch them
                print(f"\nChannel {channel_number - 1}: {name} (ID: {id_})")
                print(f"  Available fields: {', '.join(fields) if fields else 'No fields defined'}")

        except Exception as e:
            print(f"Error fetching channels with API key {api_key}: {e}")

    return channel_list


# Function to write data to a CSV file
def write_to_csv(file_name, data_rows, header):
    with open(file_name, "w", encoding="utf-8") as f:
        f.write(header)
        f.writelines(data_rows)

# Function to process data from a specific channel
def process_channel(channel, start_date, num_weeks, string_type):
    id_ = channel[0]
    name = channel[1]
    api_key = channel[2]
    end_date = start_date + num_weeks * timedelta(weeks=1)
    file_name = f"{start_date.strftime('%Y-%m-%d')}_{end_date.strftime('%Y-%m-%d')}_{name}.csv"

    data_rows = []
    first_data_date = ''
    last_data_date = ''
    one_second = timedelta(seconds=1)

    for i in range(num_weeks):
        start_string = (start_date + i * timedelta(weeks=1)).strftime("%Y-%m-%d%%20%H:%M:%S")
        end_string = (start_date + (i + 1) * timedelta(weeks=1) - one_second).strftime("%Y-%m-%d%%20%H:%M:%S")
        url = f"https://api.thingspeak.com/channels/{id_}/feeds.json?api_key={api_key}&start={start_string}&end={end_string}&timezone=Europe%2FMadrid{string_type}"

        try:
            with urllib.request.urlopen(url) as response:
                all_data = json.loads(response.read())['feeds']

            for data in all_data:
                created_at = data['created_at']
                fields = [data.get(f'field{i}', '') for i in range(1, 9)]
                date = created_at.replace('T', ' ').replace('Z', '')
                row = date + ';' + ';'.join(fields) + '\n'
                data_rows.append(row)

                if first_data_date == '':
                    first_data_date = date
                last_data_date = date

            print(f"{name} -> Week {i + 1}/{num_weeks} processed successfully.")
        except Exception as e:
            print(f"Error processing week {i + 1} for channel {name}: {e}")

    header = 'DATE;' + ';'.join([f'field{i}' for i in range(1, 9)]) + '\n'
    write_to_csv(file_name, data_rows, header)
    return first_data_date, last_data_date

# Main program start
if __name__ == "__main__":
    print("Welcome to the ThingSpeak data processing program.\n")

    # Choose the data interval type
    interval_map = {
        "A": "_",
        "B": "&average=10",
        "D": "&average=15",
        "E": "&average=20",
        "F": "&average=30",
        "G": "&average=60",
        "H": "&average=240",
        "I": "&average=720",
        "J": "&average=1440"
    }
    string_type = ""
    while string_type == "":
        choice = input(
            "Select the data interval:\n"
            "A: All data\n"
            "B: Average every 10 minutes\n"
            "D: Average every 15 minutes\n"
            "E: Average every 20 minutes\n"
            "F: Average every 30 minutes\n"
            "G: Average every 60 minutes\n"
            "H: Average every 240 minutes\n"
            "I: Average every 720 minutes\n"
            "J: Average every 1440 minutes\n"
            "Select: "
        ).upper()
        string_type = interval_map.get(choice, "")
        if string_type=="_":
            string_type==""

    # Get the start date and number of weeks
    start_date = None
    while not start_date:
        try:
            date_input = input("Enter the start date (YYYY-MM-DD): ")
            start_date = datetime.strptime(date_input, "%Y-%m-%d")
        except ValueError:
            print("Invalid date format.")

    num_weeks = 0
    while num_weeks < 1:
        try:
            num_weeks = int(input("Enter the number of weeks to process: "))
        except ValueError:
            print("Invalid number.")

    # Fetch the list of channels and display them
    channels = fetch_channels(user_API_Key)

    # Select channels to process
    selected_channels = input("\nSelect the channel numbers separated by commas (or leave blank to select all): ")
    if selected_channels:
        selected_channels = list(map(int, selected_channels.split(",")))
        channels = [ch for ch in channels if ch[3] in selected_channels]

    # Process the selected channels
    for channel in channels:
        print(f"\nProcessing channel: {channel[1]}")
        process_channel(channel, start_date, num_weeks, string_type)

    print("\nProcessing complete. Goodbye!")
