import tkinter as tk
from tkinter import ttk  # Import ttk for more modern-looking interface elements
from datetime import date, timedelta  # Import date tools for calculating weeks and days
from math import ceil  # Import ceil to round the chart's scale up to a whole step

from data_manager import (
    calculate_daily_totals_by_subject,
    get_first_session_date,
    get_subject_by_id
)  # Import data functions from our own data_manager module

from styles import (
    CARD_COLOR,
    GRID_COLOR,
    MUTED_TEXT_COLOR,
    OTHER_SUBJECT_COLOR,
    SUBJECT_COLORS,
    TEXT_COLOR,
    configure_statistics_styles
)  # Import colors and styles for the statistics page


DAY_NAMES = ["Mandag", "Tirsdag", "Onsdag", "Torsdag", "Fredag", "Lørdag", "Søndag"]  # Full day names
SHORT_DAY_NAMES = ["ma", "ti", "on", "to", "fr", "lø", "sø"]  # Short day names under the bars
MONTH_NAMES = ["jan", "feb", "mar", "apr", "mai", "jun", "jul", "aug", "sep", "okt", "nov", "des"]  # Short month names

CHART_HEIGHT = 190  # Height of the bar chart in pixels
BAR_MAX_WIDTH = 24  # Bars never get wider than this, so there is air between them
SEGMENT_GAP = 2  # White gap between the subjects stacked in one bar
AXIS_LABEL_WIDTH = 44  # Space on the right side for the hour labels
SCALE_STEPS = [1800, 3600, 7200, 10800, 14400, 21600, 28800]  # Possible distances between helper lines (30 min to 8 hours)

BASELINE_COLOR = "#c3c2b7"  # Slightly darker line at the bottom of the chart
HOVER_COLOR = "#F4F4F4"  # Light background behind the day the mouse is over


def format_duration(seconds):  # Function to format seconds like the phone's screen time ("1 t 20 min")
    hours = seconds // 3600  # Calculate whole hours
    minutes = (seconds % 3600) // 60  # Calculate remaining minutes

    if hours == 0:
        return f"{minutes} min"  # Skip the hours when there are none

    return f"{hours} t {minutes} min"


def format_axis_label(seconds):  # Function to format the hour labels next to the chart
    if seconds == 0:
        return "0"

    if seconds < 3600:
        return f"{seconds // 60} min"

    return f"{seconds // 3600} t"


def format_short_date(day):  # Function to format a date like "14. okt"
    return f"{day.day}. {MONTH_NAMES[day.month - 1]}"


def get_week_start(day):  # Function to find the Monday of the week a date belongs to
    return day - timedelta(days=day.weekday())


class StatisticsPage:  # A class keeps all the widgets and data for the statistics page together in one place
    def __init__(self, parent, app_data, go_back):  # Runs once, when the page is created
        self.app_data = app_data  # The application's subjects and sessions
        self.daily_totals = {}  # Study time per day and subject, calculated in refresh()
        self.week_start = get_week_start(date.today())  # Start by showing the current week
        self.hover_index = None  # Which day of the week the mouse is over (None = none)
        self.slot_width = 0  # Width of each day in the chart, set when the chart is drawn

        configure_statistics_styles()  # Prepare the styles used on this page

        self.frame = ttk.Frame(
            parent,
            style="App.TFrame"
        )  # The container for the whole statistics page

        back_button = ttk.Button(
            self.frame,
            text="← TILBAKE",
            command=go_back,
            style="Secondary.TButton"
        )  # Button that returns to the timer

        back_button.pack(
            anchor="w",
            pady=(4, 14)
        )

        self.build_week_card()  # Create the card with the weekly chart
        self.build_all_time_card()  # Create the card with all-time numbers


    # -----------------------------
    # BUILDING THE PAGE
    # -----------------------------

    def build_week_card(self):  # Function to create the card with the weekly chart
        ttk.Label(
            self.frame,
            text="UKEOVERSIKT",
            style="Section.TLabel"
        ).pack(
            anchor="w",
            pady=(0, 6)
        )

        week_card = ttk.Frame(
            self.frame,
            style="Card.TFrame",
            padding=12
        )  # White card for the weekly overview

        week_card.pack(
            fill="x",
            pady=(0, 14)
        )

        navigation_frame = ttk.Frame(
            week_card,
            style="Card.TFrame"
        )  # Row with arrows to switch between weeks

        navigation_frame.pack(
            fill="x",
            pady=(0, 10)
        )

        self.previous_button = ttk.Button(
            navigation_frame,
            text="‹",
            width=2,
            command=self.show_previous_week,
            style="Navigation.TButton"
        )  # Button to go one week back

        self.previous_button.pack(side="left")

        self.next_button = ttk.Button(
            navigation_frame,
            text="›",
            width=2,
            command=self.show_next_week,
            style="Navigation.TButton"
        )  # Button to go one week forward

        self.next_button.pack(side="right")

        self.period_label = ttk.Label(
            navigation_frame,
            text="",
            style="Period.TLabel",
            anchor="center"
        )  # Shows which week is displayed

        self.period_label.pack(
            side="left",
            fill="x",
            expand=True
        )

        ttk.Label(
            week_card,
            text="Daglig snitt",
            style="MutedCardText.TLabel"
        ).pack(anchor="w")

        self.average_label = ttk.Label(
            week_card,
            text="",
            style="Hero.TLabel"
        )  # The big number: average study time per day

        self.average_label.pack(anchor="w")

        self.week_total_label = ttk.Label(
            week_card,
            text="",
            style="MutedCardText.TLabel"
        )  # Total for the whole week

        self.week_total_label.pack(
            anchor="w",
            pady=(0, 10)
        )

        self.chart_canvas = tk.Canvas(
            week_card,
            height=CHART_HEIGHT,
            background=CARD_COLOR,
            highlightthickness=0,
            borderwidth=0
        )  # Canvas where the bar chart is drawn

        self.chart_canvas.pack(fill="x")

        self.chart_canvas.bind(
            "<Configure>",
            lambda event: self.draw_chart()
        )  # Redraw the chart when the window changes width

        self.chart_canvas.bind(
            "<Motion>",
            self.on_chart_motion
        )  # Show details for the day the mouse is over

        self.chart_canvas.bind(
            "<Leave>",
            lambda event: self.set_hover_index(None)
        )  # Go back to the whole week when the mouse leaves the chart

        self.selection_label = ttk.Label(
            week_card,
            text="",
            style="StatisticsTitle.TLabel"
        )  # Says if the list below shows the whole week or one day

        self.selection_label.pack(
            anchor="w",
            pady=(12, 6)
        )

        self.legend_frame = ttk.Frame(
            week_card,
            style="Card.TFrame"
        )  # List of subjects with color and time (also explains the colors in the chart)

        self.legend_frame.pack(fill="x")

        self.legend_frame.columnconfigure(
            1,
            weight=1
        )  # Let the subject name take the free space, so the times line up on the right

        ttk.Label(
            week_card,
            text="Hold musen over en dag for å se detaljer",
            style="MutedCardText.TLabel"
        ).pack(
            anchor="w",
            pady=(10, 0)
        )


    def build_all_time_card(self):  # Function to create the card with all-time numbers
        ttk.Label(
            self.frame,
            text="SIDEN START",
            style="Section.TLabel"
        ).pack(
            anchor="w",
            pady=(0, 6)
        )

        all_time_card = ttk.Frame(
            self.frame,
            style="Card.TFrame",
            padding=12
        )  # White card for the all-time numbers

        all_time_card.pack(fill="x")

        self.all_time_frame = ttk.Frame(
            all_time_card,
            style="Card.TFrame"
        )  # Container for the rows of numbers

        self.all_time_frame.pack(fill="x")

        self.all_time_frame.columnconfigure(
            0,
            weight=1
        )  # Push the values to the right side


    # -----------------------------
    # UPDATING THE PAGE
    # -----------------------------

    def refresh(self):  # Function to recalculate and redraw everything (called each time the page is opened)
        self.daily_totals = calculate_daily_totals_by_subject(self.app_data)  # Sum up study time per day
        self.week_start = get_week_start(date.today())  # Always start on the current week
        self.hover_index = None

        self.update_week()  # Update the weekly card
        self.update_all_time()  # Update the all-time card


    def show_previous_week(self):  # Function for the ‹ button
        self.week_start -= timedelta(weeks=1)
        self.update_week()


    def show_next_week(self):  # Function for the › button
        self.week_start += timedelta(weeks=1)
        self.update_week()


    def get_week_days(self):  # Function to get the seven dates of the displayed week
        return [
            self.week_start + timedelta(days=day_index)
            for day_index in range(7)
        ]


    def get_day_total(self, day):  # Function to get the total study time for one day
        return sum(self.daily_totals.get(day, {}).values())


    def update_week(self):  # Function to update everything in the weekly card
        today = date.today()
        current_week_start = get_week_start(today)
        first_session_date = get_first_session_date(self.app_data)

        can_go_back = (
            first_session_date is not None
            and self.week_start > get_week_start(first_session_date)
        )  # Only allow going back to the week of the first session

        self.previous_button.config(state="normal" if can_go_back else "disabled")
        self.next_button.config(state="normal" if self.week_start < current_week_start else "disabled")

        week_days = self.get_week_days()

        if self.week_start == current_week_start:
            period_text = "Denne uken"
        elif self.week_start == current_week_start - timedelta(weeks=1):
            period_text = "Forrige uke"
        else:
            period_text = f"{format_short_date(week_days[0])} – {format_short_date(week_days[6])}"

        self.period_label.config(text=period_text)

        week_total = sum(self.get_day_total(day) for day in week_days)  # Total for the whole week

        if self.week_start == current_week_start:
            days_so_far = today.weekday() + 1  # In the current week, only count the days that have started
        else:
            days_so_far = 7

        self.average_seconds = week_total // days_so_far  # Average per day, like on the phone

        self.average_label.config(text=format_duration(self.average_seconds))
        self.week_total_label.config(text=f"Totalt for uken: {format_duration(week_total)}")

        self.draw_chart()  # Draw the bars
        self.update_legend()  # Update the list of subjects


    def set_hover_index(self, day_index):  # Function to show details for one day (or the whole week with None)
        if day_index == self.hover_index:
            return  # Nothing changed

        self.hover_index = day_index

        self.draw_chart()  # Redraw so the hovered day gets a light background
        self.update_legend()  # Show the subjects for the hovered day


    def on_chart_motion(self, event):  # Function that runs when the mouse moves over the chart
        if self.slot_width <= 0:
            return

        day_index = int(event.x // self.slot_width)  # Find the day from the mouse position

        if 0 <= day_index < 7:
            self.set_hover_index(day_index)
        else:
            self.set_hover_index(None)  # The mouse is over the hour labels on the right


    def get_subject_color(self, subject_id):  # Function to find a subject's color (always the same color for the same subject)
        for subject_index, subject in enumerate(self.app_data["subjects"]):
            if subject["id"] == subject_id and subject_index < len(SUBJECT_COLORS):
                return SUBJECT_COLORS[subject_index]

        return OTHER_SUBJECT_COLOR  # Grey if the subject has no color of its own


    def get_subject_order(self, subject_id):  # Function to sort subjects the same way everywhere (the order they were added)
        for subject_index, subject in enumerate(self.app_data["subjects"]):
            if subject["id"] == subject_id:
                return subject_index

        return len(self.app_data["subjects"])  # Unknown subjects go last


    # -----------------------------
    # DRAWING THE CHART
    # -----------------------------

    def draw_chart(self):  # Function to draw the weekly bar chart
        canvas = self.chart_canvas
        canvas.delete("all")  # Remove the old drawing

        width = canvas.winfo_width()

        if width <= 1:
            return  # The canvas is not visible yet; it is drawn again when it gets a size

        top_padding = 8
        bottom_padding = 22  # Room for the day names
        plot_width = width - AXIS_LABEL_WIDTH
        plot_height = CHART_HEIGHT - top_padding - bottom_padding
        baseline_y = top_padding + plot_height

        week_days = self.get_week_days()
        day_totals = [self.get_day_total(day) for day in week_days]

        highest_value = max(
            max(day_totals),
            self.average_seconds,
            3600
        )  # The chart always shows at least one hour

        scale_step = SCALE_STEPS[-1]

        for step in SCALE_STEPS:
            if highest_value / step <= 3:  # Use the smallest step that needs at most 3 helper lines
                scale_step = step
                break

        scale_top = ceil(highest_value / scale_step) * scale_step  # The value at the top of the chart

        def value_to_y(seconds):  # Convert seconds to a position on the canvas
            return baseline_y - seconds / scale_top * plot_height

        average_y = value_to_y(self.average_seconds)

        # Helper lines with hour labels on the right
        for line_value in range(scale_step, scale_top + 1, scale_step):
            line_y = value_to_y(line_value)

            canvas.create_line(
                0, line_y, plot_width, line_y,
                fill=GRID_COLOR,
                width=1
            )

            if self.average_seconds == 0 or abs(line_y - average_y) > 12:  # Skip the label if it would collide with "snitt"
                canvas.create_text(
                    plot_width + 6, line_y,
                    text=format_axis_label(line_value),
                    anchor="w",
                    fill=MUTED_TEXT_COLOR,
                    font=("Helvetica Neue", 9)
                )

        slot_width = plot_width / 7  # Each day gets an equal share of the width
        self.slot_width = slot_width  # Remember it, so we can tell which day the mouse is over
        bar_width = min(BAR_MAX_WIDTH, slot_width * 0.55)
        today = date.today()

        for day_index, day in enumerate(week_days):
            slot_left = day_index * slot_width
            bar_center = slot_left + slot_width / 2

            if day_index == self.hover_index:
                canvas.create_rectangle(
                    slot_left + 2, top_padding, slot_left + slot_width - 2, baseline_y,
                    fill=HOVER_COLOR,
                    outline=""
                )  # Light background behind the hovered day

            self.draw_stacked_bar(
                day,
                bar_center - bar_width / 2,
                bar_center + bar_width / 2,
                value_to_y
            )

            if day == today:
                label_color = TEXT_COLOR
                label_font = ("Helvetica Neue", 10, "bold")  # Highlight today
            else:
                label_color = MUTED_TEXT_COLOR
                label_font = ("Helvetica Neue", 10)

            canvas.create_text(
                bar_center, baseline_y + bottom_padding / 2 + 2,
                text=SHORT_DAY_NAMES[day_index],
                fill=label_color,
                font=label_font
            )

        canvas.create_line(
            0, baseline_y, plot_width, baseline_y,
            fill=BASELINE_COLOR,
            width=1
        )  # The bottom line of the chart

        if self.average_seconds > 0:
            canvas.create_line(
                0, average_y, plot_width, average_y,
                fill=MUTED_TEXT_COLOR,
                width=1
            )  # Line showing the daily average

            canvas.create_text(
                plot_width + 6, average_y,
                text="snitt",
                anchor="w",
                fill=MUTED_TEXT_COLOR,
                font=("Helvetica Neue", 9, "bold")
            )


    def draw_stacked_bar(self, day, left, right, value_to_y):  # Function to draw one day's bar, with one colored piece per subject
        subjects_that_day = self.daily_totals.get(day, {})

        segments = sorted(
            (
                (subject_id, seconds)
                for subject_id, seconds in subjects_that_day.items()
                if seconds > 0
            ),
            key=lambda segment: self.get_subject_order(segment[0])
        )  # Stack the subjects in the same order every day

        running_total = 0

        for segment_index, (subject_id, seconds) in enumerate(segments):
            bottom_y = value_to_y(running_total)
            running_total += seconds
            top_y = value_to_y(running_total)

            if segment_index > 0:
                bottom_y -= SEGMENT_GAP  # Leave a small white gap between subjects

            if bottom_y - top_y < 1:
                top_y = bottom_y - 1  # Make very short sessions at least 1 pixel tall

            is_top_segment = segment_index == len(segments) - 1

            self.draw_bar_segment(
                left, top_y, right, bottom_y,
                self.get_subject_color(subject_id),
                rounded_top=is_top_segment
            )


    def draw_bar_segment(self, left, top, right, bottom, color, rounded_top):  # Function to draw one piece of a bar
        radius = min(4, (right - left) / 2, bottom - top)  # Rounded corners, but never bigger than the piece itself

        if not rounded_top or radius < 1:
            self.chart_canvas.create_rectangle(
                left, top, right, bottom,
                fill=color,
                outline=""
            )
            return

        self.chart_canvas.create_rectangle(
            left, top + radius, right, bottom,
            fill=color,
            outline=""
        )  # The square lower part

        self.chart_canvas.create_rectangle(
            left + radius, top, right - radius, top + radius,
            fill=color,
            outline=""
        )  # The middle of the top edge

        for corner_left in (left, right - 2 * radius):
            self.chart_canvas.create_oval(
                corner_left, top, corner_left + 2 * radius, top + 2 * radius,
                fill=color,
                outline=""
            )  # The two rounded top corners


    # -----------------------------
    # SUBJECT LIST AND ALL-TIME NUMBERS
    # -----------------------------

    def update_legend(self):  # Function to list the subjects for the week (or the hovered day)
        for widget in self.legend_frame.winfo_children():
            widget.destroy()  # Remove the old rows

        week_days = self.get_week_days()

        if self.hover_index is None:
            selected_days = week_days
            self.selection_label.config(text="Hele uken")
        else:
            selected_day = week_days[self.hover_index]
            selected_days = [selected_day]
            self.selection_label.config(
                text=f"{DAY_NAMES[self.hover_index]} {format_short_date(selected_day)}"
            )

        subject_totals = {}  # Total time per subject for the selected days

        for day in selected_days:
            for subject_id, seconds in self.daily_totals.get(day, {}).items():
                subject_totals[subject_id] = subject_totals.get(subject_id, 0) + seconds

        rows = sorted(
            (
                (subject_id, seconds)
                for subject_id, seconds in subject_totals.items()
                if seconds > 0
            ),
            key=lambda row: row[1],
            reverse=True
        )  # Show the subject with the most time first

        if not rows:
            ttk.Label(
                self.legend_frame,
                text="Ingen økter",
                style="MutedCardText.TLabel"
            ).grid(row=0, column=0, columnspan=3, sticky="w")

            return

        for row_index, (subject_id, seconds) in enumerate(rows):
            subject = get_subject_by_id(self.app_data, subject_id)
            subject_name = subject["name"] if subject is not None else "Ukjent fag"

            color_dot = tk.Canvas(
                self.legend_frame,
                width=10,
                height=10,
                background=CARD_COLOR,
                highlightthickness=0
            )  # Small colored square that matches the bar color

            color_dot.create_rectangle(
                0, 0, 10, 10,
                fill=self.get_subject_color(subject_id),
                outline=""
            )

            color_dot.grid(row=row_index, column=0, padx=(0, 8), pady=2)

            ttk.Label(
                self.legend_frame,
                text=subject_name,
                style="CardText.TLabel"
            ).grid(row=row_index, column=1, sticky="w")

            ttk.Label(
                self.legend_frame,
                text=format_duration(seconds),
                style="CardText.TLabel"
            ).grid(row=row_index, column=2, sticky="e")


    def update_all_time(self):  # Function to update the all-time numbers
        for widget in self.all_time_frame.winfo_children():
            widget.destroy()  # Remove the old rows

        studied_days = sorted(
            day
            for day in self.daily_totals
            if self.get_day_total(day) > 0
        )  # All days with at least some study time

        if not studied_days:
            ttk.Label(
                self.all_time_frame,
                text="Ingen økter ennå",
                style="MutedCardText.TLabel"
            ).grid(row=0, column=0, sticky="w")

            return

        all_time_total = sum(self.get_day_total(day) for day in studied_days)

        best_day = max(studied_days, key=self.get_day_total)  # The day with the most study time

        longest_streak = 1  # Longest number of days in a row with studying
        current_run = 1

        for previous_day, day in zip(studied_days, studied_days[1:]):
            if day - previous_day == timedelta(days=1):
                current_run += 1
            else:
                current_run = 1

            longest_streak = max(longest_streak, current_run)

        today = date.today()
        studied_day_set = set(studied_days)

        streak_day = today if today in studied_day_set else today - timedelta(days=1)  # The streak is still alive if you studied yesterday
        current_streak = 0

        while streak_day in studied_day_set:
            current_streak += 1
            streak_day -= timedelta(days=1)

        rows = [
            ("Totalt", format_duration(all_time_total)),
            ("Dager med studier", str(len(studied_days))),
            ("Snitt per studiedag", format_duration(all_time_total // len(studied_days))),
            ("Beste dag", f"{format_short_date(best_day)} {best_day.year} · {format_duration(self.get_day_total(best_day))}"),
            ("Lengste rekke", f"{longest_streak} {'dag' if longest_streak == 1 else 'dager'} på rad"),
            ("Nåværende rekke", f"{current_streak} {'dag' if current_streak == 1 else 'dager'}")
        ]  # Each row is (description, value)

        for row_index, (description, value) in enumerate(rows):
            ttk.Label(
                self.all_time_frame,
                text=description,
                style="MutedCardText.TLabel"
            ).grid(row=row_index, column=0, sticky="w", pady=2)

            ttk.Label(
                self.all_time_frame,
                text=value,
                style="CardText.TLabel"
            ).grid(row=row_index, column=1, sticky="e", pady=2)
