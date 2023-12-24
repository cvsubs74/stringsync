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

    def display_recommendations(self, user_id, allow_selection=True):
        # Get recommended tracks
        recommended_tracks = self.track_recommender.recommend_tracks(user_id)
        # Style and divider
        custom_style = "<style>h2 {font-size: 20px;}</style>"
        if allow_selection:
            st.markdown(
                """
                - Explore our curated **track recommendations** designed to enhance your skill development and address challenges from past sessions.
                - Each track includes details on **complexity**, your **average and top scores**, **peer benchmarks**, and a **tailored assessment** with suggestions for improvement.
                - **Select a track** that aligns with your goals, consistently practice, and aim to surpass threshold scores for mastery.
                - Remember to **review your recordings** and score trends for insights into areas of improvement and to track your progress.
                """,
                unsafe_allow_html=True
            )

        st.write("")
        # Create columns for each track
        cols = st.columns(5)
        selected_track_name = None
        selected_track_id = None

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
                if track_info['user_avg_score'] == 0:
                    st.info(f"**Your Top Score: {track_info['user_max_score']}**", icon="🚀")
                elif track_info['user_max_score'] < max_score_80_percent:
                    st.error(f"**Your Top Score: {track_info['user_max_score']}**", icon="🚀")
                else:
                    st.success(f"**Your Top Score: {track_info['user_max_score']}**", icon="🚀")

                st.info(f"**Track Top Score: {track_info['overall_max_score']}**", icon="🥇")

                st.info(f"**Track Threshold Score: {track_info['threshold_score']}**", icon="🎯")

                # Days on Track with color coding
                days_on_track = track_info['days_on_track']
                optimal_days = days_on_track <= 3
                moderate_days = 4 <= days_on_track <= 7
                high_days = 8 <= days_on_track <= 10
                very_high_days = days_on_track > 10
                if high_days or very_high_days:
                    st.error(f"**Days on Track: {days_on_track}**", icon="📅")
                elif moderate_days:
                    st.warning(f"**Days on Track: {days_on_track}**", icon="📅")
                else:  # Optimal: 0-3 days
                    st.success(f"**Days on Track: {days_on_track}**", icon="📅")

                # Determine bands for scores and days
                avg_equals_0 = track_info['user_avg_score'] == 0
                avg_below_threshold = track_info['user_avg_score'] < threshold_80_percent
                avg_above_threshold = track_info['user_avg_score'] >= threshold_80_percent
                top_below_max = track_info['user_max_score'] < max_score_80_percent
                top_above_max = track_info['user_max_score'] >= max_score_80_percent

                # Enumerate all combinations for assessment
                if very_high_days:
                    if avg_equals_0:
                        assessment = "**Assessment**: Considerable time on this track without any recordings. It's " \
                                     "critical to start recording to make progress. "
                        st.error(self.pad_assessment(assessment), icon="📝")
                    elif avg_below_threshold and top_below_max:
                        assessment = "**Assessment**: Significant time spent with both average and top scores low. " \
                                     "Critical to reassess learning approach and seek targeted guidance for " \
                                     "improvement. "
                        st.error(self.pad_assessment(assessment), icon="📝")
                    elif avg_below_threshold and top_above_max:
                        assessment = "**Assessment**: Extensive time on track; low average but high top scores. " \
                                     "Essential to focus on consistent performance improvement across sessions. "
                        st.warning(self.pad_assessment(assessment), icon="📝")
                    elif avg_above_threshold and top_below_max:
                        assessment = "**Assessment**: Considerable time invested with good average scores, yet there " \
                                     "is room for improvement in your top scores. Aim to elevate your peak " \
                                     "performance. "

                        st.warning(self.pad_assessment(assessment), icon="📝")
                    elif avg_above_threshold and top_above_max:
                        assessment = "**Assessment**: Significant duration on track with strong scores achieved. Time " \
                                     "to consider completing this track and exploring new learning challenges. "
                        st.info(self.pad_assessment(assessment), icon="📝")

                elif high_days:
                    if avg_equals_0:
                        assessment = "**Assessment**: You've spent quite some time on this track but haven't started " \
                                     "recording yet. Begin recording to see improvement. "
                        st.warning(self.pad_assessment(assessment), icon="📝")
                    elif avg_below_threshold and top_below_max:
                        assessment = "**Assessment**: High days on track with both average and top scores below " \
                                     "potential. Imperative to intensify learning efforts and seek improvement " \
                                     "strategies. "
                        st.warning(self.pad_assessment(assessment), icon="📝")
                    elif avg_below_threshold and top_above_max:
                        assessment = "**Assessment**: High days on track; average score lower, top score higher. " \
                                     "Crucial to strive for balanced skill enhancement across all aspects.",
                        st.info(self.pad_assessment(assessment), icon="📝")
                    elif avg_above_threshold and top_below_max:
                        assessment = "**Assessment**: High days on track; solid average performance but top scores " \
                                     "can improve. Push towards achieving peak performance in future sessions. "
                        st.info(self.pad_assessment(assessment), icon="📝")
                    elif avg_above_threshold and top_above_max:
                        assessment = "**Assessment**: Good duration spent on track with excellent scores achieved. " \
                                     "Now ready to wrap up this learning chapter and advance to new challenges. "
                        st.success(self.pad_assessment(assessment), icon="📝")

                elif moderate_days:
                    if avg_equals_0:
                        assessment = "**Assessment**: Some time has passed since this track was recommended. Starting " \
                                     "your recordings now can greatly benefit your learning. "
                        st.info(self.pad_assessment(assessment), icon="📝")
                    elif avg_below_threshold and top_below_max:
                        assessment = "**Assessment**: Moderate days on track; both average and top scores need a " \
                                     "significant boost. Focus on holistic skill development for better outcomes. "
                        st.info(self.pad_assessment(assessment), icon="📝")
                    elif avg_below_threshold and top_above_max:
                        assessment = "**Assessment**: Moderate days on track; room for improvement in average score. " \
                                     "Utilize existing strengths to foster overall growth and progress. "
                        st.success(self.pad_assessment(assessment), icon="📝")
                    elif avg_above_threshold and top_below_max:
                        assessment = "**Assessment**: Steady progress over moderate days; consistent average but " \
                                     "higher top scores achievable. Set sights on higher goals to maximize potential. "
                        st.success(self.pad_assessment(assessment), icon="📝")
                    elif avg_above_threshold and top_above_max:
                        assessment = "**Assessment**: Balanced effort over moderate days leading to excellent scores. " \
                                     "Continue this momentum to maintain and further enhance your learning journey. "
                        st.success(self.pad_assessment(assessment), icon="📝")

                elif optimal_days:
                    if avg_equals_0:
                        assessment = "**Assessment**: This is a great moment to eagerly start your first recording " \
                                     "for this track! Embark confidently on this journey to unlock valuable insights " \
                                     "and experiences "
                        st.success(self.pad_assessment(assessment), icon="📝")
                    elif avg_below_threshold and top_below_max:
                        assessment = "**Assessment**: Quick start with both scores needing enhancement. Dedicate time " \
                                     "to targeted practice for noticeable improvement in performance. "
                        st.info(self.pad_assessment(assessment), icon="📝")
                    elif avg_below_threshold and top_above_max:
                        assessment = "**Assessment**: Fast-paced progress with high top scores. Work on raising " \
                                     "average consistently to match top performance for well-rounded success. "
                        st.success(self.pad_assessment(assessment), icon="📝")
                    elif avg_above_threshold and top_below_max:
                        assessment = "**Assessment**: Optimal days on track with solid average; top score yet to " \
                                     "match. Strive for comprehensive success by enhancing peak performance levels. "
                        st.success(self.pad_assessment(assessment), icon="📝")
                    elif avg_above_threshold and top_above_max:
                        assessment = "**Assessment**: Optimal days on track culminating in impressive scores across " \
                                     "the board. An exceptional beginning indicative of great potential ahead! "
                        st.success(self.pad_assessment(assessment), icon="📝")

                # Select button
                if allow_selection:
                    if st.button(f"🌟 Select 🌟", key=f"btn_{i}", type="primary"):
                        selected_track_name = track_info['track_name']
                        selected_track_id = track_info['track_id']
                else:
                    if st.button(f"🌟 View Remarks 🌟", key=f"remarks_btn_{i}", type="primary"):
                        selected_track_name = track_info['track_name']
                        selected_track_id = track_info['track_id']

        return selected_track_id, selected_track_name, recommended_tracks

    def analyze_student_performance(self, user_id, days_on_track_threshold):
        # Get recommended tracks
        recommended_tracks = self.track_recommender.recommend_tracks(user_id)

        # Filter tracks based on days_on_track
        tracks_needing_attention = [
            track for track in recommended_tracks
            if track['days_on_track'] >= days_on_track_threshold
        ]

        return tracks_needing_attention

    @staticmethod
    def pad_assessment(assessment, max_length=250):
        padding = ' ' * (max_length - len(assessment))
        return assessment + padding

    @staticmethod
    def divider(height=1):
        """Utility function to create a divider with specified height."""
        st.markdown(f"<hr style='height:{height}px; "
                    f"margin-top: 0;  margin-bottom: 0; border-width:0; background: lightblue;'>",
                    unsafe_allow_html=True)
