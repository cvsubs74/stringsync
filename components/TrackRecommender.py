from datetime import datetime

from repositories.RecordingRepository import RecordingRepository
from repositories.UserRepository import UserRepository


class TrackRecommender:
    def __init__(self, recording_repo: RecordingRepository,
                 user_repo: UserRepository):
        self.recording_repo = recording_repo
        self.user_repo = user_repo

    def recommend_tracks(self, user_id):
        recommended_tracks = []

        # Retrieve user-specific track statistics and average scores for each track
        user_track_stats = self.recording_repo.get_track_statistics_by_user(user_id)
        user_avg_scores_by_track = self.recording_repo.get_average_track_scores_by_user(user_id)
        user_avg_scores = {stat['track_id']: stat['avg_score'] for stat in user_avg_scores_by_track}
        user_max_scores = {stat['track_id']: stat['max_score'] for stat in user_track_stats}
        user_days_on_tracks = {
            stat['track_id']: (datetime.now() - stat['earliest_recording_date']).days
            for stat in user_track_stats if stat['earliest_recording_date'] and stat['latest_recording_date']
        }

        # Fetch latest remarks for all tracks recorded by the user
        last_remarks_data = self.recording_repo.get_latest_recording_remarks_by_user(user_id)
        last_remarks_map = {item['track_id']: item['latest_remarks'] for item in last_remarks_data}

        # Retrieve overall track statistics and average scores for all tracks
        all_track_stats = self.recording_repo.get_all_track_statistics()
        all_avg_scores_by_track = self.recording_repo.get_average_track_scores()
        all_avg_scores = {stat['track_id']: stat['avg_score'] for stat in all_avg_scores_by_track}
        all_max_scores = {stat['track_id']: stat['max_score'] for stat in all_track_stats}

        # Build a map of track_id to earliest_recording_date
        earliest_recording_date_map = {
            stat['track_id']: stat['earliest_recording_date']
            for stat in user_track_stats
            if stat['earliest_recording_date']
        }

        # Iterate through tracks and recommend based on the new conditions
        for track_stat in all_track_stats:
            track_id = track_stat['track_id']

            # Check if the track is already recommended and get the first recommended date
            # Use the earliest recording date from the map, if available
            earliest_recording_date = earliest_recording_date_map.get(track_id)
            recommended_on_date = earliest_recording_date or datetime.now()

            # Check if the track is already recommended and get the first recommended date
            first_recommended_date = self.recording_repo.get_first_recommendation_date(
                user_id, track_id)

            if first_recommended_date is None:
                # Persist the recommendation date
                self.recording_repo.add_user_track_recommendation(user_id, track_id, recommended_on_date)
                first_recommended_date = recommended_on_date

            # Calculate days on track using first_recommended_date
            days_on_track = (datetime.now() - first_recommended_date).days

            if user_avg_scores.get(track_id, 0) < track_stat['recommendation_threshold_score']:
                recommended_track_info = {
                    'track_name': track_stat['name'],
                    'level': track_stat['level'],
                    'ordering_rank': track_stat['ordering_rank'],
                    'user_avg_score': round(user_avg_scores.get(track_id, 0), 2),
                    'user_max_score': round(user_max_scores.get(track_id, 0), 2),
                    'overall_avg_score': round(all_avg_scores.get(track_id, 0), 2),
                    'overall_max_score': round(all_max_scores.get(track_id, 0), 2),
                    'threshold_score': round(track_stat['recommendation_threshold_score'], 2),
                    'days_on_track': days_on_track,
                    'last_remark': last_remarks_map.get(track_id, "")
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
        track_recommendation_details = {}

        for user_id in user_ids:
            recommended_tracks = self.recommend_tracks(user_id)
            for track in recommended_tracks:
                track_name = track['track_name']
                if track_name not in track_recommendation_details:
                    track_recommendation_details[track_name] = {
                        'count': 0,
                        'level': track['level'],
                        'ordering_rank': track['ordering_rank']
                    }
                track_recommendation_details[track_name]['count'] += 1

        # Sort tracks by their recommendation frequency
        sorted_tracks = sorted(track_recommendation_details.items(), key=lambda x: x[1]['count'], reverse=True)

        # Get the top 5 most common tracks with their details
        top_common_tracks = sorted_tracks[:5]

        return [{'name': track[0], 'level': track[1]['level'], 'ordering_rank': track[1]['ordering_rank']}
                for track in top_common_tracks]

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
                unique_tracks.add((track['level'], track['ordering_rank'], user_id))

        # Sort tracks first by level (descending) then by ordering rank (descending)
        sorted_tracks = sorted(unique_tracks, key=lambda x: (-x[0], -x[1]))

        # Get the top 5 most advanced tracks
        top_advanced_tracks = sorted_tracks[:5]

        return [{'level': track[0], 'ordering_rank': track[1], 'user_id': track[2]}
                for track in top_advanced_tracks]

    def find_top_performer_in_group(self, group_id):
        # Get top advanced tracks along with user IDs
        top_advanced_tracks = self.get_top_advanced_tracks_for_group(group_id)

        # Create a dictionary to count the frequency of advanced tracks per user
        user_advanced_track_count = {}
        for track in top_advanced_tracks:
            user_id = track['user_id']
            user_advanced_track_count[user_id] = user_advanced_track_count.get(user_id, 0) + 1

        # Find the user with the most advanced tracks
        top_performer_id = None
        max_count = 0
        for user_id, count in user_advanced_track_count.items():
            if count > max_count:
                max_count = count
                top_performer_id = user_id

        # Return the top performer's user ID
        return top_performer_id
