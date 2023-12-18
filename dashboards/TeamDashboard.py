import base64
import os

from components.AvatarLoader import AvatarLoader
from components.BadgeAwarder import BadgeAwarder
from components.ListBuilder import ListBuilder
from enums.TimeFrame import TimeFrame
from repositories.PortalRepository import PortalRepository
from repositories.UserAchievementRepository import UserAchievementRepository
from repositories.UserRepository import UserRepository
import streamlit as st


class TeamDashboard:
    def __init__(self,
                 portal_repo: PortalRepository,
                 user_repo: UserRepository,
                 user_achievement_repo: UserAchievementRepository,
                 badge_awarder: BadgeAwarder,
                 avatar_loader: AvatarLoader):
        self.portal_repo = portal_repo
        self.user_repo = user_repo
        self.user_achievement_repo = user_achievement_repo
        self.badge_awarder = badge_awarder
        self.avatar_loader = avatar_loader

    def build(self, group_ids, time_frame: TimeFrame):
        with st.spinner("Please wait.."):
            # Iterate over each group ID and fetch the dashboard data
            for group_id in group_ids:
                dashboard_data = self.portal_repo.fetch_team_dashboard_data(
                    group_id, time_frame)

                # Display group information
                group = self.user_repo.get_group(group_id)
                st.markdown(f"### {group['name']}")

                column_widths = [12.5, 12.5, 12.5, 12.5, 12.5, 12.5, 13.5, 10]
                list_builder = ListBuilder(column_widths)
                list_builder.build_header(
                    column_names=["Student", "Tracks", "Recs",
                                  "Recs Time (m)", "Pracs (m)",
                                  "Max Daily Prac (m)", "Score", "Badges"])

                # Display each team and its member count in a row
                for data in dashboard_data:
                    user_id = data['user_id']
                    badges = self.user_achievement_repo.get_user_badges(user_id, time_frame)
                    avatar = data.get('avatar')
                    avatar_file_path = self.avatar_loader.get_avatar(avatar) if avatar else None

                    # If an avatar file path is provided and the file exists
                    avatar_image_html = ""
                    if avatar_file_path and os.path.isfile(avatar_file_path):
                        with open(avatar_file_path, "rb") as image_file:
                            encoded_string = base64.b64encode(image_file.read()).decode()
                        avatar_image_html = f'<img src="data:image/png;base64,{encoded_string}" alt="avatar" style="width: ' \
                                            f'60px; height: 60px; border-radius: 50%; margin-right: 10px;"> '

                    divider = "<hr style='height:1px; margin-top: 0; border-width:0; background: lightblue;'>"
                    with st.container():
                        col1, col2, col3, col4, col5, col6, col7, col8 = st.columns([1, 1, 1, 1, 1, 1, 0.5, 1.5])
                        col1.markdown(f"<div style='display: flex; align-items: center;'>{avatar_image_html}<span "
                                      f"style='padding-top:5px;color:black;font-size:14px;'>{data['teammate']}</span></div>",
                                      unsafe_allow_html=True)
                        col2.write("")
                        col2.markdown(
                            f"<div style='padding-top:8px;color:black;font-size:14px;'>{data['unique_tracks']}</div>",
                            unsafe_allow_html=True)
                        col3.write("")
                        col3.markdown(
                            f"<div style='padding-top:5px;color:black;font-size:14px;'>{data['recordings']}</div>",
                            unsafe_allow_html=True)
                        col4.write("")
                        col4.markdown(
                            f"<div style='padding-top:5px;color:black;font-size:14px;'>{data['recording_minutes']}</div>",
                            unsafe_allow_html=True)
                        col5.write("")
                        col5.markdown(
                            f"<div style='padding-top:5px;color:black;font-size:14px;'>{data['practice_minutes']}</div>",
                            unsafe_allow_html=True)
                        col6.write("")
                        col6.markdown(
                            f"<div style='padding-top:5px;color:black;font-size:14px;'>{data['max_daily_practice_minutes']}</div>",
                            unsafe_allow_html=True)
                        col7.write("")
                        col7.markdown(
                            f"<div style='padding-top:5px;color:black;font-size:14px;'>{data['score']}</div>",
                            unsafe_allow_html=True)
                        with col8:
                            st.write("")
                            if badges:
                                num_badges = len(badges)
                                total_cols = 4
                                max_badges_per_row = 5

                                # If the number of badges is less than or equal to 4, center them
                                if num_badges <= total_cols:
                                    padding_cols = (total_cols - num_badges) // 2
                                    cols = st.columns([1] * padding_cols + [1] * num_badges + [1] * padding_cols)
                                    for i, badge in enumerate(badges):
                                        with cols[i + padding_cols]:
                                            st.image(self.badge_awarder.get_badge(badge), width=55)
                                else:
                                    # If there are more than 4 badges, display them in rows of up to 5 badges each
                                    for i in range(0, num_badges, max_badges_per_row):
                                        row_badges = badges[i:i + max_badges_per_row]
                                        row_padding = (max_badges_per_row - len(row_badges)) // 2
                                        cols = st.columns([1] * row_padding + [1] * len(row_badges) + [1] * row_padding)
                                        for j, badge in enumerate(row_badges):
                                            with cols[j + row_padding]:
                                                st.image(self.badge_awarder.get_badge(badge), width=55)
                            else:
                                _, center_column, _ = st.columns([1, 0.5, 1])
                                with center_column:
                                    st.write("N/A")

                        st.write("")
                        st.markdown(f"{divider}", unsafe_allow_html=True)

    def show_winners(self, group_id, timeframe):
        # Mapping of timeframes to badge types
        timeframe_to_badge_type = {
            TimeFrame.PREVIOUS_WEEK: 'Weekly',
            TimeFrame.CURRENT_WEEK: 'Weekly',
            TimeFrame.PREVIOUS_MONTH: 'Monthly',
            TimeFrame.CURRENT_MONTH: 'Monthly',
            TimeFrame.PREVIOUS_YEAR: 'Yearly',
            TimeFrame.CURRENT_YEAR: 'Yearly'
        }

        # Determine the badge type based on the timeframe
        badge_type = timeframe_to_badge_type.get(timeframe)

        # Get the winners from the repository based on the specified timeframe
        winners = self.portal_repo.get_winners(group_id, timeframe)

        # Create a divider line
        divider = "<hr style='height:1px; margin-top: 0; border-width:0; background: lightblue;'>"

        # Check if there are any winners
        if winners:
            st.markdown(
                f"<div style='padding-top:5px;color:#287DAD;font-size:20px;text-align:left'><b>Congratulations</b> "
                f"to all the <b>{badge_type} Badge Winners!!!</b>",
                unsafe_allow_html=True)
            st.write("")

            # Create a dictionary to store winners by badge
            winners_by_badge = {}

            # Group winners by badge
            for winner in winners:
                student_name = winner['student_name']
                badge = winner['weekly_badge']
                avatar = winner['avatar']

                # Get the avatar image file path
                avatar_file_path = self.avatar_loader.get_avatar(
                    avatar) if avatar else 'path_to_default_avatar'

                # Convert the image to a base64 string for embedding
                encoded_string = self.get_avatar_base64_string(avatar_file_path)

                # Embed the base64 string into the HTML image tag
                avatar_image_html = f'<img src="data:image/png;base64,{encoded_string}" alt="avatar" style="width: ' \
                                    f'60px; height: 60px; border-radius: 50%; margin-right: 10px;"> '
                winner['avatar_image_html'] = avatar_image_html

                if badge not in winners_by_badge:
                    winners_by_badge[badge] = []

                winners_by_badge[badge].append(winner)

            # Create 3 columns with equal width
            col1, col2, col3 = st.columns(3)

            # Keep track of the number of badges processed
            badge_count = 0

            # Iterate through badges and display the winners
            for badge, winners in winners_by_badge.items():
                # Decide in which column to place the badge based on the count
                if badge_count % 6 < 3:
                    if badge_count % 3 == 0:
                        col = col1
                    elif badge_count % 3 == 1:
                        col = col2
                    else:
                        col = col3
                else:
                    if badge_count % 3 == 0:
                        col = col1
                    elif badge_count % 3 == 1:
                        col = col2
                    else:
                        col = col3

                # Using the chosen column, display the badge and the winners
                with col:
                    if badge_count % 6 >= 3:
                        col.write("")

                    col.image(self.badge_awarder.get_badge(badge), width=175)

                    # Add congratulatory emojis next to each winner's name
                    winners_with_avatars = []
                    for winner in winners:
                        # Get the winner's avatar and name
                        avatar_image_html = winner['avatar_image_html']
                        student_name = winner['student_name']
                        # Create a HTML snippet for each winner
                        winner_html = f"<span style='display: flex; align-items: center;'>{avatar_image_html}" \
                                      f"<span style='margin-left: 0px; font-size:14px'>{student_name} 🎉</span></span> "
                        winners_with_avatars.append(winner_html)

                    # Join the winners' HTML snippets with commas and display them
                    col.markdown(
                        f"<div style='padding-top:0px;padding-left:20px;color:black;font-size:18px;'> {''.join(winners_with_avatars)}</div>",
                        unsafe_allow_html=True
                    )
                # Increment the badge count
                badge_count += 1

            st.write("")
            st.markdown(f"{divider}", unsafe_allow_html=True)

    @staticmethod
    def get_avatar_base64_string(avatar_file_path):
        # Check if the avatar file exists, else use a default image
        if avatar_file_path and os.path.isfile(avatar_file_path):
            with open(avatar_file_path, "rb") as image_file:
                encoded_string = base64.b64encode(image_file.read()).decode()
        else:
            # Use a default base64 encoded string for a placeholder image
            encoded_string = 'base64_string_of_a_default_placeholder_avatar'
        return encoded_string
