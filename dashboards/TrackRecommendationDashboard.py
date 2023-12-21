from decimal import Decimal

import streamlit as st

from components.TrackRecommender import TrackRecommender
from repositories.RecordingRepository import RecordingRepository
from repositories.UserRepository import UserRepository


class TrackRecommendationDashboard:
    def __init__(self, recording_repo: RecordingRepository,
                 user_repo: UserRepository):
        self.recording_repo = recording_repo
        self.user_repo = user_repo
        self.track_recommender = TrackRecommender(self.recording_repo, self.user_repo)

    def display_recommendations(self, user_id):
        # Get recommended tracks
        recommended_tracks = self.track_recommender.recommend_tracks(user_id)
        # Style and divider
        custom_style = "<style>h2 {font-size: 20px;}</style>"
        st.markdown(f"{custom_style}<h2>Track Recommendations</h2>", unsafe_allow_html=True)
        st.markdown("""
            <p>The following tracks have been selected based on your recording submissions and the scores you have obtained. 
            Each track is chosen to help you develop specific skills and overcome challenges you've encountered in past sessions. 
            Here's how you can make the most of these recommendations:</p>
            <ul>
                <li><b>Review each track</b>: Take a moment to look at the details of each recommended track. 
                Notice the overall average score and threshold score to gauge the track's difficulty.</li>
                <li><b>Color Coding Explained</b>:
                    <ul>
                        <li><span style='color: red;'>Red</span>: Indicates concern or areas needing improvement. For example, if your average score is below 80% of the threshold, or your days on track are high.</li>
                        <li><span style='color: green;'>Green</span>: Shows you are on track. For example, if your average score is within 80%  of the threshold.</li>
                    </ul>
                </li>
                <li><b>Start Practicing</b>: Choose a track that interests you and start practicing. 
                It's important to note that surpassing the threshold score is about your average performance on the track, not just a one-time achievement. 
                Consistently scoring high on the track is key to surpassing the threshold average score, reflecting steady improvement and mastery.</li>
            </ul>
        """, unsafe_allow_html=True)

        st.write("")
        # Create columns for each track
        cols = st.columns(5)
        selected_track_name = None

        for i, track_info in enumerate(recommended_tracks):
            with cols[i]:
                # Display track details with enhanced styling
                st.markdown(f"<span style='color: black; font-size: 17px;'><b>{track_info['track_name']}</b></span>",
                            unsafe_allow_html=True)
                self.divider(2)
                st.info(f"**Level: {track_info['level']}**", icon="🌟")

                # Convert 0.8 to a Decimal before multiplication
                threshold_80_percent = track_info['threshold_score'] * Decimal('0.8')

                # Your Average Score compared to Threshold
                if track_info['user_avg_score'] == 0:
                    st.info(f"**Your Avg. Score: {track_info['user_avg_score']}**", icon="📊")
                elif track_info['user_avg_score'] < threshold_80_percent:
                    st.error(f"**Your Avg. Score: {track_info['user_avg_score']}**", icon="📊")
                else:
                    st.success(f"**Your Avg. Score: {track_info['user_avg_score']}**", icon="📊")

                # Convert 0.8 to a Decimal before multiplication
                max_score_80_percent = track_info['overall_max_score'] * Decimal('0.8')

                # Your Top Score compared to Overall Top Score
                if track_info['user_max_score'] < max_score_80_percent:
                    st.error(f"**Your Top Score: {track_info['user_max_score']}**", icon="🚀")
                else:
                    st.success(f"**Your Top Score: {track_info['user_max_score']}**", icon="🚀")

                # Display remaining information using st.info
                st.info(f"**Overall Avg. Score: {track_info['overall_avg_score']}**", icon="⭐")
                st.info(f"**Top Score: {track_info['overall_max_score']}**", icon="🥇")
                st.info(f"**Threshold Avg. Score: {track_info['threshold_score']}**", icon="🎯")

                # Days on Track with color coding
                if track_info['days_on_track'] > 5:
                    st.error(f"**Days on Track: {track_info['days_on_track']}**", icon="📅")
                else:
                    st.info(f"**Days on Track: {track_info['days_on_track']}**", icon="📅")

                st.success(f"**Last Remark: {track_info['last_remark']}**", icon="💬")

                # Display button with creative emoji for track selection
                if st.button(f"🌟 Select 🌟", key=f"btn_{i}", type="primary"):
                    selected_track_name = track_info['track_name']

        return selected_track_name, recommended_tracks

    @staticmethod
    def divider(height=1):
        """Utility function to create a divider with specified height."""
        st.markdown(f"<hr style='height:{height}px; "
                    f"margin-top: 0;  margin-bottom: 0; border-width:0; background: lightblue;'>",
                    unsafe_allow_html=True)

