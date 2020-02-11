
import collections as _collections
import re as _re
import typing as _typing

import bs4 as _bs4

import oneupsdk.integration.api
import oneupsdk.integration.exceptions
import oneupsdk.integration.util


ONEUP_STUDENT_ATTRIBUTES_CAPTION = [
    ("Avatar", "avatar_link"),
    ("First Name", "first"),
    ("Last Name", "last"),
    ("Email", "email"),
    ("Last Action", "last_action")
]

ONEUP_STUDENT_ATTRIBUTES_FORM = [
    ("firstname", "first"),
    ("lastname", "last"),
    ("email", "email"),
    ("pword", "password"),
    ("uname", "id")
]

ONEUP_ACTIVITY_ATTRIBUTES_FORM = [
    ("activityID", "id"),
    ("activityName", "name"),
    ("points", "points"),
    ("startTime", "start_time"),
    ("endTime", "end_time"),
    ("deadLine", "deadline"),
    ("isGraded", "is_graded"),
    ("fileUpload", "file_upload"),
    ("attempts", "attempts"),
    ("actFile", "file"),
    ("description", "description"),
    ("instructorNotes", "instructor_notes")
]

ONEUP_STUDENT_ATTRIBUTE_CAPTION_DICT = dict(ONEUP_STUDENT_ATTRIBUTES_CAPTION)
ONEUP_STUDENT_ATTRIBUTES_FORM_DICT = dict(ONEUP_STUDENT_ATTRIBUTES_FORM)
ONEUP_ACTIVITY_ATTRIBUTES_FORM_DICT = dict(ONEUP_STUDENT_ATTRIBUTES_FORM)


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

    s = _bs4.BeautifulSoup(r.content, features="html.parser")
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


###############################################################################
# STUDENT METHODS
###############################################################################

def get_enrolled_students():
    # type: () -> _typing.List[dict]
    """
    Provide a list of students currently enrolled in the active course.
    """

    r = oneupsdk.integration.api.request("/oneUp/instructors/createStudentList")
    if r.status_code != 200:
        return list()

    s = _bs4.BeautifulSoup(r.content, features="html.parser")
    t = oneupsdk.integration.util.find_table(s, "Avatar")
    if t is None:
        return list()

    rows = t.find_all("tr")
    if rows is None or len(rows) == 0:
        return list()

    headers = list(map(
        lambda obj: ONEUP_STUDENT_ATTRIBUTE_CAPTION_DICT.get(obj.text),
        rows[0].find_all("th")))

    rows = rows[1:]

    def convert_column(c):
        if c is None:
            return ""
        if c.text != "":
            return c.text
        try:
            return c.find("img")["src"]
        except:
            return ""

    students = []
    for row in rows:
        columns = list(map(convert_column, row.find_all("td")))[:-1]

        if len(columns) != len(headers):
            continue

        try:
            user_id = row.find("input", { "name": "userID" }).get("value")
        except:
            continue

        user_record = dict(zip(headers, columns))
        user_record["id"] = user_id

        students.append(user_record)

    return students


def get_student_by_id(user_id):
    # type: (str) -> _typing.Optional[dict]
    """
    Returns a student with the provided user ID, if such a student exists in the
    active course.
    """

    r = oneupsdk.integration.api.request(
        "/oneUp/instructors/createStudentView?userID={}".format(user_id))

    if r.status_code != 200:
        return

    s = _bs4.BeautifulSoup(r.content, features="html.parser")

    obj_form = s.find("form", { "id": "createStudentForm" })
    if obj_form is None:
        return

    lst_fields = list(
        map(lambda field: (field.get("name"), field.get("value")),
            obj_form.find_all("input")))

    student_info = {}
    for (name, value) in lst_fields:
        if name in ONEUP_STUDENT_ATTRIBUTES_FORM_DICT:
            internal_name = ONEUP_STUDENT_ATTRIBUTES_FORM_DICT.get(name)
            student_info[internal_name] = value

    return student_info


def add_student(email, password, first=None, last=None, user_id=None):
    # type: (str, str, _typing.Optional[str], _typing.Optional[str], _typing.Optional[str]) -> bool
    """
    Creates a new student and enrolls them in the active course.
    """
    if email is None or email == "":
        return False

    if password is None or password == "":
        return False

    r = oneupsdk.integration.api.request(
        endpoint="/oneUp/instructors/createStudentView",
        data={
            "csrfmiddlewaretoken": oneupsdk.integration.api.get_csrf_token(),

            "firstname": first or "",
            "lastname": last or "",
            "email": email,
            "uname": user_id or email,
            "pword": password,
            "pword2": password,
        })

    return r.status_code == 200


def delete_student(user_id):
    # type: (str) -> bool
    """
    Unenrolls a student from the active course.
    """
    r = oneupsdk.integration.api.request(
        endpoint="/oneUp/instructors/deleteStudent",
        data={
            "userID": user_id,
            "csrfmiddlewaretoken": oneupsdk.integration.api.get_csrf_token()
        })

    return r.status_code == 200


def modify_student(user_id, email=None, password=None, first=None, last=None, new_user_id=None):
    """
    Creates a new student and enrolls them in the active course.
    """
    user_info = get_student_by_id(user_id=user_id)

    if user_info is None:
        return False

    payload = {
        "userID": user_info.get("id"),
        "sUsernamePrev": user_info.get("id"),
        "sEmailPrev": user_info.get("email"),

        # Existing fields
        "firstname": user_info.get("first"),
        "lastname": user_info.get("last"),
        "email": user_info.get("email"),
        "uname": user_info.get("id"),
        "pword": user_info.get("password"),
        "pword2": "",
    }

    # NOTE: the names of the dict entries come from the FORM

    if email is not None:
        payload["email"] = email
    if password is not None:
        payload["pword"] = password
        payload["pword2"] = password
    if first is not None:
        payload["firstname"] = first
    if last is not None:
        payload["lastname"] = last
    if new_user_id is not None:
        payload["uname"] = new_user_id

    # add CSRF token
    payload["csrfmiddlewaretoken"] = oneupsdk.integration.api.get_csrf_token()

    print(payload)
    r = oneupsdk.integration.api.request(
        endpoint="/oneUp/instructors/createStudentView",
        data=payload)

    return r.status_code == 200


###############################################################################
# ACTIVITY METHODS
###############################################################################

def get_activity_categories():
    # type: () -> list
    """
    Returns a list of the activity categories for the active course.
    """
    r = oneupsdk.integration.api.request("/oneUp/instructors/activitiesList")
    if r is None or r.status_code != 200:
        return []

    s = _bs4.BeautifulSoup(r.content, features="html.parser")
    o = s.find("select", { "name": "actCat" })
    if o is None:
        return []

    raw_cats = o.find_all("option")
    cats = []
    for c in raw_cats:
        if c.get("value") == "all":
            continue

        cats.append((int(c.get("value")), c.text))

    return cats


