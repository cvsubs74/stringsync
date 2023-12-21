import json


from enums.ActivityType import ActivityType


class NotificationsDashboard:
    def __init__(self, user_session_repo, portal_repo):
        self.user_session_repo = user_session_repo
        self.portal_repo = portal_repo

    def notify(self, user_id, group_id, org_id, last_activity_time):
        # Fetch new notifications since the last activity time
        notifications = self.portal_repo.get_notifications(
            user_id, group_id, org_id, last_activity_time)
        # Display each notification
        messages = []
        for notification in notifications:
            metadata = json.loads(notification.get('metadata', '{}'))
            # Skip notifications that do not belong to the current user or group
            if 'user_id' in metadata and metadata['user_id'] != user_id:
                continue
            if 'group_id' in metadata and metadata['group_id'] != group_id:
                continue

            # Get the user-friendly message and icon for the activity type
            activity_type = notification['activity_type']
            activity_message = ActivityType.from_value(activity_type).message
            activity_icon = ActivityType.from_value(activity_type).icon

            # Construct the display message
            message = f"{activity_icon} {notification['user_name']} {activity_message}"

            # If the activity type is PLAY_TRACK or CREATE_TRACK, append the track name
            if activity_type in ('Play Track', 'Create Track') and 'track_name' in metadata:
                message += f" - {metadata['track_name']}"

            messages.append(message)

        return messages





