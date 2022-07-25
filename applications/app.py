from datetime import date
from http import HTTPStatus
import io
import logging

from minio import Minio, S3Error
import requests


logger = logging.getLogger(__name__)


SCOREBOARD_URL = 'https://stats.nba.com/stats/scoreboardv3?GameDate={date}&LeagueID={league_id}'
NBA_LEAGUE_ID = '00'
DATE_FORMAT_PATTERN = '%Y-%m-%d'
TIMEOUT = 10


CONTENT_TYPE_JSON = 'application/json'


S3_HOST = 'minio'
S3_PORT = 9000
S3_ENDPOINT = '{host}:{port}'.format(host=S3_HOST, port=S3_PORT)
S3_ACCESS_KEY = 'minioadmin'
S3_SECRET_KEY = 'minioadmin'


BUCKET_NAME_SCOREBOARD = 'scoreboard'
OBJECT_NAME_FORMAT_SCOREBOARD = '/nba/{year:04d}/{month:02d}/{date_str}.json'


S3_CLIENT = Minio(endpoint=S3_ENDPOINT,
                  access_key=S3_ACCESS_KEY, secret_key=S3_SECRET_KEY,
                  secure=False)


def fetch_and_load_scoreboard(a_date, overwritten=False):
    # When not overwritten,
    # would check the existence of raw data to decide whether skip fetching or not
    if not overwritten:
        obj_path = OBJECT_NAME_FORMAT_SCOREBOARD.format(year=a_date.year,
                                                        month=a_date.month,
                                                        date_str=a_date.strftime(DATE_FORMAT_PATTERN))
        try:
            S3_CLIENT.stat_object(BUCKET_NAME_SCOREBOARD, obj_path)
            logger.info('scoreboard - {date} - success - exist in local')
            return
        except S3Error:
            pass

    resp = fetch_nba_daily_scoreboard(a_date)
    upload_nba_daily_scoreboard_to_s3(a_date, resp)
    logger.info('scoreboard - {date} - success - from remote')
    return


def fetch_nba_daily_scoreboard(a_date: date):
    """
    :param a_date: datetime.date as target date of data
    :return: HTTP response
    """
    target_url = SCOREBOARD_URL.format(date=a_date.strftime(DATE_FORMAT_PATTERN),
                                       league_id=NBA_LEAGUE_ID)
    req_headers = {
        'host': 'stats.nba.com',
        'origin': 'https://www.nba.com',
        'referer': 'https://www.nba.com/',
        'accept-language': 'en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7',
        'user-agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 12_2 like Mac OS X) '
                      'AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148'
    }

    s = requests.session()
    resp = s.get(url=target_url, headers=req_headers, timeout=TIMEOUT)

    if resp.status_code != HTTPStatus.OK:
        # TODO: define an exception
        raise Exception
    return resp


def upload_nba_daily_scoreboard_to_s3(a_date, response):
    content = response.content
    data = io.BytesIO(content)
    length = len(content)
    obj_path = OBJECT_NAME_FORMAT_SCOREBOARD.format(year=a_date.year,
                                                    month=a_date.month,
                                                    date_str=a_date.strftime(DATE_FORMAT_PATTERN))
    try:
        S3_CLIENT.put_object(BUCKET_NAME_SCOREBOARD, obj_path,
                             data, length, content_type=CONTENT_TYPE_JSON)
    except S3Error:
        # TODO: define an exception
        raise Exception
