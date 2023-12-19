import os
import datetime

from components.TrackRecommender import TrackRecommender
from enums.Badges import UserBadges, TrackBadges
from enums.TimeFrame import TimeFrame
from repositories.PortalRepository import PortalRepository
from repositories.RecordingRepository import RecordingRepository
from repositories.SettingsRepository import SettingsRepository
from repositories.StorageRepository import StorageRepository
from repositories.UserAchievementRepository import UserAchievementRepository
from repositories.UserPracticeLogRepository import UserPracticeLogRepository


class BadgeAwarder:
    def __init__(self, settings_repo: SettingsRepository,
                 recording_repo: RecordingRepository,
                 user_achievement_repo: UserAchievementRepository,
                 practice_log_repo: UserPracticeLogRepository,
                 portal_repo: PortalRepository,
                 storage_repo: StorageRepository,
                 track_recommender: TrackRecommender):
        self.settings_repo = settings_repo
        self.recording_repo = recording_repo
        self.user_achievement_repo = user_achievement_repo
        self.practice_log_repo = practice_log_repo
        self.portal_repo = portal_repo
        self.storage_repo = storage_repo
        self.track_recommender = track_recommender

    def auto_award_badge(self, user_id, practice_date):
        badge_awarded = False

        badge = self.practice_log_repo.get_streak(user_id, practice_date)
        if badge:
            badge_awarded, _ = self.user_achievement_repo.award_user_badge(
                user_id, badge, practice_date)

        return badge_awarded

    def auto_award_badges(self, group_id, timeframe=TimeFrame.PREVIOUS_WEEK):
        print(group_id, timeframe.get_date_range())
        # Retrieve weekly stats for all users in the group within the date range
        stats = self.portal_repo.get_group_stats(group_id, timeframe)
        # No data for the previous week
        if len(stats) == 0:
            return False
        # Iterate through each stat and check if the threshold is met
        for stat in stats:
            # Check if the category from stat is a valid badge and has a threshold
            badge_category = stat['category']
            if badge_category and stat['value'] >= badge_category.threshold:
                # Award the weekly badges to the students if they meet the threshold
                self.user_achievement_repo.award_user_badge_by_time_frame(
                    stat['student_id'], badge_category, timeframe, stat['value'])
        # Trailblazer badge award
        top_performer_id = self.track_recommender.find_top_performer_in_group(group_id)
        self.user_achievement_repo.award_user_badge_by_time_frame(
            top_performer_id, UserBadges.WEEKLY_TRAILBLAZER, timeframe, 0)
        return True

    def award_track_badge(self, org_id, user_id, recording_id, badge: TrackBadges,
                          timestamp=datetime.datetime.now()):
        badge_awarded, _ = self.user_achievement_repo.award_track_badge(
            user_id, recording_id, badge, timestamp)
        return badge_awarded

    def award_user_badge(self, org_id, user_id, badge: UserBadges,
                         timestamp=datetime.datetime.now()):
        badge_awarded, _ = self.user_achievement_repo.award_user_badge(
            user_id, badge, timestamp)
        return badge_awarded

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
