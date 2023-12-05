import base64
import os

from core.AvatarLoader import AvatarLoader
from core.BadgeAwarder import BadgeAwarder
from enums.Badges import UserBadges
from enums.TimeFrame import TimeFrame
from repositories.PortalRepository import PortalRepository
import streamlit as st


class HallOfFameDashboardBuilder:
    def __init__(self,
                 portal_repo: PortalRepository,
                 badge_awarder: BadgeAwarder,
                 avatar_loader: AvatarLoader):
        self.portal_repo = portal_repo
        self.badge_awarder = badge_awarder
        self.avatar_loader = avatar_loader

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

        start_date, end_date = timeframe.get_date_range()
        formatted_start_date = self.ordinal(int(start_date.strftime('%d'))) + start_date.strftime(' %b, %Y')
        formatted_end_date = self.ordinal(int(end_date.strftime('%d'))) + end_date.strftime(' %b, %Y')

        # Get the winners from the repository based on the specified timeframe
        winners = self.get_winners(group_id, timeframe)

        # Check if there are any winners
        if winners:
            st.markdown(
                f"<div style='padding-top:5px; color:#954444; font-size:24px; text-align:center; font-weight:bold;'>"
                f"<b>{badge_type} Hall of Fame : {formatted_start_date} to {formatted_end_date}</b>",
                unsafe_allow_html=True)
            st.write("")

            # Create a dictionary to store winners by badge
            winners_by_badge = {}

            # Group winners by badge
            for winner in winners:
                badge = winner['weekly_badge']
                if badge not in winners_by_badge:
                    winners_by_badge[badge] = []

                winners_by_badge[badge].append(winner)

            # Iterate through badges and display the winners
            for badge, winners in winners_by_badge.items():
                badge_enum = UserBadges.from_value(badge)
                appreciation_note = badge_enum.message

                # Accumulate names of all winners for the current badge
                winner_names = [winner['student_name'] for winner in winners]
                value = winners[0]['value']

                # Create a single congratulatory note for all winners of the badge
                # Format the winner names as a comma-separated list with each name bolded
                bolded_winner_names = ', '.join([f"<strong>{name}</strong>" for name in winner_names])

                # Create the congratulatory note with bolded winner names
                congratulatory_note = f"Congratulations {bolded_winner_names}!!! {appreciation_note}"

                # Use columns to display the badge and congratulatory note side by side
                col1, col2 = st.columns([1, 3])

                with col1:
                    # Display the badge image
                    st.image(self.badge_awarder.get_badge(badge), width=150)

                with col2:
                    # Display the congratulatory note
                    st.write("")
                    st.write("")
                    st.markdown(f"<span style='font-size: 20px;color:#954444;'>{congratulatory_note}</span>",
                                unsafe_allow_html=True)
                    st.markdown(f"<span style='font-size: 20px;color:#954444;'>{badge_enum.format_stats_info(value)}</span>",
                                unsafe_allow_html=True)

                st.write("")  # Add some space before the next badge

            st.write("")

    def get_winners(self, group_id, timeframe):
        if "hall_of_fame_winners" not in st.session_state:
            winners = self.portal_repo.get_winners(group_id, timeframe)
            st.session_state["hall_of_fame_winners"] = winners
        else:
            winners = st.session_state["hall_of_fame_winners"]
        return winners

    @staticmethod
    def clear_cache():
        if 'hall_of_fame_winners' in st.session_state:
            st.session_state.pop('hall_of_fame_winners')

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

    @staticmethod
    def ordinal(n):
        suffix = ['th', 'st', 'nd', 'rd', 'th'][min(n % 10, 4)]
        if 11 <= (n % 100) <= 13:
            suffix = 'th'
        return str(n) + suffix