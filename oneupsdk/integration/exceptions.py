
import typing as _typing

import requests as _requests


class OneUpAPIException(Exception):

    def __init__(self, **kv):

        # Store all keyword args as internal metadata

        self.data = kv

        # Build the message

        self.message = ""

        if "msg" in self.data:
            self.message += kv['msg'] + "\n\n"
            del self.data["msg"]

        if len(self.data) > 0:
            self.message += ("Additional information:\n\n" +
                             "\n".join("  %s: %r" % x for x in kv.items()))

        # Call parent class constructor

        super(OneUpAPIException, self).__init__(self.message)


def handle_api_error(res):
    # type: (_requests.Response) -> _typing.Optional[_typing.Dict]

    # Exit on malformed argument or successful status code
    if res is None or res.status_code == 200:
        return

    # Assume there is an error and build information dictionary
    data = {
        "url": res.url,
        "http_code": res.status_code,
        "http_msg": res.content.decode(),
        "json_msg": None,
    }

    # data["username"] = username or ROSTER_USER
    # data["src_exception"] = err

    # Try to get JSON error.
    try:
        data["json_msg"] = res.json()

        # No need for plain version if successful
        del data["http_msg"]
    except ValueError:
        # Could not parse, so it's probably not JSON.
        pass

    if res.status_code == 401 and "json_msg" in data and data["json_msg"]["message"] == "Missing token":
        raise OneUpAPIException(
            msg="Authentication token was not generated.",
            **data,
        )

    # Detecting a very specific kind of error to provide helpful message
    if res.status_code == 500 and "http_msg" in data:
        if "<title>DoesNotExist" in data["http_msg"]:
            if "CourseConfigParams matching query does not exist." in data["http_msg"]:
                raise OneUpAPIException(
                    msg="Likely no course has been selected yet, use `set_active_course()` before any activity.",
                    **data,
                )

    raise OneUpAPIException(
        msg="Unknown HTTP error, see source exception headers.",
        **data)
