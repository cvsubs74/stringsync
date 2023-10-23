import datetime
from abc import ABC

import pandas as pd
import hashlib
import librosa
import streamlit as st
import os
import matplotlib.pyplot as plt
import numpy as np

from notations.NotationBuilder import NotationBuilder
from portals.BasePortal import BasePortal
from repositories.RecordingRepository import RecordingRepository
from repositories.StorageRepository import StorageRepository
from repositories.TrackRepository import TrackRepository
from core.AudioProcessor import AudioProcessor


class StudentPortal(BasePortal, ABC):
    def __init__(self):
        super().__init__()
        self.track_repo = TrackRepository()
        self.recording_repo = RecordingRepository()
        self.storage_repo = StorageRepository("stringsync")
        self.audio_processor = AudioProcessor()

    def get_tab_dict(self):
        return {
            "🎵 Tracks": self.display_tracks,
            "🎤 Record": self.record,
            "📝 Assignments": self.assignments,
            "📊 Progress Dashboard": self.display_progress_dashboard  # New tab
        }

    def show_introduction(self):
        st.write("""
            Welcome to the **Student Portal** of String Sync, your personal space for musical growth and exploration. 
            This platform is designed to offer you a comprehensive and interactive music learning experience.

            ### How Does it Work?
            1. **Listen to Tracks**: Explore a wide range of tracks to find the ones that resonate with you.
            2. **Record Performances**: Once you've practiced, record your performances for these tracks.
            3. **Work on Assignments**: Complete assignments given by your teacher and submit them for review.

            ### Why Use String Sync for Learning?
            - **Personalized Learning**: Tailor your learning experience by choosing tracks that suit your taste and skill level.
            - **Instant Feedback**: Receive immediate, data-driven feedback on your performances.
            - **Track Your Progress**: Keep an eye on your improvement over time with easy-to-understand metrics.
            - **Interactive Assignments**: Engage with assignments that challenge you and help you grow as a musician.

            Ready to dive in? Use the sidebar to explore all the exciting features available on your Student Portal!
        """)

    def display_tracks(self):
        tracks = self.get_tracks()
        # Create an empty DataFrame with the desired columns
        df = pd.DataFrame(columns=["Track Name", "Number of Recordings", "Average Score", "Min Score", "Max Score"])

        # Populate the DataFrame
        for track_detail in tracks:
            # Create a DataFrame for this row
            row_df = pd.DataFrame({
                "Track Name": [track_detail['track'][1]],
                "Number of Recordings": [track_detail['num_recordings']],
                "Average Score": [track_detail['avg_score']],
                "Min Score": [track_detail['min_score']],
                "Max Score": [track_detail['max_score']]
            })

            # Append this track's details to the DataFrame
            df = pd.concat([df, row_df], ignore_index=True)

        # Display the table using Streamlit
        st.table(df)

    def record(self):
        track = self.filter_tracks()
        if not track:
            return
        self.create_track_headers()
        offset_distance = self.audio_processor.compare_audio(track[2], track[3])
        col1, col2, col3 = st.columns([5, 5, 5])
        with col1:
            self.display_track_files(track[2])
            notation_builder = NotationBuilder(track, track[4])
            unique_notes = notation_builder.display_notation()
        with col2:
            student_recording, recording_id, is_success = self.handle_file_upload(self.get_user_id(), track[0])
        with col3:
            if is_success:
                score, analysis = self.display_student_performance(track[2], student_recording, unique_notes,
                                                                   offset_distance)
                self.recording_repo.update_score_and_analysis(recording_id, score, analysis)

        self.performances(track[0])

    @staticmethod
    def display_performances_header():
        st.markdown("<h3 style='text-align: center; margin-bottom: 0;'>Performances</h3>", unsafe_allow_html=True)
        st.markdown("<hr style='height:2px; margin-top: 0; border-width:0; background: lightblue;'>",
                    unsafe_allow_html=True)

    def performances(self, track_id):
        self.display_performances_header()
        recordings = self.recording_repo.get_recordings_by_user_id_and_track_id(self.get_user_id(), track_id)

        if not recordings:
            st.write("No recordings found.")
            return

        # Create a DataFrame to hold the recording data
        df = pd.DataFrame(recordings)
        self.build_header(["Track", "Remarks", "Score", "Analysis", "Time"])

        # Loop through each recording and create a table row
        for index, recording in df.iterrows():
            col1, col2, col3, col4, col5 = st.columns([2, 2, 2, 2, 2])
            if recording['blob_url']:
                filename = self.storage_repo.download_blob(recording['blob_name'])
                col1.write("")
                col1.audio(filename, format='core/m4a')
            else:
                col1.write("No core data available.")

            # Use Markdown to make the text black and larger
            col2.write("")
            col2.markdown(
                f"<div style='padding-top:5px;color:black;font-size:14px;'>{recording.get('remarks', 'N/A')}</div>",
                unsafe_allow_html=True)
            col3.write("")
            col3.markdown(
                f"<div style='padding-top:5px;color:black;font-size:14px;'>{recording.get('score')}</div>",
                unsafe_allow_html=True)
            col4.write("")
            col4.markdown(
                f"<div style='padding-top:5px;color:black;font-size:14px;'>{recording.get('analysis', 'N/A')}</div>",
                unsafe_allow_html=True)
            formatted_timestamp = recording['timestamp'].strftime('%I:%M %p, ') + self.ordinal(
                int(recording['timestamp'].strftime('%d'))) + recording['timestamp'].strftime(' %b, %Y')
            col5.write("")
            col5.markdown(f"<div style='padding-top:5px;color:black;font-size:14px;'>{formatted_timestamp}</div>",
                          unsafe_allow_html=True)

    def get_audio_data(self, recording):
        if recording['blob_url']:
            filename = self.storage_repo.download_blob(recording['blob_name'])
            return f"<audio controls><source src='{filename}' type='audio/m4a'></audio>"
        return "No core data available."

    def format_timestamp(self, timestamp):
        formatted_timestamp = timestamp.strftime('%I:%M %p, ') + self.ordinal(
            int(timestamp.strftime('%d'))) + timestamp.strftime(' %b, %Y')
        return formatted_timestamp

    def assignments(self):
        pass

    def display_progress_dashboard(self):
        user_id = self.get_user_id()
        time_series_data = self.recording_repo.get_time_series_data(user_id)

        if not time_series_data:
            st.write("No data available.")
            return

        date = [point['date'].timetuple().tm_yday for point in time_series_data]
        total_durations = [max(0, int(point['total_duration'])) / 60 for point in time_series_data if
                           point['total_duration'] is not None]
        total_tracks = [int(point['total_tracks']) for point in time_series_data]
        print(total_tracks)
        assert all(np.isfinite(total_durations)), "total_durations contains non-finite values"
        assert all(np.isfinite(total_tracks)), "total_tracks contains non-finite values"

        df = pd.DataFrame({
            'Day of Year': date,
            'Total Duration': total_durations,
            'Total Tracks': total_tracks
        })

        # Create the first line chart for Total Duration
        fig1, ax1 = plt.subplots(figsize=(4, 2))
        ax1.set_xlabel('Day of Year', fontsize=5)
        ax1.set_ylabel('Total Duration (minutes)', fontsize=5)
        ax1.plot(df['Day of Year'], df['Total Duration'], marker='', linestyle='-', linewidth=0.5, color='blue')
        ax1.set_yticks(np.arange(0, max(25, max(total_durations) + 1), 5))
        ax1.tick_params(axis='both', labelsize=5)
        ax1.set_xlim(1, 365)
        ax1.set_ylim(0, max(25, max(total_durations) + 1))
        ax1.grid(True, linestyle='--', alpha=0.7)

        # Create the second line chart for Total Tracks
        fig2, ax2 = plt.subplots(figsize=(4, 2))
        ax2.set_xlabel('Day of Year', fontsize=5)
        ax2.set_ylabel('Total Tracks', fontsize=5)
        ax2.plot(df['Day of Year'], df['Total Tracks'], marker='', linestyle='-', linewidth=0.5, color='green')
        ax2.set_yticks(np.arange(0, max(25, max(total_tracks) + 1), 5))
        ax2.tick_params(axis='both', labelsize=5)
        ax2.set_xlim(1, 365)
        ax2.set_ylim(0, max(25, max(total_tracks) + 1))
        ax2.grid(True, linestyle='--', alpha=0.7)

        # Display the charts side by side
        col1, col2 = st.columns(2)
        col1.pyplot(fig1)
        col2.pyplot(fig2)

    def get_tracks(self):
        # Fetch all tracks and track statistics for this user
        tracks = self.track_repo.get_all_tracks()
        track_statistics = self.recording_repo.get_track_statistics_by_user(self.get_user_id())

        # Create a dictionary for quick lookup of statistics by track_id
        stats_dict = {stat['track_id']: stat for stat in track_statistics}

        # Build track details list using list comprehension
        track_details = [
            {
                'track': track,
                'num_recordings': stats_dict.get(track[0], {}).get('num_recordings', 0),
                'avg_score': stats_dict.get(track[0], {}).get('avg_score', 0),
                'min_score': stats_dict.get(track[0], {}).get('min_score', 0),
                'max_score': stats_dict.get(track[0], {}).get('max_score', 0)
            }
            for track in tracks
        ]

        return track_details

    def filter_tracks(self):
        filter_options = self.fetch_filter_options()

        # Create four columns
        col1, col2, col3, col4 = st.columns(4)

        # Place a dropdown in each column
        track_type = col1.selectbox("Filter by Track Type", ["All"] + filter_options["Track Type"])
        level = col2.selectbox("Filter by Level", ["All"] + filter_options["Level"])
        ragam = col3.selectbox("Filter by Ragam", ["All"] + filter_options["Ragam"])
        tags = col4.multiselect("Filter by Tags", ["All"] + filter_options["Tags"], default=["All"])

        tracks = self.track_repo.search_tracks(
            ragam=None if ragam == "All" else ragam,
            level=None if level == "All" else level,
            tags=None if tags == ["All"] else tags,
            track_type=None if track_type == "All" else track_type)

        if not tracks:
            return None

        selected_track_name = self.get_selected_track_name(tracks)
        return self.get_selected_track_details(tracks, selected_track_name)

    def fetch_filter_options(self):
        return {
            "Track Type": self.track_repo.get_all_track_types(),
            "Level": self.track_repo.get_all_levels(),
            "Ragam": self.track_repo.get_all_ragams(),
            "Tags": self.track_repo.get_all_tags()
        }

    @staticmethod
    def get_selected_track_name(tracks):
        track_names = [track[1] for track in tracks]
        return st.selectbox("Select a Track", ["Select a Track"] + track_names, index=0)

    @staticmethod
    def get_selected_track_details(tracks, selected_track_name):
        return next((track for track in tracks if track[1] == selected_track_name), None)

    @staticmethod
    def create_track_headers():
        col1, col2, col3 = st.columns([5, 5, 5])
        custom_style = "<style>h2 {font-size: 20px;}</style>"
        divider = "<hr style='height:1px; margin-top: 0; border-width:0; background: lightblue;'>"

        with col1:
            st.markdown(f"{custom_style}<h2>Track</h2>{divider}", unsafe_allow_html=True)
        with col2:
            st.markdown(f"{custom_style}<h2>Upload</h2>{divider}", unsafe_allow_html=True)
        with col3:
            st.markdown(f"{custom_style}<h2>Analysis</h2>{divider}", unsafe_allow_html=True)

    @staticmethod
    def display_track_files(track_file):
        st.write("")
        st.write("")
        st.audio(track_file, format='core/m4a')

    def handle_file_upload(self, user_id, track_id):
        uploaded_student_file = st.file_uploader("", type=["m4a", "wav", "mp3"])
        if uploaded_student_file is None:
            return "", -1, False

        timestamp = datetime.datetime.now()
        student_path = f"{user_id}-{track_id}-{timestamp}.m4a"
        recording_data = uploaded_student_file.getbuffer()
        file_hash = self.calculate_file_hash(recording_data)

        if self.recording_repo.is_duplicate_recording(user_id, track_id, file_hash):
            st.error("You have already uploaded this recording.")
            return student_path, -1, False

        duration = self.calculate_audio_duration(student_path, recording_data)
        url, recording_id = self.add_recording(user_id, track_id, student_path, timestamp, duration,
                                               file_hash)

        st.audio(student_path, format='core/m4a')
        return student_path, recording_id, True

    @staticmethod
    def calculate_file_hash(recording_data):
        return hashlib.md5(recording_data).hexdigest()

    @staticmethod
    def calculate_audio_duration(student_path, recording_data):
        with open(student_path, "wb") as f:
            f.write(recording_data)
        y, sr = librosa.load(student_path)
        return librosa.get_duration(y=y, sr=sr)

    def add_recording(self, user_id, track_id, student_path, timestamp, duration, file_hash):
        url = self.storage_repo.upload_file(student_path, student_path)
        recording_id = self.recording_repo.add_recording(
            user_id, track_id, student_path, url, timestamp, duration, file_hash)
        return url, recording_id

    def display_student_performance(self, track_file, student_path, track_notes, offset_distance):
        if not student_path:
            return -1, ""

        distance = self.get_audio_distance(track_file, student_path, offset_distance)
        track_notes = self.get_filtered_track_notes(track_file, track_notes)
        student_notes = self.get_filtered_student_notes(student_path)
        error_notes, missing_notes = self.audio_processor.error_and_missing_notes(track_notes, student_notes)
        score = self.audio_processor.distance_to_score(distance)
        analysis = self.display_score_and_analysis(score, error_notes, missing_notes)

        os.remove(student_path)
        return score, analysis

    def get_audio_distance(self, track_file, student_path, offset_distance):
        distance = self.audio_processor.compare_audio(track_file, student_path)
        print("Distance: ", distance)
        return distance - offset_distance

    def get_filtered_track_notes(self, track_file, track_notes):
        if len(track_notes) == 0:
            track_notes = self.audio_processor.get_notes(track_file)
            track_notes = self.audio_processor.filter_consecutive_notes(track_notes)
        print("Track notes:", track_notes)
        return track_notes

    def get_filtered_student_notes(self, student_path):
        student_notes = self.audio_processor.get_notes(student_path)
        print("Student notes:", student_notes)
        return self.audio_processor.filter_consecutive_notes(student_notes)

    def display_score_and_analysis(self, score, error_notes, missing_notes):
        self.display_similarity_score(score)
        analysis = self.generate_note_analysis(error_notes, missing_notes)
        st.info(analysis)
        encouragement_message = self.generate_message(score)
        st.info(encouragement_message)
        return analysis + encouragement_message

    @staticmethod
    def display_similarity_score(score):
        message = f"Similarity score: {score}\n"
        if score <= 3:
            st.error(message)
        elif score <= 7:
            st.warning(message)
        else:
            st.success(message)

    def generate_note_analysis(self, error_notes, missing_notes):
        error_dict = self.group_notes_by_first_letter(error_notes)
        missing_dict = self.group_notes_by_first_letter(missing_notes)

        message = "Note analysis:\n"
        if error_dict == missing_dict:
            message += "Your recording had all the notes that the track had.\n"
        else:
            message += self.correlate_notes(error_dict, missing_dict)
        return message

    @staticmethod
    def group_notes_by_first_letter(notes):
        note_dict = {}
        for note in notes:
            first_letter = note[0]
            note_dict.setdefault(first_letter, []).append(note)
        return note_dict

    @staticmethod
    def correlate_notes(error_dict, missing_dict):
        message = ""
        for first_letter, error_note_list in error_dict.items():
            if first_letter in missing_dict:
                for error_note in error_note_list:
                    message += f"Play {missing_dict[first_letter][0]} instead of {error_note}\n"
            else:
                for error_note in error_note_list:
                    message += f"You played the note {error_note}, however that is not present in the track\n"

        for first_letter, missing_note_list in missing_dict.items():
            if first_letter not in error_dict:
                for missing_note in missing_note_list:
                    message += f"You missed playing the note {missing_note}\n"
        return message

    @staticmethod
    def generate_message(score):
        if score <= 3:
            return "Keep trying. You can do better!"
        elif score <= 7:
            return "Good job. You are almost there!"
        elif score <= 9:
            return "Great work. Keep it up!"
        else:
            return "Excellent! You've mastered this track!"

    @staticmethod
    def ordinal(n):
        suffix = ['th', 'st', 'nd', 'rd', 'th'][min(n % 10, 4)]
        if 11 <= (n % 100) <= 13:
            suffix = 'th'
        return str(n) + suffix
