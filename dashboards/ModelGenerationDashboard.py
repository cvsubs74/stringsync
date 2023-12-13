import tempfile

import streamlit as st

from components.ListBuilder import ListBuilder
from components.ScorePredictor import ScorePredictor
from enums.LearningModels import LearningModels
from repositories.ModelPerformanceRepository import ModelPerformanceRepository
from repositories.PortalRepository import PortalRepository
from repositories.RecordingRepository import RecordingRepository
from repositories.ScorePredictionModelRepository import ScorePredictionModelRepository
from repositories.StorageRepository import StorageRepository
from repositories.TrackRepository import TrackRepository

import pandas as pd


class ModelGenerationDashboard:
    def __init__(self, track_repo: TrackRepository,
                 recording_repo: RecordingRepository,
                 portal_repo: PortalRepository,
                 storage_repo: StorageRepository,
                 score_prediction_model_repo: ScorePredictionModelRepository,
                 model_performance_repo: ModelPerformanceRepository,
                 audio_processor,
                 model_bucket):
        self.track_repo = track_repo
        self.storage_repo = storage_repo
        self.recording_repo = recording_repo
        self.portal_repo = portal_repo
        self.score_prediction_model_repo = score_prediction_model_repo
        self.model_performance_repo = model_performance_repo
        self.audio_processor = audio_processor
        self.model_bucket = model_bucket
        self.score_predictor = ScorePredictor(
            self.score_prediction_model_repo, self.track_repo,
            self.model_performance_repo, self.model_bucket)

    def build(self):
        # Button to trigger model generation
        if st.button("Generate Models"):
            self.score_predictor.build_models()
            st.success("Model generation process completed.")

        self.test_model()
        st.divider()
        self.show_model_performance()

    def show_model_performance(self):
        # Fetch model performance data
        model_performance_data = self.model_performance_repo.get_model_performance()

        if not model_performance_data:
            st.info("No model performance data available.")
            return

        st.header("Model Performance Metrics")
        list_builder = ListBuilder(column_widths=[25, 25, 25, 25])
        list_builder.build_header(
            column_names=["Model", "Mean Squared Error", "Mean Absolute Error", "R-squared score"])
        # Display recent submission summary
        for model_data in model_performance_data:
            # Extract the specific fields from model_data
            extracted_data = {
                'model_name': model_data['model_name'],
                'mse': model_data['mse'],
                'mae': model_data['mae'],
                'r2_score': model_data['r2_score']
            }

            # Pass the extracted data as a dictionary to the build_row method
            list_builder.build_row(extracted_data)

        # Display visualizations
        df = pd.DataFrame(model_performance_data)
        self.display_performance_charts(df)

    def display_performance_charts(self, df):
        # Filter data for visualization
        track_model_df = df[df['model_name'].str.contains('model_')]
        generic_model_df = df[df['model_name'] == 'generic_score_predictor']

        # Visualize MSE for track models over time
        st.markdown("#### Mean Squared Error (MSE) Over Time for Track Models")
        self.display_chart(track_model_df, 'mse', 'Mean Squared Error (MSE)')

        # Visualize MAE for track models over time
        st.markdown("#### Mean Absolute Error (MAE) Over Time for Track Models")
        self.display_chart(track_model_df, 'mae', 'Mean Absolute Error (MAE)')

        # Visualize R2 score for generic model over time
        st.markdown("#### R² Score Over Time for Generic Model")
        self.display_chart(generic_model_df, 'r2_score', 'R² Score')

    @staticmethod
    def display_chart(df, metric, title):
        import plotly.express as px
        fig = px.line(df, x='timestamp', y=metric, color='model_name', title=title)
        st.plotly_chart(fig, use_container_width=True)

    def test_model(self):
        tracks = self.track_repo.get_all_tracks()

        if not tracks:
            st.info("No tracks found. Create a track to get started.")
            return
        # Additional functionality (if any)
        track_name_to_track = {track['name']: track for track in tracks}

        # Display multi-select widget for tracks
        selected_track_name = st.selectbox(
            "Select Track for Testing", options=track_name_to_track.keys())
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
            # Predict scores
            model_scores = {}

            # Iterate through LearningModels enum and predict scores for each model
            for model_type in LearningModels:
                model_name = model_type.value['name']
                predicted_score = self.score_predictor.predict_score(
                    selected_track['level'], offset, duration, distance, model_name)

                model_scores[model_name] = predicted_score

            list_builder = ListBuilder(column_widths=[50, 50])
            list_builder.build_header(
                column_names=["Model", "Score"])
            # Display recent submission summary
            for model_name, score in model_scores.items():
                # Create a dictionary with the model name and score
                extracted_data = {
                    'model_name': model_name,
                    'score': score
                }

                # Pass the extracted data as a dictionary to the build_row method
                list_builder.build_row(extracted_data)

    def analyze_recording(self, track, track_audio_path, recording_audio_path):
        offset = self.get_offset(track)
        distance = self.get_audio_distance(track_audio_path, recording_audio_path)
        duration = self.audio_processor.calculate_audio_duration(recording_audio_path)
        return offset, duration, distance

    @staticmethod
    def get_offset(track):
        # TODO: control it via settings
        base = 1.1
        multiplier = base ** (track['level'] - 1)
        return int(round(multiplier * track['offset']))

    def get_audio_distance(self, track_file, student_path):
        return self.audio_processor.compare_audio(track_file, student_path)
