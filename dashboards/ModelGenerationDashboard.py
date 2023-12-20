import tempfile
from datetime import datetime

import streamlit as st
import plotly.express as px
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
        influential_submission_ids = []
        if st.button("Generate Models", type="primary"):
            self.score_predictor.build_models()

        # self.test_model()
        st.divider()
        self.show_model_performance()

    def show_model_performance(self):
        # Initialize an empty list to store performance data for all models
        all_model_performance_data = []

        for model_type in LearningModels.get_enabled_models():
            model_name = model_type.value['name']
            # Fetch model performance data
            model_performance_data = self.model_performance_repo.get_model_performance(
                model_name)

            if model_performance_data:
                # Append the performance data for this model to the consolidated list
                all_model_performance_data.extend(model_performance_data)

        if not all_model_performance_data:
            st.info("No model performance data available.")
            return

        # Display recent submission summary for all models
        for model_type in LearningModels.get_enabled_models():
            model_name = model_type.value['name']
            model_performance_data = [data for data in all_model_performance_data if data['model_name'] == model_name]

            if model_performance_data:
                st.subheader(f"{model_type.value['description']}")
                list_builder = ListBuilder(column_widths=[20, 20, 20, 20, 20])
                list_builder.build_header(
                    column_names=["Model", "Mean Squared Error", "Mean Absolute Error", "R-squared score", "Time"])

                for model_data in model_performance_data:
                    # Extract the specific fields from model_data
                    time = model_data['timestamp'].strftime('%-I:%M %p | %b %d') \
                        if isinstance(model_data['timestamp'], datetime) else model_data['timestamp']
                    extracted_data = {
                        'model_name': model_data['model_name'],
                        'mse': model_data['mse'],
                        'mae': model_data['mae'],
                        'r2_score': model_data['r2_score'],
                        'time': time
                    }

                    # Pass the extracted data as a dictionary to the build_row method
                    list_builder.build_row(extracted_data)

            st.write("")

        # Display consolidated visualizations using the DataFrame
        df = pd.DataFrame(all_model_performance_data)
        self.display_performance_charts(df)

    @staticmethod
    def display_performance_charts(df):
        # Create a line chart for all three metrics, separated by model name
        fig = px.line(df, x=df.index, y=['mse', 'mae', 'r2_score'], color_discrete_map={
            'mse': 'blue', 'mae': 'green', 'r2_score': 'red'
        }, facet_col='model_name', title='Performance Metrics Comparison')

        # Customize the chart layout
        fig.update_layout(
            xaxis_title='Index',
            yaxis_title='Metric Value',
        )

        # Update the axis labels for clarity if needed
        fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))

        # Indicate optimal values for each metric
        # Assuming optimal MSE and MAE are close to 0, and optimal R2 is 1
        optimal_mse_mae = 0.5
        optimal_r2 = 0.9

        fig.add_hline(y=optimal_mse_mae, line_dash="dot",
                      annotation_text="Optimal MSE/MAE",
                      annotation_position="top left",
                      line_color="blue")

        fig.add_hline(y=optimal_r2, line_dash="dot",
                      annotation_text="Optimal R2",
                      annotation_position="bottom right",
                      line_color="red")

        # Display the chart
        st.plotly_chart(fig, use_container_width=True)

    @staticmethod
    def display_chart(df, metric, title):
        import plotly.express as px
        fig = px.line(df, x=df.index, y=metric, color='model_name', title=title)
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
            for model_type in LearningModels.get_all_models():
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
