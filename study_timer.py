import json  # Import JSON so we can save and load study data
import tkinter as tk
from datetime import date, datetime, timedelta  # Import tools for dates and weekly calculations
from pathlib import Path  # Import Path to work with file paths
from tkinter import messagebox, simpledialog  # Import popup windows for messages and text input
from uuid import uuid4  # Import uuid4 so every new subject can get a unique ID


DATA_FILE = Path(__file__).with_name("study_data.json")  # Location of the file where study data is stored
MAX_ACTIVE_SUBJECTS = 5  # Maximum number of active subjects allowed


elapsed_seconds = 0  # Variable to keep track of elapsed seconds in the current session
timer_running = False  # Variable to track if the timer is running
timer_job = None  # Variable to remember the scheduled timer update
current_subject_id = None  # Variable to remember which subject is currently selected


def format_time(seconds):  # Function to format seconds into HH:MM:SS
    hours = seconds // 3600  # Calculate the number of whole hours
    minutes = (seconds % 3600) // 60  # Calculate the remaining whole minutes
    secs = seconds % 60  # Calculate the remaining seconds

    return f"{hours:02}:{minutes:02}:{secs:02}"  # Return the formatted time


def format_hours_minutes(seconds):  # Function to format seconds into hours and minutes for statistics
    hours = seconds // 3600  # Calculate the number of whole hours
    minutes = (seconds % 3600) // 60  # Calculate the remaining whole minutes

    return f"{hours} t {minutes:02} min"  # Return the time in a readable hours-and-minutes format


def write_data(data):  # Function to write data to the JSON file
    with DATA_FILE.open("w", encoding="utf-8") as file:
        json.dump(
            data,
            file,
            indent=4,
            ensure_ascii=False
        )  # Save the data in a readable JSON format


def create_default_data():  # Function to create the starting data for a new user
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
    subjects = []  # List that will contain the converted subjects
    sessions = []  # List that will contain the converted study sessions
    subject_ids = {}  # Dictionary that connects old subject names to new subject IDs

    for old_session in old_sessions:  # Go through every session saved using the old format
        subject_name = old_session.get("subject", "Matematikk")  # Get the old subject name

        if subject_name not in subject_ids:  # Check if we have already created this subject
            subject_id = f"subject_{len(subjects) + 1}"  # Create a simple ID for the migrated subject

            subject_ids[subject_name] = subject_id  # Remember which ID belongs to this subject

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
        )  # Convert the old study session into the new format

    if not subjects:  # Check if the old file contained no subjects
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
    }  # Create the new data structure

    write_data(new_data)  # Save the converted data to the JSON file

    return new_data  # Return the converted data


def load_data():  # Function to load saved subjects and study sessions
    if not DATA_FILE.exists():  # Check if the data file exists
        new_data = create_default_data()  # Create starting data
        write_data(new_data)  # Save the starting data
        return new_data  # Return the starting data

    with DATA_FILE.open("r", encoding="utf-8") as file:
        loaded_data = json.load(file)  # Read the saved JSON data

    if isinstance(loaded_data, list):  # Check if the file uses our old list-based format
        return migrate_old_data(loaded_data)  # Convert the old data automatically

    return loaded_data  # Return the data if it already uses the new format


def save_data():  # Function to save all subjects and sessions
    write_data(app_data)  # Write the current application data to the JSON file


def get_active_subjects():  # Function to get all subjects that have not been archived
    active_subjects = []  # Create an empty list for active subjects

    for subject in app_data["subjects"]:  # Go through every subject
        if not subject["archived"]:  # Check if the subject is active
            active_subjects.append(subject)  # Add the subject to the active list

    return active_subjects  # Return all active subjects


def get_current_subject():  # Function to find the currently selected subject
    for subject in app_data["subjects"]:  # Go through every subject
        if subject["id"] == current_subject_id:  # Check if the ID matches the selected subject
            return subject  # Return the matching subject

    return None  # Return nothing if no matching subject exists


def calculate_total_logged_seconds(subject_id):  # Function to calculate total saved time for one subject
    total_seconds = 0  # Start the total at zero

    for session in app_data["sessions"]:  # Go through every saved study session
        if session["subject_id"] == subject_id:  # Check if the session belongs to this subject
            total_seconds += session["duration_seconds"]  # Add the session time to the total

    return total_seconds  # Return the total saved time


def calculate_weekly_logged_seconds(subject_id):  # Function to calculate study time for one subject this week
    today = date.today()  # Get today's date

    week_start = today - timedelta(
        days=today.weekday()
    )  # Find Monday of the current week

    week_end = week_start + timedelta(days=6)  # Find Sunday of the current week

    total_seconds = 0  # Start the weekly total at zero

    for session in app_data["sessions"]:  # Go through every saved study session
        if session["subject_id"] != subject_id:  # Skip sessions belonging to another subject
            continue

        session_date = date.fromisoformat(
            session["date"]
        )  # Convert the saved date text into a real Python date

        if week_start <= session_date <= week_end:  # Check if the session happened this week
            total_seconds += session["duration_seconds"]  # Add the session time to the weekly total

    return total_seconds  # Return the total study time for this subject this week


def update_statistics():  # Function to update the weekly and all-time statistics
    weekly_lines = []  # List of text lines for the weekly overview
    total_lines = []  # List of text lines for the all-time overview

    weekly_grand_total = 0  # Total study time across all subjects this week
    all_time_grand_total = 0  # Total study time across all subjects since the beginning

    for subject in app_data["subjects"]:  # Go through every subject, including archived subjects
        subject_id = subject["id"]  # Get the subject's permanent ID

        weekly_seconds = calculate_weekly_logged_seconds(
            subject_id
        )  # Calculate this week's study time for the subject

        total_seconds = calculate_total_logged_seconds(
            subject_id
        )  # Calculate all saved study time for the subject

        weekly_grand_total += weekly_seconds  # Add the subject time to the weekly grand total
        all_time_grand_total += total_seconds  # Add the subject time to the all-time grand total

        if not subject["archived"] or weekly_seconds > 0:
            weekly_lines.append(
                f'{subject["name"]}: {format_hours_minutes(weekly_seconds)}'
            )  # Show active subjects and archived subjects studied this week

        if not subject["archived"] or total_seconds > 0:
            archived_text = " (arkivert)" if subject["archived"] else ""

            total_lines.append(
                f'{subject["name"]}{archived_text}: {format_hours_minutes(total_seconds)}'
            )  # Show subjects in the all-time overview without deleting archived history

    weekly_lines.append(
        f"\nTotalt: {format_hours_minutes(weekly_grand_total)}"
    )  # Add the combined weekly total

    total_lines.append(
        f"\nTotalt: {format_hours_minutes(all_time_grand_total)}"
    )  # Add the combined all-time total

    weekly_statistics_label.config(
        text="\n".join(weekly_lines)
    )  # Update the weekly statistics shown on screen

    total_statistics_label.config(
        text="\n".join(total_lines)
    )  # Update the all-time statistics shown on screen


def update_subject_display():  # Function to update the selected subject and its total time
    subject = get_current_subject()  # Get the currently selected subject

    if subject is None:  # Stop if no subject is selected
        return

    subject_label.config(
        text=subject["name"]
    )  # Display the name of the selected subject

    total_seconds = calculate_total_logged_seconds(
        subject["id"]
    )  # Calculate the saved time for the selected subject

    total_label.config(
        text=f"Logget totalt: {format_time(total_seconds)}"
    )  # Display the total saved time for the selected subject


def refresh_subject_buttons():  # Function to rebuild the subject buttons on the main screen
    for widget in subject_buttons_frame.winfo_children():  # Go through existing subject buttons
        widget.destroy()  # Remove the old buttons

    for subject in get_active_subjects():  # Create one button for each active subject
        button = tk.Button(
            subject_buttons_frame,
            text=subject["name"],
            command=lambda subject_id=subject["id"]: select_subject(subject_id),
            relief="sunken" if subject["id"] == current_subject_id else "raised"
        )

        button.pack(
            side="left",
            padx=4,
            pady=4
        )  # Place the subject button inside the subject button frame


def select_subject(subject_id):  # Function to switch to another subject
    global current_subject_id  # Access the selected subject variable

    if timer_running or elapsed_seconds > 0:  # Check if a study session is currently in progress
        messagebox.showwarning(
            "Økt pågår",
            "Lagre eller kast den nåværende økten før du bytter fag."
        )

        return  # Stop the function without changing subject

    current_subject_id = subject_id  # Change the selected subject

    refresh_subject_buttons()  # Update which subject button looks selected
    update_subject_display()  # Update the subject name and total time


def add_subject():  # Function to add a new subject
    active_subjects = get_active_subjects()  # Get all active subjects

    if len(active_subjects) >= MAX_ACTIVE_SUBJECTS:  # Check if the user already has five active subjects
        messagebox.showwarning(
            "Maks antall fag",
            "Du kan ha maksimalt 5 aktive fag."
        )

        return  # Stop without adding another subject

    subject_name = simpledialog.askstring(
        "Legg til fag",
        "Hva skal faget hete?"
    )  # Ask the user to enter a name for the new subject

    if subject_name is None:  # Check if the user pressed Cancel
        return

    subject_name = subject_name.strip()  # Remove unnecessary spaces around the name

    if not subject_name:  # Check if the entered name is empty
        messagebox.showwarning(
            "Ugyldig navn",
            "Faget må ha et navn."
        )

        return

    for subject in active_subjects:  # Check existing active subjects
        if subject["name"].lower() == subject_name.lower():  # Compare names without caring about capital letters
            messagebox.showwarning(
                "Faget finnes allerede",
                "Du har allerede et aktivt fag med dette navnet."
            )

            return

    new_subject = {
        "id": uuid4().hex,
        "name": subject_name,
        "archived": False
    }  # Create the new subject with a unique ID

    app_data["subjects"].append(new_subject)  # Add the new subject to the subject list

    save_data()  # Save the new subject permanently

    refresh_subject_buttons()  # Show the new subject on the main screen
    update_statistics()  # Update the statistics to include the new subject


def rename_subject():  # Function to rename the currently selected subject
    if timer_running or elapsed_seconds > 0:  # Check if a study session is in progress
        messagebox.showwarning(
            "Økt pågår",
            "Lagre eller kast den nåværende økten før du endrer faget."
        )

        return

    subject = get_current_subject()  # Get the currently selected subject

    if subject is None:  # Stop if no subject is selected
        return

    new_name = simpledialog.askstring(
        "Endre navn",
        "Nytt navn på faget:",
        initialvalue=subject["name"]
    )  # Ask the user for a new subject name

    if new_name is None:  # Check if the user pressed Cancel
        return

    new_name = new_name.strip()  # Remove unnecessary spaces

    if not new_name:  # Check if the new name is empty
        messagebox.showwarning(
            "Ugyldig navn",
            "Faget må ha et navn."
        )

        return

    for other_subject in get_active_subjects():  # Check all active subjects
        if (
            other_subject["id"] != subject["id"]
            and other_subject["name"].lower() == new_name.lower()
        ):  # Check if another active subject already has the same name
            messagebox.showwarning(
                "Navnet finnes allerede",
                "Et annet aktivt fag har allerede dette navnet."
            )

            return

    subject["name"] = new_name  # Change only the visible name of the subject

    save_data()  # Save the new name permanently

    refresh_subject_buttons()  # Update the subject buttons
    update_subject_display()  # Update the subject title
    update_statistics()  # Update the subject names shown in the statistics


def archive_subject():  # Function to remove the selected subject from the main screen
    global current_subject_id  # Access the selected subject variable

    if timer_running or elapsed_seconds > 0:  # Check if a session is currently in progress
        messagebox.showwarning(
            "Økt pågår",
            "Lagre eller kast den nåværende økten før du fjerner faget."
        )

        return

    active_subjects = get_active_subjects()  # Get all active subjects

    if len(active_subjects) <= 1:  # Make sure at least one active subject remains
        messagebox.showwarning(
            "Kan ikke fjerne fag",
            "Du må ha minst ett aktivt fag."
        )

        return

    subject = get_current_subject()  # Get the currently selected subject

    if subject is None:  # Stop if no subject is selected
        return

    should_archive = messagebox.askyesno(
        "Fjern fag",
        (
            f'Vil du fjerne "{subject["name"]}" fra hovedskjermen?\n\n'
            "Tid du allerede har logget på faget blir ikke slettet."
        )
    )  # Ask the user to confirm before archiving the subject

    if not should_archive:  # Stop if the user chooses No
        return

    subject["archived"] = True  # Mark the subject as archived instead of deleting it

    remaining_subjects = get_active_subjects()  # Get the subjects that are still active

    current_subject_id = remaining_subjects[0]["id"]  # Select the first remaining subject

    save_data()  # Save the archived state permanently

    refresh_subject_buttons()  # Remove the archived subject from the main screen
    update_subject_display()  # Show the newly selected subject
    update_statistics()  # Update the statistics after archiving the subject


def update_timer():  # Function to update the timer every second
    global elapsed_seconds  # Access the elapsed seconds variable
    global timer_job  # Access the scheduled timer job

    if timer_running:  # Only update the timer if it is running
        elapsed_seconds += 1  # Add one second to the current study session

        timer_label.config(
            text=format_time(elapsed_seconds)
        )  # Update the timer display

        timer_job = window.after(
            1000,
            update_timer
        )  # Schedule another update after one second


def start_timer():  # Function to start or resume the timer
    global timer_running  # Access the timer state
    global timer_job  # Access the scheduled timer job

    if not timer_running:  # Check that the timer is not already running
        timer_running = True  # Mark the timer as running

        start_button.config(state="disabled")  # Disable Start while the timer is running
        stop_button.config(state="normal")  # Enable Stop

        session_label.config(text="")  # Hide the paused session text
        decision_frame.pack_forget()  # Hide save and discard buttons

        timer_job = window.after(
            1000,
            update_timer
        )  # Schedule the first timer update


def stop_timer():  # Function to stop or pause the timer
    global timer_running  # Access the timer state
    global timer_job  # Access the scheduled timer job

    timer_running = False  # Pause the timer

    if timer_job is not None:  # Check if an update is currently scheduled
        window.after_cancel(timer_job)  # Cancel the scheduled update
        timer_job = None  # Clear the scheduled job

    start_button.config(state="normal")  # Allow the user to resume the session
    stop_button.config(state="disabled")  # Disable Stop while paused

    session_label.config(
        text=f"Økt: {format_time(elapsed_seconds)}"
    )  # Show the current study session time

    decision_frame.pack(pady=10)  # Show the save and discard buttons


def save_session():  # Function to permanently save the current study session
    global elapsed_seconds  # Access the current session time

    if elapsed_seconds > 0:  # Only save if at least one second has been recorded
        new_session = {
            "subject_id": current_subject_id,
            "date": datetime.now().date().isoformat(),
            "duration_seconds": elapsed_seconds
        }  # Create a new study session connected to the selected subject

        app_data["sessions"].append(new_session)  # Add the session to the saved session list

        save_data()  # Save everything permanently

    reset_session()  # Reset the current timer
    update_subject_display()  # Update the total saved study time
    update_statistics()  # Update the weekly and all-time statistics


def discard_session():  # Function to discard the current study session
    reset_session()  # Reset the timer without saving the session


def reset_session():  # Function to reset the current study session
    global elapsed_seconds  # Access the elapsed seconds variable

    elapsed_seconds = 0  # Reset the session time

    timer_label.config(text="00:00:00")  # Reset the timer display
    session_label.config(text="")  # Remove the paused session text

    decision_frame.pack_forget()  # Hide save and discard buttons

    start_button.config(state="normal")  # Enable Start
    stop_button.config(state="disabled")  # Disable Stop


app_data = load_data()  # Load saved subjects and study sessions when the app starts

active_subjects = get_active_subjects()  # Get the active subjects

current_subject_id = active_subjects[0]["id"]  # Select the first active subject when the app starts


window = tk.Tk()  # Create the main application window

window.title("Study Timer")  # Set the application window title
window.geometry("700x700")  # Set the size of the window


title_label = tk.Label(
    window,
    text="Study Timer",
    font=("Arial", 24)
)  # Create the main application title

title_label.pack(pady=20)  # Add the title to the window


subjects_title_label = tk.Label(
    window,
    text="Fag",
    font=("Arial", 12)
)  # Create a small title above the subject buttons

subjects_title_label.pack()


subject_buttons_frame = tk.Frame(window)  # Create a frame that will contain all active subject buttons

subject_buttons_frame.pack(pady=5)  # Add the subject button frame to the window


subject_label = tk.Label(
    window,
    text="",
    font=("Arial", 18)
)  # Create the title for the currently selected subject

subject_label.pack(pady=10)  # Add the selected subject title


timer_label = tk.Label(
    window,
    text="00:00:00",
    font=("Arial", 32)
)  # Create the timer display

timer_label.pack(pady=15)  # Add the timer display


start_button = tk.Button(
    window,
    text="START",
    command=start_timer
)  # Create the Start button

start_button.pack()  # Add the Start button


stop_button = tk.Button(
    window,
    text="STOPP",
    command=stop_timer,
    state="disabled"
)  # Create the Stop button

stop_button.pack(pady=10)  # Add the Stop button


session_label = tk.Label(
    window,
    text="",
    font=("Arial", 14)
)  # Create a label for the paused session time

session_label.pack()  # Add the session label


decision_frame = tk.Frame(window)  # Create a frame for the Save and Discard buttons


save_button = tk.Button(
    decision_frame,
    text="LAGRE TID",
    command=save_session
)  # Create the Save button

save_button.pack(side="left", padx=5)  # Place the Save button inside the frame


discard_button = tk.Button(
    decision_frame,
    text="KAST TID",
    command=discard_session
)  # Create the Discard button

discard_button.pack(side="left", padx=5)  # Place the Discard button beside the Save button


total_label = tk.Label(
    window,
    text="",
    font=("Arial", 14)
)  # Create a label for the selected subject's total saved time

total_label.pack(pady=15)  # Add the total time label


management_frame = tk.Frame(window)  # Create a frame for subject management buttons

management_frame.pack(pady=10)  # Add the management frame


add_subject_button = tk.Button(
    management_frame,
    text="+ LEGG TIL FAG",
    command=add_subject
)  # Create a button for adding subjects

add_subject_button.pack(side="left", padx=5)  # Add the button to the management frame


rename_subject_button = tk.Button(
    management_frame,
    text="ENDRE NAVN",
    command=rename_subject
)  # Create a button for renaming the selected subject

rename_subject_button.pack(side="left", padx=5)  # Add the button beside Add Subject


archive_subject_button = tk.Button(
    management_frame,
    text="FJERN FAG",
    command=archive_subject
)  # Create a button for archiving the selected subject

archive_subject_button.pack(side="left", padx=5)  # Add the button beside Rename Subject

statistics_frame = tk.Frame(window)  # Create a frame to contain the statistics sections

statistics_frame.pack(
    pady=15,
    padx=20,
    fill="x"
)  # Add the statistics frame to the window


weekly_frame = tk.Frame(
    statistics_frame,
    bd=1,
    relief="solid"
)  # Create a bordered frame for weekly statistics

weekly_frame.pack(
    side="left",
    padx=10,
    fill="both",
    expand=True
)  # Place the weekly overview on the left


weekly_title_label = tk.Label(
    weekly_frame,
    text="DENNE UKEN",
    font=("Arial", 14, "bold")
)  # Create the weekly statistics title

weekly_title_label.pack(pady=(10, 5))


weekly_statistics_label = tk.Label(
    weekly_frame,
    text="",
    font=("Arial", 12),
    justify="left",
    anchor="w"
)  # Create the text area for weekly statistics

weekly_statistics_label.pack(
    padx=15,
    pady=(5, 15),
    anchor="w"
)


all_time_frame = tk.Frame(
    statistics_frame,
    bd=1,
    relief="solid"
)  # Create a bordered frame for all-time statistics

all_time_frame.pack(
    side="left",
    padx=10,
    fill="both",
    expand=True
)  # Place the all-time overview on the right


total_title_label = tk.Label(
    all_time_frame,
    text="TOTALT SIDEN START",
    font=("Arial", 14, "bold")
)  # Create the all-time statistics title

total_title_label.pack(pady=(10, 5))


total_statistics_label = tk.Label(
    all_time_frame,
    text="",
    font=("Arial", 12),
    justify="left",
    anchor="w"
)  # Create the text area for all-time statistics

total_statistics_label.pack(
    padx=15,
    pady=(5, 15),
    anchor="w"
)


refresh_subject_buttons()  # Create the subject buttons when the application starts
update_subject_display()  # Display the selected subject and its saved total
update_statistics()  # Display the weekly and all-time statistics when the application starts


window.mainloop()  # Start the Tkinter event loop and keep the application running