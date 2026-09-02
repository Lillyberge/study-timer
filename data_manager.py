import json  # Import JSON so we can save and load study data
from datetime import date, timedelta  # Import date tools for weekly calculations
from pathlib import Path  # Import Path to work with file paths


DATA_FILE = Path(__file__).with_name("study_data.json")  # Location of the file where study data is stored


def write_data(data):  # Function to write application data to the JSON file
    with DATA_FILE.open("w", encoding="utf-8") as file:
        json.dump(
            data,
            file,
            indent=4,
            ensure_ascii=False
        )  # Save the data in a readable JSON format


def create_default_data():  # Function to create starting data for a new user
    return {
        "subjects": [
            {
                "id": "subject_1",
                "name": "Matematikk",
                "archived": False
            }
        ],
        "sessions": []
    }


def migrate_old_data(old_sessions):  # Function to convert the old data format into the new format
    subjects = []  # List that will contain converted subjects
    sessions = []  # List that will contain converted study sessions
    subject_ids = {}  # Dictionary connecting old subject names to new subject IDs

    for old_session in old_sessions:  # Go through every session stored using the old format
        subject_name = old_session.get(
            "subject",
            "Matematikk"
        )  # Get the old subject name

        if subject_name not in subject_ids:  # Check if this subject has already been created
            subject_id = f"subject_{len(subjects) + 1}"  # Create an ID for the migrated subject

            subject_ids[subject_name] = subject_id  # Remember which ID belongs to the subject

            subjects.append(
                {
                    "id": subject_id,
                    "name": subject_name,
                    "archived": False
                }
            )  # Add the subject to the new subject list

        sessions.append(
            {
                "subject_id": subject_ids[subject_name],
                "date": old_session["date"],
                "duration_seconds": old_session["duration_seconds"]
            }
        )  # Convert the old study session to the new format

    if not subjects:  # Check if there were no subjects in the old data
        subjects.append(
            {
                "id": "subject_1",
                "name": "Matematikk",
                "archived": False
            }
        )  # Create a default subject if necessary

    new_data = {
        "subjects": subjects,
        "sessions": sessions
    }  # Create the new application data structure

    write_data(new_data)  # Save the converted data

    return new_data  # Return the converted data


def load_data():  # Function to load saved subjects and study sessions
    if not DATA_FILE.exists():  # Check if a data file exists
        new_data = create_default_data()  # Create starting data

        write_data(new_data)  # Save the starting data

        return new_data  # Return the new data

    with DATA_FILE.open("r", encoding="utf-8") as file:
        loaded_data = json.load(file)  # Read the saved JSON data

    if isinstance(loaded_data, list):  # Check if the data uses our old format
        return migrate_old_data(loaded_data)  # Convert the old format automatically

    return loaded_data  # Return data already using the current format


def save_data(app_data):  # Function to permanently save all subjects and sessions
    write_data(app_data)  # Write the application data to the JSON file


def get_active_subjects(app_data):  # Function to get subjects that are not archived
    active_subjects = []  # Create an empty list for active subjects

    for subject in app_data["subjects"]:  # Go through every subject
        if not subject["archived"]:  # Check if the subject is active
            active_subjects.append(subject)  # Add it to the active subject list

    return active_subjects  # Return all active subjects


def get_subject_by_id(app_data, subject_id):  # Function to find a subject using its permanent ID
    for subject in app_data["subjects"]:  # Go through every subject
        if subject["id"] == subject_id:  # Check if the ID matches
            return subject  # Return the matching subject

    return None  # Return nothing if the subject cannot be found


def calculate_total_logged_seconds(app_data, subject_id):  # Function to calculate all-time study time for one subject
    total_seconds = 0  # Start the total at zero

    for session in app_data["sessions"]:  # Go through every saved session
        if session["subject_id"] == subject_id:  # Check if the session belongs to this subject
            total_seconds += session["duration_seconds"]  # Add the session time

    return total_seconds  # Return the calculated total


def calculate_weekly_logged_seconds(app_data, subject_id):  # Function to calculate this week's study time for one subject
    today = date.today()  # Get today's date

    week_start = today - timedelta(
        days=today.weekday()
    )  # Find Monday of the current week

    week_end = week_start + timedelta(days=6)  # Find Sunday of the current week

    total_seconds = 0  # Start the weekly total at zero

    for session in app_data["sessions"]:  # Go through every saved study session
        if session["subject_id"] != subject_id:  # Skip sessions belonging to other subjects
            continue

        session_date = date.fromisoformat(
            session["date"]
        )  # Convert the saved date text into a Python date

        if week_start <= session_date <= week_end:  # Check if the session happened this week
            total_seconds += session["duration_seconds"]  # Add the session time

    return total_seconds  # Return the weekly total