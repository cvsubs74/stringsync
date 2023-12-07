import os
import tempfile
from datetime import datetime

import streamlit as st

from components.ListBuilder import ListBuilder
from components.RecordingUploader import RecordingUploader
from components.TimeConverter import TimeConverter
from dashboards.ResourceDashboard import ResourceDashboard
from repositories.AssignmentRepository import AssignmentRepository
from repositories.RecordingRepository import RecordingRepository
from repositories.ResourceRepository import ResourceRepository
from repositories.StorageRepository import StorageRepository
from repositories.TrackRepository import TrackRepository


class AssignmentDashboard:
    def __init__(self,
                 resource_repo: ResourceRepository,
                 track_repo: TrackRepository,
                 recording_repo: RecordingRepository,
                 assignment_repo: AssignmentRepository,
                 storage_repo: StorageRepository,
                 resource_dashboard: ResourceDashboard,
                 recording_uploader: RecordingUploader):
        self.resource_repo = resource_repo
        self.track_repo = track_repo
        self.recording_repo = recording_repo
        self.assignment_repo = assignment_repo
        self.resource_dashboard = resource_dashboard
        self.storage_repo = storage_repo
        self.recording_uploader = recording_uploader

    def build(self, session_id, org_id, user_id, bucket, timezone='America/Los_Angeles'):
        # Retrieve assignments for the specific user
        user_assignments = self.assignment_repo.get_assignments(user_id)
        if not user_assignments:
            st.info("No assignments available.")
            return

        # Create a list of assignment options with title and due date
        assignment_options = [f"{assignment['title']} - Due: {assignment['due_date'].strftime('%Y-%m-%d')}"
                              for assignment in user_assignments]

        # Create a select box for assignments
        selected_assignment_name = st.selectbox("Select an Assignment", options=assignment_options)

        # Find the selected assignment from the list
        selected_assignment = next((assignment for assignment in user_assignments
                                    if f"{assignment['title']} - Due: {assignment['due_date'].strftime('%Y-%m-%d')}"
                                    == selected_assignment_name), None)

        if selected_assignment:
            st.markdown(f"""
                <h3 style='font-weight: bold; font-size: 20px; text-align: left; margin-bottom: 0;'>
                    {selected_assignment['title']} - Due: {selected_assignment['due_date'].strftime('%Y-%m-%d')}
                </h3>
                <hr style="height:2px;border-width:0;color:gray;background-color:gray;margin-top: 0;">
                """, unsafe_allow_html=True)
            st.write(selected_assignment['description'])

            # Display assigned tracks with their own expanders and status updates
            assigned_tracks = self.assignment_repo.get_assigned_tracks(
                selected_assignment['id'], user_id)
            st.subheader("Tracks")
            for track in assigned_tracks:
                with st.expander(f"**Track**: {track['track_name']}"):
                    st.write(f"**Instructions**: {track['description']}")
                    # Assume self.storage_repo has a method to get the audio URL directly
                    st.write("**Track**")
                    audio_data = self.storage_repo.download_blob_by_url(track['track_path'])
                    with tempfile.NamedTemporaryFile(mode="wb", delete=False) as temp_file:
                        temp_file.write(audio_data)
                        recording_path = temp_file.name

                    st.audio(audio_data, format='audio/m4a')
                    st.write("**Recording**")
                    uploaded, badge_awarded, recording_id, recording_name = \
                        self.recording_uploader.upload(
                            session_id, org_id, user_id, track, bucket, selected_assignment['id'])
                    if uploaded:
                        with st.spinner("Please wait..."):
                            distance, score, analysis = self.recording_uploader.analyze_recording(
                                track, recording_path, recording_name)
                            self.recording_repo.update_score_and_analysis(
                                recording_id, distance, score, analysis)
                        st.write(f"**Score**: {score}")
                        # Update assignment status
                        self.assignment_repo.update_assignment_status_by_detail(
                            user_id, track['assignment_detail_id'], "Completed")

                    self._display_status_update(track['assignment_detail_id'], user_id)
                    self._display_remarks_and_score_for_recordings(
                        user_id, track['id'], selected_assignment['id'], timezone)
                    if recording_path:
                        os.remove(recording_path)
                    if recording_name:
                        os.remove(recording_name)
                    st.write("")

            st.divider()
            # Display assigned resources with their own expanders and status updates
            assigned_resources = self.assignment_repo.get_assigned_resources(
                selected_assignment['id'], user_id)
            st.subheader("Videos")
            for resource in assigned_resources:
                with st.expander(f"Resource: {resource['title']} - Details"):
                    st.write(f"Description: {resource['description']}")
                    if resource.get('link'):
                        st.markdown(f"[Watch the video]({resource['link']})")
                    self._display_status_update(resource['assignment_detail_id'], user_id)
            st.write("")

    def build_by_group(self, group_id):
        # Retrieve assignments for the specific user
        user_assignments = self.assignment_repo.get_all_assignments_by_group(group_id)
        if not user_assignments:
            st.info("No assignments available.")
            return

        # Loop through assignments and display them
        for assignment in user_assignments:
            st.markdown(f"""
                <h3 style='font-weight: bold; font-size: 20px; text-align: left; margin-bottom: 0;'>
                    {assignment['title']} - Due: {assignment['due_date'].strftime('%Y-%m-%d')}
                </h3>
                <hr style="height:2px;border-width:0;color:gray;background-color:gray;margin-top: 0;">
                """, unsafe_allow_html=True)
            st.write(assignment['description'])

            # Display assigned tracks with their own expanders and status updates
            assigned_tracks = self.assignment_repo.get_assigned_tracks_by_id(
                assignment['assignment_id'])
            for track in assigned_tracks:
                with st.expander(f"**Track**: {track['name']}"):
                    st.write(f"**Instructions**: {track['description']}")
                    # Add a button to load the audio track
                    if st.button(f"Load Track", key=f"load_group_{track['assignment_detail_id']}"):
                        # Assume self.storage_repo has a method to get the audio URL directly
                        audio_url = self.storage_repo.download_blob_by_url(track['track_path'])
                        st.audio(audio_url, format='audio/m4a')

            # Display assigned resources with their own expanders and status updates
            assigned_resources = self.assignment_repo.get_assigned_resources_by_id(
                assignment['assignment_id'])
            for resource in assigned_resources:
                with st.expander(f"Resource: {resource['title']} - Details"):
                    st.write(f"Description: {resource['description']}")
                    if resource.get('link'):
                        st.markdown(f"[Watch the video]({resource['link']})")
            st.write("")

    def _display_status_update(self, assignment_detail_id, user_id):
        # Fetch current status from the database
        current_status = self.assignment_repo.get_detail_status(assignment_detail_id, user_id)

        # If there is no status yet for this detail, default to 'Not Started'
        current_status = current_status or 'Not Started'

        status_options = ["Not Started", "In Progress", "Completed"]
        new_status = st.selectbox(
            "Status",
            options=status_options,
            index=status_options.index(current_status),
            key=f"status_{assignment_detail_id}"
        )

        if st.button("Update", key=f"update_{assignment_detail_id}", type="primary"):
            self.assignment_repo.update_assignment_status_by_detail(
                user_id, assignment_detail_id, new_status)
            st.success(f"Status updated to {new_status}")

    @staticmethod
    def display_score(score):
        st.write(f"**{score}**")

    def _display_remarks_and_score_for_recordings(
            self, user_id, track_id, assignment_id, timezone='America/Los_Angeles'):
        recordings = self.recording_repo.get_recordings_by_user_id_and_track_id_and_assignment_id(
            user_id, track_id, assignment_id, timezone)
        if not recordings:
            return

        column_widths = [33.33, 33.33, 33.33]
        list_builder = ListBuilder(column_widths)
        list_builder.build_header(
            column_names=['Remarks', 'Score', 'Time'])

        # Build rows for the user activities listing
        for recording in recordings:
            local_timestamp = recording['timestamp'].strftime('%-I:%M %p | %b %d') \
                if isinstance(recording['timestamp'], datetime) else recording['timestamp']

            list_builder.build_row(row_data={
                'Activity Type': recording['remarks'],
                'Score': recording['score'],
                'Timestamp': local_timestamp
            })