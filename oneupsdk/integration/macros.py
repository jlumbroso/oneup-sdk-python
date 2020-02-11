
import collections as _collections
import re as _re
import typing as _typing

import bs4 as _bs4

import oneupsdk.integration.api
import oneupsdk.integration.exceptions
import oneupsdk.integration.util


###############################################################################
# COURSE METHODS
###############################################################################

def get_instructor_courses():
    # type: () -> list
    """
    Returns a list of all courses that the logged in instructor has access to.
    """
    r = oneupsdk.integration.api.request("/oneUp/instructors/instructorHome")

    if r.status_code != 200:
        return []

    s = _bs4.BeautifulSoup(r.content)
    t = oneupsdk.integration.util.find_table(s, header_query="Your Courses")
    if t is None:
        return []

    rows = t.find_all("tr")

    courses = []
    for row in rows:
        try:
            course_caption = row.find("td").text
            course_id = int(row.find("input", { "name": "courseID" })["value"])
            courses.append((course_id, course_caption))
        except ValueError:
            continue
        except:
            continue

    return sorted(courses)


def set_active_course(course_id):
    # type: (int) -> bool
    """
    Switch the active OneUp Learning course that the API is operating on.
    """

    r = oneupsdk.integration.api.request(
        endpoint="/oneUp/setCourse",
        data={
            "courseID": course_id,
            "csrfmiddlewaretoken": oneupsdk.integration.api.get_csrf_token()
        })

    return r.status_code == 200


def get_active_course():
    # type: () -> _typing.Optional[int]
    """
    Returns the actively selected course, if any.
    """
    try:
        r = oneupsdk.integration.api.request("/oneUp/instructors/instructorCourseHome")
    except oneupsdk.integration.exceptions.OneUpAPIException as exc:
        # This happens when no course is selected
        if exc.data.get("http_code") == 500:
            return

        # Unknown error
        raise

    if r.status_code != 200:
        return

    c = r.content.decode()
    m = _re.search(r"course_id\s*=\s*'([^';]*)'", c)
    if m is None:
        return

    try:
        i = int(m.group(1).strip("'\""))
    except ValueError:
        return

    return i

