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
            <p>Based on your recording submissions and scores, we've curated these <b>track recommendations</b> to aid in your skill development and address challenges from past sessions. Here's a guide to understanding and utilizing this information:</p>
            <ul>
                <li><b>Track Details</b>: Each track is accompanied by specific details. <b>Pay attention to the 'Level', 'Your Average Score', 'Track Average Score', 'Your Top Score', 'Track Top Score', and 'Track Threshold Score'</b>. These metrics provide insights into the track's difficulty and your performance in comparison to the overall and threshold scores.</li>
                <li><b>Color Coding</b>: Colors represent your performance status.
                    <ul>
                        <li><span style='color: red;'><b>Red</b></span>: Indicates <b>areas needing improvement</b>, such as an average score below 80% of the threshold or high days on track.</li>
                        <li><span style='color: green;'><b>Green</b></span>: Signifies that you are <b>on track</b>, like an average score within 80% of the threshold.</li>
                    </ul>
                </li>
                <li><b>Days on Track</b>: Reflects the time you've spent on each track. A higher number may indicate a need for more practice or different learning strategies.</li>
                <li><b>Last Remark</b>: Provides the latest feedback or note on your track performance.</li>
                <li><b>Assessments</b>: Each track comes with a tailored assessment based on your performance. This includes <b>suggestions and observations</b> aimed at helping you understand your current standing and how to improve. <b>Read these carefully</b> to gain insights into your learning journey.</li>
                <li><b>Action Steps</b>: <b>Choose a track</b> that aligns with your learning goals. <b>Consistent practice</b> and striving to surpass the threshold scores are crucial for your skill development and mastery of the track.</li>
            </ul>
            <p><b>Important Note:</b> Once you select a track, make sure to <b>review your recordings and score trends</b> displayed below. Each recording for the selected track will be shown along with scores and reviews. <b>Listen to your own recordings</b> and <b>pay close attention to the reviews</b> to understand the corrections that need to be made. This <b>>self-review</b> process is vital for recognizing areas of improvement and tracking your progress over time.</p>
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

                st.info(f"**Track Avg. Score: {track_info['overall_avg_score']}**", icon="⭐")

                # Convert 0.8 to a Decimal before multiplication
                max_score_80_percent = track_info['overall_max_score'] * Decimal('0.8')

                # Your Top Score compared to Overall Top Score
                if track_info['user_max_score'] < max_score_80_percent:
                    st.error(f"**Your Top Score: {track_info['user_max_score']}**", icon="🚀")
                else:
                    st.success(f"**Your Top Score: {track_info['user_max_score']}**", icon="🚀")

                st.info(f"**Track Top Score: {track_info['overall_max_score']}**", icon="🥇")

                st.info(f"**Track Threshold Score: {track_info['threshold_score']}**", icon="🎯")

                # Days on Track with color coding
                if track_info['days_on_track'] > 5:
                    st.error(f"**Days on Track: {track_info['days_on_track']}**", icon="📅")
                else:
                    st.info(f"**Days on Track: {track_info['days_on_track']}**", icon="📅")

                st.success(f"**Last Remark: {track_info['last_remark']}**", icon="💬")

                # Build and display the summary
                if track_info['user_avg_score'] == 0:
                    st.info(
                        "**Assessment**: No recordings uploaded. Start working on this track to see improvement and "
                        "gain insights.",
                        icon="📝")
                else:
                    # Assess performance and days on track
                    if track_info['user_avg_score'] < threshold_80_percent or \
                            track_info['user_max_score'] < max_score_80_percent:
                        performance_issue = True
                    else:
                        performance_issue = False

                    if track_info['days_on_track'] > 10:
                        st.error(
                            "**Assessment**: Considerable time spent with limited progress. Review the basics or seek "
                            "professional guidance.",
                            icon="📝")
                    elif track_info['days_on_track'] > 5:
                        if performance_issue:
                            st.warning(
                                "**Assessment**: Performance below par, and track challenging. Seek additional help "
                                "or revisit fundamentals.",
                                icon="📝")
                        else:
                            st.warning(
                                "**Assessment**: Making progress, but review challenging parts. Time spent exceeds "
                                "usual learning curve.",
                                icon="📝")
                    else:
                        if performance_issue:
                            st.warning(
                                "**Assessment**: Scores below threshold. Focus on improving weak areas to meet "
                                "expected standards.",
                                icon="📝")
                        else:
                            st.success(
                                "**Assessment**: Good progress and on the right track. Continue your efforts to "
                                "maintain the momentum.",
                                icon="📝")

                # Select button
                if st.button(f"🌟 Select 🌟", key=f"btn_{i}", type="primary"):
                    selected_track_name = track_info['track_name']

        return selected_track_name, recommended_tracks

    @staticmethod
    def divider(height=1):
        """Utility function to create a divider with specified height."""
        st.markdown(f"<hr style='height:{height}px; "
                    f"margin-top: 0;  margin-bottom: 0; border-width:0; background: lightblue;'>",
                    unsafe_allow_html=True)
