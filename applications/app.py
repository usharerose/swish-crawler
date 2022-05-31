from datetime import date
from http import HTTPStatus

import requests


SCOREBOARD_URL = 'https://stats.nba.com/stats/scoreboardv3?GameDate={date}&LeagueID={league_id}'
NBA_LEAGUE_ID = '00'
DATE_FORMAT_PATTERN = '%Y-%m-%d'
TIMEOUT = 10


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
        raise
    return resp
