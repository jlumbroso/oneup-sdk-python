
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
    ("uname", "username"),
    # Added by Keith Irwin on 2020-02-16
    ("student_internal_id", "id"),
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
    ("actCat", "category_id"),
    ("description", "description"),
    ("instructorNotes", "instructor_notes")
]

ONEUP_ACTIVITY_CATEGORY_DEFAULT_NAME = "Uncategorized"

ONEUP_ACTIVITY_DEFAULTS = {
    "points": 100,
    "start_time": "",
    "end_time": "",
    "deadline": "",
    "is_graded": False,
    "description": "",
    "instructor_notes": "",
}

ONEUP_STUDENT_ATTRIBUTE_CAPTION_DICT = dict(ONEUP_STUDENT_ATTRIBUTES_CAPTION)
ONEUP_STUDENT_ATTRIBUTES_FORM_DICT = dict(ONEUP_STUDENT_ATTRIBUTES_FORM)
ONEUP_ACTIVITY_ATTRIBUTES_FORM_DICT = dict(ONEUP_ACTIVITY_ATTRIBUTES_FORM)
ONEUP_ACTIVITY_ATTRIBUTES_FORM_RDICT = dict(map(lambda pair: (pair[1], pair[0]),
                                                ONEUP_ACTIVITY_ATTRIBUTES_FORM))

ONEUP_COURSE_TITLE_PARSER = _re.compile("(?P<name>.*) \xa0 \((?P<university>.*)\)")

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

            # newly introduced: University marker
            # <caption> \xa0 (<university>)
            m = ONEUP_COURSE_TITLE_PARSER.match(course_caption)
            if m is not None:
                course_caption = m.group("name")

            course_id = int(row.find("input", {"name": "courseID"})["value"])
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
            user_name = row.find("input", { "name": "userID" }).get("value")
        except:
            continue

        # Added 2020-02-16 after adding field by Keith Irwin on forms
        try:
            user_id = row.find("input", { "name": "student_internal_id" }).get("value")
            user_id = int(user_id)
        except ValueError:
            continue
        except:
            continue

        user_record = dict(zip(headers, columns))
        user_record["username"] = user_name
        user_record["id"] = user_id

        students.append(user_record)

    return students


def get_student_by_username(username):
    # type: (str) -> _typing.Optional[dict]
    """
    Returns a student with the provided username, if such a student exists in the
    active course.
    """

    r = oneupsdk.integration.api.request(
        "/oneUp/instructors/createStudentView?userID={}".format(username))

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

    # Hackish: Try to convert ID to integer
    if "id" in student_info:
        try:
            student_info["id"] = int(student_info["id"])
        except ValueError:
            pass

    return student_info


def get_student_by_id(user_id):
    # type: (int) -> _typing.Optional[dict]
    """
    Returns a student with the provided user ID, if such a student exists in the
    active course.
    """
    students = oneupsdk.integration.get_enrolled_students()
    id_to_username_mapping = {
        student.get("id") : student.get("username")
        for student in students
    }
    student_username = id_to_username_mapping.get(user_id)

    if student_username is None or student_username == "":
        return

    return oneupsdk.integration.get_student_by_username(username=student_username)


def add_student(email, password, first=None, last=None, username=None):
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
            "uname": username or email,
            "pword": password,
            "pword2": password,
        })

    return r.status_code == 200


def delete_student(username):
    # type: (str) -> bool
    """
    Unenrolls a student from the active course.
    """
    r = oneupsdk.integration.api.request(
        endpoint="/oneUp/instructors/deleteStudent",
        data={
            "userID": username,
            "csrfmiddlewaretoken": oneupsdk.integration.api.get_csrf_token()
        })

    return r.status_code == 200


def modify_student(username, email=None, password=None, first=None, last=None, new_user_id=None):
    """
    Creates a new student and enrolls them in the active course.
    """
    user_info = get_student_by_username(username=username)

    if user_info is None:
        return False

    payload = {
        "userID": user_info.get("username"),
        "sUsernamePrev": user_info.get("username"),
        "sEmailPrev": user_info.get("email"),

        # Existing fields
        "firstname": user_info.get("first"),
        "lastname": user_info.get("last"),
        "email": user_info.get("email"),
        "uname": user_info.get("username"),
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

    r = oneupsdk.integration.api.request(
        endpoint="/oneUp/instructors/createStudentView",
        data=payload)

    return r.status_code == 200


###############################################################################
# ACTIVITY METHODS
###############################################################################

def get_default_activity_category():
    # type: () -> dict
    """
    Returns the default activity category.
    """

    # Get all activities
    activities = oneupsdk.integration.macros.get_activity_categories()

    # Find the default category (filter by name, then sort and take smallest ID)
    default = sorted(
        filter(lambda c: c.get("name") == oneupsdk.integration.macros.ONEUP_ACTIVITY_CATEGORY_DEFAULT_NAME,
               activities),
        key=lambda c: c.get("id")
    )

    if len(default) == 0:
        raise ValueError("something wrong")

    return default[0]


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

        cats.append({
            "id": int(c.get("value")),
            "name": c.text,
        })

    return cats


def create_activity_category(name, xp_weight=1):
    # type: (str) -> _typing.Optional[dict]
    """
    Creates a new activity category in the active course and returns its ID.
    """

    # Uses the presumption that IDs are creating in ascending order
    # to be able to identify the activity category that was created

    # Select existing activity categories, filter those who have
    # the same name, and sort by decreasing IDs

    existing_cats = sorted(filter(lambda c: c["name"] == name,
                                  get_activity_categories()),
                           key=lambda c: -c["id"])

    r = oneupsdk.integration.api.request(
        endpoint="/oneUp/instructors/activityCatsCreate",
        data={
            "catName": name,
            "xpWeight": xp_weight,
            "csrfmiddlewaretoken": oneupsdk.integration.api.get_csrf_token(),
        })

    # Find categories with name and see if there is a new category

    after_cats = sorted(filter(lambda c: c["name"] == name,
                               get_activity_categories()),
                        key=lambda c: -c["id"])

    if r.status_code in [302, 200] and len(existing_cats) + 1 == len(after_cats):
        return after_cats[0]


def get_activities():
    # type: () -> list
    """
    Returns a list of the activity categories for the active course.
    """
    r = oneupsdk.integration.api.request("/oneUp/instructors/activitiesList")
    if r is None or r.status_code != 200:
        return []

    s = _bs4.BeautifulSoup(r.content, features="html.parser")

    pane_tag = s.find("ul", {"id": "sortable-categories"})
    if pane_tag is None:
        return []

    activity_tags = list(filter(
        lambda tag: tag.get("id") is not None and tag.get("data-category-id") is not None,
        pane_tag.find_all("li")))

    activities = []
    for tag in activity_tags:
        activity_id = tag.get("id")
        category_id = tag.get("data-category-id")
        try:
            divs = tag.find("div", {"class": "sortable-item"}).find_all("div")
            divs_text = list(map(
                lambda tag: tag.text.strip(),
                divs,
            ))
        except:
            divs_text = None

        activity = {
            "id": int(activity_id),
            "category_id": int(category_id),
        }
        if divs_text is not None:
            activity.update({
                "name": divs_text[1],
                "description": divs_text[2],
                "points": float(divs_text[3].split(" Points")[0]),
            })

        activities.append(activity)

    return activities


def get_activity_by_id(activity_id):
    # type: (int) -> _typing.Optional[dict]
    """
    Returns an activity with the provided activity ID, if such an activity exists in the
    active course.
    """

    r = oneupsdk.integration.api.request(
        "/oneUp/instructors/createActivity?activityID={}".format(activity_id))

    if r.status_code != 200:
        return

    s = _bs4.BeautifulSoup(r.content, features="html.parser")

    obj_form = s.find("form", { "id": "actForm" })
    if obj_form is None:
        return

    def compute_value(field):
        val = field.get("value")
        if val is not None:
            return val

        if field.get("type") == "checkbox":
            return field.get("checked") is not None

        return field.text.strip()

    lst_fields = list(
        map(lambda field: (field.get("name"), compute_value(field)),
            obj_form.find_all("input") + obj_form.find_all("textarea")))

    activity_info = {}
    for (name, value) in lst_fields:
        if name in oneupsdk.integration.macros.ONEUP_ACTIVITY_ATTRIBUTES_FORM_DICT:
            internal_name = oneupsdk.integration.macros.ONEUP_ACTIVITY_ATTRIBUTES_FORM_DICT.get(name)
            activity_info[internal_name] = value

    # Determine category
    obj_cat = obj_form.find("select").find("option", selected=True)

    activity_info["category_id"] = int(obj_cat.get("value"))

    # NOTE: unsupported currently
    if "file" in activity_info:
        del activity_info["file"]

    # Hackish: Try to convert ID to integer
    if "id" in activity_info:
        try:
            activity_info["id"] = int(activity_info["id"])
        except ValueError:
            pass

    # Hackish: Try to convert points to integer
    if "id" in activity_info:
        try:
            activity_info["points"] = int(activity_info["points"])
        except ValueError:
            pass

    return activity_info


def delete_activity_category(category_id):
    # type: (int) -> bool

    """
    Deletes an activity category from the active course.
    """
    r = oneupsdk.integration.api.request(
        endpoint="/oneUp/instructors/activityCatsDelete",
        data={
            "catID": category_id,
            "csrfmiddlewaretoken": oneupsdk.integration.api.get_csrf_token()
        })

    return r.status_code == 200


def create_activity(name, **kwargs):
    # type: (str, str) -> bool
    """
    Modify the properties of an existing activity.
    """

    payload = {
        oneupsdk.integration.macros.ONEUP_ACTIVITY_ATTRIBUTES_FORM_RDICT.get(name): value
        for (name, value) in oneupsdk.integration.macros.ONEUP_ACTIVITY_DEFAULTS.items()
        if name in oneupsdk.integration.macros.ONEUP_ACTIVITY_ATTRIBUTES_FORM_RDICT
        if type(value) is not bool or value
    }
    default_cat_id = oneupsdk.integration.macros.get_default_activity_category().get("id")
    payload["actCat"] = default_cat_id

    # NOTE: the names of the dict entries come from the FORM

    changes = {
        oneupsdk.integration.macros.ONEUP_ACTIVITY_ATTRIBUTES_FORM_RDICT.get(name): value
        for (name, value) in kwargs.items()
        if name in oneupsdk.integration.macros.ONEUP_ACTIVITY_ATTRIBUTES_FORM_RDICT
        if type(value) is not bool or value
    }
    payload.update(changes)

    payload["activityName"] = name

    # add CSRF token
    payload["csrfmiddlewaretoken"] = oneupsdk.integration.api.get_csrf_token()
    payload["submit"] = ""

    r = oneupsdk.integration.api.request(
        endpoint="/oneUp/instructors/createActivity",
        data=payload, multipart=True)

    return r.status_code == 200


def modify_activity(activity_id, **kwargs):
    # type: (int, str) -> bool
    """
    Modify the properties of an existing activity.
    """
    activity_info = oneupsdk.integration.macros.get_activity_by_id(activity_id=activity_id)

    if activity_info is None:
        return False

    payload = {
        oneupsdk.integration.macros.ONEUP_ACTIVITY_ATTRIBUTES_FORM_RDICT.get(name): value
        for (name, value) in activity_info.items()
        if name in oneupsdk.integration.macros.ONEUP_ACTIVITY_ATTRIBUTES_FORM_RDICT
        if type(value) is not bool or value
    }

    # NOTE: the names of the dict entries come from the FORM

    changes = {
        oneupsdk.integration.macros.ONEUP_ACTIVITY_ATTRIBUTES_FORM_RDICT.get(name): value
        for (name, value) in kwargs.items()
        if name in oneupsdk.integration.macros.ONEUP_ACTIVITY_ATTRIBUTES_FORM_RDICT
        if type(value) is not bool or value
    }
    payload.update(changes)

    # if name is not None:
    #     payload["activityName"] = name
    # if total is not None:
    #     payload["points"] = total
    # if description is not None:
    #     payload["description"] = description
    # if notes is not None:
    #     payload["instructorNotes"] = notes

    # add CSRF token
    payload["csrfmiddlewaretoken"] = oneupsdk.integration.api.get_csrf_token()
    payload["submit"] = ""

    r = oneupsdk.integration.api.request(
        endpoint="/oneUp/instructors/createActivity",
        data=payload, multipart=True)

    return r.status_code == 200


def post_activity_points(activity_id, data, as_dict=False):
    # type: (int, _typing.Union[list, dict], bool) -> bool
    """
    Assign the points of a given activity for a set of students. The input data
    can be presented in one of multiple forms: Either as a list of records:
    ```python
    [
        { "username": "oneup_username", "points": 23 },
        { "email": "student@university.edu", "points": 23 },
        { "id": 413, "points": 23, "feedback": "Everything good!" },
        ...
    ]
    ```
    or as a dictionary:
    ```python
    {
        "student@university.edu": 23.5
    }
    ```
    """

    r = oneupsdk.integration.api.request(
        "/oneUp/instructors/activityAssignPointsForm?activityID={}".format(activity_id))
    s = _bs4.BeautifulSoup(r.content, "html.parser")

    # Extract the existing information (as it all must be submitted)

    s_feedback = {
        int(row.get("name").replace("student_Feedback", "")) : row.text
        for row in s.find_all("textarea", { "id": "student_feedback" })
    }
    s_points = {
        int(row.get("id").split("_")[0]) : row.get("value")
        for row in s.find_all("input", { "type": "number" })
    }
    s_ids = s_points.keys()

    # Create mapping to resolve input data

    students = oneupsdk.integration.macros.get_enrolled_students()
    id_to_username_mapping = dict()
    username_to_id_mapping = dict()
    email_to_id_mapping = dict()

    for student in students:
        student_id = student.get("id")
        student_username = student.get("username")
        student_email = student.get("email")

        # Create mapping
        id_to_username_mapping[student_id] = student_username
        username_to_id_mapping[student_username] = student_id
        email_to_id_mapping[student_email] = student_id

    # Modify data based on input data

    if as_dict:
        # Data is given as { "username": points }

        for str_id, points in data.items():

            user_id = None

            if "@" in str_id:
                # Email
                if str_id not in email_to_id_mapping:
                    continue
                user_id = email_to_id_mapping.get(str_id)
            else:
                # Username
                if str_id not in username_to_id_mapping:
                    continue
                user_id = username_to_id_mapping.get(str_id)

            s_points[user_id] = points

    else:
        # Data is given as [ { "username": "", "email": "", "feedback": "", "points": 0 }, ... ]

        for record in data:

            # Retrieve ID by order of preference
            record_id = None
            if "id" in record:
                record_id = int(record.get("id"))

            elif "email" in record and record.get("email") in email_to_id_mapping:
                record_email = record.get("email")
                record_id = email_to_id_mapping.get(record_email)

            elif "username" in record and record.get("username") in username_to_id_mapping:
                record_username = record.get("username")
                record_id = username_to_id_mapping.get(record_username)

            # Change points
            if "points" in record:
                s_points[record_id] = record["points"]

            # Change feedback
            if "feedback" in record:
                s_feedback[record_id] = record["feedback"]

    # Build payload to be sent

    payload = {
        "csrfmiddlewaretoken": oneupsdk.integration.api.get_csrf_token(),
        "activityID": "{}".format(activity_id),
        "submit": "",
    }
    for user_id in s_ids:
        student_payload = {
            "student_Points{}".format(user_id) : s_points.get(user_id),
            "student_Feedback{}".format(user_id) : s_feedback.get(user_id),
        }
        payload.update(student_payload)

    r = oneupsdk.integration.api.request(
        endpoint="/oneUp/instructors/activityAssignPoints",
        data=payload)

    return r.status_code in [200, 302]


def delete_activity(activity_id):
    # type: (int) -> bool

    """
    Deletes an activity from the active course.
    """
    r = oneupsdk.integration.api.request(
        endpoint="/oneUp/instructors/deleteActivity",
        data={
            "activityID": activity_id,
            "csrfmiddlewaretoken": oneupsdk.integration.api.get_csrf_token()
        })

    return r.status_code == 200


