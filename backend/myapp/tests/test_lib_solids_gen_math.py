"""Math-correctness tests for the ``lib_solids_gen`` library overrides.

For each override this parses the numeric inputs out of the PROBLEM string,
recomputes the expected answer independently (rounding the same way, to the
nearest thousandth via the shared ``num`` helper), and asserts the generator's
solution matches — over many seeded random samples. Also guards that neither the
problem nor the solution contains a banned LaTeX token or a number with more
than three decimal places.
"""
import math
import random
import re

from django.test import TestCase

# Importing the module runs its @register side effect.
from myapp.generators import lib_solids_gen  # noqa: F401
from myapp.generators import LOCAL_GENERATORS
from myapp.generators._variants import classic
from myapp.generators._format import num

SAMPLES = 2000

# Tokens that must never appear in a typeable problem/solution answer.
_BANNED = [
    r"\frac", r"\sqrt", r"\langle", r"\rangle", r"\geq", r"\leq", r"\neq",
    r"\times", r"\cdot", r"\infty", r"\begin",
]

# Matches any number written with 4+ decimal places (an over-precise leak).
_LONG_DECIMAL = re.compile(r"\d+\.\d{4,}")
# Matches a trailing ``.0`` style number (banned by the typeable rules).
_TRAILING_DOT_ZERO = re.compile(r"\d+\.0\b")


def _assert_typeable(test, problem, solution):
    for tok in _BANNED:
        test.assertNotIn(tok, problem, f"banned {tok!r} in problem: {problem!r}")
        test.assertNotIn(tok, solution, f"banned {tok!r} in solution: {solution!r}")
    for text, label in ((problem, "problem"), (solution, "solution")):
        test.assertIsNone(
            _LONG_DECIMAL.search(text),
            f">3dp number in {label}: {text!r}",
        )
        test.assertIsNone(
            _TRAILING_DOT_ZERO.search(text),
            f"trailing .0 in {label}: {text!r}",
        )


class SurfaceAreaSphereTests(TestCase):
    def test_solution(self):
        random.seed(0)
        gen = classic(LOCAL_GENERATORS["surface_area_sphere"])
        m = re.compile(r"radius \$= (\d+) m\$")
        for _ in range(SAMPLES):
            problem, solution = gen()[:2]
            _assert_typeable(self, problem, solution)
            r = int(m.search(problem).group(1))
            expected = num(4 * math.pi * r ** 2)
            self.assertEqual(solution, f"${expected} m^2$", problem)


class VolumeSphereTests(TestCase):
    def test_solution(self):
        random.seed(0)
        gen = classic(LOCAL_GENERATORS["volume_sphere"])
        m = re.compile(r"radius \$= (\d+) m\$")
        for _ in range(SAMPLES):
            problem, solution = gen()[:2]
            _assert_typeable(self, problem, solution)
            r = int(m.search(problem).group(1))
            expected = num((4 / 3) * math.pi * r ** 3)
            self.assertEqual(solution, f"${expected} m^3$", problem)


class VolumeHemisphereTests(TestCase):
    def test_solution(self):
        random.seed(0)
        gen = classic(LOCAL_GENERATORS["volume_hemisphere"])
        m = re.compile(r"radius \$= (\d+) m\$")
        for _ in range(SAMPLES):
            problem, solution = gen()[:2]
            _assert_typeable(self, problem, solution)
            r = int(m.search(problem).group(1))
            expected = num((2 / 3) * math.pi * r ** 3)
            self.assertEqual(solution, f"${expected} m^3$", problem)


class VolumePyramidTests(TestCase):
    def test_solution(self):
        random.seed(0)
        gen = classic(LOCAL_GENERATORS["volume_pyramid"])
        m = re.compile(r"base area \$= (\d+) m\^2\$ and height \$= (\d+) m\$")
        for _ in range(SAMPLES):
            problem, solution = gen()[:2]
            _assert_typeable(self, problem, solution)
            base_area, height = (int(g) for g in m.search(problem).groups())
            expected = num((1 / 3) * base_area * height)
            self.assertEqual(solution, f"${expected} m^3$", problem)


class CurvedSurfaceAreaCylinderTests(TestCase):
    def test_solution(self):
        random.seed(0)
        gen = classic(LOCAL_GENERATORS["curved_surface_area_cylinder"])
        m = re.compile(r"radius \$= (\d+) m\$ and height \$= (\d+) m\$")
        for _ in range(SAMPLES):
            problem, solution = gen()[:2]
            _assert_typeable(self, problem, solution)
            r, h = (int(g) for g in m.search(problem).groups())
            expected = num(2 * math.pi * r * h)
            self.assertEqual(solution, f"${expected} m^2$", problem)


class CubeRootTests(TestCase):
    def test_solution(self):
        random.seed(0)
        gen = classic(LOCAL_GENERATORS["cube_root"])
        m = re.compile(r"cube root of \$(\d+)\$")
        for _ in range(SAMPLES):
            problem, solution = gen()[:2]
            _assert_typeable(self, problem, solution)
            n = int(m.search(problem).group(1))
            root = round(n ** (1 / 3))
            # The generator only picks perfect cubes: verify that invariant.
            self.assertEqual(root ** 3, n, f"not a perfect cube: {problem!r}")
            self.assertEqual(solution, f"${num(root)}$", problem)


class AreaOfTriangleTests(TestCase):
    def test_solution(self):
        random.seed(0)
        gen = classic(LOCAL_GENERATORS["area_of_triangle"])
        m = re.compile(
            r"side lengths \$= (\d+) m\$, \$= (\d+) m\$, and \$= (\d+) m\$"
        )
        for _ in range(SAMPLES):
            problem, solution = gen()[:2]
            _assert_typeable(self, problem, solution)
            a, b, c = (int(g) for g in m.search(problem).groups())
            # Sides must form a strictly valid triangle.
            self.assertTrue(a + b > c and a + c > b and b + c > a, problem)
            s = (a + b + c) / 2
            expected = num(math.sqrt(s * (s - a) * (s - b) * (s - c)))
            self.assertEqual(solution, f"${expected} m^2$", problem)


class PythagoreanTheoremTests(TestCase):
    def test_solution(self):
        random.seed(0)
        gen = classic(LOCAL_GENERATORS["pythagorean_theorem"])
        m = re.compile(r"lengths \$= (\d+)\$ and \$= (\d+)\$")
        for _ in range(SAMPLES):
            problem, solution = gen()[:2]
            _assert_typeable(self, problem, solution)
            a, b = (int(g) for g in m.search(problem).groups())
            expected = num(math.sqrt(a ** 2 + b ** 2))
            self.assertEqual(solution, f"${expected}$", problem)


_ROUND_HINT = "Round your answer to the nearest thousandth."


def _samples(name):
    """Yield ``(problem, solution)`` for SAMPLES seeded runs of a generator."""
    random.seed(0)
    gen = classic(LOCAL_GENERATORS[name])
    for _ in range(SAMPLES):
        yield gen()[:2]


class VolumeCubeTests(TestCase):
    def test_solution(self):
        m = re.compile(r"side length \$= (\d+) m\$\.$")
        for problem, solution in _samples("volume_cube"):
            _assert_typeable(self, problem, solution)
            a = int(m.search(problem).group(1))
            self.assertEqual(solution, f"${a * a * a} m^3$", problem)


class VolumeCuboidTests(TestCase):
    def test_solution(self):
        m = re.compile(
            r"length \$= (\d+) m\$, width \$= (\d+) m\$, and height \$= (\d+) m\$"
        )
        for problem, solution in _samples("volume_cuboid"):
            _assert_typeable(self, problem, solution)
            l, w, h = (int(g) for g in m.search(problem).groups())
            self.assertEqual(solution, f"${l * w * h} m^3$", problem)


class VolumeCylinderTests(TestCase):
    def test_solution(self):
        m = re.compile(r"radius \$= (\d+) m\$ and height \$= (\d+) m\$")
        for problem, solution in _samples("volume_cylinder"):
            _assert_typeable(self, problem, solution)
            self.assertIn(_ROUND_HINT, problem)
            r, h = (int(g) for g in m.search(problem).groups())
            expected = num(math.pi * r * r * h)
            self.assertEqual(solution, f"${expected} m^3$", problem)


class VolumeConeTests(TestCase):
    def test_solution(self):
        m = re.compile(r"cone with radius \$= (\d+) m\$ and height \$= (\d+) m\$")
        for problem, solution in _samples("volume_cone"):
            _assert_typeable(self, problem, solution)
            self.assertIn(_ROUND_HINT, problem)
            r, h = (int(g) for g in m.search(problem).groups())
            expected = num(math.pi * r * r * h / 3)
            self.assertEqual(solution, f"${expected} m^3$", problem)


class SurfaceAreaCubeTests(TestCase):
    def test_solution(self):
        m = re.compile(r"cube with side length \$= (\d+) m\$\.$")
        for problem, solution in _samples("surface_area_cube"):
            _assert_typeable(self, problem, solution)
            a = int(m.search(problem).group(1))
            self.assertEqual(solution, f"${6 * a * a} m^2$", problem)


class SurfaceAreaCuboidTests(TestCase):
    def test_solution(self):
        m = re.compile(
            r"length \$= (\d+) m\$, width \$= (\d+) m\$, and height \$= (\d+) m\$"
        )
        for problem, solution in _samples("surface_area_cuboid"):
            _assert_typeable(self, problem, solution)
            l, w, h = (int(g) for g in m.search(problem).groups())
            self.assertEqual(solution, f"${2 * (l * w + l * h + w * h)} m^2$", problem)


class SurfaceAreaConeTests(TestCase):
    def test_solution(self):
        m = re.compile(r"radius \$= (\d+) m\$ and slant height \$= (\d+) m\$")
        for problem, solution in _samples("surface_area_cone"):
            _assert_typeable(self, problem, solution)
            self.assertIn(_ROUND_HINT, problem)
            r, slant = (int(g) for g in m.search(problem).groups())
            # A real cone's slant height is longer than its radius.
            self.assertGreater(slant, r, problem)
            expected = num(math.pi * r * r + math.pi * r * slant)
            self.assertEqual(solution, f"${expected} m^2$", problem)


class SurfaceAreaCylinderTests(TestCase):
    def test_solution(self):
        m = re.compile(r"radius \$= (\d+) m\$ and height \$= (\d+) m\$")
        for problem, solution in _samples("surface_area_cylinder"):
            _assert_typeable(self, problem, solution)
            self.assertIn(_ROUND_HINT, problem)
            r, h = (int(g) for g in m.search(problem).groups())
            expected = num(2 * math.pi * r * r + 2 * math.pi * r * h)
            self.assertEqual(solution, f"${expected} m^2$", problem)


class SurfaceAreaPyramidTests(TestCase):
    def test_solution(self):
        m = re.compile(
            r"length \$= (\d+) m\$ and width \$= (\d+) m\$\. Each triangular face "
            r"on a length side has slant height \$= (\d+) m\$, and each face on a "
            r"width side has slant height \$= (\d+) m\$"
        )
        for problem, solution in _samples("surface_area_pyramid"):
            _assert_typeable(self, problem, solution)
            length, width, slant_l, slant_w = (int(g) for g in m.search(problem).groups())
            # The stated slant heights must describe one real pyramid: both
            # imply the same (positive) vertical height squared.
            h_sq_from_l = slant_l ** 2 - (width / 2) ** 2
            h_sq_from_w = slant_w ** 2 - (length / 2) ** 2
            self.assertGreater(h_sq_from_l, 0, problem)
            self.assertEqual(h_sq_from_l, h_sq_from_w, problem)
            # Base plus two triangles (1/2 * base * slant) on each pair of sides.
            expected = length * width + 2 * (length * slant_l / 2) + 2 * (width * slant_w / 2)
            self.assertEqual(solution, f"${num(expected)} m^2$", problem)
