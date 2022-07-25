import datetime
from http import HTTPStatus
import json
from unittest import TestCase
from unittest.mock import patch

from applications.app import (
    S3_CLIENT,
    BUCKET_NAME_SCOREBOARD,
    DATE_FORMAT_PATTERN,
    OBJECT_NAME_FORMAT_SCOREBOARD,
    fetch_and_load_scoreboard,
    fetch_nba_daily_scoreboard,
    upload_nba_daily_scoreboard_to_s3
)


with open('tests/data/scoreboard/2021-12-23.json', 'r') as f:
    SUCCESS_CONTENT_DICT = json.load(f)
FAILED_CONTENT = b'error happened'


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
        content = json.dumps(SUCCESS_CONTENT_DICT).encode('utf-8')
    else:
        content = FAILED_CONTENT
    return MockResponse(status_code, content)


class NBADailyScoreboardTestCases(TestCase):

    def setUp(self):
        self._clean_bucket()
        S3_CLIENT.make_bucket(BUCKET_NAME_SCOREBOARD)

    def tearDown(self):
        self._clean_bucket()

    @staticmethod
    def _clean_bucket():
        existence = S3_CLIENT.bucket_exists(BUCKET_NAME_SCOREBOARD)
        if not existence:
            return
        objs = S3_CLIENT.list_objects(BUCKET_NAME_SCOREBOARD, recursive=True)
        for obj in objs:
            S3_CLIENT.remove_object(BUCKET_NAME_SCOREBOARD, obj.object_name)
        S3_CLIENT.remove_bucket(BUCKET_NAME_SCOREBOARD)

    @patch('applications.app.requests.session')
    def test_fetch_nba_daily_scoreboard(self, mock_session):
        mock_session.return_value.get.return_value = mocked_daily_scoreboard_request(200)
        sample_date = datetime.date(2022, 5, 22)
        resp = fetch_nba_daily_scoreboard(sample_date)
        self.assertEqual(resp.status_code, HTTPStatus.OK)

    @patch('applications.app.requests.session')
    def test_fetch_nba_daily_scoreboard_failed(self, mock_session):
        mock_session.return_value.get.return_value = mocked_daily_scoreboard_request(500)
        sample_date = datetime.date(2022, 5, 21)
        with self.assertRaises(Exception):
            fetch_nba_daily_scoreboard(sample_date)

    def test_upload_nba_daily_scoreboard_to_s3(self):
        sample_date = datetime.date(2022, 6, 20)
        sample_resp = mocked_daily_scoreboard_request(200)
        upload_nba_daily_scoreboard_to_s3(sample_date, sample_resp)

        try:
            response = S3_CLIENT.get_object(
                BUCKET_NAME_SCOREBOARD,
                OBJECT_NAME_FORMAT_SCOREBOARD.format(year=sample_date.year,
                                                     month=sample_date.month,
                                                     date_str=sample_date.strftime(DATE_FORMAT_PATTERN)))
            data = response.data
        finally:
            response.close()  # NOQA
            response.release_conn()

        actual_data = json.loads(data.decode('utf-8'))
        self.assertDictEqual(actual_data, SUCCESS_CONTENT_DICT)

    def test_upload_nba_daily_scoreboard_to_nonexistent_bucket(self):
        self._clean_bucket()
        sample_date = datetime.date(2022, 6, 20)
        sample_resp = mocked_daily_scoreboard_request(200)
        with self.assertRaises(Exception):
            upload_nba_daily_scoreboard_to_s3(sample_date, sample_resp)

    def test_fetch_and_load_not_overwritten_with_existence(self):
        # prepare existing data
        _existing_date = datetime.date(2022, 5, 29)
        _legacy_data_resp = mocked_daily_scoreboard_request(200)
        upload_nba_daily_scoreboard_to_s3(_existing_date, _legacy_data_resp)

        sample_date = datetime.date(2022, 5, 29)
        fetch_and_load_scoreboard(sample_date)

        try:
            response = S3_CLIENT.get_object(
                BUCKET_NAME_SCOREBOARD,
                OBJECT_NAME_FORMAT_SCOREBOARD.format(year=sample_date.year,
                                                     month=sample_date.month,
                                                     date_str=sample_date.strftime(DATE_FORMAT_PATTERN)))
            data = response.data
        finally:
            response.close()  # NOQA
            response.release_conn()
        actual_data = json.loads(data.decode('utf-8'))
        expected_data = SUCCESS_CONTENT_DICT
        self.assertDictEqual(actual_data, expected_data)

    @patch('applications.app.requests.session')
    def test_fetch_and_load_overwritten(self, mock_session):

        # prepare existing data
        _existing_date = datetime.date(2022, 5, 29)
        _legacy_data_resp = mocked_daily_scoreboard_request(200)
        upload_nba_daily_scoreboard_to_s3(_existing_date, _legacy_data_resp)

        try:
            response_before_overwritten = S3_CLIENT.get_object(
                BUCKET_NAME_SCOREBOARD,
                OBJECT_NAME_FORMAT_SCOREBOARD.format(year=_existing_date.year,
                                                     month=_existing_date.month,
                                                     date_str=_existing_date.strftime(DATE_FORMAT_PATTERN)))
            data_before_overwritten = response_before_overwritten.data
        finally:
            response_before_overwritten.close()  # NOQA
            response_before_overwritten.release_conn()
        actual_data_before_overwritten = json.loads(data_before_overwritten.decode('utf-8'))
        expected_data_before_overwritten = SUCCESS_CONTENT_DICT
        self.assertDictEqual(actual_data_before_overwritten,
                             expected_data_before_overwritten)

        sample_date = datetime.date(2022, 5, 29)
        with open('tests/data/scoreboard/2022-05-29.json', 'r') as fp:
            latest_data = json.load(fp)
            mock_session.return_value.get.return_value = MockResponse(HTTPStatus.OK.value,
                                                                      json.dumps(latest_data).encode('utf-8'))
        fetch_and_load_scoreboard(sample_date, True)

        try:
            response = S3_CLIENT.get_object(
                BUCKET_NAME_SCOREBOARD,
                OBJECT_NAME_FORMAT_SCOREBOARD.format(year=sample_date.year,
                                                     month=sample_date.month,
                                                     date_str=sample_date.strftime(DATE_FORMAT_PATTERN)))
            data = response.data
        finally:
            response.close()  # NOQA
            response.release_conn()
        actual_data = json.loads(data.decode('utf-8'))
        expected_data = latest_data
        self.assertDictEqual(actual_data, expected_data)
