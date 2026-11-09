"""Contract tests between the seed data and the available generators.

These do NOT test the correctness of a third-party generator's math (that is
mathgenerator's responsibility). They assert only that every generator_name
the seed data relies on is a real generator that returns a (problem, solution)
pair — guarding against a library upgrade or a typo silently breaking a topic.
_make_problem_for_topic resolves a name via LOCAL_GENERATORS then getattr(mathgenerator,
name); a name that no longer exists would otherwise surface as a 500 for a
student.

Local generators (ones we maintain) get a stronger determinism check in
LocalGeneratorTests, since their logic *is* our responsibility.
"""
import random
import re
from unittest import mock

import mathgenerator
from django.test import TestCase

from myapp.generators import LOCAL_GENERATORS
from myapp.generators._steps import Steps
from myapp.generators._variants import iter_variants
from myapp.management.commands.seed_topics import TOPICS
from myapp.models import Course, Topic
from myapp.views.problems import _make_problem_for_topic


def _variant_names(generator_name):
    """Each question type of a generator to test: its variant names, or [None]."""
    variants = getattr(LOCAL_GENERATORS.get(generator_name), "variants", None)
    return list(variants) if variants else [None]


def _label(name, variant):
    return name if variant is None else f"{name}[{variant}]"

# Third-party generators pick random inputs and can occasionally produce a
# falsy-but-valid answer (e.g. 0) or hit a random degenerate case. Call each a
# few times with a fixed seed so the contract check is deterministic across
# runs and a single unlucky draw can't flake CI.
_ATTEMPTS = 5


class SeedGeneratorContractTests(TestCase):
    def test_names_exist(self):
        # getGenList() yields [id, title, generator, name, category, params];
        # the snake_case name is what the seed data references.
        known = {
            name
            for _id, _title, _gen, name, _cat, _params in mathgenerator.getGenList()
        }
        known |= set(LOCAL_GENERATORS)
        seeded = {g for _topic, g in TOPICS if g is not None}
        missing = sorted(seeded - known)
        self.assertEqual(missing, [], f"Unknown generator names: {missing}")

    def test_every_seeded_topic_uses_a_local_generator(self):
        # Library generators can't explain their answers, so every seeded topic
        # needs one of ours (see generators/_steps.py).
        library_backed = sorted(
            {g for _topic, g in TOPICS if g is not None} - set(LOCAL_GENERATORS)
        )
        self.assertEqual(library_backed, [], f"Seeded topics without a local generator: {library_backed}")

    def test_names_produce_output(self):
        random.seed(0)
        broken = []
        for _topic_name, generator_name in TOPICS:
            if generator_name is None:
                continue
            generator = LOCAL_GENERATORS.get(generator_name) or getattr(
                mathgenerator, generator_name, None
            )
            if generator is None:
                broken.append(f"{generator_name!r}: not found")
                continue
            # Passes if any attempt yields well-formed output.
            ok, last_err = False, None
            for _ in range(_ATTEMPTS):
                try:
                    problem, solution = generator()[:2]
                    if problem and solution is not None:
                        ok = True
                        break
                    last_err = "empty output"
                except Exception as exc:  # noqa: BLE001 - report any failure mode
                    last_err = repr(exc)
            if not ok:
                broken.append(f"{generator_name!r}: {last_err}")
        self.assertEqual(broken, [], "Broken generators:\n" + "\n".join(broken))


class LocalGeneratorTests(TestCase):
    """Stronger checks for the generators we own."""

    def test_all_local_generators_return_well_formed_pairs(self):
        random.seed(0)
        cases = (
            (name + label, call)
            for name, generator in LOCAL_GENERATORS.items()
            for label, call in iter_variants(generator)
        )
        for label, call in cases:
            with self.subTest(generator=label):
                problem, solution = call()[:2]
                self.assertIsInstance(problem, str)
                self.assertTrue(problem)
                self.assertIsInstance(solution, str)
                self.assertTrue(solution)

    def test_vertex_form_is_deterministic_under_seed(self):
        random.seed(42)
        problem1, solution1 = LOCAL_GENERATORS["vertex_form"]()[:2]
        random.seed(42)
        problem2, solution2 = LOCAL_GENERATORS["vertex_form"]()[:2]
        self.assertEqual((problem1, solution1), (problem2, solution2))


class ServedProblemQualityTests(TestCase):
    """Every seeded topic must serve typeable, well-formed problems.

    Runs each topic through the real serve path (`_make_problem_for_topic`, so
    the view's decimal-rounding pass applies) over many random samples and
    asserts the student never sees an answer they can't type or a malformed
    problem. This is the permanent guard behind the library-override sweep: it
    catches a regression (a new seed entry pointing at a broken library
    generator, or an override that stops rounding) the moment it ships.

    The checks encode the typeable-solution contract:
      - no LaTeX commands (a backslash followed by letters, e.g. \\frac, \\sqrt,
        \\times) in the solution — ASCII like ``csc(x)`` is fine, only escaped
        commands are banned;
      - no set/list bracket notation ({...} or [...]) in the solution;
      - no decimal carrying more than three fractional digits anywhere;
      - no float e-notation (``1e-11``) in the solution;
      - balanced ``$`` delimiters and no raw LaTeX leaking outside math mode in
        the problem text.
    """

    SAMPLES = 30
    LATEX_CMD = re.compile(r"\\[a-zA-Z]+")
    LONG_DECIMAL = re.compile(r"\d\.\d{4,}")
    # Steps carry exact intermediate values (rounding happens only at the end),
    # which can need a few more places, like 2.37 x 6.82 = 16.1634. Only a
    # float's noise digits (0.30000000000000004) are a leak there.
    FLOAT_NOISE = re.compile(r"\d\.\d{7,}")
    E_NOTATION = re.compile(r"\d[eE][+-]?\d")

    @classmethod
    def setUpTestData(cls):
        # One Topic per seeded generator_name, attached to a throwaway course,
        # so `_make_problem_for_topic` can be exercised exactly as in production.
        course = Course.objects.create(course_name="Test", grade_level=0)
        cls.topics = [
            Topic.objects.create(
                topic_name=topic_name, course=course, generator_name=gen
            )
            for topic_name, gen in TOPICS
            if gen is not None
        ]

    def test_every_seeded_topic_serves_typeable_problems(self):
        random.seed(0)
        failures = []
        for topic, variant in (
            (t, v) for t in self.topics for v in _variant_names(t.generator_name)
        ):
            name = _label(topic.generator_name, variant)
            for _ in range(self.SAMPLES):
                try:
                    result = _make_problem_for_topic(topic, variant=variant)
                except Exception as exc:  # noqa: BLE001 - a crash 500s the student
                    failures.append(f"{name}: raised {exc!r}")
                    break
                if result is None:
                    continue
                problem, solution = result["problem"], result["solution"]

                if self.LATEX_CMD.search(solution):
                    failures.append(f"{name}: LaTeX in solution {solution!r}")
                    break
                if any(c in solution for c in "{}[]"):
                    failures.append(f"{name}: bracket notation in solution {solution!r}")
                    break
                if self.E_NOTATION.search(solution):
                    failures.append(f"{name}: e-notation in solution {solution!r}")
                    break
                if self.LONG_DECIMAL.search(problem) or self.LONG_DECIMAL.search(solution):
                    failures.append(f"{name}: over-precise decimal in {problem!r} / {solution!r}")
                    break
                if problem.count("$") % 2 != 0:
                    failures.append(f"{name}: unbalanced $ in problem {problem!r}")
                    break
                # Text outside $...$ must not contain raw LaTeX commands.
                outside = "".join(problem.split("$")[::2])
                if self.LATEX_CMD.search(outside):
                    failures.append(f"{name}: raw LaTeX outside math mode {problem!r}")
                    break
                step_error = self._step_error(result["steps"])
                if step_error:
                    failures.append(f"{name}: {step_error}")
                    break
        self.assertEqual(failures, [], "Non-typeable served problems:\n" + "\n".join(failures))

    def _step_error(self, steps):
        """Why a served step-by-step explanation is malformed, or None.

        Steps may use any LaTeX (they're rendered, not typed), but only inside
        math mode: `text` needs balanced `$`, `math` is display LaTeX with none.
        """
        if not isinstance(steps, list):
            return f"steps is not a list: {steps!r}"
        for step in steps:
            if set(step) != {"text", "math"} or not isinstance(step["text"], str) or not step["text"].strip():
                return f"malformed step {step!r}"
            text, math = step["text"], step["math"]
            if text.count("$") % 2 != 0:
                return f"unbalanced $ in step {text!r}"
            if self.LATEX_CMD.search("".join(text.split("$")[::2])):
                return f"raw LaTeX outside math mode in step {text!r}"
            if math is not None and (not isinstance(math, str) or "$" in math):
                return f"bad display math in step {math!r}"
            # A non-raw "\times" or "\frac" silently becomes a tab or form feed.
            if re.search(r"[\x00-\x1f]", text + (math or "")):
                return f"control character in step {step!r}"
            # In LaTeX a bare % comments out the rest of the expression.
            latex = "".join(text.split("$")[1::2]) + (math or "")
            if re.search(r"(?<!\\)%", latex):
                return f"unescaped % in math in step {step!r}"
            if self.FLOAT_NOISE.search(text) or self.FLOAT_NOISE.search(math or ""):
                return f"float noise in step {step!r}"
        return None


class StepsReachAnswerTests(TestCase):
    """Every local generator explains its answer, ending by stating it.

    Checked on the served card (after the view's rounding), comparing with `$`
    and whitespace removed: the final step's text and math must contain the
    solution exactly as the student is asked to type it. `Steps.answer` does
    this. It catches an explanation whose arithmetic drifts from the answer
    key, or that stops short of the format the problem asks for.
    """

    SAMPLES = 200

    @staticmethod
    def _squash(text):
        return re.sub(r"\s+", "", (text or "").replace("$", ""))

    def test_final_step_states_the_answer(self):
        random.seed(0)
        failures = []
        for name, variant in (
            (n, v) for n in LOCAL_GENERATORS for v in _variant_names(n)
        ):
            topic = Topic(id=1, generator_name=name)
            name = _label(name, variant)
            for _ in range(self.SAMPLES):
                made = _make_problem_for_topic(topic, variant=variant)
                steps = made["steps"]
                if not steps:
                    failures.append(f"{name}: no step-by-step explanation")
                    break
                if len(steps) < 2:
                    failures.append(f"{name}: only {len(steps)} step for {made['problem']!r}")
                    break
                last = self._squash(steps[-1]["text"]) + self._squash(steps[-1]["math"])
                if self._squash(made["solution"]) not in last:
                    failures.append(
                        f"{name}: final step {steps[-1]!r} doesn't state {made['solution']!r}"
                    )
                    break
        self.assertEqual(failures, [], "\n".join(failures))


class ServedStepsTests(TestCase):
    """`_make_problem_for_topic`'s handling of a generator's explanation."""

    def _serve(self, generator):
        topic = Topic(id=1, generator_name="fake_gen")
        with mock.patch.dict(LOCAL_GENERATORS, {"fake_gen": generator}):
            return _make_problem_for_topic(topic)

    def test_steps_are_served_unrounded(self):
        # Rounding happens only at the end: an exact intermediate like 16.1634
        # must reach the student as written, not cut to 16.163 mid-calculation.
        steps = Steps().step("Multiply $2.37$ by $6.82$.", "16.1634").step("Done.").done()
        made = self._serve(lambda: ("$2.37 \\times 6.82$", "$16.163$", steps))
        self.assertEqual(made["steps"], [
            {"text": "Multiply $2.37$ by $6.82$.", "math": "16.1634"},
            {"text": "Done.", "math": None},
        ])

    def test_generator_without_steps_serves_empty_steps(self):
        made = self._serve(lambda: ("$1+1=$", "$2$"))
        self.assertEqual(made["solution"], "2")
        self.assertEqual(made["steps"], [])
