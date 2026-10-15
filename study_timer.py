import tkinter as tk
from tkinter import ttk  # Import ttk for more modern-looking interface elements
from datetime import datetime  # Import datetime so we can save the date of each study session
from tkinter import messagebox, simpledialog  # Import popup windows for messages and text input
from uuid import uuid4  # Import uuid4 so every new subject gets a unique ID
from time import monotonic  # Import a reliable clock for measuring elapsed time


from data_manager import (
    calculate_daily_logged_seconds,
    calculate_total_logged_seconds,
    calculate_weekly_logged_seconds,
    clear_active_session,
    get_active_subjects,
    get_subject_by_id,
    load_active_session,
    load_data,
    save_active_session,
    save_data
)  # Import data functions from our own data_manager module

from settings_manager import load_settings, save_settings  # Import functions for saving application preferences
from styles import BACKGROUND_COLOR, configure_styles  # Import the application's visual style configuration
from statistics_page import StatisticsPage  # Import the page with the detailed statistics



MAX_ACTIVE_SUBJECTS = 5  # Maximum number of active subjects allowed

AUTOSAVE_INTERVAL_MS = 30000  # How often the unfinished session is backed up while the timer runs (30 seconds)

WINDOW_WIDTH = 450  # Width of the window in both modes
SCREEN_MARGIN = 120  # Space left free on the screen so the window never gets taller than the screen


elapsed_seconds = 0.0  # Seconds recorded in the current study session (kept as a decimal number so no time is lost when pausing)
timer_running = False  # Variable to track whether the timer is running
timer_job = None  # Variable to remember the scheduled timer update
autosave_job = None  # Variable to remember the scheduled backup of the unfinished session
segment_start_time = None  # Time when the current running part of the session started
current_subject_id = None  # ID of the subject currently selected



def format_time(seconds):  # Function to format seconds into HH:MM:SS
    seconds = int(seconds)  # Ignore fractions of a second in the display

    hours = seconds // 3600  # Calculate whole hours
    minutes = (seconds % 3600) // 60  # Calculate remaining whole minutes
    secs = seconds % 60  # Calculate remaining seconds

    return f"{hours:02}:{minutes:02}:{secs:02}"  # Return formatted timer text


def format_hours_minutes(seconds):  # Function to format seconds for statistics
    hours = seconds // 3600  # Calculate whole hours
    minutes = (seconds % 3600) // 60  # Calculate remaining minutes

    return f"{hours} t {minutes:02} min"  # Return readable hours-and-minutes text


def get_current_elapsed_seconds():  # Function to calculate the complete current session time
    if timer_running and segment_start_time is not None:
        running_seconds = monotonic() - segment_start_time  # Calculate how long the current running segment has lasted

        return int(elapsed_seconds + running_seconds)  # Combine saved session time and current running time

    return int(elapsed_seconds)  # Return accumulated time when the timer is paused


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


def update_statistics():  # Function to update daily, weekly and all-time statistics
    daily_lines = []  # Text lines for today's overview
    weekly_lines = []  # Text lines for the weekly overview
    total_lines = []  # Text lines for the all-time overview

    daily_grand_total = 0  # Total study time across all subjects today
    weekly_grand_total = 0  # Total study time across all subjects this week
    all_time_grand_total = 0  # Total study time across all subjects since the beginning

    for subject in app_data["subjects"]:  # Go through all subjects, including archived ones
        subject_id = subject["id"]  # Get the permanent subject ID

        daily_seconds = calculate_daily_logged_seconds(
            app_data,
            subject_id
        )  # Calculate today's time for the subject

        weekly_seconds = calculate_weekly_logged_seconds(
            app_data,
            subject_id
        )  # Calculate this week's time for the subject

        total_seconds = calculate_total_logged_seconds(
            app_data,
            subject_id
        )  # Calculate all-time study time for the subject

        daily_grand_total += daily_seconds  # Add to the combined daily total
        weekly_grand_total += weekly_seconds  # Add to the combined weekly total
        all_time_grand_total += total_seconds  # Add to the combined all-time total

        if daily_seconds > 0:  # Only show subjects that have been studied today
            daily_lines.append(
                f'{subject["name"]}: {format_hours_minutes(daily_seconds)}'
            )  # Add the subject to today's overview

        if not subject["archived"] or weekly_seconds > 0:
            weekly_lines.append(
                f'{subject["name"]}: {format_hours_minutes(weekly_seconds)}'
            )  # Add the subject to the weekly overview

        if not subject["archived"] or total_seconds > 0:
            archived_text = " (arkivert)" if subject["archived"] else ""

            total_lines.append(
                f'{subject["name"]}{archived_text}: {format_hours_minutes(total_seconds)}'
            )  # Add the subject to the all-time overview

    if daily_lines:
        daily_lines.append(
            f"\nTotalt: {format_hours_minutes(daily_grand_total)}"
        )  # Add the combined daily total
    else:
        daily_lines.append("Ingen økter ennå i dag")  # Show a friendly message before the first session of the day

    weekly_lines.append(
        f"\nTotalt: {format_hours_minutes(weekly_grand_total)}"
    )  # Add the combined weekly total

    total_lines.append(
        f"\nTotalt: {format_hours_minutes(all_time_grand_total)}"
    )  # Add the combined all-time total

    daily_statistics_label.config(
        text="\n".join(daily_lines)
    )  # Display today's statistics

    today_label.config(
        text=f"I dag: {format_hours_minutes(daily_grand_total)}"
    )  # Display today's total in the timer card, so it is visible in compact mode too

    weekly_statistics_label.config(
        text="\n".join(weekly_lines)
    )  # Display the weekly statistics

    total_statistics_label.config(
        text="\n".join(total_lines)
    )  # Display the all-time statistics


def refresh_subject_buttons():  # Function to rebuild the subject buttons
    for widget in subject_buttons_frame.winfo_children():
        widget.destroy()  # Remove old subject buttons

    active_subjects = get_active_subjects(app_data)  # Get all active subjects

    for column_index in range(len(active_subjects)):
        subject_buttons_frame.columnconfigure(
            column_index,
            weight=1
        )  # Make every possible subject column use equal space

    for column_index, subject in enumerate(active_subjects):
        if subject["id"] == current_subject_id:
            button_style = "SelectedSubject.TButton"
        else:
            button_style = "Subject.TButton"

        button = ttk.Button(
            subject_buttons_frame,
            text=subject["name"],
            command=lambda subject_id=subject["id"]: select_subject(subject_id),
            style=button_style
        )  # Create the subject button

        button.grid(
            row=0,
            column=column_index,
            sticky="ew",
            padx=4,
            pady=4
        )  # Give each subject button an equal-width column


def select_subject(subject_id):  # Function to switch to another subject
    global current_subject_id  # Access the selected subject ID

    if timer_running or elapsed_seconds > 0:  # Check if a session is currently in progress
        messagebox.showwarning(
            "Økt pågår",
            "Lagre eller kast den nåværende økten før du bytter fag."
        )

        return

    current_subject_id = subject_id  # Select the new subject
    
    app_settings["selected_subject_id"] = current_subject_id  # Remember the newly selected subject
    save_settings(app_settings)  # Save the selected subject permanently

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


def update_timer():  # Function to refresh the visible timer
    global timer_job  # Access the scheduled timer job

    if timer_running:
        current_seconds = get_current_elapsed_seconds()  # Calculate the real elapsed session time

        timer_label.config(
            text=format_time(current_seconds)
        )  # Display the current session time

        timer_job = window.after(
            250,
            update_timer
        )  # Refresh the display again shortly


def autosave_session():  # Function to back up the unfinished session regularly while the timer runs
    global autosave_job

    save_active_session(
        current_subject_id,
        get_current_elapsed_seconds()
    )  # Save how far the session has come, in case the app crashes

    if timer_running:
        autosave_job = window.after(
            AUTOSAVE_INTERVAL_MS,
            autosave_session
        )  # Schedule the next backup


def start_timer():  # Function to start or resume the timer
    global timer_running  # Access timer state
    global timer_job  # Access scheduled timer job
    global segment_start_time # Access the start time of the current running segment    

    if not timer_running:  # Make sure the timer is not already running
        segment_start_time = monotonic()  # Remember exactly when this running segment started
        timer_running = True  # Start the timer

        start_button.config(state="disabled")  # Disable Start
        stop_button.config(state="normal")  # Enable Stop

        session_label.config(text="")  # Hide paused session text
        decision_frame.pack_forget()  # Hide Save and Discard buttons

        update_timer()  # Update the display right away and keep updating it
        autosave_session()  # Start backing up the session regularly


def stop_timer():  # Function to pause the timer
    global elapsed_seconds # Access the accumulated session time
    global timer_running # Access timer state
    global timer_job # Access scheduled timer job
    global autosave_job # Access scheduled backup job
    global segment_start_time # Access the start time of the current running segment

    if timer_running and segment_start_time is not None:
        elapsed_seconds += monotonic() - segment_start_time  # Add the current running segment to the accumulated session time

    timer_running = False  # Pause the timer
    segment_start_time = None  # Clear the start time because the timer is no longer running

    if timer_job is not None:  # Check if an update is scheduled
        window.after_cancel(timer_job)  # Cancel the scheduled update
        timer_job = None  # Clear the scheduled job

    if autosave_job is not None:  # Check if a backup is scheduled
        window.after_cancel(autosave_job)  # Cancel the scheduled backup
        autosave_job = None  # Clear the scheduled backup

    save_active_session(
        current_subject_id,
        elapsed_seconds
    )  # Back up the paused session, since it is not saved yet

    start_button.config(state="normal")  # Allow the user to resume
    stop_button.config(state="disabled")  # Disable Stop

    session_label.config(
        text=f"Økt: {format_time(elapsed_seconds)}"
    )  # Display the paused session time

    decision_frame.pack(pady=10)  # Show Save and Discard buttons


def save_session():  # Function to permanently save the current session
    global elapsed_seconds  # Access current session time

    if int(elapsed_seconds) > 0:  # Only save sessions of at least one whole second
        new_session = {
            "subject_id": current_subject_id,
            "date": datetime.now().date().isoformat(),
            "duration_seconds": int(elapsed_seconds)
        }  # Create a study session

        app_data["sessions"].append(new_session)  # Add the session to application data

        save_data(app_data)  # Save the session permanently

    reset_session()  # Reset the timer
    update_subject_display()  # Update subject total
    update_statistics()  # Update statistics


def discard_session():  # Function to discard the current session
    reset_session()  # Reset without saving


def reset_session():  # Function to reset the current study session
    global elapsed_seconds
    global segment_start_time

    elapsed_seconds = 0.0  # Reset accumulated session time
    segment_start_time = None  # Clear any previous timer start time

    clear_active_session()  # The session is saved or discarded, so the backup is no longer needed

    timer_label.config(text="00:00:00")  # Reset timer display
    session_label.config(text="")  # Remove paused session text

    decision_frame.pack_forget()  # Hide Save and Discard buttons

    start_button.config(state="normal")  # Enable Start
    stop_button.config(state="disabled")  # Disable Stop
    

def close_application():  # Function to safely save state and close the application
    if timer_running or elapsed_seconds > 0:  # Check if there is an unsaved study session
        close_choice = messagebox.askyesnocancel(
            "Ulagret økt",
            (
                f"Du har en ulagret økt på {format_time(get_current_elapsed_seconds())}.\n\n"
                "Ja = lagre økten\n"
                "Nei = kast økten\n"
                "Avbryt = gå tilbake til appen"
            )
        )  # Ask what should happen to the unfinished session

        if close_choice is None:
            return  # Cancel the closing process and return to the application

        if timer_running:
            stop_timer()  # Stop the timer before saving or discarding the session

        if close_choice:
            save_session()  # Save the study session if the user chose Yes
        else:
            discard_session()  # Discard the study session if the user chose No

    # Save the current application preferences before closing
    app_settings["selected_subject_id"] = current_subject_id

    app_settings["window_x"] = window.winfo_x()
    app_settings["window_y"] = window.winfo_y()

    app_settings["window_width"] = window.winfo_width()
    app_settings["window_height"] = window.winfo_height()  # Remember the window size, so it opens the same size next time

    save_settings(app_settings)  # Save the application preferences permanently

    window.destroy()  # Close the application window
    

def recover_unfinished_session():  # Function to offer saving a session that was left unfinished after a crash
    unfinished_session = load_active_session()  # Look for a backup from last time

    if unfinished_session is None:  # Stop if there is nothing to recover
        return

    subject = get_subject_by_id(
        app_data,
        unfinished_session.get("subject_id")
    )  # Find the subject the session belonged to

    duration_seconds = unfinished_session.get("duration_seconds", 0)  # Get how long the session lasted

    if subject is not None and duration_seconds > 0:
        should_save = messagebox.askyesno(
            "Uavsluttet økt",
            (
                f'Du har en uavsluttet økt på {format_time(duration_seconds)} '
                f'i {subject["name"]}.\n\n'
                "Vil du lagre den?"
            )
        )  # Ask whether the unfinished session should be kept

        if should_save:
            app_data["sessions"].append(
                {
                    "subject_id": subject["id"],
                    "date": unfinished_session["date"],
                    "duration_seconds": duration_seconds
                }
            )  # Add the recovered session using the day it actually happened

            save_data(app_data)  # Save the recovered session permanently

            update_subject_display()  # Update subject total
            update_statistics()  # Update statistics

    clear_active_session()  # Remove the backup so the question is not asked again


def fit_window_to_content():  # Function to make the window exactly as tall as its content
    window.update_idletasks()  # Let Tkinter calculate the size of all widgets first

    content_height = main_frame.winfo_reqheight()  # Height needed to show everything

    max_height = window.winfo_screenheight() - SCREEN_MARGIN  # Never make the window taller than the screen

    window.geometry(
        f"{WINDOW_WIDTH}x{min(content_height, max_height)}"
    )  # Resize the window; if the content doesn't fit, the user can scroll


def update_scroll_area(event=None):  # Function to update what can be scrolled when the content or window changes size
    content_height = main_frame.winfo_reqheight()  # Height of everything in the application

    scroll_canvas.configure(
        scrollregion=(0, 0, scroll_canvas.winfo_width(), content_height)
    )  # Tell the canvas how much content there is to scroll through

    if content_height <= scroll_canvas.winfo_height():
        scroll_canvas.yview_moveto(0)  # Go back to the top when everything fits


def resize_content_width(event):  # Function to make the content as wide as the window
    scroll_canvas.itemconfigure(
        content_window,
        width=event.width
    )  # Stretch the content to the full width of the canvas

    update_scroll_area()  # The visible area changed, so check if scrolling is needed


def scroll_with_mouse_wheel(event):  # Function to scroll with the mouse wheel or trackpad
    if main_frame.winfo_reqheight() <= scroll_canvas.winfo_height():
        return  # Do nothing if everything already fits

    if event.num == 4 or event.delta > 0:
        direction = -1  # Scroll up
    elif event.num == 5 or event.delta < 0:
        direction = 1  # Scroll down
    else:
        return

    scroll_canvas.yview_scroll(
        direction,
        "units"
    )  # Move the content a small step


def show_statistics_page():  # Function to open the statistics page
    main_page_frame.pack_forget()  # Hide the timer page

    statistics_page.refresh()  # Recalculate the statistics with the newest data

    statistics_page.frame.pack(
        fill="both",
        expand=True
    )  # Show the statistics page

    scroll_canvas.yview_moveto(0)  # Start at the top of the page


def show_main_page():  # Function to go back to the timer page
    statistics_page.frame.pack_forget()  # Hide the statistics page

    main_page_frame.pack(
        fill="both",
        expand=True
    )  # Show the timer page

    scroll_canvas.yview_moveto(0)  # Start at the top of the page


app_data = load_data()  # Load saved application data

app_settings = load_settings()  # Load saved application preferences

active_subjects = get_active_subjects(app_data)  # Get active subjects

saved_subject_id = app_settings["selected_subject_id"]  # Get the subject that was selected when the app was last closed

active_subject_ids = [
    subject["id"] for subject in active_subjects
]  # Create a list containing the IDs of all active subjects


if saved_subject_id in active_subject_ids:
    current_subject_id = saved_subject_id  # Restore the previously selected subject if it is still active
else:
    current_subject_id = active_subjects[0]["id"]  # Otherwise select the first active subject


window = tk.Tk()  # Create the main application window

window.title("Study Timer")  # Set the application window title


window.protocol(
    "WM_DELETE_WINDOW",
    close_application
)  # Run close_application when the user closes the window


window.minsize(420, 300)  # Allow the compact window to stay small

configure_styles(window)  # Apply the application's styles to the window and ttk widgets



# -----------------------------
# MAIN CONTAINER
# -----------------------------

scroll_canvas = tk.Canvas(
    window,
    background=BACKGROUND_COLOR,
    highlightthickness=0,
    borderwidth=0,
    width=1,
    height=1,
    yscrollincrement=20
)  # Create a canvas, which makes it possible to scroll the content when the window is small (with the trackpad or mouse wheel, without a visible scrollbar)

scroll_canvas.pack(
    side="left",
    fill="both",
    expand=True
)  # Make the canvas fill the window


main_frame = ttk.Frame(
    scroll_canvas,
    style="App.TFrame",
    padding=12
)  # Create the main container for everything in the application

content_window = scroll_canvas.create_window(
    (0, 0),
    window=main_frame,
    anchor="nw"
)  # Place the main container inside the scrollable canvas


main_frame.bind(
    "<Configure>",
    update_scroll_area
)  # Update the scroll area when the content changes size

scroll_canvas.bind(
    "<Configure>",
    resize_content_width
)  # Update the content width when the window changes size

window.bind_all(
    "<MouseWheel>",
    scroll_with_mouse_wheel
)  # Scroll with the mouse wheel or trackpad (Mac and Windows)

window.bind_all(
    "<Button-4>",
    scroll_with_mouse_wheel
)  # Scroll up with the mouse wheel (Linux)

window.bind_all(
    "<Button-5>",
    scroll_with_mouse_wheel
)  # Scroll down with the mouse wheel (Linux)


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


main_page_frame = ttk.Frame(
    main_frame,
    style="App.TFrame"
)  # Container for the timer page (it is hidden while the statistics page is open)

main_page_frame.pack(
    fill="both",
    expand=True
)



# -----------------------------
# SUBJECT SELECTOR
# -----------------------------

subjects_title_label = ttk.Label(
    main_page_frame,
    text="FAG",
    style="Section.TLabel"
)  # Create the subject section heading

subjects_title_label.pack(
    anchor="w"
)


subject_buttons_frame = ttk.Frame(
    main_page_frame,
    style="App.TFrame"
)  # Create a frame containing subject buttons

subject_buttons_frame.pack(
    fill="x",
    pady=(4, 14)
)  # Make the subject button area use the full available width


# -----------------------------
# TIMER CARD
# -----------------------------

timer_card = ttk.Frame(
    main_page_frame,
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
    padx=3
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
    padx=3
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
    padx=3
)


discard_button = ttk.Button(
    decision_frame,
    text="KAST TID",
    command=discard_session,
    style="Secondary.TButton"
)  # Create the Discard Session button

discard_button.pack(
    side="left",
    padx=3
)


total_label = ttk.Label(
    timer_card,
    text="",
    style="CardText.TLabel"
)  # Create the selected subject total

total_label.pack(
    pady=(16, 0)
)


today_label = ttk.Label(
    timer_card,
    text="",
    style="MutedCardText.TLabel"
)  # Create the label showing today's total study time

today_label.pack(
    pady=(2, 0)
)


overview_frame = ttk.Frame(
    main_page_frame,
    style="App.TFrame"
)  # Create one container for subject management and the statistics overview

overview_frame.pack(
    fill="both",
    expand=True
)


# -----------------------------
# SUBJECT MANAGEMENT
# -----------------------------

management_frame = ttk.Frame(
    overview_frame,
    style="App.TFrame"
)  # Create a frame for subject management controls

management_frame.pack(
    fill="x",
    pady=(0, 22)
)

for column_index in range(4):
    management_frame.columnconfigure(
        column_index,
        weight=1,
        uniform="management_buttons"
    )  # Give all four buttons the same width, sharing the full row


add_subject_button = ttk.Button(
    management_frame,
    text="+ LEGG TIL FAG",
    command=add_subject,
    style="Toolbar.TButton"
)  # Create the Add Subject button

add_subject_button.grid(
    row=0,
    column=0,
    sticky="ew",
    padx=(0, 3)
)


rename_subject_button = ttk.Button(
    management_frame,
    text="ENDRE NAVN",
    command=rename_subject,
    style="Toolbar.TButton"
)  # Create the Rename Subject button

rename_subject_button.grid(
    row=0,
    column=1,
    sticky="ew",
    padx=3
)


archive_subject_button = ttk.Button(
    management_frame,
    text="FJERN FAG",
    command=archive_subject,
    style="Toolbar.TButton"
)  # Create the Archive Subject button

archive_subject_button.grid(
    row=0,
    column=2,
    sticky="ew",
    padx=3
)


statistics_button = ttk.Button(
    management_frame,
    text="STATISTIKK",
    command=show_statistics_page,
    style="Toolbar.TButton"
)  # Button that opens the statistics page

statistics_button.grid(
    row=0,
    column=3,
    sticky="ew",
    padx=(3, 0)
)


# -----------------------------
# STATISTICS
# -----------------------------

statistics_title_label = ttk.Label(
    overview_frame,
    text="PROGRESJON",
    style="Section.TLabel"
)  # Create the statistics section heading

statistics_title_label.pack(
    anchor="w",
    pady=(0, 6)
)


statistics_frame = ttk.Frame(
    overview_frame,
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


daily_frame = ttk.Frame(
    statistics_frame,
    style="Card.TFrame",
    padding=9
)  # Create the card for today's statistics

daily_frame.grid(
    row=0,
    column=0,
    columnspan=2,
    sticky="nsew",
    pady=(0, 12)
)  # Let today's card use the full width above the other two cards


daily_title_label = ttk.Label(
    daily_frame,
    text="I DAG",
    style="StatisticsTitle.TLabel"
)

daily_title_label.pack(
    anchor="w",
    pady=(0, 10)
)


daily_statistics_label = ttk.Label(
    daily_frame,
    text="",
    style="Statistics.TLabel",
    justify="left"
)  # Create the text for today's statistics

daily_statistics_label.pack(
    anchor="w"
)


weekly_frame = ttk.Frame(
    statistics_frame,
    style="Card.TFrame",
    padding=9
)  # Create the weekly statistics card

weekly_frame.grid(
    row=1,
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
    row=1,
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
update_statistics()  # Prepare weekly and all-time statistics

statistics_page = StatisticsPage(
    main_frame,
    app_data,
    show_main_page
)  # Create the statistics page (it is shown when the STATISTIKK button is pressed)

fit_window_to_content()  # Make the window just tall enough for its content
    
    
saved_x = app_settings["window_x"]  # Get the previously saved horizontal window position
saved_y = app_settings["window_y"]  # Get the previously saved vertical window position


window_position_is_visible = (
    saved_x is not None
    and saved_y is not None
    and 0 <= saved_x < window.winfo_screenwidth() - 100
    and 0 <= saved_y < window.winfo_screenheight() - 100
)  # Only restore the position if the window would still be on screen (e.g. not after unplugging a second monitor)


if window_position_is_visible:
    window.geometry(
        f"+{saved_x}+{saved_y}"
    )  # Restore the window's previous screen position


saved_width = app_settings["window_width"]  # Get the window width from when the app was last closed
saved_height = app_settings["window_height"]  # Get the window height from when the app was last closed


if saved_width is not None and saved_height is not None:
    restored_width = min(
        saved_width,
        window.winfo_screenwidth()
    )  # Make sure the window is not wider than the screen

    restored_height = min(
        saved_height,
        window.winfo_screenheight() - SCREEN_MARGIN
    )  # Make sure the window is not taller than the screen

    window.geometry(
        f"{restored_width}x{restored_height}"
    )  # Restore the window size from last time (otherwise it fits the content)


window.after(
    100,
    recover_unfinished_session
)  # Check for an unfinished session once the window is visible


window.mainloop()  # Start the Tkinter event loop and keep the application running