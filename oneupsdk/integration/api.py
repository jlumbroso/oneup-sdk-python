
from __future__ import absolute_import

import json as _json
import typing as _typing

import bs4 as _bs4
import requests as _requests
import six as _six

import oneupsdk.integration
import oneupsdk.integration.exceptions


BASE_URL = "https://oneup.wssu.edu"
LOGIN_URL = _six.moves.urllib.parse.urljoin(BASE_URL, "login")


last_cookies = None


def get_auth_cookies(username=None, password=None, **kwargs):
    # type: (_typing.Optional[str], _typing.Optional[str], _typing.Dict) -> _typing.Optional[dict]
    global last_cookies

    session = _requests.sessions.session()

    # Step 1: Get a CSRF token and start the OneUp session

    try:
        response = session.get(LOGIN_URL)
    except _requests.RequestException:
        response = None

    if response is None or not response.ok:
        return

    soup = _bs4.BeautifulSoup(response.content, features="html.parser")
    csrf_token = soup.find("input", {"name": "csrfmiddlewaretoken"}).get("value")

    # Step 2: Login with credentials and get signed token

    url = LOGIN_URL

    try:
        response = session.post(
            url=url,
            allow_redirects=False,
            headers={
                # Cache liveness stuff
                "Connection": "keep-alive",
                "Pragma": "no-cache",
                "Cache-Control": "no-cache",

                # Format stuff
                "Accept": "text/html,application/xhtml+xml,application/xml",
                "Content-Type": "application/x-www-form-urlencoded; charset=utf-8",

                # CSRF security stuff
                "Cookie": "csrftoken={}".format(csrf_token),
                "Referer": LOGIN_URL,
                "Origin": BASE_URL,
                "Upgrade-Insecure-Requests": "1",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-User": "?1",
                "Sec-Fetch-Site": "same-origin",

                "User-Agent": ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) "
                               "AppleWebKit/537.36 (KHTML, like Gecko) "
                               "Chrome/77.0.3865.120 Safari/537.36"),
            },
            data={
                "csrfmiddlewaretoken": csrf_token,
                "next": "/oneUp/courses",
                "username": username or oneupsdk.integration.config["username"],
                "password": password or oneupsdk.integration.config["password"],
                "login": "Login",
            },
        )
    except _requests.RequestException:
        return

    # Step 3: Inspect cookies to make sure we are logged in
    if response.status_code in [200, 302]:
        cookies = response.cookies
        cookies_string = "; ".join(
            list(map(lambda cookie: "{name}={value}".format(
                name=cookie.name, value=cookie.value),
                     cookies)))

        if "sessionid" in cookies and "csrftoken" in cookies:
            data = {
                "sessionid": cookies["sessionid"],
                "csrftoken": cookies["csrftoken"],
                "cookies": cookies,
                "cookies_string": cookies_string
            }
            last_cookies = data
            return data


def request(endpoint=None, url=None, data=None, json=None, **kwargs):
    # type: (_typing.Optional[str], _typing.Optional[str], _typing.Optional[_typing.Union[str, dict]], _typing.Optional[dict], dict) -> _requests.Response
    """
    Make a request directly to the Ed platform's API.
    """

    if last_cookies is None:
        get_auth_cookies(**kwargs)

    # If only endpoint was passed, augment with base URL
    if endpoint is not None:
        url = _six.moves.urllib.parse.urljoin(
            base=BASE_URL,
            url=endpoint,
        )

    headers = {
        # Cache liveness stuff
        "Connection": "keep-alive",
        "Pragma": "no-cache",
        "Cache-Control": "no-cache",

        # Format stuff
        "Accept": "text/html,application/xhtml+xml,application/xml",
        "Content-Type": "application/x-www-form-urlencoded; charset=utf-8",

        # Authentication
        "Cookie": last_cookies.get("cookies_string"),

        # CSRF security stuff
        "Referer": LOGIN_URL,
        "Origin": BASE_URL,
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-User": "?1",
        "Sec-Fetch-Site": "same-origin",

        "User-Agent": ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/77.0.3865.120 Safari/537.36"),
    }

    try:

        if data is None and json is None:
            res = _requests.get(
                url=url,
                headers=headers,
            )

        elif json is not None:
            res = _requests.post(
                url=url,
                headers=headers,
                json=json,
            )

        else:
            res = _requests.post(
                url=url,
                headers=headers,
                data=data,
            )

        if res.status_code == 301 and url[-1] != "/":
            return request(url="{}/".format(url))

    except _requests.RequestException as exc:
        raise

    oneupsdk.integration.exceptions.handle_api_error(res)

    return res
