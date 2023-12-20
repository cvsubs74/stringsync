import os

import streamlit as st

from components.SoundEffectGenerator import SoundEffectGenerator
from enums.Badges import UserBadges, TrackBadges, BaseBadge
from enums.Settings import Settings
from enums.SoundEffect import SoundEffect
from repositories.SettingsRepository import SettingsRepository
from repositories.StorageRepository import StorageRepository
from repositories.UserAchievementRepository import UserAchievementRepository


class BadgesDashboard:
    def __init__(self,
                 settings_repo: SettingsRepository,
                 user_achievement_repo: UserAchievementRepository,
                 storage_repo: StorageRepository):
        self.settings_repo = settings_repo
        self.user_achievement_repo = user_achievement_repo
        self.storage_repo = storage_repo

    def build(self, org_id, user_id):
        with st.spinner("Please wait.."):
            self.show_badges_won(user_id)
            st.write("")
            self.divider()
            self.show_all_badges(org_id)

    def show_all_badges(self, org_id):
        st.markdown(f"""
                        <h2 style='text-align: center; color: {self.tab_heading_font_color(org_id)}; font-size: 24px;'>
                            🌟 Discover the Treasure Trove of Badges! 🌟
                        </h2>
                        <p style='text-align: center; color: {self.tab_heading_font_color(org_id)}; font-size: 18px;'>
                            🚀 Embark on an epic adventure and collect them all! 🚀
                        </p>
                        """, unsafe_allow_html=True)
        all_badges = list(UserBadges) + list(TrackBadges)
        # Create columns for badges
        cols = st.columns(3)
        for index, badge in enumerate(all_badges):
            with cols[index % 3]:
                st.markdown(f"### {badge.description}")
                st.markdown(f"_{badge.criteria}_")
                st.image(self.get_badge(badge.description), width=200)

    def show_badges_won(self, user_id):
        badge_counts = self.user_achievement_repo.get_user_badges_with_counts(user_id)

        total_badges = sum(badge_dict['count'] for badge_dict in badge_counts)

        if badge_counts:
            # Determine the milestone message
            if total_badges >= 10 and total_badges % 10 == 0:
                SoundEffectGenerator(self.storage_repo).play_sound_effect(SoundEffect.AWARD)
                milestone = total_badges
                milestone_message = f"**Outstanding achievement!** You've reached the **{milestone}** badge **milestone**!"
            else:
                milestone_message = f"**Congratulations**! You have earned a total of **{total_badges}** badges."

            st.markdown(
                f"<span style='font-size: 22px;color:#954444;'>{milestone_message} 🎉</span>",
                unsafe_allow_html=True)

            st.write("")

        if badge_counts:  # If there are badges
            for badge_dict in badge_counts:
                badge_name = badge_dict['badge']
                count = badge_dict['count']
                badge_enum = UserBadges.from_value(badge_name) or TrackBadges.from_value(badge_name)

                if badge_enum is None:
                    continue  # Skip if the badge is not found in either enum

                col1, col2, col3 = st.columns([1, 3, 3])  # Adjust column sizes accordingly
                with col1:
                    st.image(self.get_badge(badge_name), width=200)
                with col2:
                    st.write("")
                    st.write("")
                    st.write("")
                    st.markdown(f"<span style='font-size: 20px;color:#954444;'>{badge_enum.message}</span>",
                                unsafe_allow_html=True)
                    st.markdown(
                        f"<span style='font-size: 20px;color:#954444;'>"
                        f"You have earned the _{badge_enum.description}_ badge **{count}** times!</span>",
                        unsafe_allow_html=True)
                with col3:
                    st.write("")
                    st.write("")
                    st.write("")
                    badge_cols = st.columns(10)
                    badge_idx = 0  # To keep track of the badge index

                    for i in range(count):
                        with badge_cols[badge_idx % 10]:
                            st.image(self.get_badge(badge_name), width=50)
                        badge_idx += 1
        else:
            st.markdown("### No Badges Yet 🎖️")
            st.markdown("""
                    **What Can You Do to Earn Badges?**
        
                    1. **Listen to Tracks**: The more you listen, the more you learn.
                    2. **Record Performances**: Every recording earns you points towards your next badge.
                    3. **Keep Practicing**: The more points you earn, the more badges you unlock.
        
                    Start by listening to a track and making your first recording today!
                """)

    def get_badge(self, badge_name):
        # Directory where badges are stored locally
        local_badges_directory = 'badges'

        # Construct the local file path for the badge
        local_file_path = os.path.join(local_badges_directory, f"{badge_name}.png")

        # Check if the badge exists locally
        if os.path.exists(local_file_path):
            return local_file_path

        # If badge not found locally, attempt to download from remote
        remote_path = f"{self.get_badges_bucket()}/{badge_name}.png"
        success = self.storage_repo.download_blob_and_save(remote_path, local_file_path)

        if success:
            return local_file_path
        else:
            print(f"Failed to download badge named '{badge_name}' from remote location.")
            return None

    @staticmethod
    def get_badges_bucket():
        return 'badges'

    @staticmethod
    def divider(height=2):
        divider = f"<hr style='height:{height}px; margin-top: 0; border-width:0; background: lightblue;'>"
        st.markdown(f"{divider}", unsafe_allow_html=True)

    def tab_heading_font_color(self, org_id):
        self.settings_repo.get_setting(
            org_id, Settings.TAB_HEADING_FONT_COLOR)

