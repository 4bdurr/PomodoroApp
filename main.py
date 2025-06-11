import sys
import os # Ditambahkan untuk resource_path
from PySide6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
                               QLabel, QPushButton, QSizePolicy, QDialog, 
                               QFormLayout, QSpinBox, QDialogButtonBox) # Added QDialog, QFormLayout, QSpinBox, QDialogButtonBox
from PySide6.QtCore import QTimer, Qt, QTime, Signal, QUrl # Added QUrl
from PySide6.QtGui import QFont, QIcon
from PySide6.QtMultimedia import QSoundEffect # Added QSoundEffect

def resource_path(relative_path):
    """ Mendapatkan path absolut ke resource, berfungsi untuk dev dan PyInstaller """
    try:
        # PyInstaller membuat folder temp dan menyimpan path di _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


class SettingsDialog(QDialog):
    def __init__(self, current_durations, current_pomos_before_long_break, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setMinimumWidth(300)

        # Store a copy of the current settings to populate the spinboxes
        self.current_durations = dict(current_durations) 
        self.current_pomos_before_long_break = current_pomos_before_long_break

        main_layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        self.pomodoro_duration_spinbox = QSpinBox()
        self.pomodoro_duration_spinbox.setRange(1, 120)  # Min 1 min, Max 120 mins
        self.pomodoro_duration_spinbox.setValue(self.current_durations.get(PomodoroApp.STATE_POMODORO, 25))
        self.pomodoro_duration_spinbox.setSuffix(" min")
        form_layout.addRow("Pomodoro Duration:", self.pomodoro_duration_spinbox)

        self.short_break_duration_spinbox = QSpinBox()
        self.short_break_duration_spinbox.setRange(1, 60)
        self.short_break_duration_spinbox.setValue(self.current_durations.get(PomodoroApp.STATE_SHORT_BREAK, 5))
        self.short_break_duration_spinbox.setSuffix(" min")
        form_layout.addRow("Short Break Duration:", self.short_break_duration_spinbox)

        self.long_break_duration_spinbox = QSpinBox()
        self.long_break_duration_spinbox.setRange(1, 90)
        self.long_break_duration_spinbox.setValue(self.current_durations.get(PomodoroApp.STATE_LONG_BREAK, 15))
        self.long_break_duration_spinbox.setSuffix(" min")
        form_layout.addRow("Long Break Duration:", self.long_break_duration_spinbox)

        self.pomos_cycle_spinbox = QSpinBox()
        self.pomos_cycle_spinbox.setRange(1, 12)  # Min 1 pomo, Max 12 pomos before long break
        self.pomos_cycle_spinbox.setValue(self.current_pomos_before_long_break)
        form_layout.addRow("Pomodoros before Long Break:", self.pomos_cycle_spinbox)

        main_layout.addLayout(form_layout)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        main_layout.addWidget(button_box)

    def get_settings(self):
        new_durations = {
            PomodoroApp.STATE_POMODORO: self.pomodoro_duration_spinbox.value(),
            PomodoroApp.STATE_SHORT_BREAK: self.short_break_duration_spinbox.value(),
            PomodoroApp.STATE_LONG_BREAK: self.long_break_duration_spinbox.value()
        }
        new_pomos_before_long_break = self.pomos_cycle_spinbox.value()
        return new_durations, new_pomos_before_long_break


class PomodoroApp(QWidget):
    # Constants for Pomodoro states
    STATE_POMODORO = "POMODORO"
    STATE_SHORT_BREAK = "SHORT_BREAK"
    STATE_LONG_BREAK = "LONG_BREAK"

    # Signals
    state_changed = Signal(str)
    timer_updated = Signal(QTime)

    def __init__(self):
        super().__init__()
        self.current_state = self.STATE_POMODORO
        self.pomodoros_completed_cycle = 0
        self.pomodoros_before_long_break = 4 # Default
        self.is_paused = False # Flag to track pause state
        self.waiting_for_sound_to_finish_for_transition = False # Flag for sound-controlled transition

        # Default durations (in minutes)
        self.durations = {
            self.STATE_POMODORO: 25,
            self.STATE_SHORT_BREAK: 5,
            self.STATE_LONG_BREAK: 15
        }
        self.current_time_seconds = self.durations[self.STATE_POMODORO] * 60

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_timer)

        self.init_sound()
        self.init_ui()
        self.load_styles()
        self.update_display_time()
        self.update_state_label()

    def init_sound(self):
        """Initializes the sound effect player."""
        self.notification_sound = QSoundEffect(self)
        sound_file_path = resource_path("assets/notification.wav") # Menggunakan resource_path
        try:
            self.notification_sound.setSource(QUrl.fromLocalFile(sound_file_path))
            self.notification_sound.setVolume(0.75)
            # Connect signal for when sound playing state changes
            self.notification_sound.playingChanged.connect(self.handle_sound_state_changed)
            if self.notification_sound.status() == QSoundEffect.Error:
                print(f"Error loading sound: {self.notification_sound.errorString()} from {sound_file_path}")
                print("Please ensure the sound file exists and Qt Multimedia backend is available.")
        except Exception as e:
            print(f"Exception initializing sound: {e}")

    def init_ui(self):
        self.setWindowTitle("Pomodoro Timer")
        try:
            app_icon_path = resource_path("assets/my_pomodoro_icon.png") # Menggunakan resource_path
            app_icon = QIcon(app_icon_path)
            if not app_icon.isNull():
                self.setWindowIcon(app_icon)
            else:
                print(f"Warning: Could not load application icon from {app_icon_path}. Is the path correct and file valid?")
        except Exception as e:
            print(f"Error setting application icon: {e}")

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20) # Add some padding

        # State Label
        self.state_label = QLabel(self.current_state)
        self.state_label.setAlignment(Qt.AlignCenter)
        self.state_label.setObjectName("stateLabel") # For QSS styling
        main_layout.addWidget(self.state_label)

        # Timer Display
        self.timer_display = QLabel("25:00")
        self.timer_display.setAlignment(Qt.AlignCenter)
        self.timer_display.setObjectName("timerDisplay") # For QSS styling
        main_layout.addWidget(self.timer_display)

        # Pomodoro Cycle Display
        self.cycle_display_label = QLabel(f"Pomodoros this cycle: {self.pomodoros_completed_cycle}/{self.pomodoros_before_long_break}")
        self.cycle_display_label.setAlignment(Qt.AlignCenter)
        self.cycle_display_label.setObjectName("cycleDisplayLabel")
        main_layout.addWidget(self.cycle_display_label)

        # Controls Layout
        controls_layout = QHBoxLayout()

        self.action_button = QPushButton("Start") # Renamed from start_button
        self.action_button.setObjectName("actionButton") # New object name
        self.action_button.clicked.connect(self.handle_action_button_click) # New handler
        controls_layout.addWidget(self.action_button)

        self.reset_button = QPushButton("Reset")
        self.reset_button.setObjectName("resetButton")
        self.reset_button.clicked.connect(self.reset_timer)
        controls_layout.addWidget(self.reset_button)

        self.skip_button = QPushButton("Skip")
        self.skip_button.setObjectName("skipButton")
        self.skip_button.clicked.connect(self.skip_to_next_state)
        controls_layout.addWidget(self.skip_button)
        
        self.settings_button = QPushButton("Settings")
        self.settings_button.setObjectName("settingsButton")
        self.settings_button.clicked.connect(self.open_settings_dialog)
        controls_layout.addWidget(self.settings_button)


        main_layout.addLayout(controls_layout)

        # Settings Button (placeholder for future)
        # self.settings_button = QPushButton("Settings") # Moved into controls_layout
        # self.settings_button.setObjectName("settingsButton")
        # self.settings_button.clicked.connect(self.open_settings) # To be implemented
        # main_layout.addWidget(self.settings_button, alignment=Qt.AlignCenter)


        self.setLayout(main_layout)
        self.setMinimumSize(400, 250) # Set a minimum size for the window

    def load_styles(self):
        try:
            styles_path = resource_path("styles.qss") # Menggunakan resource_path
            with open(styles_path, "r") as f:
                self.setStyleSheet(f.read())
        except FileNotFoundError:
            print(f"styles.qss not found at {styles_path}. Using default styles.")
        except Exception as e:
            print(f"Error loading styles.qss: {e}")


    def update_timer(self):
        if self.current_time_seconds > 0:
            self.current_time_seconds -= 1
            self.update_display_time()
            self.timer_updated.emit(QTime(0,0,0).addSecs(self.current_time_seconds))
        else:
            self.timer.stop()
            self.is_paused = False
            self.action_button.setText("Start")
            # self.action_button.style().unpolish(self.action_button) # Force re-evaluation of QSS
            # self.action_button.style().polish(self.action_button)
            self.skip_button.setEnabled(True)
            # self.play_notification_sound() will now handle calling transition_to_next_state
            # either via signal or directly if sound fails.
            self.play_notification_sound()
            # self.transition_to_next_state() # REMOVED from here

    def update_display_time(self):
        minutes = self.current_time_seconds // 60
        seconds = self.current_time_seconds % 60
        self.timer_display.setText(f"{minutes:02d}:{seconds:02d}")

    def update_state_label(self):
        display_text = self.current_state.replace("_", " ").title()
        self.state_label.setText(display_text)
        self.state_changed.emit(self.current_state)

    def update_cycle_display(self):
        self.cycle_display_label.setText(f"Pomodoros this cycle: {self.pomodoros_completed_cycle}/{self.pomodoros_before_long_break}")

    def handle_action_button_click(self):
        button_text = self.action_button.text()

        if button_text == "Start":
            self.is_paused = False
            self.timer.start(1000)
            self.action_button.setText("Pause")
            self.skip_button.setEnabled(False)
        elif button_text == "Pause":
            self.timer.stop()
            self.is_paused = True
            self.action_button.setText("Resume")
            self.skip_button.setEnabled(True)
        elif button_text == "Resume":
            self.is_paused = False
            self.timer.start(1000) # QTimer continues from where it was stopped
            self.action_button.setText("Pause")
            self.skip_button.setEnabled(False)
        
        # Force QSS re-evaluation for property selectors like [text="..."]
        # self.action_button.style().unpolish(self.action_button)
        # self.action_button.style().polish(self.action_button)


    # def start_timer(self): # Replaced by handle_action_button_click
    #     if not self.timer.isActive():
    #         self.timer.start(1000) 
    #         self.start_button.setEnabled(False)
    #         self.pause_button.setEnabled(True)
    #         self.skip_button.setEnabled(False)

    # def pause_timer(self): # Replaced by handle_action_button_click
    #     if self.timer.isActive():
    #         self.timer.stop()
    #         self.start_button.setText("Resume")
    #         self.start_button.setEnabled(True)
    #         self.pause_button.setEnabled(False)
    #         self.skip_button.setEnabled(True) 

    def reset_timer(self):
        self.timer.stop()
        self.is_paused = False
        self.current_time_seconds = self.durations[self.current_state] * 60
        self.update_display_time()
        self.action_button.setText("Start")
        # self.action_button.style().unpolish(self.action_button)
        # self.action_button.style().polish(self.action_button)
        self.skip_button.setEnabled(True)
        # Reset pomodoros_completed_cycle for the current session if needed,
        # or only when a full pomodoro was actually completed.
        # For now, just resetting the current timer.

    def skip_to_next_state(self):
        self.timer.stop()
        self.is_paused = False
        # self.action_button.setText("Start") # Handled by transition_to_next_state
        # self.skip_button.setEnabled(True) # Handled by transition_to_next_state
        self.transition_to_next_state(skipped=True)

    def transition_to_next_state(self, skipped=False):
        previous_state = self.current_state

        if self.current_state == self.STATE_POMODORO:
            self.pomodoros_completed_cycle += 1
            self.update_cycle_display()
            if self.pomodoros_completed_cycle >= self.pomodoros_before_long_break:
                self.current_state = self.STATE_LONG_BREAK
                self.pomodoros_completed_cycle = 0 # Reset cycle count
            else:
                self.current_state = self.STATE_SHORT_BREAK
        elif self.current_state == self.STATE_SHORT_BREAK or self.current_state == self.STATE_LONG_BREAK:
            self.current_state = self.STATE_POMODORO

        self.current_time_seconds = self.durations[self.current_state] * 60
        self.update_display_time()
        self.update_state_label()
        self.update_cycle_display()

        self.is_paused = False
        self.action_button.setText("Start")
        self.skip_button.setEnabled(True)
        print(f"Transitioned from {previous_state} to {self.current_state}")

        # Auto-start logic
        if not skipped and self.current_state == self.STATE_POMODORO and \
           (previous_state == self.STATE_SHORT_BREAK or previous_state == self.STATE_LONG_BREAK):
            print("Auto-starting Pomodoro session...")
            self.handle_action_button_click() # Simulate a click on "Start"
        # If a Pomodoro session just ended, it will not auto-start the break.
        # The button is already set to "Start" for the upcoming break session.

    def handle_sound_state_changed(self):
        """Handles the state change of the notification sound."""
        # This method is called when sound starts and stops playing.
        # We are interested when it stops playing AND we were waiting for it.
        if self.waiting_for_sound_to_finish_for_transition and not self.notification_sound.isPlaying():
            print("Notification sound finished playing. Transitioning to next state.")
            self.waiting_for_sound_to_finish_for_transition = False # Reset the flag
            self.transition_to_next_state()

    def play_notification_sound(self):
        if self.notification_sound and self.notification_sound.isLoaded():
            print("Timer finished! Playing notification sound...")
            self.waiting_for_sound_to_finish_for_transition = True # Set flag before playing
            self.notification_sound.play()
        else:
            print("Timer finished! (Notification sound not loaded or error occurred)")
            # Fallback jika suara tidak bisa dimainkan via QSoundEffect
            if sys.platform == "win32":
                try:
                    import winsound
                    winsound.MessageBeep(winsound.MB_ICONASTERISK) # Suara sistem sederhana
                except ImportError:
                    print("winsound module not available for fallback sound on Windows.")
            # Since QSoundEffect didn't play, or fallback is synchronous, transition immediately.
            # Reset flag just in case, though it might not have been set if sound wasn't loaded.
            self.waiting_for_sound_to_finish_for_transition = False 
            self.transition_to_next_state()

    def open_settings_dialog(self):
        # Pass a copy of current_durations to avoid direct modification if dialog is cancelled
        dialog = SettingsDialog(dict(self.durations), self.pomodoros_before_long_break, self)
        if dialog.exec():  # exec() is blocking and returns True if accepted (e.g. QDialog.Accepted)
            new_durations, new_pomos_before_long_break = dialog.get_settings()

            self.durations = new_durations
            self.pomodoros_before_long_break = new_pomos_before_long_break

            self.update_cycle_display() # Update the "X/Y" display immediately

            # If the timer is not active (i.e., it's showing "Start" or has just finished a session
            # and is waiting for the user to start the next one), then update the
            # current_time_seconds to reflect the new duration for the current_state.
            if not self.timer.isActive() and not self.is_paused:
                self.current_time_seconds = self.durations[self.current_state] * 60
                self.update_display_time()
            
            print(f"Settings updated. Durations: {self.durations}, Pomodoros before long break: {self.pomodoros_before_long_break}")
            print("New durations will apply to subsequent sessions. Current session, if active, will continue with its original duration unless reset.")

    # def open_settings(self): # Replaced by open_settings_dialog
    #     # Placeholder for settings dialog
    #     # dialog = SettingsDialog(self.durations, self.pomodoros_before_long_break, self)
    #     # if dialog.exec():
    #     #     self.durations, self.pomodoros_before_long_break = dialog.get_settings()
    #     #     # Update current timer if it's not running or reset it
    #     #     if not self.timer.isActive():
    #     #         self.current_time_seconds = self.durations[self.current_state] * 60
    #     #         self.update_display_time()
    #     #     self.update_cycle_display()
    #     print("Settings dialog to be implemented.")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PomodoroApp()
    window.show()
    sys.exit(app.exec())
