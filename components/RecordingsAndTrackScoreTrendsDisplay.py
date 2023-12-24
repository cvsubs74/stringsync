from datetime import datetime

import streamlit as st

from components.ListBuilder import ListBuilder
from components.TrackScoringTrendsDisplay import TrackScoringTrendsDisplay
from repositories.RecordingRepository import RecordingRepository


class RecordingsAndTrackScoreTrendsDisplay:
    def __init__(self, recording_repo: RecordingRepository):
        self.recording_repo = recording_repo

    def show(self, user_id, track_id, timezone='America/Los_Angeles'):
        recordings = self.recording_repo.get_recordings_by_user_id_and_track_id(
            user_id, track_id, timezone)

        if not recordings:
            return None

        # Create two columns for the layout
        col1, col2 = st.columns(2)

        # Display the table in the first column
        with col1:
            recordings = self.display_remarks_and_score(recordings)

        # Display the graph in the second column
        with col2:
            TrackScoringTrendsDisplay().show(recordings)

    @staticmethod
    def display_remarks_and_score(recordings):
        st.write("**Recordings**")
        column_widths = [50, 25, 25]
        list_builder = ListBuilder(column_widths)
        list_builder.build_header(
            column_names=['Remarks', 'Score', 'Time'])

        # Build rows for the user activities listing
        for recording in recordings:
            local_timestamp = recording['timestamp'].strftime('%-I:%M %p | %b %d') \
                if isinstance(recording['timestamp'], datetime) else recording['timestamp']

            list_builder.build_row(row_data={
                'Remarks': recording['remarks'],
                'Score': recording['score'],
                'Timestamp': local_timestamp
            })

        return recordings
