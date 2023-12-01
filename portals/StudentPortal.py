# Standard library imports
import base64
import datetime
import hashlib
import json
import os

# Third-party imports
import pandas as pd
import streamlit as st
from abc import ABC
from streamlit_lottie import st_lottie

from core.AssignmentDashboardBuilder import AssignmentDashboardBuilder
from core.BadgeAwarder import BadgeAwarder
from core.BadgesDashboardBuilder import BadgesDashboardBuilder
from core.ListBuilder import ListBuilder
from core.MessageDashboardBuilder import MessageDashboardBuilder
from core.PracticeDashboardBuilder import PracticeDashboardBuilder
from core.ProgressDashboardBuilder import ProgressDashboardBuilder
from core.ResourceDashboardBuilder import ResourceDashboardBuilder
from core.StudentAssessmentDashboardBuilder import StudentAssessmentDashboardBuilder
from core.TeamDashboardBuilder import TeamDashboardBuilder
from enums.ActivityType import ActivityType
from enums.Badges import UserBadges
from enums.Features import Features
from enums.Settings import Portal
from enums.SoundEffect import SoundEffect
from enums.TimeFrame import TimeFrame
from portals.BasePortal import BasePortal
from core.AudioProcessor import AudioProcessor


class StudentPortal(BasePortal, ABC):
    def __init__(self):
        super().__init__()
        self.audio_processor = AudioProcessor()
        self.badge_awarder = BadgeAwarder(
            self.settings_repo, self.recording_repo,
            self.user_achievement_repo, self.user_practice_log_repo,
            self.portal_repo, self.storage_repo)
        self.progress_dashboard_builder = ProgressDashboardBuilder(
            self.settings_repo, self.recording_repo, self.user_achievement_repo,
            self.user_practice_log_repo, self.track_repo, self.assignment_repo)
        self.resource_dashboard_builder = ResourceDashboardBuilder(
            self.resource_repo, self.storage_repo)
        self.practice_dashboard_builder = PracticeDashboardBuilder(
            self.user_practice_log_repo)
        self.team_dashboard_builder = TeamDashboardBuilder(
            self.portal_repo, self.user_achievement_repo, self.badge_awarder, self.avatar_loader)
        self.assignment_dashboard_builder = AssignmentDashboardBuilder(
            self.resource_repo, self.track_repo, self.assignment_repo, self.storage_repo,
            self.resource_dashboard_builder)
        self.message_dashboard_builder = MessageDashboardBuilder(
            self.message_repo, self.user_activity_repo, self.avatar_loader)
        self.badges_dashboard_builder = BadgesDashboardBuilder(
            self.settings_repo, self.user_achievement_repo, self.storage_repo)
        self.student_assessment_dashboard_builder = StudentAssessmentDashboardBuilder(
            self.user_repo, self.recording_repo, self.user_activity_repo, self.user_session_repo,
            self.user_practice_log_repo, self.user_achievement_repo, self.assessment_repo,
            self.portal_repo)

    def get_portal(self):
        return Portal.STUDENT

    def get_title(self):
        return f"{self.get_app_name()} Student Portal"

    def get_icon(self):
        return "🎶"

    def get_tab_dict(self):
        tabs = [
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

    def recording_dashboard(self):
        st.markdown(f"<h2 style='text-align: center; font-weight: bold; color: {self.tab_heading_font_color}; font"
                    f"-size: 24px;'> 🎙️ Record Your Tracks 🎙️</h2>", unsafe_allow_html=True)
        self.divider()
        track = self.filter_tracks()
        if not track:
            st.info("No tracks found.")
            return

        self.create_track_headers()

        # Download and save the audio files to temporary locations
        with st.spinner("Please wait.."):
            track_audio_path = self.download_to_temp_file_by_url(track['track_path'])
        load_recordings = False
        badge_awarded = False

        col1, col2, col3 = st.columns([5, 5, 5])
        with col1:
            self.display_track_files(track_audio_path)
            track_notes = self.raga_repo.get_notes(track['ragam_id'])
            if st.button("Load Recordings", type="primary"):
                load_recordings = True

        with col2:
            recording_name, recording_id, is_success, timestamp = \
                self.handle_file_upload(self.get_user_id(), track['id'])
            if is_success:
                additional_params = {
                    "track_name": track['track_name'],
                    "recording_name": recording_name,
                }
                self.user_activity_repo.log_activity(self.get_user_id(),
                                                     self.get_session_id(),
                                                     ActivityType.UPLOAD_RECORDING,
                                                     additional_params)
                self.user_session_repo.update_last_activity_time(self.get_session_id())
                badge_awarded = self.badge_awarder.award_user_badge(
                    self.get_org_id(), self.get_user_id(), UserBadges.FIRST_NOTE, timestamp)
        with col3:
            if is_success:
                with st.spinner("Please wait..."):
                    distance, score, analysis = self.display_student_performance(
                        track_audio_path, recording_name, track_notes, track)
                    self.recording_repo.update_score_and_analysis(
                        recording_id, distance, score, analysis)
        if badge_awarded:
            self.show_animations()

        if load_recordings:
            self.recordings(track['id'])
        if is_success:
            os.remove(recording_name)

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
                    col1.audio(filename, format='core/m4a')
                else:
                    col1.write("No core data available.")

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
                formatted_timestamp = recording['timestamp'].strftime('%I:%M %p, ') + self.ordinal(
                    int(recording['timestamp'].strftime('%d'))) + recording['timestamp'].strftime(' %b, %Y')
                col4.write("")
                col4.markdown(f"<div style='padding-top:5px;color:black;font-size:14px;'>{formatted_timestamp}</div>",
                              unsafe_allow_html=True)

                badge = self.user_achievement_repo.get_badge_by_recording(recording['id'])
                if badge:
                    col5.image(self.get_badge(badge), width=75)

    def get_audio_data(self, recording):
        if recording['blob_url']:
            filename = self.storage_repo.download_blob_by_name(recording['blob_name'])
            return f"<audio controls><source src='{filename}' type='audio/m4a'></audio>"
        return "No core data available."

    def format_timestamp(self, timestamp):
        formatted_timestamp = timestamp.strftime('%I:%M %p, ') + self.ordinal(
            int(timestamp.strftime('%d'))) + timestamp.strftime(' %b, %Y')
        return formatted_timestamp

    def submissions_dashboard(self):
        st.markdown(f"<h2 style='text-align: center; font-weight: bold; color: {self.tab_heading_font_color}; font"
                    f"-size: 24px;'> 📝 Review Your Submissions & Feedback 📝</h2>", unsafe_allow_html=True)
        self.divider()
        col1, col2, col3 = st.columns([2.4, 2, 1])
        with col2:
            if not st.button("Load Submissions", key='load_submissions', type='primary'):
                return

        # Fetch submissions from the database
        submissions = self.portal_repo.get_submissions_by_user_id(
            self.get_user_id(), limit=self.limit)

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
                    f"<div style='padding-top:5px;color:black;font-size:14px;text-align:left;'>{submission['track_name']}</div>",
                    unsafe_allow_html=True)
                if submission['track_audio_url']:
                    track_audio = self.storage_repo.download_blob_by_url(submission['track_audio_url'])
                    col2.audio(track_audio, format='core/m4a')
                else:
                    col2.warning("No audio available.")

                if submission['recording_audio_url']:
                    track_audio = self.storage_repo.download_blob_by_url(submission['recording_audio_url'])
                    col3.audio(track_audio, format='core/m4a')
                else:
                    col3.warning("No audio available.")

                col4.markdown(
                    f"<div style='padding-top:5px;color:black;font-size:14px;text-align:left;'>{submission.get('score', 'N/A')}</div>",
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
        st.markdown(f"<h2 style='text-align: center; font-weight: bold; color: {self.tab_heading_font_color}; font"
                    f"-size: 24px;'> 📈 Track Your Progress & Development 📈</h2>", unsafe_allow_html=True)
        self.divider()
        st.markdown("<h1 style='font-size: 20px;'>Report Card</h1>", unsafe_allow_html=True)
        self.student_assessment_dashboard_builder.show_assessment(self.get_user_id())
        self.divider(5)
        col1, col2, col3 = st.columns([2.5, 2, 1])
        with col2:
            if not st.button("Load Statistics", type="primary"):
                return

        self.progress_dashboard_builder.progress_dashboard(self.get_user_id())

    def team_dashboard(self):
        st.markdown(f"<h2 style='text-align: center; font-weight: bold; color: {self.tab_heading_font_color}; "
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
            self.team_dashboard_builder.team_dashboard(self.get_group_id(), time_frame)
        else:
            st.info("Please wait for your teacher to assign you to a team!!")

    def team_connect(self):
        st.markdown(f"<h2 style='text-align: center; font-weight: bold; color: {self.tab_heading_font_color}; "
                    "font-size: 24px;'> 💼 Team Engagement & Insight 💼</h2>", unsafe_allow_html=True)
        self.divider()
        if self.get_group_id():
            self.message_dashboard_builder.message_dashboard(
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
            st.markdown(f"{custom_style}<h2>Upload</h2>{divider}", unsafe_allow_html=True)
        with col3:
            st.markdown(f"{custom_style}<h2>Analysis</h2>{divider}", unsafe_allow_html=True)

    @staticmethod
    def display_track_files(track_file):
        st.audio(track_file, format='audio/mp4')

    def handle_file_upload(self, user_id, track_id):
        with st.form("recording_uploader_form", clear_on_submit=True):
            uploaded_student_file = st.file_uploader("Choose an audio file", type=["m4a", "mp3"])
            original_date = st.date_input("Original File Date", value=None)  # Default value is None
            uploaded = st.form_submit_button("Upload", type="primary")

            if uploaded:
                if uploaded_student_file is None:
                    st.error("File is required.")
                    return None, -1, False, datetime.datetime.now()

                # If the original date is provided, use it to create a datetime object,
                # otherwise use the current date and time.
                if original_date:
                    original_timestamp = datetime.datetime.combine(original_date, datetime.datetime.min.time())
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
                    recording_name, url, recording_id = self.add_recording(user_id,
                                                                           track_id,
                                                                           recording_data,
                                                                           original_timestamp,
                                                                           file_hash)

                    st.audio(recording_name, format='audio/mp4')
                return recording_name, recording_id, True, original_timestamp
        return None, -1, False, datetime.datetime.now()

    @staticmethod
    def calculate_file_hash(recording_data):
        return hashlib.md5(recording_data).hexdigest()

    def add_recording(self, user_id, track_id, recording_data, timestamp, file_hash):
        recording_name = f"{user_id}-{track_id}-{timestamp.strftime('%Y%m%d%H%M%S')}.m4a"
        blob_name = f'{self.get_recordings_bucket()}/{recording_name}'
        blob_url = self.storage_repo.upload_blob(recording_data, blob_name)
        self.storage_repo.download_blob(blob_url, recording_name)
        duration = self.audio_processor.calculate_audio_duration(recording_name)
        recording_id = self.recording_repo.add_recording(
            user_id, track_id, blob_name, blob_url, timestamp, duration, file_hash)
        return recording_name, blob_url, recording_id

    def display_student_performance(
            self, track_file, student_path, track_notes, track):
        if not student_path:
            return -1, ""

        offset = self.get_offset(track)
        distance = self.get_audio_distance(track_file, student_path)
        offset_corrected_distance = distance - offset
        student_notes = self.get_filtered_student_notes(student_path)
        error_notes, missing_notes = self.audio_processor.error_and_missing_notes(
            track_notes, student_notes)
        score = self.audio_processor.distance_to_score(
            offset_corrected_distance, 0, offset)
        analysis, score = self.display_score_and_analysis(score, error_notes, missing_notes)
        return distance, score, analysis

    @staticmethod
    def get_offset(track):
        # TODO: control it via settings
        base = 1.2
        multiplier = base ** (track['level']-1)
        return int(round(multiplier * track['offset']))

    def get_audio_distance(self, track_file, student_path):
        return self.audio_processor.compare_audio(track_file, student_path)

    def get_filtered_student_notes(self, student_path):
        student_notes = self.audio_processor.get_notes(student_path)
        return self.audio_processor.filter_consecutive_notes(student_notes)

    def display_score_and_analysis(self, score, error_notes, missing_notes):
        analysis, off_notes = self.audio_processor.generate_note_analysis(
            error_notes, missing_notes)
        new_score = self.display_score(score, off_notes)
        # st.info(analysis)
        encouragement_message = ""
        """
        encouragement_message = self.generate_message(new_score)
        st.info(encouragement_message)
        """
        return analysis + encouragement_message, new_score

    @staticmethod
    def display_score(score, errors):
        new_score = score
        """
        if score == 10 and errors > 0:
            new_score = score - errors
        """
        message = f"Score: {new_score}\n"
        if score <= 3:
            st.error(message)
        elif score <= 7:
            st.warning(message)
        else:
            st.success(message)
        return new_score

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

    def badges_dashboard(self):
        st.markdown(f"<h2 style='text-align: center; font-weight: bold; color: {self.tab_heading_font_color}; font"
                    f"-size: 24px;'> 🏆 Your Achievements & Badges 🏆</h2>", unsafe_allow_html=True)
        self.divider()
        self.badges_dashboard_builder.badges_dashboard(self.get_org_id(), self.get_user_id())

    def resources_dashboard(self):
        st.markdown(f"<h2 style='text-align: center; font-weight: bold; color: {self.tab_heading_font_color}; font"
                    f"-size: 24px;'> 📚 Access Your Learning Resources 📚</h2>", unsafe_allow_html=True)
        self.divider()
        self.resource_dashboard_builder.resources_dashboard()

    def assignments_dashboard(self):
        st.markdown(f"<h2 style='text-align: center; font-weight: bold; color: {self.tab_heading_font_color}; font"
                    f"-size: 24px;'> 📚 Your Music Assignments & Progress 📚</h2>", unsafe_allow_html=True)
        self.divider()
        self.assignment_dashboard_builder.assignments_dashboard(self.get_user_id())

    def practice_dashboard(self):
        st.markdown(f"<h2 style='text-align: center; font-weight: bold; color: {self.tab_heading_font_color}; font"
                    f"-size: 24px;'> 🎼 Log Your Practice Sessions 🎼</h2>", unsafe_allow_html=True)
        self.divider()
        # Initialize session state variables if they aren't already
        if 'form_submitted' not in st.session_state:
            st.session_state.form_submitted = False
        if 'badge_awarded_in_last_run' not in st.session_state:
            st.session_state.badge_awarded_in_last_run = False
        if 'practice_time' not in st.session_state:
            st.session_state.practice_time = datetime.datetime.now()
        if 'practice_minutes' not in st.session_state:
            st.session_state.practice_minutes = 15

        badge_awarded = False
        cols = st.columns(2)
        with cols[0]:
            st.write("")
            st.write("")
            st.write("")
            with st.form("log_practice_time_form"):
                # Use the session_state to remember the previously selected practice date
                practice_date = datetime.date.today() \
                    if 'practice_date' not in st.session_state else st.session_state.practice_date
                practice_time = datetime.datetime.now() \
                    if 'practice_time' not in st.session_state else st.session_state.practice_time

                practice_date = st.date_input("Practice Date",
                                              value=practice_date,
                                              key="practice_date")
                practice_time = st.time_input("Practice Time",
                                              value=practice_time,
                                              key="practice_time",
                                              step=300)
                practice_minutes = st.selectbox("Minutes Practiced",
                                                [i for i in range(10, 61, 5)],
                                                key="practice_minutes")
                submit = st.form_submit_button("Log Practice", type="primary")

                if submit and not st.session_state.form_submitted:
                    # Validate if the practice_date is not in the future
                    if practice_date > datetime.date.today():
                        st.error("The practice date cannot be in the future.")
                    else:
                        user_id = self.get_user_id()
                        practice_datetime = datetime.datetime.combine(practice_date, practice_time)
                        self.user_practice_log_repo.log_practice(user_id, practice_datetime, practice_minutes)
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
            self.practice_dashboard_builder.practice_dashboard(self.get_user_id())

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
