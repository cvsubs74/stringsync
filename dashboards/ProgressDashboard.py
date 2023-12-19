from decimal import Decimal

import streamlit as st

from components.ListBuilder import ListBuilder
from components.TrackRecommender import TrackRecommender
from repositories.AssignmentRepository import AssignmentRepository
from repositories.RecordingRepository import RecordingRepository
from repositories.SettingsRepository import SettingsRepository
from repositories.TrackRepository import TrackRepository
from repositories.UserAchievementRepository import UserAchievementRepository
from repositories.UserPracticeLogRepository import UserPracticeLogRepository
import pandas as pd
import plotly.express as px

from repositories.UserRepository import UserRepository


class ProgressDashboard:
    def __init__(self,
                 settings_repo: SettingsRepository,
                 recording_repo: RecordingRepository,
                 user_achievement_repo: UserAchievementRepository,
                 user_practice_log_repo: UserPracticeLogRepository,
                 track_repo: TrackRepository,
                 assignment_repo: AssignmentRepository,
                 user_repo: UserRepository):
        self.settings_repo = settings_repo
        self.recording_repo = recording_repo
        self.user_achievement_repo = user_achievement_repo
        self.user_practice_log_repo = user_practice_log_repo
        self.track_repo = track_repo
        self.assignment_repo = assignment_repo
        self.user_repo = user_repo

    def build(self, user_id, group_id):
        with st.spinner("Please wait.."):
            tracks = self.get_tracks(user_id)
            if len(tracks) == 0:
                st.info("Please wait for lessons to be available.")
                return
            self.show_recording_stats(user_id, group_id, tracks)

    def show_assignment_stats(self, user_id):
        # Retrieve assignment stats for the specific user
        assignment_stats = self.assignment_repo.get_assignment_stats_for_user(user_id)
        if not assignment_stats:
            return

        st.markdown("<h1 style='font-size: 20px;'>Assignment Statistics</h1>", unsafe_allow_html=True)
        # Display the assignment stats in a table using ListBuilder
        column_widths = [20, 20, 20, 20, 20]
        list_builder = ListBuilder(column_widths)
        list_builder.build_header(column_names=[
            "Assignment", "Total Details", "Completed", "Pending", "Due Date"])

        for stat in assignment_stats:
            row_data = {
                "Assignment": stat['title'],
                "Total Details": stat['total_details'],
                "Completed": stat['completed_details'],
                "Pending": stat['pending_details'],
                "Due Date": stat["due_date"]
            }
            list_builder.build_row(row_data=row_data)

        st.write("")

    def get_tracks(self, user_id):
        # Fetch user-specific track statistics
        user_track_statistics = self.recording_repo.get_track_statistics_by_user(user_id)
        track_statistics = self.recording_repo.get_all_track_statistics()

        # Get the highest level the user has attempted
        highest_user_level = max(stat['level'] for stat in user_track_statistics)

        # Include all levels up to the highest level the user has attempted
        included_levels = set(range(1, highest_user_level + 1))

        # Filter all tracks to include only those in levels up to the highest attempted level
        filtered_tracks = [track for track in track_statistics if track['level'] in included_levels]

        # Create a dictionary for quick lookup of statistics by track_id
        stats_dict = {stat['track_id']: stat for stat in user_track_statistics}

        # Build track details list
        track_details = [
            {
                'track': track,
                'recommendation_threshold_score': track.get('recommendation_threshold_score', 0),
                'num_recordings': stats_dict.get(track['track_id'], {}).get('num_recordings', 0),
                'avg_score': stats_dict.get(track['track_id'], {}).get('avg_score', 0),
                'min_score': stats_dict.get(track['track_id'], {}).get('min_score', 0),
                'max_score': stats_dict.get(track['track_id'], {}).get('max_score', 0)
            }
            for track in filtered_tracks
        ]

        return track_details

    def show_recording_stats(self, user_id, group_id, tracks):
        track_recommender = TrackRecommender(self.recording_repo, self.user_repo)
        recommended_tracks = track_recommender.recommend_tracks(user_id)
        group_tracks = track_recommender.get_top_common_tracks_for_group(group_id)
        recommended_track_names = [track['track_name'] for track in recommended_tracks]
        group_track_names = [track['name'] for track in group_tracks]
        advanced_group_tracks = track_recommender.get_top_advanced_tracks_for_group(group_id)
        advanced_group_track_info = [(track['level'], track['ordering_rank']) for track in advanced_group_tracks]
        # Identify the top performer
        top_performer_id = max(advanced_group_tracks, key=lambda track: (track['level'], track['ordering_rank']),
                               default={'user_id': None})['user_id']

        # Determine the user's, group's common, and advanced group's highest level and ordering rank
        user_highest_info = max([(track['level'], track['ordering_rank']) for track in recommended_tracks],
                                default=(0, 0))
        group_highest_info = max([(track['level'], track['ordering_rank']) for track in advanced_group_tracks],
                                 default=(0, 0))
        group_common_info = max([(track['level'], track['ordering_rank']) for track in group_tracks], default=(0, 0))

        # Determine the user's progress status and provide context with color icon explanations
        if user_highest_info in advanced_group_track_info and user_highest_info >= group_highest_info:
            if top_performer_id == user_id:
                # Congratulatory message for the current user
                progress_status = "<h4 style='font-size: 18px;'>🏆 You're the Top Performer - Leading the Way!</h4>" \
                                  "<p style='font-size: 16px;'>Fantastic! You're at the forefront, leading the pack " \
                                  "with those cool <span style='color: red;'>♦️</span> red diamonds. Keep up the " \
                                  "amazing work and continue to set the pace for your friends!</p>"
            else:
                progress_status = "<h4 style='font-size: 18px;'>🏆 Top Performer - Keep Soaring High!</h4>" \
                                  "<p style='font-size: 16px;'>You're leading the pack (indicated by the ♦️ red " \
                                  "diamonds). You're hitting the advanced tracks that even the fastest learners in " \
                                  "the group are working on. Amazing job!</p>"
        elif user_highest_info > group_common_info:
            progress_status = "<h4 style='font-size: 18px;'>🚀 Excelling Ahead - Fantastic Progress!</h4>" \
                              "<p style='font-size: 16px;'>You're outpacing the average group progress " \
                              "(marked by the 🔶 orange diamonds). This means you're learning faster than most, " \
                              "taking on more challenging tracks. Keep it up!</p>"
        elif user_highest_info == group_common_info:
            progress_status = "<h4 style='font-size: 18px;'>✅ Right on Track - Steady and Strong!</h4>" \
                              "<p style='font-size: 16px;'>You're moving in sync with the group's average progress " \
                              "(🔶 orange diamonds). This shows you're keeping pace with your peers and are right " \
                              "where you should be.</p> "
        else:
            progress_status = "<h4 style='font-size: 18px;'>🌟 Time to Shine - Let's Catch Up!</h4>" \
                              "<p style='font-size: 16px;'>You've got some catching up to do, as you're currently " \
                              "behind the group's average (🔶 orange diamonds). But don't worry, it's your time to " \
                              "shine! With a little extra practice, you can quickly move up.</p>"

        # Display progress status with color icon context and formatted text
        st.markdown(progress_status, unsafe_allow_html=True)

        # Additional message for top performer if not the current user
        if top_performer_id and top_performer_id != user_id:
            st.markdown(
                f"<p style='font-size: 16px;'>Heads up! One of your friends is racing ahead, "
                f"setting an exciting pace! See those cool <span style='color: red;'>♦️</span> red diamonds? "
                f"They mark the tracks your friend is mastering. Think you can catch up or even zoom ahead? "
                f"Let's turn up the music and show what you've got! 🎵🚀</p>",
                unsafe_allow_html=True)

        column_widths = [22, 13, 13, 13, 13, 13, 13]
        list_builder = ListBuilder(column_widths)

        list_builder.build_header(
            column_names=["Track", "Level", "Recordings", "Average Score", "Threshold", "Min Score", "Max Score"])

        # Define margin as 80% of the threshold
        margin = float(Decimal(0.8))

        # Define the criteria for changing the row color
        criteria_colors = [
            (lambda row: row['is_recommended'], "#ADD8E6"),
            (lambda row: row['is_group_track'], "#B0E0E6"),
            (lambda row: float(row['Average Score']) >= float(row['Threshold']), "#C9FF9E"),
            (lambda row: float(row['Threshold']) * margin <= float(row['Average Score']) < float(row['Threshold']),
             "#FFF9B9"),
            (lambda row: float(row['Average Score']) < float(row['Threshold']) * margin, "#FABFBF"),
            (lambda row: float(row['Average Score']) == 0, "#FDFEFE"),
        ]

        for track_detail in tracks:
            track_name = track_detail['track']['name']
            is_recommended = track_name in recommended_track_names
            is_group_track = track_name in group_track_names
            is_advanced_group_track = (track_detail['track']['level'],
                                       track_detail['track']['ordering_rank']) in advanced_group_track_info

            # Icon logic with fixed length
            icons = ["&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"] * 3
            if is_group_track:
                icons[0] = "🔶"
            if is_advanced_group_track:
                icons[1] = "♦️"
            if is_recommended:
                icons[2] = "🔷"
            icons.append("&nbsp;&nbsp;")

            row_data = {
                "Track": f"{''.join(icons)} {track_name}",
                "Level": track_detail['track']['level'],
                "Number of Recordings": track_detail['num_recordings'],
                "Average Score": round(track_detail['avg_score'], 2),
                "Threshold": round(track_detail['recommendation_threshold_score'], 2),
                "Min Score": track_detail['min_score'],
                "Max Score": track_detail['max_score'],
                "is_recommended": is_recommended,
                "is_group_track": is_group_track,
                "is_advanced_group_track": is_advanced_group_track
            }
            list_builder.build_row(row_data=row_data, criteria_colors=criteria_colors)

    def show_track_count_and_duration_trends(self, user_id):
        recording_duration_data = self.recording_repo.get_recording_duration_by_date(user_id)
        if not recording_duration_data:
            return

        # Create a DataFrame from time_series_data
        df = pd.DataFrame(recording_duration_data)

        # Convert 'date' to datetime and ensure it's the index
        df['date'] = pd.to_datetime(df['date'])
        df.set_index('date', inplace=True)

        # Determine the full range of dates from the available data
        full_date_range_start = df.index.min()
        full_date_range_end = df.index.max()

        # Determine the range of dates for plotting
        plot_start_date = min(full_date_range_start, (pd.Timestamp.today() - pd.DateOffset(weeks=4)).normalize())

        # Create a date range that includes every day from the earliest data or the last 4 weeks to the latest data
        all_days = pd.date_range(start=plot_start_date, end=full_date_range_end, freq='D')

        # Reindex the DataFrame to include all days, filling missing values with 0
        df = df.reindex(all_days).fillna(0).reset_index()
        df.rename(columns={'index': 'date'}, inplace=True)

        # Plotting the line graph for Total Duration
        fig_duration = px.line(
            df,
            x='date',
            y='total_duration',
            title='Total Recording Duration Over Time',
            labels={'date': 'Date', 'total_duration': 'Total Duration (minutes)'}
        )
        fig_duration.update_yaxes(range=[0, max(60, df['total_duration'].max())])

        # Plotting the line graph for Total Tracks
        fig_tracks = px.line(
            df,
            x='date',
            y='total_tracks',
            title='Total Tracks Practiced Over Time',
            labels={'date': 'Date', 'total_tracks': 'Total Tracks'}
        )
        fig_tracks.update_yaxes(range=[0, df['total_tracks'].max()])

        col1, col2 = st.columns(2)
        with col1:
            st.plotly_chart(fig_duration, use_container_width=True)
        with col2:
            st.plotly_chart(fig_tracks, use_container_width=True)

    def show_practice_trends(self, user_id):
        practice_data = self.user_practice_log_repo.fetch_daily_practice_minutes(user_id)

        if not practice_data:
            return

        df = pd.DataFrame(practice_data)
        df['date'] = pd.to_datetime(df['date'])

        # Determine the full range of dates in the dataset
        full_date_range_start = df['date'].min()
        full_date_range_end = df['date'].max()

        # Determine the start date for plotting which is the earlier of the two: the start date of your data or 4
        # weeks ago
        plot_start_date = min(full_date_range_start, (pd.Timestamp.today() - pd.DateOffset(weeks=4)).normalize())

        # Create a date range that includes every day from the start of your data or the last 4 weeks to today
        all_days = pd.date_range(start=plot_start_date, end=pd.Timestamp.today().normalize(), freq='D')

        # Reindex the DataFrame to include all days, filling missing values with 0 for 'total_minutes'
        df.set_index('date', inplace=True)
        df = df.reindex(all_days).fillna(0).reset_index()
        df.rename(columns={'index': 'date'}, inplace=True)
        df['total_minutes'] = df['total_minutes'].astype(int)

        # Plotting the line graph for total practice minutes
        fig_line = px.line(
            df,
            x='date',
            y='total_minutes',
            title='Daily Practice Minutes Over the Last 4 Weeks',
            labels={'date': 'Date', 'total_minutes': 'Total Minutes'}
        )

        # Set the y-axis to start from 0
        fig_line.update_yaxes(range=[0, max(60, df['total_minutes'].max())])

        # Adding the line graph to the Streamlit app
        st.plotly_chart(fig_line, use_container_width=True)

    @staticmethod
    def show_score_graph_by_track(tracks):
        # Flatten the track details for easier DataFrame creation
        flattened_tracks = [
            {
                'Track Name': track_detail['track']['name'],
                'Number of Recordings': track_detail['num_recordings'],
                'Average Score': track_detail['avg_score'],
                'Min Score': track_detail['min_score'],
                'Max Score': track_detail['max_score']
            }
            for track_detail in tracks
        ]

        # Create a DataFrame for the track statistics
        df_track_stats = pd.DataFrame(flattened_tracks)
        df_track_stats.sort_values('Average Score', ascending=False, inplace=True)

        # Visualize with a bar chart
        fig = px.bar(
            df_track_stats,
            x='Track Name',  # Use the 'Track Name' for x-axis
            y='Average Score',
            color='Average Score',
            labels={'Track Name': 'Track', 'Average Score': 'Average Score'},
            title='Average Score per Track Comparison'
        )
        st.plotly_chart(fig, use_container_width=True)

    @staticmethod
    def show_attempt_graph_by_track(tracks):
        # Ensure the track details are flattened for DataFrame creation
        flattened_tracks = [
            {
                'Track Name': track_detail['track']['name'],
                'Number of Recordings': track_detail['num_recordings'],
                'Average Score': float(track_detail['avg_score']),
                'Min Score': float(track_detail['min_score']),
                'Max Score': float(track_detail['max_score'])
            }
            for track_detail in tracks
        ]

        # Create a DataFrame for the track statistics
        df_track_stats = pd.DataFrame(flattened_tracks)

        # Sort by 'Number of Recordings' for attempt comparison
        df_track_stats.sort_values('Number of Recordings', ascending=False, inplace=True)

        # Visualize with a bar chart comparing attempts
        fig = px.bar(
            df_track_stats,
            x='Track Name',
            y='Number of Recordings',
            color='Number of Recordings',
            labels={'Track Name': 'Track', 'Number of Recordings': 'Attempts'},
            title='Attempt Comparison per Track'
        )
        st.plotly_chart(fig, use_container_width=True)
