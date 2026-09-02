import tkinter as tk
from tkinter import ttk  # Import ttk for more modern-looking interface elements
from datetime import datetime  # Import datetime so we can save the date of each study session
from tkinter import messagebox, simpledialog  # Import popup windows for messages and text input
from uuid import uuid4  # Import uuid4 so every new subject gets a unique ID


from data_manager import (
    calculate_total_logged_seconds,
    calculate_weekly_logged_seconds,
    get_active_subjects,
    get_subject_by_id,
    load_data,
    save_data
)  # Import data functions from our own data_manager module


from styles import configure_styles  # Import the application's visual style configuration



MAX_ACTIVE_SUBJECTS = 5  # Maximum number of active subjects allowed


elapsed_seconds = 0  # Seconds recorded in the current study session
timer_running = False  # Variable to track whether the timer is running
timer_job = None  # Variable to remember the scheduled timer update
current_subject_id = None  # ID of the subject currently selected


def format_time(seconds):  # Function to format seconds into HH:MM:SS
    hours = seconds // 3600  # Calculate whole hours
    minutes = (seconds % 3600) // 60  # Calculate remaining whole minutes
    secs = seconds % 60  # Calculate remaining seconds

    return f"{hours:02}:{minutes:02}:{secs:02}"  # Return formatted timer text


def format_hours_minutes(seconds):  # Function to format seconds for statistics
    hours = seconds // 3600  # Calculate whole hours
    minutes = (seconds % 3600) // 60  # Calculate remaining minutes

    return f"{hours} t {minutes:02} min"  # Return readable hours-and-minutes text


def get_current_subject():  # Function to get the currently selected subject
    return get_subject_by_id(
        app_data,
        current_subject_id
    )  # Ask data_manager to find the subject using its ID


def update_subject_display():  # Function to update the selected subject and its total time
    subject = get_current_subject()  # Get the selected subject

    if subject is None:  # Stop if no subject is selected
        return

    subject_label.config(
        text=subject["name"]
    )  # Display the selected subject name

    total_seconds = calculate_total_logged_seconds(
        app_data,
        subject["id"]
    )  # Calculate the subject's all-time study time

    total_label.config(
        text=f"Logget totalt: {format_time(total_seconds)}"
    )  # Display the selected subject's total study time


def update_statistics():  # Function to update weekly and all-time statistics
    weekly_lines = []  # Text lines for the weekly overview
    total_lines = []  # Text lines for the all-time overview

    weekly_grand_total = 0  # Total study time across all subjects this week
    all_time_grand_total = 0  # Total study time across all subjects since the beginning

    for subject in app_data["subjects"]:  # Go through all subjects, including archived ones
        subject_id = subject["id"]  # Get the permanent subject ID

        weekly_seconds = calculate_weekly_logged_seconds(
            app_data,
            subject_id
        )  # Calculate this week's time for the subject

        total_seconds = calculate_total_logged_seconds(
            app_data,
            subject_id
        )  # Calculate all-time study time for the subject

        weekly_grand_total += weekly_seconds  # Add to the combined weekly total
        all_time_grand_total += total_seconds  # Add to the combined all-time total

        if not subject["archived"] or weekly_seconds > 0:
            weekly_lines.append(
                f'{subject["name"]}: {format_hours_minutes(weekly_seconds)}'
            )  # Add the subject to the weekly overview

        if not subject["archived"] or total_seconds > 0:
            archived_text = " (arkivert)" if subject["archived"] else ""

            total_lines.append(
                f'{subject["name"]}{archived_text}: {format_hours_minutes(total_seconds)}'
            )  # Add the subject to the all-time overview

    weekly_lines.append(
        f"\nTotalt: {format_hours_minutes(weekly_grand_total)}"
    )  # Add the combined weekly total

    total_lines.append(
        f"\nTotalt: {format_hours_minutes(all_time_grand_total)}"
    )  # Add the combined all-time total

    weekly_statistics_label.config(
        text="\n".join(weekly_lines)
    )  # Display the weekly statistics

    total_statistics_label.config(
        text="\n".join(total_lines)
    )  # Display the all-time statistics


def refresh_subject_buttons():  # Function to rebuild the subject buttons
    for widget in subject_buttons_frame.winfo_children():  # Go through existing buttons
        widget.destroy()  # Remove each old subject button

    for subject in get_active_subjects(app_data):  # Create a button for every active subject
        if subject["id"] == current_subject_id:
            button_style = "SelectedSubject.TButton"  # Use highlighted style for selected subject
        else:
            button_style = "Subject.TButton"  # Use normal style for other subjects

        button = ttk.Button(
            subject_buttons_frame,
            text=subject["name"],
            command=lambda subject_id=subject["id"]: select_subject(subject_id),
            style=button_style
        )  # Create the subject button

        button.pack(
            side="left",
            padx=4,
            pady=4
        )  # Add the subject button to the subject selector


def select_subject(subject_id):  # Function to switch to another subject
    global current_subject_id  # Access the selected subject ID

    if timer_running or elapsed_seconds > 0:  # Check if a session is currently in progress
        messagebox.showwarning(
            "Økt pågår",
            "Lagre eller kast den nåværende økten før du bytter fag."
        )

        return

    current_subject_id = subject_id  # Select the new subject

    refresh_subject_buttons()  # Update the selected subject button
    update_subject_display()  # Update the subject name and total time


def add_subject():  # Function to add a new subject
    active_subjects = get_active_subjects(app_data)  # Get all active subjects

    if len(active_subjects) >= MAX_ACTIVE_SUBJECTS:  # Check if five subjects already exist
        messagebox.showwarning(
            "Maks antall fag",
            "Du kan ha maksimalt 5 aktive fag."
        )

        return

    subject_name = simpledialog.askstring(
        "Legg til fag",
        "Hva skal faget hete?"
    )  # Ask the user for the new subject name

    if subject_name is None:  # Stop if the user presses Cancel
        return

    subject_name = subject_name.strip()  # Remove unnecessary spaces

    if not subject_name:  # Check if the entered name is empty
        messagebox.showwarning(
            "Ugyldig navn",
            "Faget må ha et navn."
        )

        return

    for subject in active_subjects:  # Check all active subjects
        if subject["name"].lower() == subject_name.lower():  # Check for duplicate names
            messagebox.showwarning(
                "Faget finnes allerede",
                "Du har allerede et aktivt fag med dette navnet."
            )

            return

    new_subject = {
        "id": uuid4().hex,
        "name": subject_name,
        "archived": False
    }  # Create the new subject

    app_data["subjects"].append(new_subject)  # Add the subject to application data

    save_data(app_data)  # Save the subject permanently

    refresh_subject_buttons()  # Show the new subject
    update_statistics()  # Update statistics


def rename_subject():  # Function to rename the currently selected subject
    if timer_running or elapsed_seconds > 0:  # Check if a session is in progress
        messagebox.showwarning(
            "Økt pågår",
            "Lagre eller kast den nåværende økten før du endrer faget."
        )

        return

    subject = get_current_subject()  # Get the selected subject

    if subject is None:  # Stop if no subject exists
        return

    new_name = simpledialog.askstring(
        "Endre navn",
        "Nytt navn på faget:",
        initialvalue=subject["name"]
    )  # Ask the user for a new name

    if new_name is None:  # Stop if Cancel is pressed
        return

    new_name = new_name.strip()  # Remove unnecessary spaces

    if not new_name:  # Check if the name is empty
        messagebox.showwarning(
            "Ugyldig navn",
            "Faget må ha et navn."
        )

        return

    for other_subject in get_active_subjects(app_data):  # Check all active subjects
        if (
            other_subject["id"] != subject["id"]
            and other_subject["name"].lower() == new_name.lower()
        ):
            messagebox.showwarning(
                "Navnet finnes allerede",
                "Et annet aktivt fag har allerede dette navnet."
            )

            return

    subject["name"] = new_name  # Change the visible subject name

    save_data(app_data)  # Save the new name

    refresh_subject_buttons()  # Update subject buttons
    update_subject_display()  # Update selected subject
    update_statistics()  # Update names in statistics


def archive_subject():  # Function to archive the selected subject
    global current_subject_id  # Access the selected subject ID

    if timer_running or elapsed_seconds > 0:  # Check if a session is in progress
        messagebox.showwarning(
            "Økt pågår",
            "Lagre eller kast den nåværende økten før du fjerner faget."
        )

        return

    active_subjects = get_active_subjects(app_data)  # Get all active subjects

    if len(active_subjects) <= 1:  # Make sure one active subject remains
        messagebox.showwarning(
            "Kan ikke fjerne fag",
            "Du må ha minst ett aktivt fag."
        )

        return

    subject = get_current_subject()  # Get the selected subject

    if subject is None:
        return

    should_archive = messagebox.askyesno(
        "Fjern fag",
        (
            f'Vil du fjerne "{subject["name"]}" fra hovedskjermen?\n\n'
            "Tid du allerede har logget på faget blir ikke slettet."
        )
    )  # Ask for confirmation

    if not should_archive:  # Stop if the user chooses No
        return

    subject["archived"] = True  # Archive instead of deleting the subject

    remaining_subjects = get_active_subjects(app_data)  # Get remaining active subjects

    current_subject_id = remaining_subjects[0]["id"]  # Select the first remaining subject

    save_data(app_data)  # Save the archived state

    refresh_subject_buttons()  # Update subject buttons
    update_subject_display()  # Display the new selected subject
    update_statistics()  # Update statistics


def update_timer():  # Function to update the timer every second
    global elapsed_seconds  # Access elapsed seconds
    global timer_job  # Access the scheduled timer job

    if timer_running:  # Only update while the timer is running
        elapsed_seconds += 1  # Add one second

        timer_label.config(
            text=format_time(elapsed_seconds)
        )  # Update the visible timer

        timer_job = window.after(
            1000,
            update_timer
        )  # Schedule another update after one second


def start_timer():  # Function to start or resume the timer
    global timer_running  # Access timer state
    global timer_job  # Access scheduled timer job

    if not timer_running:  # Make sure the timer is not already running
        timer_running = True  # Start the timer

        start_button.config(state="disabled")  # Disable Start
        stop_button.config(state="normal")  # Enable Stop

        session_label.config(text="")  # Hide paused session text
        decision_frame.pack_forget()  # Hide Save and Discard buttons

        timer_job = window.after(
            1000,
            update_timer
        )  # Schedule the first timer update


def stop_timer():  # Function to pause the timer
    global timer_running  # Access timer state
    global timer_job  # Access scheduled timer job

    timer_running = False  # Pause the timer

    if timer_job is not None:  # Check if an update is scheduled
        window.after_cancel(timer_job)  # Cancel the scheduled update
        timer_job = None  # Clear the scheduled job

    start_button.config(state="normal")  # Allow the user to resume
    stop_button.config(state="disabled")  # Disable Stop

    session_label.config(
        text=f"Økt: {format_time(elapsed_seconds)}"
    )  # Display the paused session time

    decision_frame.pack(pady=10)  # Show Save and Discard buttons


def save_session():  # Function to permanently save the current session
    global elapsed_seconds  # Access current session time

    if elapsed_seconds > 0:  # Only save sessions longer than zero seconds
        new_session = {
            "subject_id": current_subject_id,
            "date": datetime.now().date().isoformat(),
            "duration_seconds": elapsed_seconds
        }  # Create a study session

        app_data["sessions"].append(new_session)  # Add the session to application data

        save_data(app_data)  # Save the session permanently

    reset_session()  # Reset the timer
    update_subject_display()  # Update subject total
    update_statistics()  # Update statistics


def discard_session():  # Function to discard the current session
    reset_session()  # Reset without saving


def reset_session():  # Function to reset the current study session
    global elapsed_seconds  # Access current elapsed seconds

    elapsed_seconds = 0  # Reset session time

    timer_label.config(text="00:00:00")  # Reset timer display
    session_label.config(text="")  # Remove paused session text

    decision_frame.pack_forget()  # Hide Save and Discard buttons

    start_button.config(state="normal")  # Enable Start
    stop_button.config(state="disabled")  # Disable Stop


app_data = load_data()  # Load saved application data

active_subjects = get_active_subjects(app_data)  # Get active subjects

current_subject_id = active_subjects[0]["id"]  # Select the first active subject


window = tk.Tk()  # Create the main application window

window.title("Study Timer")  # Set the application window title
window.geometry("560x500")  # Make the application about the size of a desktop sticky note
window.minsize(520, 470)  # Allow the window to stay compact

configure_styles(window)  # Apply the application's styles to the window and ttk widgets



# -----------------------------
# MAIN CONTAINER
# -----------------------------

main_frame = ttk.Frame(
    window,
    style="App.TFrame",
    padding=12
)  # Create the main container for everything in the application

main_frame.pack(
    fill="both",
    expand=True
)  # Make the main container fill the window


# -----------------------------
# HEADER
# -----------------------------

title_label = ttk.Label(
    main_frame,
    text="Study Timer",
    style="Title.TLabel"
)  # Create the main application title

title_label.pack(
    anchor="w"
)  # Place the title on the left



# -----------------------------
# SUBJECT SELECTOR
# -----------------------------

subjects_title_label = ttk.Label(
    main_frame,
    text="FAG",
    style="Section.TLabel"
)  # Create the subject section heading

subjects_title_label.pack(
    anchor="w"
)


subject_buttons_frame = ttk.Frame(
    main_frame,
    style="App.TFrame"
)  # Create a frame containing subject buttons

subject_buttons_frame.pack(
    anchor="w",
    pady=(4, 14)
)


# -----------------------------
# TIMER CARD
# -----------------------------

timer_card = ttk.Frame(
    main_frame,
    style="Card.TFrame",
    padding=10
)  # Create the main timer card

timer_card.pack(
    fill="x",
    pady=(0, 12)
)


subject_label = ttk.Label(
    timer_card,
    text="",
    style="SubjectName.TLabel"
)  # Create the selected subject title

subject_label.pack()


timer_label = ttk.Label(
    timer_card,
    text="00:00:00",
    style="Timer.TLabel"
)  # Create the large timer display

timer_label.pack(
    pady=(4, 8)
)


timer_buttons_frame = ttk.Frame(
    timer_card,
    style="Card.TFrame"
)  # Create a frame for Start and Stop

timer_buttons_frame.pack()


start_button = ttk.Button(
    timer_buttons_frame,
    text="START",
    command=start_timer,
    style="Primary.TButton"
)  # Create the Start button

start_button.pack(
    side="left",
    padx=5
)


stop_button = ttk.Button(
    timer_buttons_frame,
    text="STOPP",
    command=stop_timer,
    state="disabled",
    style="Secondary.TButton"
)  # Create the Stop button

stop_button.pack(
    side="left",
    padx=5
)


session_label = ttk.Label(
    timer_card,
    text="",
    style="MutedCardText.TLabel"
)  # Create the label that shows the paused session time

session_label.pack(
    pady=(10, 0)
)


decision_frame = ttk.Frame(
    timer_card,
    style="Card.TFrame"
)  # Create a container for Save and Discard buttons


save_button = ttk.Button(
    decision_frame,
    text="LAGRE TID",
    command=save_session,
    style="Primary.TButton"
)  # Create the Save Session button

save_button.pack(
    side="left",
    padx=5
)


discard_button = ttk.Button(
    decision_frame,
    text="KAST TID",
    command=discard_session,
    style="Secondary.TButton"
)  # Create the Discard Session button

discard_button.pack(
    side="left",
    padx=5
)


total_label = ttk.Label(
    timer_card,
    text="",
    style="CardText.TLabel"
)  # Create the selected subject total

total_label.pack(
    pady=(16, 0)
)


# -----------------------------
# SUBJECT MANAGEMENT
# -----------------------------

management_frame = ttk.Frame(
    main_frame,
    style="App.TFrame"
)  # Create a frame for subject management controls

management_frame.pack(
    anchor="w",
    pady=(0, 22)
)


add_subject_button = ttk.Button(
    management_frame,
    text="+ LEGG TIL FAG",
    command=add_subject,
    style="Secondary.TButton"
)  # Create the Add Subject button

add_subject_button.pack(
    side="left",
    padx=(0, 5)
)


rename_subject_button = ttk.Button(
    management_frame,
    text="ENDRE NAVN",
    command=rename_subject,
    style="Secondary.TButton"
)  # Create the Rename Subject button

rename_subject_button.pack(
    side="left",
    padx=5
)


archive_subject_button = ttk.Button(
    management_frame,
    text="FJERN FAG",
    command=archive_subject,
    style="Secondary.TButton"
)  # Create the Archive Subject button

archive_subject_button.pack(
    side="left",
    padx=5
)


# -----------------------------
# STATISTICS
# -----------------------------

statistics_title_label = ttk.Label(
    main_frame,
    text="PROGRESJON",
    style="Section.TLabel"
)  # Create the statistics section heading

statistics_title_label.pack(
    anchor="w",
    pady=(0, 6)
)


statistics_frame = ttk.Frame(
    main_frame,
    style="App.TFrame"
)  # Create the container for both statistics cards

statistics_frame.pack(
    fill="both",
    expand=True
)


statistics_frame.columnconfigure(
    0,
    weight=1
)

statistics_frame.columnconfigure(
    1,
    weight=1
)  # Make both statistics columns use equal space


weekly_frame = ttk.Frame(
    statistics_frame,
    style="Card.TFrame",
    padding=9
)  # Create the weekly statistics card

weekly_frame.grid(
    row=0,
    column=0,
    sticky="nsew",
    padx=(0, 6)
)


weekly_title_label = ttk.Label(
    weekly_frame,
    text="DENNE UKEN",
    style="StatisticsTitle.TLabel"
)

weekly_title_label.pack(
    anchor="w",
    pady=(0, 10)
)


weekly_statistics_label = ttk.Label(
    weekly_frame,
    text="",
    style="Statistics.TLabel",
    justify="left"
)  # Create the weekly statistics text

weekly_statistics_label.pack(
    anchor="w"
)


all_time_frame = ttk.Frame(
    statistics_frame,
    style="Card.TFrame",
    padding=9
)  # Create the all-time statistics card

all_time_frame.grid(
    row=0,
    column=1,
    sticky="nsew",
    padx=(6, 0)
)


total_title_label = ttk.Label(
    all_time_frame,
    text="TOTALT SIDEN START",
    style="StatisticsTitle.TLabel"
)

total_title_label.pack(
    anchor="w",
    pady=(0, 10)
)


total_statistics_label = ttk.Label(
    all_time_frame,
    text="",
    style="Statistics.TLabel",
    justify="left"
)  # Create the all-time statistics text

total_statistics_label.pack(
    anchor="w"
)


# -----------------------------
# INITIAL DISPLAY
# -----------------------------

refresh_subject_buttons()  # Create subject buttons when the application starts
update_subject_display()  # Display the selected subject and its saved total
update_statistics()  # Display weekly and all-time statistics


window.mainloop()  # Start the Tkinter event loop and keep the application running