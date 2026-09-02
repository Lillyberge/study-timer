from tkinter import ttk  # Import ttk so we can configure the application's visual styles


# -----------------------------
# COLORS
# -----------------------------

BACKGROUND_COLOR = "#BFE4FF"  # Light blue application background
CARD_COLOR = "#FFFFFF"  # White background used for cards

TEXT_COLOR = "#243447"  # Main dark text color
MUTED_TEXT_COLOR = "#6B7C93"  # Softer text color for secondary information

BUTTON_COLOR = "#F7C6D9"  # Light pink default button color
BUTTON_HOVER_COLOR = "#E88FAF"  # Darker pink when hovering over a button
BUTTON_PRESSED_COLOR = "#C94F70"  # Dark pink/red when pressing a button


def configure_styles(window):  # Function to configure all visual styles used by the application
    window.configure(
        bg=BACKGROUND_COLOR
    )  # Set the background color of the main window

    style = ttk.Style()  # Create a ttk Style object used to control widget appearance

    if "clam" in style.theme_names():
        style.theme_use("clam")  # Use a theme that gives us more control over widget colors


    # -----------------------------
    # FRAMES
    # -----------------------------

    style.configure(
        "App.TFrame",
        background=BACKGROUND_COLOR
    )  # Style for frames that use the main application background


    style.configure(
        "Card.TFrame",
        background=CARD_COLOR
    )  # Style for white card sections


    # -----------------------------
    # LABELS
    # -----------------------------

    style.configure(
        "Title.TLabel",
        background=BACKGROUND_COLOR,
        foreground=TEXT_COLOR,
        font=("Helvetica Neue", 21, "bold")
    )  # Style for the main application title


    style.configure(
        "Subtitle.TLabel",
        background=BACKGROUND_COLOR,
        foreground=MUTED_TEXT_COLOR,
        font=("Helvetica Neue", 12)
    )  # Style for secondary text below the main title


    style.configure(
        "Section.TLabel",
        background=BACKGROUND_COLOR,
        foreground=MUTED_TEXT_COLOR,
        font=("Helvetica Neue", 11, "bold")
    )  # Style for section headings such as FAG and PROGRESJON


    style.configure(
        "SubjectName.TLabel",
        background=CARD_COLOR,
        foreground=TEXT_COLOR,
        font=("Helvetica Neue", 18, "bold")
    )  # Style for subject names and statistics card titles


    style.configure(
        "Timer.TLabel",
        background=CARD_COLOR,
        foreground=TEXT_COLOR,
        font=("Helvetica Neue", 32, "bold")
    )  # Style for the large timer display


    style.configure(
        "CardText.TLabel",
        background=CARD_COLOR,
        foreground=TEXT_COLOR,
        font=("Helvetica Neue", 12)
    )  # Style for normal text inside cards


    style.configure(
        "MutedCardText.TLabel",
        background=CARD_COLOR,
        foreground=MUTED_TEXT_COLOR,
        font=("Helvetica Neue", 11)
    )  # Style for secondary text inside cards


    # -----------------------------
    # SUBJECT BUTTONS
    # -----------------------------

    
    style.configure(
        "Subject.TButton",
        font=("Helvetica Neue", 11),
        padding=(9, 5),
        foreground=TEXT_COLOR,
        background=BUTTON_COLOR
    )  # Style for normal subject buttons


    style.map(
        "Subject.TButton",
        background=[
            ("pressed", BUTTON_PRESSED_COLOR),
            ("active", BUTTON_HOVER_COLOR),
            ("!disabled", BUTTON_COLOR)
        ],
        foreground=[
            ("pressed", "white"),
            ("!disabled", TEXT_COLOR)
        ]
    )  # Change the subject button color when hovering or pressing


    style.configure(
        "SelectedSubject.TButton",
        font=("Helvetica Neue", 11, "bold"),
        padding=(9, 5),
        foreground="white",
        background=BUTTON_PRESSED_COLOR
    )  # Use a darker pink for the currently selected subject


    style.map(
        "SelectedSubject.TButton",
        background=[
            ("pressed", BUTTON_PRESSED_COLOR),
            ("active", BUTTON_PRESSED_COLOR),
            ("!disabled", BUTTON_PRESSED_COLOR)
        ],
        foreground=[
            ("!disabled", "white")
        ]
    )  # Keep the selected subject dark pink


    # -----------------------------
    # ACTION BUTTONS
    # -----------------------------

    style.configure(
        "Primary.TButton",
        font=("Helvetica Neue", 12, "bold"),
        padding=(12, 6),
        foreground=TEXT_COLOR,
        background=BUTTON_COLOR
    )  # Style for important action buttons such as Start and Save


    style.map(
        "Primary.TButton",
        background=[
            ("pressed", BUTTON_PRESSED_COLOR),
            ("active", BUTTON_HOVER_COLOR),
            ("!disabled", BUTTON_COLOR)
        ],
        foreground=[
            ("pressed", "white"),
            ("!disabled", TEXT_COLOR)
        ]
    )  # Make primary buttons darker when hovering or pressing


    style.configure(
        "Secondary.TButton",
        font=("Helvetica Neue", 11),
        padding=(9, 5),
        foreground=TEXT_COLOR,
        background=BUTTON_COLOR
    )  # Style for secondary buttons


    style.map(
        "Secondary.TButton",
        background=[
            ("pressed", BUTTON_PRESSED_COLOR),
            ("active", BUTTON_HOVER_COLOR),
            ("!disabled", BUTTON_COLOR)
        ],
        foreground=[
            ("pressed", "white"),
            ("!disabled", TEXT_COLOR)
        ]
    )  # Make secondary buttons darker when hovering or pressing
    
    
    style.configure(
        "Statistics.TLabel",
        background=CARD_COLOR,
        foreground=TEXT_COLOR,
        font=("Helvetica Neue", 10)
    )  # Compact text used inside statistics cards
    
    
    style.configure(
        "StatisticsTitle.TLabel",
        background=CARD_COLOR,
        foreground=TEXT_COLOR,
        font=("Helvetica Neue", 12, "bold")
    )  # Compact title for statistics cards