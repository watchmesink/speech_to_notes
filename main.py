import os  # Move this import above the usage of os
import sys
import PyQt5.QtWidgets
import PyQt5.QtCore
import pyaudio
import wave
import tempfile
from openai import OpenAI
import dotenv
from datetime import datetime
import subprocess  # Add this import for opening files

dotenv.load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))





class SpeechToTextApp(PyQt5.QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Speech to Text App")
        self.setGeometry(100, 100, 400, 420)  # Increased height for the new button

        layout = PyQt5.QtWidgets.QVBoxLayout()

        self.mic_label = PyQt5.QtWidgets.QLabel("Select Microphone:")
        layout.addWidget(self.mic_label)

        self.mic_selector = PyQt5.QtWidgets.QComboBox()

        # Initialize audio before populating mic selector
        self.audio = pyaudio.PyAudio()
        self.populate_mic_selector()

        self.mic_selector.currentIndexChanged.connect(self.update_selected_mic)
        layout.addWidget(self.mic_selector)

        self.record_button = PyQt5.QtWidgets.QPushButton("Start Recording")
        self.record_button.clicked.connect(self.toggle_recording)
        layout.addWidget(self.record_button)

        self.timer_label = PyQt5.QtWidgets.QLabel("00:00")
        self.timer_label.setAlignment(PyQt5.QtCore.Qt.AlignCenter)
        layout.addWidget(self.timer_label)

        self.recording_indicator = PyQt5.QtWidgets.QLabel()
        self.recording_indicator.setAlignment(PyQt5.QtCore.Qt.AlignCenter)
        layout.addWidget(self.recording_indicator)

        self.transcription_text = PyQt5.QtWidgets.QTextEdit()
        self.transcription_text.setReadOnly(True)
        layout.addWidget(self.transcription_text)

        # Add a new button to open the Markdown file
        self.open_file_button = PyQt5.QtWidgets.QPushButton("Open Transcriptions File")
        self.open_file_button.clicked.connect(self.open_markdown_file)
        layout.addWidget(self.open_file_button)

        container = PyQt5.QtWidgets.QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        self.is_recording = False
        self.frames = []
        self.stream = None
        self.temp_file = None
        self.selected_device_index = self.audio.get_default_input_device_info()['index']

        self.timer = PyQt5.QtCore.QTimer(self)
        self.timer.timeout.connect(self.update_timer)
        self.recording_duration = 0

        # Get and display the default input device
        self.update_mic_label()

    def populate_mic_selector(self):
        for i in range(self.audio.get_device_count()):
            device_info = self.audio.get_device_info_by_index(i)
            if device_info['maxInputChannels'] > 0:  # This is an input device
                self.mic_selector.addItem(device_info['name'], device_info['index'])

    def update_selected_mic(self, index):
        self.selected_device_index = self.mic_selector.itemData(index)
        self.update_mic_label()

    def toggle_recording(self):
        self.is_recording = not self.is_recording
        if self.is_recording:
            self.record_button.setText("Stop Recording")
            self.start_recording()
        else:
            self.record_button.setText("Start Recording")
            self.stop_recording()

    def start_recording(self):
        self.frames = []
        try:
            # Debug print to check selected device index
            print(f"Selected device index: {self.selected_device_index}")
            
            self.stream = self.audio.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=44100,
                input=True,
                input_device_index=self.selected_device_index,
                frames_per_buffer=1024,
                stream_callback=self.audio_callback
            )
            self.stream.start_stream()
            self.recording_duration = 0
            self.timer.start(1000)  # Update every second
            self.update_recording_indicator(True)
        except OSError as e:
            print(f"Failed to start recording: {e}")
            self.update_recording_indicator(False)
            PyQt5.QtWidgets.QMessageBox.critical(self, "Recording Error", f"Failed to start recording: {e}")

    def stop_recording(self):
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
            self.stream = None
            self.save_audio()
            self.transcribe_audio()
        self.timer.stop()
        self.update_recording_indicator(False)

    def audio_callback(self, in_data, frame_count, time_info, status):
        self.frames.append(in_data)
        return (in_data, pyaudio.paContinue)

    def save_audio(self):
        self.temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
        wf = wave.open(self.temp_file.name, 'wb')
        wf.setnchannels(1)
        wf.setsampwidth(self.audio.get_sample_size(pyaudio.paInt16))
        wf.setframerate(44100)
        wf.writeframes(b''.join(self.frames))
        wf.close()
        print(f"Audio saved to {self.temp_file.name}")

    def transcribe_audio(self):
        try:
            with open(self.temp_file.name, "rb") as audio_file:
                transcript = client.audio.transcriptions.create(
                    model="whisper-1", 
                    file=audio_file,
                    timestamp_granularities=["segment"])
            
            transcription_text = transcript.text
            self.transcription_text.setText(transcription_text)
            
            # Save to Markdown file
            self.save_to_markdown(transcription_text)
            
            # Update status message
            print("Transcription saved!")
        except Exception as e:
            error_message = f"Error during transcription: {str(e)}"
            self.transcription_text.setText(error_message)
            print("Failed to transcribe and save")

    def update_timer(self):
        self.recording_duration += 1
        minutes = self.recording_duration // 60
        seconds = self.recording_duration % 60
        self.timer_label.setText(f"{minutes:02d}:{seconds:02d}")

    def update_recording_indicator(self, is_recording):
        if is_recording:
            self.recording_indicator.setText("🔴 Recording")
        else:
            self.recording_indicator.setText("")

    def closeEvent(self, event):
        self.audio.terminate()
        super().closeEvent(event)

    def save_to_markdown(self, transcription_text):
        save_file_path = "/Users/Gleb.Melnikov/Library/Mobile Documents/iCloud~md~obsidian/Documents/Obsidian/Inbox.md"

        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        markdown_content = f"\n- **Transcription {current_time}** {transcription_text}\n\n"

        try:
            with open(save_file_path, "a", encoding="utf-8") as md_file:
                md_file.write(markdown_content)
            print(f"Transcription saved to {save_file_path}")
        except Exception as e:
            print(f"Error saving to Markdown: {str(e)}")
            PyQt5.QtWidgets.QMessageBox.warning(self, "Save Error", f"Failed to save transcription: {str(e)}")

    def update_mic_label(self):
        device_name = self.audio.get_device_info_by_index(self.selected_device_index)['name']
        self.mic_label.setText(f"Selected Microphone: {device_name}")

    def open_markdown_file(self):
        save_file_path = "/Users/Gleb.Melnikov/Library/Mobile Documents/iCloud~md~obsidian/Documents/Obsidian/Inbox.md"
        if os.path.exists(save_file_path):
            if sys.platform == "win32":
                os.startfile(save_file_path)
            elif sys.platform == "darwin":  # macOS
                subprocess.call(["open", save_file_path])
            else:  # linux variants
                subprocess.call(["xdg-open", save_file_path])
        else:
            PyQt5.QtWidgets.QMessageBox.warning(self, "File Not Found", "The transcriptions file could not be found.")

if __name__ == "__main__":
    app = PyQt5.QtWidgets.QApplication(sys.argv)
    window = SpeechToTextApp()
    window.show()
    sys.exit(app.exec_())
