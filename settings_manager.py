import json  # Import JSON so application settings can be saved and loaded
from pathlib import Path  # Import Path to work with file locations

from data_manager import write_json_safely  # Reuse the safe JSON writer


SETTINGS_FILE = Path(__file__).with_name(
    "app_settings.json"
)  # Location of the local application settings file


DEFAULT_SETTINGS = {
    "selected_subject_id": None,
    "view_expanded": False,
    "window_x": None,
    "window_y": None
}  # Default settings used when the application is opened for the first time


def load_settings():  # Function to load previously saved application settings
    if not SETTINGS_FILE.exists():  # Check if a settings file exists
        return DEFAULT_SETTINGS.copy()  # Return default settings if this is the first launch

    try:
        with SETTINGS_FILE.open("r", encoding="utf-8") as file:
            saved_settings = json.load(file)  # Read settings from the JSON file
    except (OSError, json.JSONDecodeError):
        return DEFAULT_SETTINGS.copy()  # Use defaults if the settings file is unreadable, since settings are not important data

    if not isinstance(saved_settings, dict):
        return DEFAULT_SETTINGS.copy()  # Use defaults if the file contains something unexpected

    settings = DEFAULT_SETTINGS.copy()  # Start with all default settings

    settings.update(saved_settings)  # Replace defaults with settings that were previously saved

    return settings  # Return the complete settings dictionary


def save_settings(settings):  # Function to permanently save application settings
    write_json_safely(SETTINGS_FILE, settings)  # Write the settings to the JSON file safely