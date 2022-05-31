import datetime
from http import HTTPStatus
import json
from unittest import TestCase
from unittest.mock import patch

from applications.app import fetch_nba_daily_scoreboard
from .mock_data import FAILED_CONTENT, SUCCESS_CONTENT_JSON


class MockResponse(object):

    def __init__(self, status_code, content):
        self._status_code = status_code
        self._content = content

    @property
    def status_code(self):
        return self._status_code

    @property
    def content(self):
        return self._content


def mocked_daily_scoreboard_request(status_code):
    if status_code == HTTPStatus.OK:
        content = json.dumps(SUCCESS_CONTENT_JSON).encode('utf-8')
    else:
        content = FAILED_CONTENT
    return MockResponse(status_code, content)


class NBADailyScoreboardTestCases(TestCase):

    @patch('applications.app.requests.session')
    def test_fetch_nba_daily_scoreboard(self, mock_session):
        mock_session.return_value.get.return_value = mocked_daily_scoreboard_request(200)
        sample_date = datetime.date(2022, 5, 22)
        resp = fetch_nba_daily_scoreboard(sample_date)
        self.assertEqual(resp.status_code, HTTPStatus.OK.value)

    @patch('applications.app.requests.session')
    def test_fetch_nba_daily_scoreboard_failed(self, mock_session):
        mock_session.return_value.get.return_value = mocked_daily_scoreboard_request(500)
        sample_date = datetime.date(2022, 5, 21)
        with self.assertRaises(Exception):
            fetch_nba_daily_scoreboard(sample_date)
