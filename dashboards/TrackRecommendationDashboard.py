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
        st.markdown(f"{custom_style}<h2>Track Recommendations</h2>", unsafe_allow_html=True)
        if allow_selection:
            st.markdown("""
                <p>Based on your recording submissions and scores, we've curated these <b>track recommendations</b> to aid in your <b>skill development</b> and address challenges from past sessions. Here's a guide to understanding and utilizing this information:</p>
                <ul>
                    <li><b>Track Details</b>: Each track is accompanied by the following details:
                        <ul>
                            <li><b>Level</b>: Indicates the <b>complexity</b> and <b>skill requirement</b> of the track. It helps you select a track that matches your current ability and challenges you to grow further.</li>
                            <li><b>Your Average Score</b>: Calculated from your <b>top 3 scoring recordings</b> for the track. This score reflects your <b>consistent performance</b> at your best and helps identify your strengths in the track.</li>
                            <li><b>Track Average Score</b>: Derived from the <b>top 10 scoring recordings</b> across all students for that track. This provides a comparative benchmark, showing where you stand among peers and what excellence in the track looks like.</li>
                            <li><b>Your Top Score</b>: The highest score you've achieved in a single recording for the track. It highlights your <b>peak performance</b> and potential in mastering the track's content.</li>
                            <li><b>Track Top Score</b>: The highest score achieved by any student on the track. It serves as an <b>aspirational goal</b>, showcasing the highest level of achievement possible on the track.</li>
                            <li><b>Track Threshold Score</b>: A predefined benchmark score for the track. Surpassing this score consistently signifies your <b>proficiency</b> and understanding of the track's material.</li>
                            <li><b>Days on Track</b>: Represents the total number of days you have spent working on this track. It helps in assessing the <b>time you've invested</b> and could indicate if a different learning approach may be required based on the duration.</li>
                            <li><b>Assessment</b>: Each track comes with a tailored assessment based on your performance. This includes <b>suggestions and observations</b> aimed at helping you understand your current standing and how to improve. <b>Read these carefully</b> to gain insights into your learning journey.</li>
                        </ul>
                    </li>
                    <li><b>Action Steps</b>: <b>Choose a track</b> that aligns with your learning goals. <b>Consistent practice</b> and striving to surpass the threshold scores are crucial for your <b>skill development</b> and mastery of the track.</li>
                </ul>
                <p><b>Important Note:</b> Once you select a track, make sure to <b>review your recordings</b> and <b>score trends</b> displayed below. Each recording for the selected track will be shown along with scores and reviews. <b>Listen to your own recordings</b> and <b>pay close attention to the reviews</b> to understand the corrections that need to be made. This self-review process is vital for recognizing <b>areas of improvement</b> and tracking your <b>progress</b> over time.</p>
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

                if not allow_selection:
                    last_remark = track_info['last_remark']
                    if track_info['user_avg_score'] == 0:
                        formatted_message = f"**Last Remark:** N/A"
                    else:
                        formatted_message = f"**Last Remark:** {last_remark}"

                    # Use markdown to display the message with a line break
                    st.info(formatted_message)

                # Determine bands for scores and days
                avg_below_threshold = track_info['user_avg_score'] < threshold_80_percent
                avg_above_threshold = track_info['user_avg_score'] >= threshold_80_percent
                top_below_max = track_info['user_max_score'] < max_score_80_percent
                top_above_max = track_info['user_max_score'] >= max_score_80_percent

                # Enumerate all combinations for assessment
                if track_info['user_avg_score'] == 0:
                    assessment = "**Assessment**: No recordings yet. "\
                                 "Embark on your first recording to unlock valuable insights and make meaningful " \
                                 "progress. It is time dive in and explore."
                    st.error(self.pad_assessment(assessment), icon="📝")

                elif very_high_days:
                    if avg_below_threshold and top_below_max:
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
                    if avg_below_threshold and top_below_max:
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
                    if avg_below_threshold and top_below_max:
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
                    if avg_below_threshold and top_below_max:
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

        return selected_track_name, recommended_tracks

    def analyze_student_performance(self, user_id):
        # Get recommended tracks
        recommended_tracks = self.track_recommender.recommend_tracks(user_id)

        students_needing_attention = []

        for track_info in recommended_tracks:
            # Determine bands for scores and days
            threshold_80_percent = track_info['threshold_score'] * Decimal('0.8')
            max_score_80_percent = track_info['overall_max_score'] * Decimal('0.8')
            avg_below_threshold = track_info['user_avg_score'] < threshold_80_percent
            top_below_max = track_info['user_max_score'] < max_score_80_percent
            days_on_track = track_info['days_on_track']
            very_high_days = days_on_track > 10

            # Determine if the student needs attention
            needs_attention = False
            attention_reason = ""

            if track_info['user_avg_score'] == 0:
                needs_attention = True
                attention_reason = "No recordings submitted"
            elif very_high_days and (avg_below_threshold or top_below_max):
                needs_attention = True
                attention_reason = "High days on track with low performance"
            elif avg_below_threshold and top_below_max:
                needs_attention = True
                attention_reason = "Both average and top scores below potential"

            if needs_attention:
                students_needing_attention.append({
                    "track_name": track_info['track_name'],
                    "reason": attention_reason
                })

        return students_needing_attention

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
