# OneUp Learning SDK

This is a Python SDK to allow for the scripting and integration of the [OneUp Learning platform](https://oneup.wssu.edu/login) developed by West-Salem State University.

## Installation

The package is available through Python's package management system:

```shell
pip install oneupsdk
```

## Configuration

You can request an account by contacting [Darina Dicheva](https://www.wssu.edu/profiles/dichevad/index.html). Once you have an account, create a `config.yaml` file containing your authentication information. This file is parsed by the SDK to authenticate your API calls.

```yaml
oneup:
  username: "username"
  password: "OneUP-P4ssW04d!"
```

## Usage

Below are the macros that are available from the subpackage `oneupsdk.integration`. Note that a call to `set_active_course()` must be made before most of the other calls will work.

- Courses
    - `get_instructor_courses()`
    - `set_active_course(course_id)`
    - `get_active_course()`

- Students
    - `get_enrolled_students()`
    - `get_student_by_id(user_id)`
    - `get_student_by_username(username)`
    - `add_student(email, password, first=None, last=None, user_id=None)`
    - `modify_student(username, email=None, password=None, first=None, last=None, new_user_id=None)`
    - `delete_student(user_id)`

- Activities
    - `get_activities()` 
    - `get_activity_by_id(activity_id)`
    - `create_activity(name, category_id=None, **kwargs)`
    - `modify_activity(activity_id, **kwargs)`
    - `post_activity_points(activity_id, data, as_dict=False)`
    - `delete_activity(activity_id)`
    - Activity categories
        - `get_activity_categories()`
        - `get_default_activity_category()`
        - `create_activity_category(name)`
        - `delete_activity_category(category_id)`

## References

Dicheva, Darina, Keith Irwin, and Christo Dichev. "OneUp learning: a course gamification platform." In _International Conference on Games and Learning Alliance_, pp. 148-158. Springer, Cham, 2017. ([link](https://link.springer.com/chapter/10.1007/978-3-319-71940-5_14))

Dicheva, Darina, Keith Irwin, and Christo Dichev. "OneUp: Supporting Practical and Experimental Gamification of Learning." _International Journal of Serious Games_ 5, no. 3 (2018): 5-21. ([link](http://journal.seriousgamessociety.org/index.php/IJSG/article/view/236))

Dicheva, Darina, Keith Irwin, and Christo Dichev. "OneUp: Engaging Students in a Gamified Data Structures Course." In _Proceedings of the 50th ACM Technical Symposium on Computer Science Education_, pp. 386-392. 2019. ([link](https://dl.acm.org/doi/abs/10.1145/3287324.3287480))