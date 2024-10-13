# Speech to Text App

## Overview

This Speech to Text App is a desktop application that allows users to record audio and transcribe it using OpenAI's Whisper API. The app is built with Python and PyQt5, providing a user-friendly interface for audio recording and transcription.

## Features

- Select input device (microphone) from available options
- Record audio with a start/stop button
- Display recording duration
- Transcribe audio using OpenAI's Whisper API
- Save transcriptions to a Markdown file
- Open the saved transcriptions file directly from the app

## Requirements

- Python 3.7 or higher
- PyQt5
- PyAudio
- OpenAI Python library
- dotenv

## Setup

1. Clone this repository or download the source code.

2. Install the required dependencies:   ```
   pip install PyQt5 pyaudio openai python-dotenv   ```

3. Create a `.env` file in the root directory of the project and add your OpenAI API key:   ```
   OPENAI_API_KEY=your_api_key_here   ```

4. Modify the `save_file_path` in the `save_to_markdown` and `open_markdown_file` methods to point to your desired Markdown file location.

## Running the Application

To run the application from source:
