import tkinter as tk


elapsed_seconds = 0 # Variable to keep track of elapsed seconds
timer_running = False # Variable to track if timer is running


def format_time(seconds): # Function to format seconds into HH:MM:SS
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60

    return f"{hours:02}:{minutes:02}:{secs:02}" # Function to update the timer display


def update_timer(): # Function to update the timer display
    global elapsed_seconds # Access the global variable

    if timer_running:
        elapsed_seconds += 1 # Increment the elapsed seconds by 1

        timer_label.config(
            text=format_time(elapsed_seconds) # Update the timer label with the formatted time
        )

        window.after(1000, update_timer) # Schedule the next update_timer after 1 second


def start_timer(): # Function to start the timer
    global timer_running # Access the global variable

    if not timer_running: # Check if the timer is not already running
        timer_running = True

        start_button.config(state="disabled") # Disable the start button to prevent multiple clicks
        stop_button.config(state="normal") # Enable the stop button to allow stopping the timer

        window.after(1000, update_timer) # Schedule the first update_timer after 1 second


def stop_timer(): # Function to stop the timer
    global timer_running # Access the global variable

    timer_running = False # Set the timer_running flag to False to stop the timer

    start_button.config(state="normal") # Enable the start button to allow restarting the timer
    stop_button.config(state="disabled") # Disable the stop button to prevent stopping the timer again


window = tk.Tk() # Create the main application window

window.title("Study Timer") # Set the title of the window
window.geometry("400x300") # Set the size of the window


title_label = tk.Label( # Create a label for the title
    window,
    text="Study Timer",
    font=("Arial", 24)
)

title_label.pack(pady=20) # Pack the title label with padding


subject_label = tk.Label( # Create a label for the subject
    window,
    text="Matematikk",
    font=("Arial", 18)
)

subject_label.pack(pady=10) # Pack the subject label with padding


timer_label = tk.Label( # Create a label for the timer display
    window,
    text="00:00:00",
    font=("Arial", 32)
)

timer_label.pack(pady=20) # Pack the timer label with padding


start_button = tk.Button( # Create a button to start the timer
    window,
    text="START",
    command=start_timer
)

start_button.pack() # Pack the start button


stop_button = tk.Button( # Create a button to stop the timer
    window,
    text="STOPP",
    command=stop_timer,
    state="disabled"
)

stop_button.pack(pady=10) # Pack the stop button with padding


window.mainloop() # Start the Tkinter event loop to run the application