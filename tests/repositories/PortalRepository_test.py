import pytest
from unittest.mock import MagicMock, call
import pytz
from datetime import datetime

from repositories.PortalRepository import PortalRepository


class TestPortalRepository:

    @pytest.fixture
    def mock_connection(self):
        mock_conn = MagicMock()
        yield mock_conn
        # Teardown: reset the mock after the test
        mock_conn.reset_mock()

    @pytest.fixture
    def portal_repo(self, mock_connection):
        return PortalRepository(mock_connection)

    def test_list_tutor_assignments(self, portal_repo, mock_connection):
        # Arrange
        mock_cursor = mock_connection.cursor.return_value
        mock_cursor.fetchall.return_value = [
            (1, 'John Doe', 'johndoe', 101, 'School A', 'Description A')
        ]

        # Act
        result = portal_repo.list_tutor_assignments(123)

        # Assert
        expected_result = [
            {
                'tutor_id': 1,
                'tutor_name': 'John Doe',
                'tutor_username': 'johndoe',
                'school_id': 101,
                'school_name': 'School A',
                'school_description': 'Description A'
            }
        ]
        assert result == expected_result
        mock_cursor.execute.assert_called_once()

    def test_get_users_by_tenant_id_and_type(self, portal_repo, mock_connection):
        # Arrange
        mock_cursor = mock_connection.cursor.return_value
        mock_cursor.fetchall.return_value = [
            (2, 'Jane Doe', 'janedoe', 'jane@example.com')
        ]

        # Act
        result = portal_repo.get_users_by_tenant_id_and_type(123, 'teacher')

        # Assert
        expected_result = [
            {'id': 2, 'name': 'Jane Doe', 'username': 'janedoe', 'email': 'jane@example.com'}
        ]
        assert result == expected_result
        mock_cursor.execute.assert_called_once()

    def test_list_tracks(self, portal_repo, mock_connection):
        # Arrange
        mock_cursor = mock_connection.cursor.return_value
        mock_cursor.fetchall.return_value = [
            ('Track1', 'Ragam1', 'Level1', 'Description1', 'Path1'),
            ('Track2', 'Ragam2', 'Level2', 'Description2', 'Path2')
        ]

        # Act
        result = portal_repo.list_tracks()

        # Assert
        expected_result = [
            {
                "track_name": 'Track1',
                "ragam": 'Ragam1',
                "level": 'Level1',
                "description": 'Description1',
                "track_path": 'Path1'
            },
            {
                "track_name": 'Track2',
                "ragam": 'Ragam2',
                "level": 'Level2',
                "description": 'Description2',
                "track_path": 'Path2'
            }
        ]
        assert result == expected_result
        mock_cursor.execute.assert_called_once()

    def test_get_unremarked_submissions(self, portal_repo, mock_connection):
        # Arrange
        mock_cursor = mock_connection.cursor.return_value
        mock_cursor.fetchall.return_value = [
            {"user_name": "Alice", "group_name": "Group1", "track_names": "TrackA, TrackB"}
        ]

        # Act
        result = portal_repo.get_unremarked_submissions()

        # Assert
        expected_result = [
            {"user_name": "Alice", "group_name": "Group1", "track_names": "TrackA, TrackB"}
        ]
        assert result == expected_result
        mock_cursor.execute.assert_called_once()

    def test_get_unremarked_recordings(self, portal_repo, mock_connection):
        # Arrange
        mock_cursor = mock_connection.cursor.return_value
        mock_cursor.fetchall.return_value = [
            {
                "id": 1, "blob_name": "blob1", "blob_url": "url1",
                "track_name": "Track1", "track_path": "Path1",
                "timestamp": "2023-01-01", "duration": 60,
                "track_id": 101, "score": 90, "analysis": "Analysis1",
                "remarks": None, "user_id": 201, "user_name": "Bob"
            }
        ]
        group_id = 10
        user_id = 20
        track_id = 30

        # Act
        result = portal_repo.get_recordings(group_id, user_id, track_id)

        # Assert
        expected_result = [
            {
                "id": 1, "blob_name": "blob1", "blob_url": "url1",
                "track_name": "Track1", "track_path": "Path1",
                "timestamp": "2023-01-01", "duration": 60,
                "track_id": 101, "score": 90, "analysis": "Analysis1",
                "remarks": None, "user_id": 201, "user_name": "Bob"
            }
        ]
        assert result == expected_result
        assert mock_cursor.execute.call_args[0][1] == (group_id, user_id, track_id)

    def test_get_submissions_by_user_id(self, portal_repo, mock_connection):
        # Arrange
        mock_cursor = mock_connection.cursor.return_value
        local_tz = pytz.timezone('America/Los_Angeles')
        timestamp = datetime(2023, 1, 1, 12, 0)
        utc_timestamp = pytz.utc.localize(timestamp)
        mock_cursor.fetchall.return_value = [
            {
                "timestamp": timestamp,
                "track_name": "Track1",
                "recording_audio_url": "url1",
                "track_audio_url": "path1",
                "system_remarks": "Remark1",
                "teacher_remarks": "Remark2",
                "score": 85,
                "track_id": 100,
                "recording_id": 200
            }
        ]
        user_id = 123
        limit = 20
        timezone = 'America/Los_Angeles'

        # Act
        result = portal_repo.get_submissions_by_user_id(user_id, limit, timezone)

        # Assert
        expected_query_params = (user_id, limit)
        assert mock_cursor.execute.call_args[0][1] == expected_query_params

        # Assert
        expected_result = [
            {
                "timestamp": utc_timestamp.astimezone(local_tz),
                "track_name": "Track1",
                "recording_audio_url": "url1",
                "track_audio_url": "path1",
                "system_remarks": "Remark1",
                "teacher_remarks": "Remark2",
                "score": 85,
                "track_id": 100,
                "recording_id": 200
            }
        ]
        assert result == expected_result

    def test_get_badges_grouped_by_tracks(self, portal_repo, mock_connection):
        # Arrange
        mock_cursor = mock_connection.cursor.return_value
        mock_cursor.fetchall.return_value = [
            {"track_id": 101, "badges": "Badge1,Badge2"},
            {"track_id": 102, "badges": "Badge3,Badge4"}
        ]
        user_id = 123

        # Act
        result = portal_repo.get_badges_grouped_by_tracks(user_id)

        # Assert
        expected_result = [
            {'track_id': 101, 'badges': ['Badge1', 'Badge2']},
            {'track_id': 102, 'badges': ['Badge3', 'Badge4']}
        ]
        assert result == expected_result
        assert mock_cursor.execute.call_args[0][1] == (user_id,)
