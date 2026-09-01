import json  # Import JSON so we can save and load study data
import tkinter as tk
from datetime import datetime  # Import datetime so we can save the date of each study session
from pathlib import Path  # Import Path to work with file paths


CURRENT_SUBJECT = "Matematikk"  # The subject we are currently tracking

DATA_FILE = Path(__file__).with_name("study_data.json")  # Location of the file where study sessions are stored


elapsed_seconds = 0  # Variable to keep track of elapsed seconds in the current session
timer_running = False  # Variable to track if the timer is running
timer_job = None  # Variable to remember the scheduled timer update


def format_time(seconds):  # Function to format seconds into HH:MM:SS
    hours = seconds // 3600  # Calculate the number of whole hours
    minutes = (seconds % 3600) // 60  # Calculate the remaining whole minutes
    secs = seconds % 60  # Calculate the remaining seconds

    return f"{hours:02}:{minutes:02}:{secs:02}"  # Return the formatted time


def load_sessions():  # Function to load previously saved study sessions
    if DATA_FILE.exists():  # Check if the study data file already exists
        with DATA_FILE.open("r", encoding="utf-8") as file:
            return json.load(file)  # Read the JSON file and return the saved sessions

    return []  # Return an empty list if no data file exists yet


def save_sessions():  # Function to save all study sessions to the JSON file
    with DATA_FILE.open("w", encoding="utf-8") as file:
        json.dump(
            study_sessions,
            file,
            indent=4,
            ensure_ascii=False
        )  # Write the study sessions to the JSON file


def calculate_total_logged_seconds():  # Function to calculate the total saved time for the current subject
    total_seconds = 0  # Start the total at zero

    for session in study_sessions:  # Go through every saved study session
        if session["subject"] == CURRENT_SUBJECT:  # Only count sessions for the current subject
            total_seconds += session["duration_seconds"]  # Add the session time to the total

    return total_seconds  # Return the calculated total


def update_timer():  # Function to update the timer every second
    global elapsed_seconds  # Access the global elapsed_seconds variable
    global timer_job  # Access the scheduled timer job

    if timer_running:  # Only update the timer if it is running
        elapsed_seconds += 1  # Add one second to the current session

        timer_label.config(
            text=format_time(elapsed_seconds)  # Update the timer label with the new time
        )

        timer_job = window.after(
            1000,
            update_timer
        )  # Schedule another timer update after 1 second


def start_timer():  # Function to start or resume the timer
    global timer_running  # Access the global timer_running variable
    global timer_job  # Access the scheduled timer job

    if not timer_running:  # Check that the timer is not already running
        timer_running = True  # Set the timer state to running

        start_button.config(state="disabled")  # Disable the start button while the timer is running
        stop_button.config(state="normal")  # Enable the stop button

        session_label.config(text="")  # Remove the paused session text
        decision_frame.pack_forget()  # Hide the save and discard buttons while the timer is running

        timer_job = window.after(
            1000,
            update_timer
        )  # Schedule the first timer update after 1 second


def stop_timer():  # Function to stop or pause the timer
    global timer_running  # Access the global timer_running variable
    global timer_job  # Access the scheduled timer job

    timer_running = False  # Pause the timer

    if timer_job is not None:  # Check if a timer update has been scheduled
        window.after_cancel(timer_job)  # Cancel the scheduled timer update
        timer_job = None  # Clear the saved timer job

    start_button.config(state="normal")  # Enable the start button so the session can continue
    stop_button.config(state="disabled")  # Disable the stop button while paused

    session_label.config(
        text=f"Økt: {format_time(elapsed_seconds)}"  # Display the current session time
    )

    decision_frame.pack(pady=10)  # Show the save and discard buttons


def save_session():  # Function to permanently save the current study session
    global elapsed_seconds  # Access the current session time

    if elapsed_seconds > 0:  # Only save the session if some time has been recorded
        new_session = {
            "subject": CURRENT_SUBJECT,
            "date": datetime.now().date().isoformat(),
            "duration_seconds": elapsed_seconds
        }  # Create a dictionary containing information about the study session

        study_sessions.append(new_session)  # Add the new session to the list of saved sessions

        save_sessions()  # Save the updated list to the JSON file

        total_logged_seconds = calculate_total_logged_seconds()  # Calculate the new total study time

        total_label.config(
            text=f"Logget totalt: {format_time(total_logged_seconds)}"
        )  # Update the total time displayed in the app

    reset_session()  # Reset the current session


def discard_session():  # Function to discard the current study session
    reset_session()  # Reset the session without saving it


def reset_session():  # Function to reset the current study session
    global elapsed_seconds  # Access the current session time

    elapsed_seconds = 0  # Reset the current session time to zero

    timer_label.config(text="00:00:00")  # Reset the timer display
    session_label.config(text="")  # Remove the stopped session text

    decision_frame.pack_forget()  # Hide the save and discard buttons

    start_button.config(state="normal")  # Enable the start button
    stop_button.config(state="disabled")  # Disable the stop button


study_sessions = load_sessions()  # Load all previously saved study sessions when the program starts

total_logged_seconds = calculate_total_logged_seconds()  # Calculate the saved total when the program starts


window = tk.Tk()  # Create the main application window

window.title("Study Timer")  # Set the title of the window
window.geometry("400x420")  # Set the size of the window


title_label = tk.Label(  # Create a label for the application title
    window,
    text="Study Timer",
    font=("Arial", 24)
)

title_label.pack(pady=20)  # Add the title label to the window with padding


subject_label = tk.Label(  # Create a label for the current subject
    window,
    text=CURRENT_SUBJECT,
    font=("Arial", 18)
)

subject_label.pack(pady=10)  # Add the subject label to the window with padding


timer_label = tk.Label(  # Create a label to display the current timer
    window,
    text="00:00:00",
    font=("Arial", 32)
)

timer_label.pack(pady=20)  # Add the timer label to the window with padding


start_button = tk.Button(  # Create a button to start the timer
    window,
    text="START",
    command=start_timer
)

start_button.pack()  # Add the start button to the window


stop_button = tk.Button(  # Create a button to stop the timer
    window,
    text="STOPP",
    command=stop_timer,
    state="disabled"
)

stop_button.pack(pady=10)  # Add the stop button to the window with padding


session_label = tk.Label(  # Create a label to show the stopped session time
    window,
    text="",
    font=("Arial", 14)
)

session_label.pack()  # Add the session label to the window


decision_frame = tk.Frame(window)  # Create a frame to hold the save and discard buttons


save_button = tk.Button(  # Create a button to save the current session
    decision_frame,
    text="LAGRE TID",
    command=save_session
)

save_button.pack(side="left", padx=5)  # Place the save button on the left inside the frame


discard_button = tk.Button(  # Create a button to discard the current session
    decision_frame,
    text="KAST TID",
    command=discard_session
)

discard_button.pack(side="left", padx=5)  # Place the discard button next to the save button


total_label = tk.Label(  # Create a label to display the total saved study time
    window,
    text=f"Logget totalt: {format_time(total_logged_seconds)}",
    font=("Arial", 14)
)

total_label.pack(pady=20)  # Add the total time label to the window with padding


window.mainloop()  # Start the Tkinter event loop and keep the application running