import streamlit as st

from components.TrackRecommender import TrackRecommender
from repositories.RecordingRepository import RecordingRepository


class TrackRecommendationDashboard:
    def __init__(self, recording_repo: RecordingRepository):
        self.recording_repo = recording_repo
        self.track_recommender = TrackRecommender(self.recording_repo)

    def display_recommendations(self, user_id):
        # Get recommended tracks
        recommended_tracks = self.track_recommender.recommend_tracks(user_id)
        # Style and divider
        custom_style = "<style>h2 {font-size: 20px;}</style>"
        st.markdown(f"{custom_style}<h2>Personalized Track Recommendations</h2>", unsafe_allow_html=True)
        st.markdown("""
                    <p>The following tracks have been selected based on your recording submissions and the scores you have obtained. 
                    Each track is chosen to help you develop specific skills and overcome challenges you've encountered in past sessions. 
                    Here's how you can make the most of these recommendations:</p>
                    <ul>
                        <li><b>Review each track</b>: Take a moment to look at the details of each recommended track. 
                        Notice the overall average score and threshold score to gauge the track's difficulty.</li>
                        <li><b>Start Practicing</b>: Choose a track that interests you and start practicing. 
                        It's important to note that surpassing the threshold score is about your average performance on the track, not just a one-time achievement. 
                        Consistently scoring high on the track is key to surpassing the threshold average score, reflecting steady improvement and mastery.</li>
                    </ul>
                """, unsafe_allow_html=True)

        # Create columns for each track
        cols = st.columns(5)
        selected_track_name = None

        for i, track_info in enumerate(recommended_tracks):
            with cols[i]:
                # Display track details with enhanced styling
                st.markdown(
                    f"<span style='color: black; font-size: 18px;'><b>{track_info['name']}</b></span>",
                    unsafe_allow_html=True)
                self.divider(2)
                st.markdown(
                    f"<span style='color: black; font-size: 16px;'>🌟 <b>Your Avg. Score:</b> {track_info['user_avg_score']}</span>",
                    unsafe_allow_html=True)
                st.markdown(
                    f"<span style='color: black; font-size: 16px;'>🌍 <b>Overall Avg. Score:</b> {track_info['overall_avg_score']}</span>",
                    unsafe_allow_html=True)
                st.markdown(
                    f"<span style='color: black; font-size: 16px;'>🎯 <b>Threshold Avg. Score:</b> {track_info['threshold_score']}</span>",
                    unsafe_allow_html=True)

                # Display button with creative emoji for track selection
                if st.button(f"🌟 Select 🌟", key=f"btn_{i}", type="primary"):
                    selected_track_name = track_info['name']

        return selected_track_name

    @staticmethod
    def divider(height=1):
        """Utility function to create a divider with specified height."""
        st.markdown(f"<hr style='height:{height}px; margin-top: 0;  margin-bottom: 0; border-width:0; background: lightblue;'>",
                    unsafe_allow_html=True)

