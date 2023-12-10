import tempfile

import streamlit as st

from components.ScorePredictor import ScorePredictor
from repositories.ScorePredictionModelRepository import ScorePredictionModelRepository
from repositories.StorageRepository import StorageRepository
from repositories.TrackRepository import TrackRepository


class ModelGenerationDashboard:
    def __init__(self, track_repo: TrackRepository,
                 storage_repo: StorageRepository,
                 score_prediction_model_repo: ScorePredictionModelRepository,
                 audio_processor,
                 model_bucket):
        self.track_repo = track_repo
        self.storage_repo = storage_repo
        self.score_prediction_model_repo = score_prediction_model_repo
        self.audio_processor = audio_processor
        self.model_bucket = model_bucket
        self.score_predictor = ScorePredictor(
            self.score_prediction_model_repo, self.track_repo, self.model_bucket)

    def build(self):
        # Fetch all tracks
        tracks = self.track_repo.get_all_tracks()

        if not tracks:
            st.info("No tracks found. Create a track to get started.")
            return

        # Create a dictionary to map track names to their IDs
        track_name_to_id = {track['name']: track['id'] for track in tracks}

        # Add an "--All--" option to the selection list
        track_options = ["--All--"] + list(track_name_to_id.keys())

        # Display multi-select widget for tracks
        selected_track_names = st.multiselect(
            "Select Tracks for Model Generation", options=track_options)

        # Button to trigger model generation
        if st.button("Generate Models"):
            # Handle selection of all tracks
            if "--All--" in selected_track_names:
                self.score_predictor.build_models()
            else:
                # Convert selected track names to track IDs
                selected_track_ids = [track_name_to_id[name] for name in selected_track_names if
                                      name in track_name_to_id]
                # Validate selection
                if not selected_track_ids:
                    st.warning("Please select at least one track.")
                    return
                # Fetch the training dataset for the selected tracks
                training_dataset = self.score_prediction_model_repo.get_training_set(
                    selected_track_ids)
                # Check if there is sufficient data
                if not training_dataset:
                    st.info("Insufficient data for training the models.")
                    return

                # Build models for the selected tracks
                self.score_predictor.build_track_models(training_dataset)

            st.success("Model generation process completed.")

        # Additional functionality (if any)
        self.test_model(tracks)

    def test_model(self, tracks):
        track_name_to_track = {track['name']: track for track in tracks}

        # Display multi-select widget for tracks
        selected_track_name = st.selectbox(
            "Select Tracks for Model Generation", options=track_name_to_track.keys())
        selected_track = track_name_to_track[selected_track_name]

        track_audio = self.storage_repo.download_blob_by_url(selected_track['track_path'])
        with tempfile.NamedTemporaryFile(mode="wb", delete=False) as temp_file:
            temp_file.write(track_audio)
            track_audio_path = temp_file.name

        uploaded_student_file = st.file_uploader("Choose an audio file", type=["m4a", "mp3"])
        if uploaded_student_file:
            recording_data = uploaded_student_file.getbuffer()
            with tempfile.NamedTemporaryFile(mode="wb", delete=False) as temp_file:
                temp_file.write(recording_data)
                recording_path = temp_file.name
            st.audio(recording_path, format='audio/mp4')
            offset, duration, distance = self.analyze_recording(
                selected_track, track_audio_path, recording_path)
            # Predict score using track model
            track_score, generic_score = self.score_predictor.predict_scores(
                selected_track['name'], selected_track['level'], offset, duration, distance)
            st.write(f"Track model score: {track_score}, Generic model score: {generic_score}")

    def analyze_recording(self, track, track_audio_path, recording_audio_path):
        offset = self.get_offset(track)
        distance = self.get_audio_distance(track_audio_path, recording_audio_path)
        duration = self.audio_processor.calculate_audio_duration(recording_audio_path)
        return offset, duration, distance

    @staticmethod
    def get_offset(track):
        # TODO: control it via settings
        base = 1.1
        multiplier = base ** (track['level']-1)
        return int(round(multiplier * track['offset']))

    def get_audio_distance(self, track_file, student_path):
        return self.audio_processor.compare_audio(track_file, student_path)