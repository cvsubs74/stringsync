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

        # Separate tracks into different levels
        level_tracks = {}
        for track_stat in all_track_stats:
            track_id = track_stat['track_id']
            level = track_stat['level']  # Extract track level from the result
            if level not in level_tracks:
                level_tracks[level] = []
            level_tracks[level].append(track_stat)

        # Sort tracks within each level based on user's score in ascending order
        for level, tracks in level_tracks.items():
            tracks.sort(key=lambda x: x['avg_score'])

        # Determine the maximum number of tracks to recommend per level
        max_tracks_per_level = 10  # You can adjust this as needed

        # Calculate the user's overall average score
        overall_avg_score = sum(track_stat['avg_score'] for track_stat in user_track_stats) / len(user_track_stats)

        # Iterate through levels and recommend tracks
        for level, tracks in level_tracks.items():
            # Calculate the average score for tracks in this level
            level_avg_score = sum(track_stat['avg_score'] for track_stat in tracks) / len(tracks)

            # Check if the user has already worked on all tracks in this level
            if len(tracks) == len([t for t in tracks if t['name'] in user_track_stats]):
                continue  # Skip this level as the user has already worked on all tracks

            # Get a list of unrecorded tracks in the same level
            unrecorded_tracks_in_level = [track['name'] for track in tracks if track['name'] not in user_track_stats]
            # Recommend track IDs from this level
            num_to_recommend = min(max_tracks_per_level, len(unrecorded_tracks_in_level))
            recommended_tracks.extend(unrecorded_tracks_in_level[:num_to_recommend])

            # Check if the user's average score is below the overall average
            if level_avg_score < overall_avg_score:
                # Recommend additional track IDs from this level
                num_to_recommend_extra = max_tracks_per_level - num_to_recommend
                recommended_tracks.extend(
                    unrecorded_tracks_in_level[num_to_recommend:num_to_recommend + num_to_recommend_extra])

        # Finally, recommend the top 5 tracks from the combined list of all levels
        recommended_tracks = recommended_tracks[:5]  # Recommend the top 5 from the final list

        return recommended_tracks
