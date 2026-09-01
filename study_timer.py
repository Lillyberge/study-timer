import tkinter as tk


elapsed_seconds = 0  # Variable to keep track of elapsed seconds in the current session
total_logged_seconds = 0  # Variable to keep track of the total saved study time
timer_running = False  # Variable to track if the timer is running


def format_time(seconds):  # Function to format seconds into HH:MM:SS
    hours = seconds // 3600  # Calculate the number of whole hours
    minutes = (seconds % 3600) // 60  # Calculate the remaining whole minutes
    secs = seconds % 60  # Calculate the remaining seconds

    return f"{hours:02}:{minutes:02}:{secs:02}"  # Return the formatted time


def update_timer():  # Function to update the timer every second
    global elapsed_seconds  # Access the global elapsed_seconds variable

    if timer_running:  # Only update the timer if it is running
        elapsed_seconds += 1  # Add one second to the current session

        timer_label.config(
            text=format_time(elapsed_seconds)  # Update the timer label with the new time
        )

        window.after(1000, update_timer)  # Run update_timer again after 1 second


def start_timer():  # Function to start or resume the timer
    global timer_running  # Access the global timer_running variable

    if not timer_running:  # Check that the timer is not already running
        timer_running = True  # Set the timer state to running

        start_button.config(state="disabled")  # Disable the start button while running
        stop_button.config(state="normal")  # Enable the stop button

        session_label.config(text="")  # Hide the paused session text
        decision_frame.pack_forget()  # Hide save/discard buttons while the timer is running

        window.after(1000, update_timer)  # Continue updating the timer


def stop_timer():  # Function to stop/pause the timer
    global timer_running  # Access the global timer_running variable

    timer_running = False  # Pause the timer

    start_button.config(state="normal")  # Enable the start button so the session can continue
    stop_button.config(state="disabled")  # Disable the stop button while the timer is paused

    session_label.config(
        text=f"Økt: {format_time(elapsed_seconds)}"  # Show the current session time
    )

    decision_frame.pack(pady=10)  # Show the save and discard buttons


def save_session():  # Function to save the current study session
    global elapsed_seconds  # Access the current session time
    global total_logged_seconds  # Access the total logged study time

    total_logged_seconds += elapsed_seconds  # Add the current session to the total saved time

    total_label.config(
        text=f"Logget totalt: {format_time(total_logged_seconds)}"  # Update the total time displayed
    )

    reset_session()  # Reset the current session after saving it


def discard_session():  # Function to discard the current study session
    reset_session()  # Reset the session without adding it to the total time


def reset_session():  # Function to reset the current study session
    global elapsed_seconds  # Access the current session time

    elapsed_seconds = 0  # Reset the current session time to zero

    timer_label.config(text="00:00:00")  # Reset the timer display
    session_label.config(text="")  # Remove the completed session text

    decision_frame.pack_forget()  # Hide the save and discard buttons

    start_button.config(state="normal")  # Enable the start button again
    stop_button.config(state="disabled")  # Disable the stop button


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
    text="Matematikk",
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


session_label = tk.Label(  # Create a label to show the time of the stopped session
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
    text="Logget totalt: 00:00:00",
    font=("Arial", 14)
)

total_label.pack(pady=20)  # Add the total time label to the window with padding


window.mainloop()  # Start the Tkinter event loop and keep the application running