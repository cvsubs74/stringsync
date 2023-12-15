# Standard library imports
import json
import os
# Third-party imports
import pandas as pd
import streamlit as st
from abc import ABC
from streamlit_lottie import st_lottie

from components.BadgeAwarder import BadgeAwarder
from components.ListBuilder import ListBuilder
from components.RecordingUploader import RecordingUploader
from components.ScoreDisplay import ScoreDisplay
from components.TimeConverter import TimeConverter
from components.TrackRecommender import TrackRecommender
from components.TrackScoringTrendsDisplay import TrackScoringTrendsDisplay
from dashboards.AssignmentDashboard import AssignmentDashboard
from dashboards.BadgesDashboard import BadgesDashboard
from dashboards.HallOfFameDashboard import HallOfFameDashboard
from dashboards.MessageDashboard import MessageDashboard
from dashboards.PracticeDashboard import PracticeDashboard
from dashboards.ProgressDashboard import ProgressDashboard
from dashboards.ResourceDashboard import ResourceDashboard
from dashboards.StudentAssessmentDashboard import StudentAssessmentDashboard
from dashboards.TeamDashboard import TeamDashboard
from dashboards.TrackRecommendationDashboard import TrackRecommendationDashboard
from enums.ActivityType import ActivityType
from enums.Features import Features
from enums.Settings import Portal
from enums.SoundEffect import SoundEffect
from enums.TimeFrame import TimeFrame
from portals.BasePortal import BasePortal
from components.AudioProcessor import AudioProcessor
from repositories.ModelPerformanceRepository import ModelPerformanceRepository
from repositories.ScorePredictionModelRepository import ScorePredictionModelRepository


class StudentPortal(BasePortal, ABC):
    def __init__(self):
        super().__init__()
        self.score_prediction_model_repo = ScorePredictionModelRepository(self.get_connection())
        self.model_performance_repo = ModelPerformanceRepository(self.get_connection())
        self.badge_awarder = BadgeAwarder(
            self.settings_repo, self.recording_repo,
            self.user_achievement_repo, self.user_practice_log_repo,
            self.portal_repo, self.storage_repo)
        self.resource_dashboard_builder = ResourceDashboard(
            self.resource_repo, self.storage_repo)

    def get_recording_uploader(self):
        return RecordingUploader(
            self.recording_repo, self.track_repo, self.raga_repo, self.user_activity_repo,
            self.user_session_repo, self.score_prediction_model_repo, self.model_performance_repo,
            self.storage_repo, self.badge_awarder, AudioProcessor(), self.get_models_bucket())

    def get_progress_dashboard(self):
        return ProgressDashboard(
            self.settings_repo, self.recording_repo, self.user_achievement_repo,
            self.user_practice_log_repo, self.track_repo, self.assignment_repo)

    def get_practice_dashboard(self):
        return PracticeDashboard(self.user_practice_log_repo)

    def get_team_dashboard(self):
        return TeamDashboard(
            self.portal_repo, self.user_repo,
            self.user_achievement_repo, self.badge_awarder, self.avatar_loader)

    def get_assignment_dashboard(self):
        return AssignmentDashboard(
            self.resource_repo, self.track_repo, self.recording_repo,
            self.assignment_repo, self.storage_repo,
            self.resource_dashboard_builder, self.get_recording_uploader())

    def get_message_dashboard(self):
        return MessageDashboard(
            self.message_repo, self.user_activity_repo, self.avatar_loader)

    def get_badges_dashboard(self):
        return BadgesDashboard(
            self.settings_repo, self.user_achievement_repo, self.storage_repo)

    def get_student_assessment_dashboard(self):
        return StudentAssessmentDashboard(
            self.user_repo, self.recording_repo, self.user_activity_repo, self.user_session_repo,
            self.user_practice_log_repo, self.user_achievement_repo, self.assessment_repo,
            self.portal_repo)

    def get_hall_of_fame_dashboard(self):
        return HallOfFameDashboard(
            self.portal_repo, self.badge_awarder, self.avatar_loader)

    def get_portal(self):
        return Portal.STUDENT

    def get_title(self):
        return f"{self.get_app_name()} Student Portal"

    def get_icon(self):
        return "🎶"

    def get_tab_dict(self):
        tabs = [
            ("🏆 Hall of Fame", self.hall_of_fame),
            ("🎤 Record", self.recording_dashboard),
            ("📥 Submissions", self.submissions_dashboard),
            ("⏲️ Practice Log", self.practice_dashboard),
            ("🏆 Badges", self.badges_dashboard),
            ("📚 Resources", self.resources_dashboard),
            ("📝 Assignments", self.assignments_dashboard),
            ("📊 Progress Dashboard", self.progress_dashboard),
            ("👥 Team Dashboard", self.team_dashboard),
            ("🔗 Team Connect", self.team_connect),
            ("⚙️ Settings", self.settings) if self.is_feature_enabled(
                Features.STUDENT_PORTAL_SETTINGS) else None,
            ("🗂️ Sessions", self.sessions) if self.is_feature_enabled(
                Features.STUDENT_PORTAL_SHOW_USER_SESSIONS) else None,
            ("📊 Activities", self.activities) if self.is_feature_enabled(
                Features.STUDENT_PORTAL_SHOW_USER_ACTIVITY) else None,
        ]
        return {tab[0]: tab[1] for tab in tabs if tab}

    def show_introduction(self):
        st.write("""
            ### What Can You Do Here? 🎻

            - **Explore & Learn**: Access a variety of musical tracks and educational resources.
            - **Perform & Improve**: Record your music, submit assignments, and receive instant feedback.
            - **Track & Grow**: Monitor your progress and celebrate achievements with badges.
            - **Connect & Collaborate**: Join the community, share insights, and learn together.
        """
                 )

        st.write("""
            ### Why Choose GuruShishya? 🌟

            - **Personalized Learning**: Customize your learning journey according to your preferences and skill level.
            - **Instant Feedback**: Get real-time, data-driven feedback on your performances to know where you stand.
            - **Progress Tracking**: Visualize your growth over time with easy-to-understand charts and metrics.
            - **Achievements and Badges**: Get rewarded for your hard work and dedication with exciting badges.
            - **Comprehensive Recording**: Improve your skills by recording and reviewing your performances.
            - **Organized Submissions**: Keep track of all your work and submissions in one place.
            - **Diligent Practice Log**: Maintain a detailed log of your practice sessions to monitor your improvement.
            - **Resource Library**: Access a wide range of resources to support your learning.
            - **Structured Assignments**: Receive and submit assignments directly through the portal.
            - **Detailed Progress Dashboard**: Gain insights into your learning progression with detailed analytics.
            - **Collaborative Team Dashboard**: Engage with your peers and track team progress.
            - **Networking with Team Connect**: Build connections and collaborate with fellow learners.
        """
                 )

        st.write(
            "Ready to dive into your musical journey? Register & Login to explore all the exciting features available "
            "to you! "
        )

    def show_animations(self):
        # Center-aligned, bold text with cursive font, improved visibility, and spacing
        st.markdown("""
            <h1 style='text-align: center; font-weight: bold; color: #CB5A8A; font-size: 40px;'>
                Congratulations!!!!
            </h1>
            <h2 style='text-align: center; color: #CB5A8A; font-size: 24px;'>
                You have earned a badge!!
                🎉🎇
            </h2>
        """, unsafe_allow_html=True)

        # Load and center the Lottie animation
        byte_data = self.storage_repo.download_blob_by_name(f"animations/giftbox.json")
        lottie_json = json.loads(byte_data.decode('utf-8'))

        # Create three columns: left, center, right
        left_col, center_col, right_col = st.columns([2, 2.5, 1])

        # Use the center column to display the lottie animation
        with center_col:
            st_lottie(lottie_json, speed=1, width=400, height=200, loop=True, quality='high',
                      key="badge_awarded")
            st.balloons()
            self.play_sound_effect(SoundEffect.AWARD)

    def hall_of_fame(self):
        st.markdown(
            f"<h2 style='text-align: center; font-weight: bold; color: {self.get_tab_heading_font_color()}; font"
            f"-size: 30px;'> 🏆 Hall of Fame 🏆️ </h2>", unsafe_allow_html=True)
        hall_of_fame_dashboard = self.get_hall_of_fame_dashboard()
        hall_of_fame_dashboard.build(self.get_group_id(), TimeFrame.PREVIOUS_WEEK)
        st.write("")
        self.divider(3)
        hall_of_fame_dashboard.build(self.get_group_id(), TimeFrame.PREVIOUS_MONTH)

    def recording_dashboard(self):
        st.markdown(
            f"<h2 style='text-align: center; font-weight: bold; color: {self.get_tab_heading_font_color()}; font"
            f"-size: 24px;'> 🎙️ Record Your Tracks 🎙️</h2>", unsafe_allow_html=True)
        selected_track_name = TrackRecommendationDashboard(self.recording_repo).display_recommendations(
            self.get_user_id())

        st.write("")
        # Set the track based on the selected button
        track = None
        if selected_track_name:
            track = self.track_repo.get_track_by_name(selected_track_name)

        if not track:
            track = self.filter_tracks()
        else:
            st.button("Show filters")

        if not track:
            st.info("Please select a track to continue.")
            return

        if not selected_track_name:
            selected_track_name = track['track_name']

        self.create_track_headers()

        # Download and save the audio files to temporary locations
        with st.spinner("Please wait.."):
            track_audio_path = self.download_to_temp_file_by_url(track['track_path'])
            track_ref_audio_path = self.download_to_temp_file_by_url(track['track_ref_path'])
        load_recordings = False
        col1, col2, col3 = st.columns([5, 5, 5])
        recording_uploader = self.get_recording_uploader()
        with col1:
            self.display_track_files(f"Track: {selected_track_name}", track_audio_path)
            self.display_track_files("Reference Track", track_ref_audio_path)
            if st.button("Load Recordings", type="primary"):
                load_recordings = True

        with col2:
            uploaded, badge_awarded, recording_id, recording_audio_path = recording_uploader.upload(
                self.get_session_id(), self.get_org_id(),
                self.get_user_id(), track, self.get_recordings_bucket())
        with col3:
            if uploaded:
                with st.spinner("Please wait..."):
                    recording = self.recording_repo.get_recording(recording_id)
                    distance, score = recording_uploader.analyze_recording(
                        track, recording, track_audio_path, recording_audio_path)
                    self.recording_repo.update_score_distance_analysis(
                        recording_id, distance, score)
                    ScoreDisplay(self.storage_repo).display_score(score)

        if badge_awarded:
            self.show_animations()

        if load_recordings:
            recordings = self.recordings(track['id'])
            TrackScoringTrendsDisplay().show(recordings)

        if uploaded:
            os.remove(recording_audio_path)

    @staticmethod
    def display_recordings_header():
        st.markdown("<h3 style='text-align: center; margin-bottom: 0;'>Recordings</h3>", unsafe_allow_html=True)
        st.markdown("<hr style='height:2px; margin-top: 0; border-width:0; background: lightblue;'>",
                    unsafe_allow_html=True)

    def recordings(self, track_id):
        self.display_recordings_header()
        recordings = self.recording_repo.get_recordings_by_user_id_and_track_id(
            self.get_user_id(), track_id)

        if not recordings:
            st.info("No recordings found.")
            return

        # Create a DataFrame to hold the recording data
        df = pd.DataFrame(recordings)
        column_widths = [20, 20, 21, 21, 18]
        list_builder = ListBuilder(column_widths)
        list_builder.build_header(
            column_names=["Track", "Remarks", "Score", "Time", "Badges"])

        # Loop through each recording and create a table row
        for index, recording in df.iterrows():
            st.markdown("<div style='border-top:1px solid #AFCAD6; height: 1px;'>", unsafe_allow_html=True)
            with st.container():
                col1, col2, col3, col4, col5 = st.columns([1, 1, 1, 1, 1])
                if recording['blob_url']:
                    filename = self.storage_repo.download_blob_by_name(recording['blob_name'])
                    col1.write("")
                    col1.audio(filename, format='dashboards/m4a')
                else:
                    col1.write("No dashboards data available.")

                col2.write("")
                # Get the remarks, replacing new lines with <br> for HTML display
                remarks_html = recording.get('remarks', 'N/A').replace("\n", "<br>")

                # Now use markdown to display the remarks with HTML new lines
                col2.markdown(
                    f"<div style='padding-top:5px;color:black;font-size:14px;'>{remarks_html}</div>",
                    unsafe_allow_html=True)

                col3.write("")
                col3.markdown(
                    f"<div style='padding-top:8px;color:black;font-size:14px;'>{recording.get('score')}</div>",
                    unsafe_allow_html=True)
                local_timestamp = recording['timestamp'].strftime('%-I:%M %p | %b %d')
                col4.write("")
                col4.markdown(f"<div style='padding-top:5px;color:black;font-size:14px;'>{local_timestamp}</div>",
                              unsafe_allow_html=True)

                badge = self.user_achievement_repo.get_badge_by_recording(recording['id'])
                if badge:
                    col5.image(self.get_badge(badge), width=75)

        return recordings

    def get_audio_data(self, recording):
        if recording['blob_url']:
            filename = self.storage_repo.download_blob_by_name(recording['blob_name'])
            return f"<audio controls><source src='{filename}' type='audio/m4a'></audio>"
        return "No dashboards data available."

    def format_timestamp(self, timestamp):
        formatted_timestamp = timestamp.strftime('%I:%M %p, ') + self.ordinal(
            int(timestamp.strftime('%d'))) + timestamp.strftime(' %b, %Y')
        return formatted_timestamp

    def submissions_dashboard(self):
        st.markdown(
            f"<h2 style='text-align: center; font-weight: bold; color: {self.get_tab_heading_font_color()}; font"
            f"-size: 24px;'> 📝 Review Your Submissions & Feedback 📝</h2>", unsafe_allow_html=True)
        self.divider()
        col1, col2, col3 = st.columns([2.4, 2, 1])
        with col2:
            if not st.button("Load Submissions", key='load_submissions', type='primary'):
                return

        # Fetch submissions from the database
        submissions = self.portal_repo.get_submissions_by_user_id(
            self.get_user_id(), limit=self.get_limit())

        if not submissions:
            st.info("No submissions found.")
            return
        column_widths = [16.66, 16.66, 16.66, 17.2, 17.8, 15]
        list_builder = ListBuilder(column_widths)
        list_builder.build_header(
            column_names=["Track Name", "Track", "Recording", "Score", "Teacher Remarks", "Badges"])

        # Display submissions
        for submission in submissions:
            st.markdown("<div style='border-top:1px solid #AFCAD6; height: 1px;'>", unsafe_allow_html=True)
            with st.container():
                col1, col2, col3, col4, col5, col6 = st.columns([0.9, 1, 1.1, 1, 1, 1])

                col1.markdown(
                    f"<div style='padding-top:5px;color:black;font-size:14px;text-align:left;'>"
                    f"{submission['track_name']}</div>",
                    unsafe_allow_html=True)
                if submission['track_audio_url']:
                    track_audio = self.storage_repo.download_blob_by_url(submission['track_audio_url'])
                    col2.audio(track_audio, format='dashboards/m4a')
                else:
                    col2.warning("No audio available.")

                if submission['recording_audio_url']:
                    track_audio = self.storage_repo.download_blob_by_url(submission['recording_audio_url'])
                    col3.audio(track_audio, format='dashboards/m4a')
                else:
                    col3.warning("No audio available.")

                col4.markdown(
                    f"<div style='padding-top:5px;color:black;font-size:14px;text-align:left;'>"
                    f"{submission.get('score', 'N/A')}</div>",
                    unsafe_allow_html=True)

                # Get the teacher_remarks, replacing new lines with <br> for HTML display
                teacher_remarks_html = submission.get('teacher_remarks', 'N/A').replace("\n", "<br>")

                # Now use markdown to display the teacher_remarks with HTML new lines
                col5.markdown(
                    f"<div style='padding-top:5px;color:black;font-size:14px;'>{teacher_remarks_html}</div>",
                    unsafe_allow_html=True)

                badge = self.user_achievement_repo.get_badge_by_recording(submission['recording_id'])
                if badge:
                    col6.image(self.get_badge(badge), width=75)

                # End of the border div
                st.markdown("</div>", unsafe_allow_html=True)

    def progress_dashboard(self):
        st.markdown(
            f"<h2 style='text-align: center; font-weight: bold; color: {self.get_tab_heading_font_color()}; font"
            f"-size: 24px;'> 📈 Track Your Progress & Development 📈</h2>", unsafe_allow_html=True)
        self.divider()
        st.markdown("<h1 style='font-size: 20px;'>Report Card</h1>", unsafe_allow_html=True)
        self.get_student_assessment_dashboard().show_assessment(self.get_user_id())
        self.divider(5)
        col1, col2, col3 = st.columns([2.5, 2, 1])
        with col2:
            if not st.button("Load Statistics", type="primary"):
                return

        self.get_progress_dashboard().build(self.get_user_id())

    def team_dashboard(self):
        st.markdown(f"<h2 style='text-align: center; font-weight: bold; color: {self.get_tab_heading_font_color()}; "
                    "font-size: 24px;'> 👥 Team Performance & Collaboration 👥</h2>", unsafe_allow_html=True)
        self.divider()
        options = [time_frame for time_frame in TimeFrame]

        # Find the index for 'CURRENT_WEEK' to set as default
        default_index = next((i for i, time_frame in enumerate(TimeFrame)
                              if time_frame == TimeFrame.CURRENT_WEEK), 0)

        # Create the select box with the default set to 'Current Week'
        time_frame = st.selectbox(
            'Select a time frame:',
            options,
            index=default_index,
            format_func=lambda x: x.value
        )

        if self.get_group_id():
            self.get_team_dashboard().build([self.get_group_id()], time_frame)
        else:
            st.info("Please wait for your teacher to assign you to a team!!")

    def team_connect(self):
        st.markdown(f"<h2 style='text-align: center; font-weight: bold; color: {self.get_tab_heading_font_color()}; "
                    "font-size: 24px;'> 💼 Team Engagement & Insight 💼</h2>", unsafe_allow_html=True)
        self.divider()
        if self.get_group_id():
            self.get_message_dashboard().build(
                self.get_user_id(), self.get_group_id(), self.get_session_id())
        else:
            st.info("Please wait for your teacher to assign you to a team!!")

    def filter_tracks(self):
        ragas = self.raga_repo.get_all_ragas()
        filter_options = self.fetch_filter_options(ragas)

        # Create three columns
        col1, col2, col3 = st.columns(3)

        level = col1.selectbox("Filter by Level", ["All"] + filter_options["Level"])
        raga = col2.selectbox("Filter by Ragam", ["All"] + filter_options["Ragam"])
        tags = col3.multiselect("Filter by Tags", ["All"] + filter_options["Tags"])

        tracks = self.track_repo.search_tracks(
            raga=None if raga == "All" else raga,
            level=None if level == "All" else level,
            tags=None if tags == ["All"] else tags
        )

        if not tracks:
            return None

        selected_track_name = self.get_selected_track_name(tracks)

        # Update the last selected track in session state
        if st.session_state['last_selected_track'] != selected_track_name and \
                selected_track_name != "Select a Track":
            # Log the track selection change
            self.log_track_selection_change(selected_track_name)

        st.session_state['last_selected_track'] = selected_track_name

        return self.get_selected_track_details(tracks, selected_track_name)

    def log_track_selection_change(self, selected_track_name):
        user_id = self.get_user_id()
        additional_params = {
            "track_name": selected_track_name,
        }
        self.user_activity_repo.log_activity(
            user_id, self.get_session_id(), ActivityType.PLAY_TRACK, additional_params)
        self.user_session_repo.update_last_activity_time(self.get_session_id())

    def fetch_filter_options(self, ragas):
        return {
            "Level": self.track_repo.get_all_levels(),
            "Ragam": [raga['name'] for raga in ragas],
            "Tags": self.track_repo.get_all_tags()
        }

    @staticmethod
    def get_selected_track_name(tracks):
        track_names = [track['track_name'] for track in tracks]
        return st.selectbox("Select a Track", ["Select a Track"] + track_names, index=0)

    @staticmethod
    def get_selected_track_details(tracks, selected_track_name):
        return next((track for track in tracks if track['track_name'] == selected_track_name), None)

    @staticmethod
    def create_track_headers():
        col1, col2, col3 = st.columns([5, 5, 5])
        custom_style = "<style>h2 {font-size: 20px;}</style>"
        divider = "<hr style='height:1px; margin-top: 0; border-width:0; background: lightblue;'>"

        with col1:
            st.markdown(f"{custom_style}<h2>Track</h2>{divider}", unsafe_allow_html=True)
        with col2:
            st.markdown(f"{custom_style}<h2>Recording</h2>{divider}", unsafe_allow_html=True)
        with col3:
            st.markdown(f"{custom_style}<h2>Score</h2>{divider}", unsafe_allow_html=True)

    @staticmethod
    def display_track_files(title, track_file):
        st.write(title)
        st.audio(track_file, format='audio/mp4')

    def badges_dashboard(self):
        st.markdown(
            f"<h2 style='text-align: center; font-weight: bold; color: {self.get_tab_heading_font_color()}; font"
            f"-size: 24px;'> 🏆 Your Achievements & Badges 🏆</h2>", unsafe_allow_html=True)
        self.divider()
        self.get_badges_dashboard().build(self.get_org_id(), self.get_user_id())

    def resources_dashboard(self):
        st.markdown(
            f"<h2 style='text-align: center; font-weight: bold; color: {self.get_tab_heading_font_color()}; font"
            f"-size: 24px;'> 📚 Access Your Learning Resources 📚</h2>", unsafe_allow_html=True)
        self.divider()
        col1, col2, col3 = st.columns([2.4, 2, 1])
        with col2:
            if not st.button("Load Resources", key='load_resources', type='primary'):
                return
        self.resource_dashboard_builder.resources_dashboard()

    def assignments_dashboard(self):
        st.markdown(
            f"<h2 style='text-align: center; font-weight: bold; color: {self.get_tab_heading_font_color()}; font"
            f"-size: 24px;'> 📚 Your Music Assignments & Progress 📚</h2>", unsafe_allow_html=True)
        self.divider()
        self.get_assignment_dashboard().build(
            self.get_session_id(), self.get_org_id(), self.get_user_id(), self.get_recordings_bucket())

    def practice_dashboard(self, timezone='America/Los_Angeles'):
        st.markdown(
            f"<h2 style='text-align: center; font-weight: bold; color: {self.get_tab_heading_font_color()}; font"
            f"-size: 24px;'> 🎼 Log Your Practice Sessions 🎼</h2>", unsafe_allow_html=True)
        self.divider()
        local_date, local_time = TimeConverter.get_current_date_and_time(timezone)
        # Initialize session state variables if they aren't already
        if 'form_submitted' not in st.session_state:
            st.session_state.form_submitted = False
        if 'badge_awarded_in_last_run' not in st.session_state:
            st.session_state.badge_awarded_in_last_run = False
        if 'practice_time' not in st.session_state:
            st.session_state.practice_time = local_time
        if 'practice_minutes' not in st.session_state:
            st.session_state.practice_minutes = 15

        badge_awarded = False
        cols = st.columns(2)
        with cols[0]:
            st.write("")
            st.write("")
            st.write("")
            with st.form("log_practice_time_form"):
                # Set default practice date and time based on the local timezone
                practice_date = st.session_state.practice_date \
                    if 'practice_date' in st.session_state else local_date
                practice_time = st.session_state.practice_time \
                    if 'practice_time' in st.session_state else local_time.time()

                # Create date and time inputs
                practice_date = st.date_input("Practice Date", value=practice_date, key="practice_date")
                practice_time = st.time_input("Practice Time", value=practice_time, key="practice_time", step=300)
                practice_minutes = st.selectbox("Minutes Practiced", [i for i in range(10, 121, 5)],
                                                key="practice_minutes")
                submit = st.form_submit_button("Log Practice", type="primary")

                if submit and not st.session_state.form_submitted:
                    practice_datetime = TimeConverter.get_local_datetime(
                        practice_date, practice_time, timezone)
                    if practice_datetime > local_time:
                        st.error("The practice time cannot be in the future.")
                    else:
                        user_id = self.get_user_id()
                        self.user_practice_log_repo.log_practice(
                            user_id, practice_datetime, practice_minutes)
                        st.success(f"Logged {practice_minutes} minutes of practice on {practice_datetime}.")
                        additional_params = {
                            "minutes": practice_minutes,
                        }
                        self.user_activity_repo.log_activity(self.get_user_id(),
                                                             self.get_session_id(),
                                                             ActivityType.LOG_PRACTICE,
                                                             additional_params)
                        badge_awarded = self.badge_awarder.auto_award_badge(
                            self.get_user_id(), practice_date)
                    st.session_state.form_submitted = True

        with cols[1]:
            self.get_practice_dashboard().build(self.get_user_id())

        if badge_awarded:
            st.session_state.badge_awarded_in_last_run = True
            st.rerun()

        # Reset form submission status after handling it
        if st.session_state.form_submitted:
            st.session_state.form_submitted = False

        if st.session_state.badge_awarded_in_last_run:
            self.show_animations()
            st.session_state.badge_awarded_in_last_run = False

    @staticmethod
    def ordinal(n):
        suffix = ['th', 'st', 'nd', 'rd', 'th'][min(n % 10, 4)]
        if 11 <= (n % 100) <= 13:
            suffix = 'th'
        return str(n) + suffix
