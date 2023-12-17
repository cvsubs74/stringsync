from repositories.RecordingRepository import RecordingRepository


class TrackRecommender:
    def __init__(self, recording_repo: RecordingRepository):
        self.recording_repo = recording_repo

    def recommend_tracks(self, user_id):
        recommended_tracks = []

        # Retrieve user-specific track statistics from the database
        user_track_stats = self.recording_repo.get_track_statistics_by_user(user_id)

        # Retrieve statistics for all tracks from the database
        all_track_stats = self.recording_repo.get_all_track_statistics()

        # Initialize a dictionary to store user's average scores for each track
        user_avg_scores = {stat['name']: stat['avg_score'] for stat in user_track_stats}
        user_max_scores = {stat['name']: stat['max_score'] for stat in user_track_stats}

        # Iterate through tracks and recommend tracks based on the new conditions
        for track_stat in all_track_stats:
            track_name = track_stat['name']
            overall_avg_score = round(track_stat['avg_score'], 2)
            top_score = round(track_stat['max_score'], 2)
            recommendation_threshold_score = round(track_stat['recommendation_threshold_score'], 2)

            # Check if the user has no recordings for this track
            # or if the user's average score for this track is below the threshold
            user_avg_score = round(user_avg_scores.get(track_name, 0), 2)
            user_max_score = round(user_max_scores.get(track_name, 0), 2)
            if track_name not in user_avg_scores or user_avg_score < recommendation_threshold_score:
                recommended_track_info = {
                    'track_name': track_name,
                    'user_avg_score': user_avg_score,
                    'user_max_score': user_max_score,
                    'overall_avg_score': overall_avg_score,
                    'overall_max_score': top_score,
                    'threshold_score': recommendation_threshold_score
                }
                recommended_tracks.append(recommended_track_info)

                # If we have recommended 5 tracks, break the loop
                if len(recommended_tracks) == 5:
                    break

        return recommended_tracks
