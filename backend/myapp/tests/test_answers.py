import json
from pathlib import Path

from django.test import SimpleTestCase

from myapp.answers import answer_matches

# Shared with frontend/src/answerMatch.test.js, so the server matcher and the
# diagnostic's in-browser port agree case for case.
_CASES = Path(__file__).resolve().parents[3] / "frontend" / "src" / "answerCases.json"


class AnswerMatchesTests(SimpleTestCase):
    def test_shared_cases(self):
        cases = json.loads(_CASES.read_text(encoding="utf-8"))["cases"]
        self.assertGreater(len(cases), 0)
        for answer, solution, expected in cases:
            with self.subTest(answer=answer, solution=solution):
                self.assertIs(answer_matches(answer, solution), expected)
