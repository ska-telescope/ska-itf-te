"""."""

from pathlib import Path


def find_in_test_file(search_string: str):
    """_summary_.

    :param search_string: _description_
    :type search_string: str
    :return: _description_
    :rtype: _type_
    """
    for path in Path().glob("**/*test*.py"):
        with path.open() as file:
            if search_string in file.read():
                return str(path)
    return search_string
