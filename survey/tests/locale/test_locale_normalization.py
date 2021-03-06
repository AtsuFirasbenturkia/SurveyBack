import logging
import os
import platform
import subprocess
import unittest
from pathlib import Path

from django import __version__ as django_version
from django.conf import settings


class TestLocaleNormalization(unittest.TestCase):

    LOCALE_PATH = Path("survey", "locale").absolute()

    def test_normalization(self):
        """We test if the messages were properly created with makemessages --no-obsolete --no-wrap."""
        if platform.system() == "Windows":
            python_3 = ["py", "-3"]
        else:
            python_3 = ["python3"]
        makemessages_command = python_3 + [
            "manage.py",
            "makemessages",
            "--no-obsolete",
            "--no-wrap",
            "--ignore",
            "venv",
        ]
        if django_version > "3.0":
            for x in settings.LANGUAGES:
                if x[0] not in ["en"]:
                    makemessages_command += ["--locale", x[0]]
            logging.warning("Command to launch for makemessages is : %s", " ".join(makemessages_command))
        number_of_language = len(os.listdir(self.LOCALE_PATH))
        subprocess.check_call(makemessages_command)
        git_diff_command = ["git", "diff", self.LOCALE_PATH]
        git_diff = subprocess.check_output(git_diff_command).decode("utf8")
        # In the diff we should have a change only for the date of the generation
        # So 2 * @@ * number of language
        number_of_change = git_diff.count("@@") / 2
        msg = (
            "You did not update the translation following your changes. Maybe you did not use the "
            "normalized 'python3 manage.py makemessages --no-obsolete --no-wrap' ? If you're "
            "working locally, just use 'git add {}', we launched it during tests.".format(self.LOCALE_PATH),
        )
        self.assertEqual(number_of_change, number_of_language, msg)
