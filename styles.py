from tkinter import ttk  # Import ttk so we can configure the application's visual styles


# -----------------------------
# COLORS
# -----------------------------

BACKGROUND_COLOR = "#F4F5F7"  # Main application background
CARD_COLOR = "#FFFFFF"  # Background used for cards
TEXT_COLOR = "#1F2937"  # Main text color
MUTED_TEXT_COLOR = "#6B7280"  # Secondary text color
ACCENT_COLOR = "#2563EB"  # Main accent color
ACCENT_HOVER_COLOR = "#1D4ED8"  # Darker accent color used when hovering or pressing


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
        font=("Helvetica Neue", 26, "bold")
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
        font=("Helvetica Neue", 40, "bold")
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
        padding=(12, 7)
    )  # Style for subject buttons that are not selected


    style.configure(
        "SelectedSubject.TButton",
        font=("Helvetica Neue", 11, "bold"),
        padding=(12, 7),
        foreground="white",
        background=ACCENT_COLOR
    )  # Style for the currently selected subject


    style.map(
        "SelectedSubject.TButton",
        background=[
            ("active", ACCENT_HOVER_COLOR),
            ("!disabled", ACCENT_COLOR)
        ],
        foreground=[
            ("!disabled", "white")
        ]
    )  # Define how the selected subject button looks in different states


    # -----------------------------
    # ACTION BUTTONS
    # -----------------------------

    style.configure(
        "Primary.TButton",
        font=("Helvetica Neue", 12, "bold"),
        padding=(18, 9),
        foreground="white",
        background=ACCENT_COLOR
    )  # Style for important buttons such as Start and Save


    style.map(
        "Primary.TButton",
        background=[
            ("active", ACCENT_HOVER_COLOR),
            ("!disabled", ACCENT_COLOR)
        ],
        foreground=[
            ("!disabled", "white")
        ]
    )  # Define how primary buttons look in different states


    style.configure(
        "Secondary.TButton",
        font=("Helvetica Neue", 11),
        padding=(12, 7)
    )  # Style for secondary buttons such as Stop and Rename