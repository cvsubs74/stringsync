import re
from datetime import datetime
from decimal import Decimal

import pandas as pd

from enums.ActivityType import ActivityType
from enums.TimeFrame import TimeFrame
from enums.UserType import UserType
from repositories.PortalRepository import PortalRepository
from repositories.RecordingRepository import RecordingRepository
from repositories.UserAchievementRepository import UserAchievementRepository
from repositories.UserActivityRepository import UserActivityRepository
from repositories.UserAssessmentRepository import UserAssessmentRepository
from repositories.UserPracticeLogRepository import UserPracticeLogRepository
from repositories.UserRepository import UserRepository
from repositories.UserSessionRepository import UserSessionRepository
import streamlit as st
from prompts import  prompts


class StudentAssessmentDashboard:
    def __init__(self,
                 user_repo: UserRepository,
                 recording_repo: RecordingRepository,
                 user_activity_repo: UserActivityRepository,
                 user_session_repo: UserSessionRepository,
                 user_practice_log_repo: UserPracticeLogRepository,
                 user_achievement_repo: UserAchievementRepository,
                 user_assessment_repo: UserAssessmentRepository,
                 portal_repo: PortalRepository):
        self.user_repo = user_repo
        self.recording_repo = recording_repo
        self.user_activity_repo = user_activity_repo
        self.user_session_repo = user_session_repo
        self.user_practice_log_repo = user_practice_log_repo
        self.user_achievement_repo = user_achievement_repo
        self.user_assessment_repo = user_assessment_repo
        self.portal_repo = portal_repo

    def generate_assessments(self, group_id, llm, time_frame):
        # Fetch all users within the group
        users = self.user_repo.get_users_by_group(group_id)

        # Check if there are users in the group
        if not users:
            print("No users found in the group.")
            return

        # Generate and save an assessment for each user
        for user in users:
            user_id = user['user_id']
            username = user['name']

            # Assessment already generated?
            if self.user_assessment_repo.exists_assessment(user_id, time_frame):
                continue

            # Fetch data needed for the LLM to generate the assessment
            data = self.get_student_data(user_id, time_frame)
            print(data)
            data = f"Student Name: {username}\nMusic Data:\n{data}"

            # Generate the assessment text with the LLM
            assessment = llm(prompts.PROGRESS_REPORT_GENERATION_PROMPT.format(data=data))

            # Create the assessment
            self.user_assessment_repo.create_assessment(user_id, assessment, time_frame)
            print(f"Assessment generated for user {user_id}.")

    def provide_feedback(self, llm, org_id):
        groups = self.user_repo.get_all_groups(org_id)

        if not groups:
            return

        group_options = ["--Select a Team--"] + [group['group_name'] for group in groups]
        group_name_to_id = {group['group_name']: group['group_id'] for group in groups}
        user_id = None
        time_frame_selected = None

        selected_group = st.selectbox(
            "Select a Team", group_options, key="student_assessment_group_selector")

        if selected_group != "--Select a Team--":
            selected_group_id = group_name_to_id[selected_group]

            users = self.user_repo.get_users_by_org_id_group_and_type(
                org_id, selected_group_id, UserType.STUDENT.value)

            user_options = {user['name']: user['id'] for user in users}
            options = ['--Select a student--'] + list(user_options.keys())
            username = st.selectbox(key="assessment_student_selection",
                                    label="Select a student:",
                                    options=options)

            options = [time_frame for time_frame in TimeFrame]

            # Find the index for 'CURRENT_WEEK' to set as default
            default_index = next((i for i, time_frame in enumerate(TimeFrame)
                                  if time_frame == TimeFrame.CURRENT_WEEK), 0)

            # Create the select box with the default set to 'Current Week'
            time_frame_selected = st.selectbox(
                key='weekly_assessment_time_frame_selection',
                label='Select a time frame:',
                options=options,
                index=default_index,
                format_func=lambda x: x.value
            )

            formatted_data = ""
            if username != '--Select a student--':
                user_id = user_options[username]
                data = self.get_student_data(
                    user_id, time_frame_selected)
                formatted_data = f"Student Name: {username}\nMusic Data:\n{data}"

            if "assessment" not in st.session_state:
                st.session_state["assessment"] = ""

            if st.button("Generate Report"):
                if formatted_data:
                    st.session_state["assessment"] = llm(
                        prompts.PROGRESS_REPORT_GENERATION_PROMPT.format(data=formatted_data))
            with st.form(key="assessment_submission", clear_on_submit=True):
                assessment = st.text_area("Student Assessment:",
                                          value=st.session_state["assessment"], height=150)
                submit = st.form_submit_button("Submit Assessment 🚀")
                if submit and assessment and time_frame_selected:
                    start_date, end_date = time_frame_selected.get_date_range()
                    self.user_assessment_repo.create_assessment(
                        user_id, assessment, start_date, end_date)
                    st.success("Your assessment has been submitted 🌟")
                    st.session_state["assessment"] = ""
                    st.rerun()

        self.show_assessment(user_id)

    def publish_assessments(self, publisher_id, publisher_session_id, group_id, llm):
        with st.spinner("Please wait.."):
            options = [time_frame for time_frame in TimeFrame]

            # Find the index for 'CURRENT_WEEK' to set as default
            default_index = next((i for i, time_frame in enumerate(TimeFrame)
                                  if time_frame == TimeFrame.CURRENT_WEEK), 0)

            # Create the select box with the default set to 'Current Week'
            time_frame = st.selectbox(
                key='weekly_assessment_time_frame_selection',
                label='Select a time frame:',
                options=options,
                index=default_index,
                format_func=lambda x: x.value
            )

            # Fetch assessments for the group within the selected time frame
            assessments = self.user_assessment_repo.get_assessments_by_group(group_id, time_frame)
            if not assessments:
                st.info("No assessments have been provided yet.")
                return

            # Fetch student stats for the group within the selected time frame
            stats_list = self.portal_repo.fetch_team_dashboard_data(
                group_id, time_frame)
            student_stats = {stat['user_id']: stat for stat in stats_list}

            for assessment in assessments:
                user_id = assessment['user_id']
                user_name = assessment['user_name']
                assessment_id = assessment['id']
                report_key = f"{user_id}-report"
                if report_key in st.session_state:
                    assessment_text = st.session_state[report_key]
                else:
                    assessment_text = assessment['assessment_text']
                stats = student_stats.get(user_id, {})

                with st.expander(f"Assessment for {user_name}"):
                    # Display stats as a table
                    if stats:
                        # Format the Decimal values into floats for display
                        for key in ['recording_minutes', 'score', 'practice_minutes']:
                            if key in stats and isinstance(stats[key], Decimal):
                                stats[key] = float(stats[key])

                        stats_df = pd.DataFrame([stats])

                        df = stats_df.style.set_table_styles(
                            [{'selector': 'th, td', 'props': [('text-align', 'left')]},  # Align text to left
                             {'selector': 'table', 'props': [('width', '100%')]}]  # Set table width to 100%
                        )

                        df.hide_index_names = True
                        # Render DataFrame with left-aligned text
                        st.write(df)

                    # Streamlit text area for displaying and editing the assessment text
                    edited_text = st.text_area("Edit Assessment:",
                                               value=assessment_text,
                                               height=150,
                                               key=f"textarea_{user_id}")

                    # Create a container for buttons
                    col1, col2, col3, col4 = st.columns([1, 1, 3, 12])
                    message_type = None
                    message = None
                    with col1:
                        if st.button("Update", key=f"update_{user_id}", type="primary"):
                            # Update the assessment text in the database
                            self.user_assessment_repo.update_assessment(
                                assessment_id, edited_text)
                            message, message_type = f"Assessment updated for {user_name}!", "success"
                            # Clear the session key
                            if report_key in st.session_state:
                                del st.session_state[report_key]

                    with col2:
                        if st.button("Publish", key=f"publish_{user_id}", type="primary"):
                            # Update the assessment status to 'published'
                            self.user_assessment_repo.publish_assessment(assessment_id)
                            message, message_type = f"Assessment published for {user_name}!", "success"
                            additional_params = {
                                "user_id": user_id,
                            }
                            # Log Activity
                            self.user_activity_repo.log_activity(publisher_id, publisher_session_id,
                                                                 ActivityType.PUBLISH_PROGRESS_REPORT,
                                                                 additional_params)

                    with col3:
                        if st.button("Regenerate Report", key=f"regenerate-report-{user_id}", type="primary"):
                            data = self.get_student_data(user_id, time_frame)
                            formatted_data = f"Student Name: {user_name}\nMusic Data:\n{data}"

                            if formatted_data:
                                st.session_state[report_key] = llm(
                                    prompts.PROGRESS_REPORT_GENERATION_PROMPT.format(data=formatted_data))
                                st.rerun()

                    if message_type == "success":
                        st.success(message)
                    elif message_type == "info":
                        st.info(message)

    def show_assessment(self, user_id):
        with st.spinner("Please wait.."):
            assessments = self.user_assessment_repo.get_published_assessments(user_id)
            if not assessments:
                st.info("No assessments have been provided yet.")
                return

            # Create a list of date range strings for the select box
            date_ranges = [f"{assessment['assessment_start_date'].strftime('%Y-%m-%d')} - "
                           f"{assessment['assessment_end_date'].strftime('%Y-%m-%d')}"
                           for assessment in assessments]

            # Let the user select a date range
            selected_range = st.selectbox('Select an assessment period:',
                                          ["--Select a date range--"] + date_ranges)

            if selected_range == "--Select a date range--":
                st.info("Please select a date range to view the report card..")
                return

            # Find the selected assessment
            for assessment in assessments:
                start_date = assessment['assessment_start_date'].strftime('%Y-%m-%d')
                end_date = assessment['assessment_end_date'].strftime('%Y-%m-%d')
                date_range = f"{start_date} - {end_date}"
                if date_range == selected_range:
                    timestamp = assessment['timestamp'].strftime('%-I:%M %p | %b %d') \
                        if isinstance(assessment['timestamp'], datetime) else assessment['timestamp']
                    text = assessment['assessment_text']
                    st.markdown(f"""
                        <div style='display: flex; flex-direction: column; background-color: #E8F4FA; border-radius: 10px; padding: 10px; margin-bottom: 5px;'>
                        <div style='display: flex; gap: 10px; align-items: baseline;'>
                            <p style='color: black; font-size: 1em; margin-top: 5px;'>
                                Assessment Start Date: <span style='font-weight: bold;'>{start_date}</span>
                            </p>
                            <p style='color: black; font-size: 1em; margin-top: 5px;'>
                                Assessment End Date: <span style='font-weight: bold;'>{end_date}</span>
                            </p>
                        </div>
                        <p style='margin: 0;'>{self.format_text(text)}</p>
                        <p style='color: #6C757D; font-size: 0.8em; margin-top: 5px;'>{timestamp}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    # Break after finding and displaying the selected assessment
                    break

    @staticmethod
    def format_text(text):
        # Remove newline characters
        text = text.replace('\n', ' ')

        # Bold the phrases within quotes
        quoted_strings = re.findall(r'"([^"]*)"', text)
        for string in quoted_strings:
            text = text.replace(f'"{string}"', f'<strong>"{string}"</strong>')

        # Bold the first word if it's followed by a comma (likely the student's name)
        text = re.sub(r'^(\w+),', r'<strong>\1,</strong>', text)

        # Bold the phrase "practice logs"
        text = text.replace('practice logs', '<strong>practice logs</strong>')

        # Bold any numerics, including those followed by an 's' like 10s, 9s, etc.
        text = re.sub(r'(\b\d+s?\b)', r'<strong>\1</strong>', text)

        # Bold date references like 22nd, 23rd, 25th, etc.
        text = re.sub(r'\b(\d+(st|nd|rd|th))\b', r'<strong>\1</strong>', text)

        # Bold "P string" and "S string"
        text = re.sub(r'\b(P string|S string)\b', r'<strong>\1</strong>', text)

        # Bold the word "streaks"
        text = text.replace('streaks', '<strong>streaks</strong>')

        return text

    def get_students_data_by_group(self, group_id, time_frame: TimeFrame = TimeFrame.PREVIOUS_WEEK):
        students = self.user_repo.get_users_by_group(group_id)
        students_data = {}
        for student in students:
            students_data[student['user_id']] = \
                self.get_student_data(student['user_id'], time_frame)

        return students_data

    def get_student_data(self, user_id, time_frame: TimeFrame = TimeFrame.PREVIOUS_WEEK):
        practice_logs = self.user_practice_log_repo.get_user_practice_logs_by_timeframe(
            user_id, time_frame)
        achievements = self.user_achievement_repo.get_user_achievements_by_timeframe(
            user_id, time_frame)
        recordings = self.recording_repo.get_submissions_by_timeframe(user_id, time_frame)
        # Define a list of fields to exclude
        fields_to_exclude = ["recording_audio_url", "track_audio_url", "timestamp", "recording_id", "track_id", "id"]
        # Create a new list without the URL fields
        filtered_recordings = []
        filtered_achievements = []
        filtered_logs = []
        for recording in recordings:
            filtered_recording = {key: value for key, value in recording.items() if key not in fields_to_exclude}
            filtered_recordings.append(filtered_recording)
        for achievement in achievements:
            filtered_achievement = {key: value for key, value in achievement.items() if key not in fields_to_exclude}
            filtered_achievements.append(filtered_achievement)
        for log in practice_logs:
            filtered_log = {key: value for key, value in log.items() if key not in fields_to_exclude}
            filtered_logs.append(filtered_log)
        # Combine all the data into a single dictionary
        student_data = {
            'recordings': filtered_recordings,
            'practice_logs': filtered_logs,
            'achievements': filtered_achievements
        }

        return student_data
