import datetime
import hashlib
import uuid

import streamlit as st

from components.AudioProcessor import AudioProcessor
from components.BadgeAwarder import BadgeAwarder
from components.ScorePredictor import ScorePredictor
from components.TimeConverter import TimeConverter
from enums.ActivityType import ActivityType
from enums.Badges import UserBadges
from repositories.RagaRepository import RagaRepository
from repositories.RecordingRepository import RecordingRepository
from repositories.ScorePredictionModelRepository import ScorePredictionModelRepository
from repositories.StorageRepository import StorageRepository
from repositories.TrackRepository import TrackRepository
from repositories.UserActivityRepository import UserActivityRepository
from repositories.UserSessionRepository import UserSessionRepository


class RecordingUploader:
    def __init__(self, recording_repo: RecordingRepository,
                 track_repo: TrackRepository,
                 raga_repo: RagaRepository,
                 user_activity_repo: UserActivityRepository,
                 user_session_repo: UserSessionRepository,
                 score_prediction_model_repo: ScorePredictionModelRepository,
                 storage_repo: StorageRepository,
                 badge_awarder: BadgeAwarder,
                 audio_processor: AudioProcessor,
                 model_bucket):
        self.recording_repo = recording_repo
        self.track_repo = track_repo
        self.raga_repo = raga_repo
        self.user_activity_repo = user_activity_repo
        self.user_session_repo = user_session_repo
        self.score_prediction_model_repo = score_prediction_model_repo
        self.storage_repo = storage_repo
        self.badge_awarder = badge_awarder
        self.audio_processor = audio_processor
        self.model_bucket = model_bucket

    def upload(self, session_id, org_id, user_id,
               track, bucket, assignment_id=None, timezone='America/Los_Angeles'):
        track_id = track["id"]
        if assignment_id:
            form_key = f"recording_upload_{track['id'] - assignment_id}"
        else:
            form_key = f"recording_upload_{track['id']}"
        with st.form(form_key, clear_on_submit=True):
            uploaded_student_file = st.file_uploader("Choose an audio file", type=["m4a", "mp3"])
            original_date = st.date_input("Original File Date", value=None)  # Default value is None
            uploaded = st.form_submit_button("Upload", type="primary")

            upload_successful = False
            badge_awarded = False
            recording_id = -1
            recording_audio_path = None
            if uploaded:
                if uploaded_student_file is None:
                    st.error("Please upload a recording..")
                    return False, False, -1, None

                # If the original date is provided, use it to create a datetime object,
                # otherwise use the current date and time.
                if original_date:
                    original_timestamp = datetime.datetime.combine(
                        original_date, datetime.datetime.min.time())
                else:
                    original_timestamp = datetime.datetime.now()

                with st.spinner("Please wait.."):
                    recording_data = uploaded_student_file.getbuffer()
                    file_hash = self.calculate_file_hash(recording_data)

                    # Check for duplicates
                    if self.recording_repo.is_duplicate_recording(user_id, track_id, file_hash):
                        st.error("You have already uploaded this recording.")
                        return "", -1, False, original_timestamp

                    # Upload the recording to storage repo and recording repo
                    recording_audio_path, url, recording_id = self.add_recording(
                        user_id, track_id, recording_data, original_timestamp,
                        file_hash, bucket, assignment_id)

                    st.audio(recording_audio_path, format='audio/mp4')
                    # Success
                    additional_params = {
                        "track_name": track['track_name'],
                        "recording_name": recording_audio_path,
                    }
                    self.user_activity_repo.log_activity(
                        user_id, session_id, ActivityType.UPLOAD_RECORDING, additional_params)
                    self.user_session_repo.update_last_activity_time(session_id)
                    badge_awarded = self.badge_awarder.award_user_badge(
                        org_id, user_id, UserBadges.FIRST_NOTE, original_timestamp)
                    upload_successful = True

        return upload_successful, badge_awarded, recording_id, recording_audio_path

    def add_recording(self, user_id, track_id, recording_data,
                      timestamp, file_hash, bucket, assignment_id):
        recording_audio_path = f"{user_id}-{track_id}-{timestamp.strftime('%Y%m%d%H%M%S')}.m4a"
        blob_name = f'{bucket}/{recording_audio_path}'
        blob_url = self.storage_repo.upload_blob(recording_data, blob_name)
        self.storage_repo.download_blob(blob_url, recording_audio_path)
        duration = self.audio_processor.calculate_audio_duration(recording_audio_path)
        recording_id = self.recording_repo.add_recording(
            user_id, track_id, blob_name, blob_url, timestamp,
            duration, file_hash, "", "", assignment_id)
        return recording_audio_path, blob_url, recording_id

    def analyze_recording(self, track, recording, track_audio_path, recording_audio_path):
        track_name = track['track_name']
        level = track['level']
        offset = track['offset']
        duration = recording['duration']
        distance = recording['distance']
        distance = self.get_audio_distance(track_audio_path, recording_audio_path)

        score = self.calculate_score(track_name, level, offset, duration, distance)
        return distance, score

    def calculate_score(self, track_name, level, offset, duration, distance):
        score_predictor = ScorePredictor(
            self.score_prediction_model_repo, self.track_repo, self.model_bucket)
        # Predict score using both track-specific and generic models
        is_track_model_score_available, track_model_score = score_predictor.predict_score_by_track_model(
            track_name, level, offset, duration, distance)
        is_generic_model_score_available, generic_model_score = score_predictor.predict_score_by_generic_model(
            level, offset, duration, distance)

        # Initialize variables to store total score and count of valid scores
        total_score = 0
        valid_scores_count = 0

        # Add track model score if available
        if is_track_model_score_available:
            total_score += track_model_score
            valid_scores_count += 1

        # Add generic model score if available
        if is_generic_model_score_available:
            total_score += generic_model_score
            valid_scores_count += 1

        # Avoid division by zero and calculate the final score
        if valid_scores_count > 0:
            final_score = total_score / valid_scores_count
            # Ensuring the score is within the range 0 to 10.00
            final_score = max(0.00, min(final_score, 10.00))
            # Formatting the score to have two decimal places
            final_score = round(final_score, 2)
        else:
            # Handle case where no valid scores are available
            final_score = None  # Or some default value based on your application's logic

        return final_score

    @staticmethod
    def calculate_file_hash(recording_data):
        return hashlib.md5(recording_data).hexdigest()

    @staticmethod
    def get_offset(track):
        # TODO: control it via settings
        base = 1.1
        multiplier = base ** (track['level'] - 1)
        return int(round(multiplier * track['offset']))

    def get_audio_distance(self, track_file, student_path):
        return self.audio_processor.compare_audio(track_file, student_path)

    def get_filtered_student_notes(self, student_path):
        student_notes = self.audio_processor.get_notes(student_path)
        return self.audio_processor.filter_consecutive_notes(student_notes)
