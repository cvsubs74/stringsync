from repositories.RecordingRepository import RecordingRepository
from repositories.UserRepository import UserRepository


class TrackRecommender:
    def __init__(self, recording_repo: RecordingRepository,
                 user_repo: UserRepository):
        self.recording_repo = recording_repo
        self.user_repo = user_repo

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
                    'level': track_stat['level'],
                    'ordering_rank': track_stat['ordering_rank'],
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

    def get_top_common_tracks_for_group(self, group_id):
        # Get the list of user IDs in the group
        users = self.user_repo.get_users_by_group(group_id)
        user_ids = [user['user_id'] for user in users]

        # Dictionary to count the frequency of each track being recommended
        track_recommendation_count = {}

        for user_id in user_ids:
            print("UserId:", user_id)
            recommended_tracks = self.recommend_tracks(user_id)
            for track in recommended_tracks:
                track_name = track['track_name']
                track_recommendation_count[track_name] = track_recommendation_count.get(track_name, 0) + 1

        # Sort tracks by their recommendation frequency
        sorted_tracks = sorted(track_recommendation_count.items(), key=lambda x: x[1], reverse=True)

        # Get the top 5 most common tracks
        top_common_tracks = sorted_tracks[:5]

        return [track[0] for track in top_common_tracks]

    def get_top_advanced_tracks_for_group(self, group_id):
        # Get the list of user IDs in the group
        users = self.user_repo.get_users_by_group(group_id)
        user_ids = [user['user_id'] for user in users]

        # Set to store unique tracks (level, ordering_rank)
        unique_tracks = set()

        for user_id in user_ids:
            recommended_tracks = self.recommend_tracks(user_id)
            for track in recommended_tracks:
                # Add level and ordering rank tuple to the set
                unique_tracks.add((track['level'], track['ordering_rank']))

        # Sort tracks first by level (descending) then by ordering rank (descending)
        sorted_tracks = sorted(unique_tracks, key=lambda x: (-x[0], -x[1]))

        # Get the top 5 most advanced tracks
        top_advanced_tracks = sorted_tracks[:5]

        return [{'level': track[0], 'ordering_rank': track[1]} for track in top_advanced_tracks]
