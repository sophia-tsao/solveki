"""Math-correctness tests for the geometry, angle and solid variants (geometry_variants.py).

Each test forces one variant, parses the problem text, recomputes the answer
independently, and checks the served solution, over 2000 seeded samples.
"""
import math
import random
import re
from fractions import Fraction

from django.test import SimpleTestCase

from myapp.generators import LOCAL_GENERATORS
from myapp.generators import geometry_variants  # noqa: F401 - attaches the variants
from myapp.tests.test_prealgebra_variants_math import INT, frac

SAMPLES = 2000
TOL = 0.0005 + 1e-9  # half-up rounding can land exactly 0.0005 away


def pt(text):
    """'(x, y)' -> (Fraction, Fraction)."""
    m = re.fullmatch(r"\((-?[\d./]+), (-?[\d./]+)\)", text.strip())
    assert m, text
    return Fraction(m[1]), Fraction(m[2])


class _Base(SimpleTestCase):
    name = variant = None

    def samples(self):
        random.seed(0)
        gen = LOCAL_GENERATORS[self.name]
        for _ in range(SAMPLES):
            problem, solution, _steps = gen(variant=self.variant)
            yield problem, solution.replace("$", "").strip()

    def search(self, pattern, problem):
        m = re.search(pattern, problem)
        self.assertIsNotNone(m, problem)
        return m

    def close(self, solution, value, problem):
        self.assertAlmostEqual(float(solution), value, delta=TOL, msg=problem)


class RightTriangleAngleFromSides(_Base):
    name, variant = "geo_right_triangle_side", "angle_from_sides"

    def test(self):
        for problem, solution in self.samples():
            m = re.search(r"opposite angle \$A\$ is \$(\d+)\$ and the side adjacent to it is \$(\d+)\$", problem)
            if m:
                angle = math.degrees(math.atan(int(m[1]) / int(m[2])))
            else:
                m = self.search(r"the side (opposite|adjacent to) angle \$A\$ is \$(\d+)\$ and the hypotenuse is "
                                r"\$(\d+)\$", problem)
                r = int(m[2]) / int(m[3])
                angle = math.degrees(math.asin(r) if m[1] == "opposite" else math.acos(r))
            self.close(solution, angle, problem)


class PythagIsoscelesHeight(_Base):
    name, variant = "geo_solve_right_triangle_pythag", "isosceles_height"

    def test(self):
        for problem, solution in self.samples():
            side, base = map(int, self.search(r"two sides of length \$(\d+)\$ and a base of length \$(\d+)\$",
                                              problem).groups())
            self.assertEqual(int(solution) ** 2, side * side - (base // 2) ** 2, problem)
            self.assertEqual(base % 2, 0)


class PythagoreanIsoscelesHeight(_Base):
    name, variant = "pythagorean_theorem", "isosceles_height"

    def test(self):
        for problem, solution in self.samples():
            side, base = map(int, self.search(r"two sides of length \$(\d+)\$ and a base of length \$(\d+)\$",
                                              problem).groups())
            self.close(solution, math.sqrt(side * side - (base / 2) ** 2), problem)


class SpecialTriangleInShapes(_Base):
    name, variant = "geo_special_right_triangle", "in_shapes"

    def test(self):
        for problem, solution in self.samples():
            s = int(self.search(r"sides of length \$(\d+)\$", problem)[1])
            value = s * math.sqrt(2) if "diagonal" in problem else s * math.sqrt(3) / 2
            self.close(solution, value, problem)


def circle_equation(solution):
    """(h, k, c) of '(x - h)^2 + (y + k)^2 = c'."""
    m = re.fullmatch(r"\(x ([+-]) (\d+)\)\^2 \+ \(y ([+-]) (\d+)\)\^2 = (\d+)", solution)
    assert m, solution
    h = int(m[2]) * (1 if m[1] == "-" else -1)
    k = int(m[4]) * (1 if m[3] == "-" else -1)
    return h, k, int(m[5])


class CircleEquationFromDiameter(_Base):
    name, variant = "geo_circle_equation_from_center_radius", "from_diameter"

    def test(self):
        for problem, solution in self.samples():
            (x1, y1), (x2, y2) = [tuple(map(int, p)) for p in re.findall(r"\((-?\d+), (-?\d+)\)", problem)]
            h, k, c = circle_equation(solution)
            self.assertEqual((Fraction(x1 + x2, 2), Fraction(y1 + y2, 2)), (h, k), problem)
            self.assertEqual((x1 - h) ** 2 + (y1 - k) ** 2, c, problem)


class CircleGeneralFormRadius(_Base):
    name, variant = "geo_circle_center_radius_from_equation", "general_form_radius"

    def test(self):
        for problem, solution in self.samples():
            eq = self.search(r"circle \$([^$]+) = 0\$", problem)[1].replace(" ", "")
            D = re.search(r"([+-]\d+)x", eq)
            E = re.search(r"([+-]\d+)y", eq)
            F = re.search(r"([+-]\d+)$", eq)
            D, E, F = (int(m[1]) if m else 0 for m in (D, E, F))
            if F and re.search(r"[xy]" + re.escape(f"{F:+d}") + "$", eq) is None and not eq.endswith(f"{F:+d}"):
                F = 0
            r2 = Fraction(D * D + E * E, 4) - F
            self.assertEqual(int(solution) ** 2, r2, problem)


class CircleRadiusFromArea(_Base):
    name, variant = "area_of_circle", "radius_from_area"

    def test(self):
        for problem, solution in self.samples():
            a = int(self.search(r"area of \$(\d+)\\pi\$", problem)[1])
            self.assertEqual(int(solution) ** 2, a, problem)


class CircleRadiusFromCircumference(_Base):
    name, variant = "circumference", "radius_from_circumference"

    def test(self):
        for problem, solution in self.samples():
            c = int(self.search(r"circumference of \$(\d+)\\pi\$", problem)[1])
            self.assertEqual(2 * int(solution), c, problem)


class CircleTangentToAxis(_Base):
    name, variant = "area_of_circle_given_center_and_point", "tangent_to_axis"

    def test(self):
        for problem, solution in self.samples():
            m = self.search(r"center \$\(" + INT + ", " + INT + r"\)\$ is tangent to the (x|y)-axis", problem)
            r = abs(int(m[2])) if m[3] == "x" else abs(int(m[1]))
            self.close(solution, math.pi * r * r, problem)


class SectorAngleFromArea(_Base):
    name, variant = "sector_area", "angle_from_area"

    def test(self):
        for problem, solution in self.samples():
            r, k = map(int, self.search(r"radius \$(\d+)\$ has an area of \$(\d+)\\pi\$", problem).groups())
            self.assertEqual(Fraction(int(solution) * r * r, 360), k, problem)


class ArcAngleFromArc(_Base):
    name, variant = "arc_length", "angle_from_arc"

    def test(self):
        for problem, solution in self.samples():
            r, k = map(int, self.search(r"radius \$(\d+)\$ has length \$(\d+)\\pi\$", problem).groups())
            self.assertEqual(Fraction(int(solution) * 2 * r, 360), k, problem)


class InscribedCyclicQuadrilateral(_Base):
    name, variant = "geo_inscribed_angle", "cyclic_quadrilateral"

    def test(self):
        for problem, solution in self.samples():
            a = int(self.search(r"Angle \$A\$ measures \$(\d+)\^", problem)[1])
            self.assertEqual(int(solution) + a, 180, problem)


class CircleSecantSecant(_Base):
    name, variant = "geo_circle_segments", "secant_secant"

    def test(self):
        for problem, solution in self.samples():
            a, w1, c = map(int, self.search(r"external segment of \$(\d+)\$ and a total length of \$(\d+)\$\. "
                                            r"The second has an external segment of \$(\d+)\$", problem).groups())
            w2 = Fraction(a * w1, c)
            self.assertGreater(w1, a)
            self.assertGreater(w2, c)
            self.close(solution, float(w2), problem)


class TranslatePreimage(_Base):
    name, variant = "geo_translate_point", "preimage"

    def test(self):
        for problem, solution in self.samples():
            a, b = map(int, self.search(r"\\langle " + INT + ", " + INT + r" \\rangle", problem).groups())
            ix, iy = map(int, self.search(r"image is \$\(" + INT + ", " + INT + r"\)\$", problem).groups())
            x, y = pt(solution)
            self.assertEqual((x + a, y + b), (ix, iy), problem)


class ReflectPreimage(_Base):
    name, variant = "geo_reflect_point", "preimage"
    MAPS = {"x-axis": lambda x, y: (x, -y), "y-axis": lambda x, y: (-x, y), "line y = x": lambda x, y: (y, x)}

    def test(self):
        for problem, solution in self.samples():
            line = self.search(r"reflected over the (x-axis|y-axis|line y = x)", problem)[1]
            image = tuple(map(int, self.search(r"image is \$\(" + INT + ", " + INT + r"\)\$", problem).groups()))
            self.assertEqual(self.MAPS[line](*pt(solution)), image, problem)


class RotatePreimage(_Base):
    name, variant = "geo_rotate_point", "preimage"

    def test(self):
        for problem, solution in self.samples():
            deg = int(self.search(r"rotated \$(\d+)\^", problem)[1])
            image = tuple(map(int, self.search(r"image is \$\(" + INT + ", " + INT + r"\)\$", problem).groups()))
            x, y = pt(solution)
            t = math.radians(deg)
            rot = (round(x * math.cos(t) - y * math.sin(t)), round(x * math.sin(t) + y * math.cos(t)))
            self.assertEqual(rot, image, problem)


class DilatePreimage(_Base):
    name, variant = "geo_dilate_point", "preimage"

    def test(self):
        for problem, solution in self.samples():
            k = int(self.search(r"scale factor of \$(\d+)\$", problem)[1])
            image = tuple(map(int, self.search(r"image is \$\(" + INT + ", " + INT + r"\)\$", problem).groups()))
            x, y = pt(solution)
            self.assertEqual((k * x, k * y), image, problem)


class ConditionalMissingCell(_Base):
    name, variant = "geo_conditional_probability_table", "missing_cell"

    def test(self):
        for problem, solution in self.samples():
            row, known = map(int, self.search(r"\$(\d+)\$ people are in group A, and \$(\d+)\$", problem).groups())
            self.assertEqual(frac(solution), Fraction(row - known, row), problem)


class CompoundMissingProbability(_Base):
    name, variant = "geo_compound_probability", "missing_probability"

    def test(self):
        for problem, solution in self.samples():
            pa = frac(self.search(r"\$P\(A\) = ([\d/]+)\$", problem)[1])
            p_or = frac(self.search(r"B\) = ([\d/]+)\$", problem)[1])
            pb = frac(solution)
            self.assertEqual(pa + pb - pa * pb, p_or, problem)


class ExpectedFairPrice(_Base):
    name, variant = "geo_expected_value", "fair_price"

    def test(self):
        for problem, solution in self.samples():
            prizes = [int(v) for v in re.findall(r"\$(\d+)\$", problem.split("pays", 1)[1].split("dollars")[0])]
            self.assertEqual(len(prizes), 4)
            self.assertEqual(Fraction(solution), Fraction(sum(prizes), 4), problem)


class SimilarShadows(_Base):
    name, variant = "geo_similar_triangle_side", "shadows"

    def test(self):
        for problem, solution in self.samples():
            h, s1, s2 = map(int, self.search(r"A \$(\d+)\$-foot person casts a \$(\d+)\$-foot shadow\. At the "
                                             r"same time, a tree casts a \$(\d+)\$", problem).groups())
            self.close(solution, h * s2 / s1, problem)


class ScaleRatioReverse(_Base):
    name, variant = "geo_scale_factor_ratio", "reverse"

    def test(self):
        for problem, solution in self.samples():
            given = frac(self.search(r"in the ratio \$([\d/]+)\$", problem)[1])
            ans = frac(solution)
            if "areas in the ratio" in problem:
                self.assertEqual(ans ** 2, given, problem)
            else:
                # volume ratio = k^3, area ratio = k^2
                k = Fraction(round(given.numerator ** (1 / 3)), round(given.denominator ** (1 / 3)))
                self.assertEqual(k ** 3, given)
                self.assertEqual(ans, k ** 2, problem)


class HexagonFromTriangles(_Base):
    name, variant = "geo_regular_polygon_area", "hexagon_triangles"

    def test(self):
        for problem, solution in self.samples():
            s = int(self.search(r"sides of length \$(\d+)\$", problem)[1])
            # Generic regular-polygon formula: n s^2 / (4 tan(pi/n)).
            self.close(solution, 6 * s * s / (4 * math.tan(math.pi / 6)), problem)


class CompositeHollowPipe(_Base):
    name, variant = "geo_composite_solid", "hollow_pipe"

    def test(self):
        for problem, solution in self.samples():
            R, L, r = map(int, self.search(r"radius \$(\d+)\$ and length \$(\d+)\$ with a cylindrical hole of "
                                           r"radius \$(\d+)\$", problem).groups())
            self.assertGreater(R, r)
            self.close(solution, math.pi * (R * R - r * r) * L, problem)


class FrustumDifferenceOfCones(_Base):
    name, variant = "geo_frustum_volume", "difference_of_cones"

    def test(self):
        for problem, solution in self.samples():
            R, H = map(int, self.search(r"base radius \$(\d+)\$ and height \$(\d+)\$ has", problem).groups())
            r, h = map(Fraction, self.search(r"base radius \$([\d.]+)\$ and height \$([\d.]+)\$\. What",
                                             problem).groups())
            self.assertEqual(r / R, h / H, problem)   # the removed top is similar
            # Frustum formula: pi h_f / 3 (R^2 + R r + r^2) with h_f = H - h.
            hf = H - h
            self.close(solution, math.pi * float(hf) / 3 * (R * R + R * float(r) + float(r) ** 2), problem)


class PolygonMissingVertex(_Base):
    name, variant = "geo_polygon_area_vertices", "missing_vertex"

    def test(self):
        for problem, solution in self.samples():
            b = int(self.search(r"\$\((\d+), 0\)\$, and", problem)[1])
            p = int(self.search(r"and \$\(" + INT + r", k\)\$", problem)[1])
            area = Fraction(self.search(r"area is \$([\d.]+)\$", problem)[1])
            k = int(solution)
            pts = [(0, 0), (b, 0), (p, k)]
            shoelace = abs(sum(x1 * y2 - x2 * y1 for (x1, y1), (x2, y2) in zip(pts, pts[1:] + pts[:1])))
            self.assertGreater(k, 0)
            self.assertEqual(Fraction(shoelace, 2), area, problem)


class DistanceMissingCoordinate(_Base):
    name, variant = "distance_two_points", "missing_coordinate"

    def test(self):
        for problem, solution in self.samples():
            m = self.search(r"from \$\(" + INT + ", " + INT + r"\)\$ to \$\(" + INT + r", k\)\$ is \$(\d+)\$", problem)
            x1, y1, x2, d = (int(g) for g in m.groups())
            ks = [k for k in range(y1 + 1, y1 + 200) if (x2 - x1) ** 2 + (k - y1) ** 2 == d * d]
            self.assertEqual(ks, [int(solution)], problem)


class MidpointMissingEndpoint(_Base):
    name, variant = "midpoint_of_two_points", "missing_endpoint"

    def test(self):
        for problem, solution in self.samples():
            mx, my = map(int, self.search(r"\$M\(" + INT + ", " + INT + r"\)\$", problem).groups())
            ax, ay = map(int, self.search(r"\$A\$ is \$\(" + INT + ", " + INT + r"\)\$", problem).groups())
            bx, by = pt(solution)
            self.assertEqual(((ax + bx) / 2, (ay + by) / 2), (mx, my), problem)


class NormMissingComponent(_Base):
    name, variant = "euclidian_norm", "missing_component"

    def test(self):
        for problem, solution in self.samples():
            known, length = map(int, self.search(r"vector \$\(" + INT + r", a\)\$ has length \$(\d+)\$",
                                                 problem).groups())
            a = int(solution)
            self.assertGreater(a, 0)
            self.assertEqual(known * known + a * a, length * length, problem)


class LineCollinear(_Base):
    name, variant = "equation_of_line_from_two_points", "collinear"

    def test(self):
        for problem, solution in self.samples():
            pts = [tuple(map(int, p)) for p in re.findall(r"\((-?\d+), (-?\d+)\)", problem)]
            (x1, y1), (x2, y2) = pts
            x3 = int(self.search(r"\$\(" + INT + r", k\)\$", problem)[1])
            k = int(solution)
            self.assertEqual((y2 - y1) * (x3 - x1), (k - y1) * (x2 - x1), problem)


class PerimeterMissingSide(_Base):
    name, variant = "perimeter_of_polygons", "missing_side"

    def test(self):
        for problem, solution in self.samples():
            total = int(self.search(r"perimeter of \$(\d+)\$", problem)[1])
            known = [int(v) for v in re.findall(r"\$(\d+)\$", problem.split("sides measure", 1)[1])]
            self.assertEqual(int(solution) + sum(known), total, problem)


class TriangleCountThirdSides(_Base):
    name, variant = "valid_triangle", "count_third_sides"

    def test(self):
        for problem, solution in self.samples():
            a, b = map(int, self.search(r"length \$(\d+)\$ and \$(\d+)\$", problem).groups())
            count = sum(1 for c in range(1, 100) if a + b > c and a + c > b and b + c > a)
            self.assertEqual(int(solution), count, problem)


class PolygonSidesFromAngle(_Base):
    name, variant = "angle_regular_polygon", "sides_from_angle"

    def test(self):
        for problem, solution in self.samples():
            angle = int(self.search(r"measures \$(\d+)\^", problem)[1])
            n = int(solution)
            self.assertEqual(Fraction((n - 2) * 180, n), angle, problem)


class PolygonSidesFromSum(_Base):
    name, variant = "sum_of_polygon_angles", "sides_from_sum"

    def test(self):
        for problem, solution in self.samples():
            total = int(self.search(r"add up to \$(\d+)\^", problem)[1])
            self.assertEqual((int(solution) - 2) * 180, total, problem)


class ComplementToSupplement(_Base):
    name, variant = "complementary_and_supplementary_angle", "complement_to_supplement"

    def test(self):
        for problem, solution in self.samples():
            comp = int(self.search(r"complement of an angle measures \$(\d+)\^", problem)[1])
            angle = 90 - comp
            self.assertEqual(int(solution), 180 - angle, problem)


class ThirdAngleIsosceles(_Base):
    name, variant = "third_angle_of_triangle", "isosceles"

    def test(self):
        for problem, solution in self.samples():
            m = re.search(r"vertex angle of \$(\d+)\^", problem)
            if m:
                v = int(m[1])
                self.assertEqual(2 * int(solution) + v, 180, problem)
            else:
                base = int(self.search(r"base angle of an isosceles triangle measures \$(\d+)\^", problem)[1])
                self.assertEqual(2 * base + int(solution), 180, problem)


class FourthAngleParallelogram(_Base):
    name, variant = "fourth_angle_of_quadrilateral", "parallelogram"

    def test(self):
        for problem, solution in self.samples():
            a = int(self.search(r"angle \$A\$ measures \$(\d+)\^", problem)[1])
            which = self.search(r"measure of angle \$(B|C|D)\$", problem)[1]
            angles = {"A": a, "B": 180 - a, "C": a, "D": 180 - a}
            self.assertEqual(sum(angles.values()), 360)
            self.assertEqual(int(solution), angles[which], problem)


class DegreesExactPi(_Base):
    name, variant = "degree_to_rad", "exact_multiple_of_pi"

    def test(self):
        for problem, solution in self.samples():
            deg = int(self.search(r"Write \$(\d+)\^", problem)[1])
            self.assertEqual(frac(solution) * 180, deg, problem)


class RadiansExactPi(_Base):
    name, variant = "radian_to_deg", "exact_multiple_of_pi"

    def test(self):
        for problem, solution in self.samples():
            m = self.search(r"Convert \$(?:(\d+)|\\frac\{(\d+)\}\{(\d+)\})\\pi\$", problem)
            k = Fraction(int(m[1])) if m[1] else Fraction(int(m[2]), int(m[3]))
            self.assertEqual(Fraction(solution), k * 180, problem)


class VectorsDotFromAngle(_Base):
    name, variant = "angle_btw_vectors", "dot_from_angle"

    def test(self):
        for problem, solution in self.samples():
            a, b, t = map(int, self.search(r"lengths \$(\d+)\$ and \$(\d+)\$, and the angle between them is "
                                           r"\$(\d+)\^", problem).groups())
            self.close(solution, a * b * math.cos(math.radians(t)), problem)


class DotPerpendicularParameter(_Base):
    name, variant = "vector_dot", "perpendicular_parameter"

    def test(self):
        for problem, solution in self.samples():
            a = int(self.search(r"vectors \$\(" + INT + r", k\)\$", problem)[1])
            c, d = map(int, self.search(r"and \$\(" + INT + ", " + INT + r"\)\$ perpendicular", problem).groups())
            self.assertEqual(a * c + int(solution) * d, 0, problem)


class ComplexArgumentDegrees(_Base):
    name, variant = "complex_to_polar", "argument_degrees"

    def test(self):
        for problem, solution in self.samples():
            m = self.search(r"argument of \$" + INT + r" ([+-]) (\d+)i\$", problem)
            a = int(m[1])
            b = int(m[3]) * (1 if m[2] == "+" else -1)
            self.close(solution, math.degrees(math.atan2(b, a)), problem)


class TrigDerivativeValue(_Base):
    name, variant = "trig_differentiation", "value_at_angle"
    DERIV = {"sin": math.cos, "cos": lambda x: -math.sin(x), "tan": lambda x: 1 / math.cos(x) ** 2,
             "cot": lambda x: -1 / math.sin(x) ** 2}
    ANGLES = {r"\frac{\pi}{6}": math.pi / 6, r"\frac{\pi}{4}": math.pi / 4, r"\frac{\pi}{3}": math.pi / 3}

    def test(self):
        for problem, solution in self.samples():
            func = self.search(r"\$f\(x\) = \\(\w+) x\$", problem)[1]
            angle = self.search(r"f'\\left\((.+?)\\right\)", problem)[1]
            # Numerical derivative, independent of the generator's table.
            f = {"sin": math.sin, "cos": math.cos, "tan": math.tan, "cot": lambda x: 1 / math.tan(x)}[func]
            x = self.ANGLES[angle]
            h = 1e-6
            self.close(solution, (f(x + h) - f(x - h)) / (2 * h), problem)


class FractionTerminates(_Base):
    name, variant = "fraction_to_decimal", "terminates"

    def test(self):
        for problem, solution in self.samples():
            n, d = map(int, self.search(r"form of \$(\d+)/(\d+)\$", problem).groups())
            value = Fraction(n, d)
            terminates = any((value * 10 ** p).denominator == 1 for p in range(0, 20))
            self.assertEqual(solution, "yes" if terminates else "no", problem)


class CelsiusChange(_Base):
    name, variant = "celsius_to_fahrenheit", "change"

    def test(self):
        for problem, solution in self.samples():
            c = int(self.search(r"rises by \$(\d+)\$ degrees Celsius", problem)[1])
            to_f = lambda t: Fraction(9, 5) * t + 32  # noqa: E731
            self.assertEqual(Fraction(solution), to_f(20 + c) - to_f(20), problem)


class AngleSumTangent(_Base):
    name, variant = "angle_sum", "tangent"

    def test(self):
        for problem, solution in self.samples():
            t1 = frac(self.search(r"\\tan A = ([\d/]+)\$", problem)[1])
            t2 = frac(self.search(r"\\tan B = ([\d/]+)\$", problem)[1])
            value = math.tan(math.atan(t1) + math.atan(t2))
            self.assertAlmostEqual(float(frac(solution)), value, places=9, msg=problem)


# --- Further variants ----------------------------------------------------------------

def strip_unit(solution):
    return re.sub(r"\s*m(\^\d)?$", "", solution)


class RightTriangleComplementaryRatio(_Base):
    name, variant = "geo_right_triangle_side", "complementary_ratio"
    OF_B = {"cos": lambda A: math.cos(math.pi / 2 - A), "sin": lambda A: math.sin(math.pi / 2 - A),
            "cot": lambda A: 1 / math.tan(math.pi / 2 - A)}
    INV = {"sin": math.asin, "cos": math.acos, "tan": math.atan}

    def test(self):
        for problem, solution in self.samples():
            f, v = self.search(r"\$\\(sin|cos|tan) A = ([\d/]+)\$", problem).groups()
            g = self.search(r"What is \$\\(sin|cos|cot) B\$", problem)[1]
            A = self.INV[f](float(frac(v)))
            self.assertAlmostEqual(float(frac(solution)), self.OF_B[g](A), places=9, msg=problem)


class RightTriangleElevation(_Base):
    name, variant = "geo_right_triangle_side", "angle_of_elevation"

    def test(self):
        for problem, solution in self.samples():
            d, t = map(int, self.search(r"\$(\d+)\$ meters from the base.*is \$(\d+)\^", problem).groups())
            self.close(solution, d * math.tan(math.radians(t)), problem)


class PythagLadder(_Base):
    name, variant = "geo_solve_right_triangle_pythag", "ladder"

    def test(self):
        for problem, solution in self.samples():
            ladder, base = map(int, self.search(r"\$(\d+)\$-foot ladder .* foot \$(\d+)\$ feet", problem).groups())
            self.assertEqual(int(solution) ** 2 + base ** 2, ladder ** 2, problem)


class PythagIsRight(_Base):
    name, variant = "geo_solve_right_triangle_pythag", "is_right"

    def test(self):
        for problem, solution in self.samples():
            a, b, c = map(int, self.search(r"sides \$(\d+)\$, \$(\d+)\$, and \$(\d+)\$", problem).groups())
            angle = math.degrees(math.acos((a * a + b * b - c * c) / (2 * a * b))) if a + b > c else None
            right = angle is not None and abs(angle - 90) < 1e-9
            self.assertEqual(solution, "yes" if right else "no", problem)


class PythagoreanSpaceDiagonal(_Base):
    name, variant = "pythagorean_theorem", "space_diagonal"

    def test(self):
        for problem, solution in self.samples():
            l, w, h = map(int, self.search(r"measures \$(\d+)\$ by \$(\d+)\$ by \$(\d+)\$", problem).groups())
            self.close(solution, math.dist((0, 0, 0), (l, w, h)), problem)


class SpecialLegFromHypotenuse(_Base):
    name, variant = "geo_special_right_triangle", "leg_from_hypotenuse"

    def test(self):
        for problem, solution in self.samples():
            h = int(self.search(r"hypotenuse of length \$(\d+)\$", problem)[1])
            self.close(solution, h * math.sin(math.pi / 4), problem)


class CircleEquationCenterAndPoint(_Base):
    name, variant = "geo_circle_equation_from_center_radius", "center_and_point"

    def test(self):
        for problem, solution in self.samples():
            (h, k), (x, y) = [tuple(map(int, p)) for p in re.findall(r"\((-?\d+), (-?\d+)\)", problem)]
            self.assertEqual(circle_equation(solution), (h, k, (x - h) ** 2 + (y - k) ** 2), problem)


class CircleInsideOrOutside(_Base):
    name, variant = "geo_circle_equation_from_center_radius", "inside_or_outside"

    def test(self):
        seen = set()
        for problem, solution in self.samples():
            x, y = map(int, self.search(r"point \$\(" + INT + ", " + INT + r"\)\$", problem).groups())
            h, k, c = circle_equation(self.search(r"circle \$([^$]+)\$\?", problem)[1])
            d = math.dist((x, y), (h, k))
            want = "on" if abs(d - math.sqrt(c)) < 1e-9 else ("inside" if d < math.sqrt(c) else "outside")
            self.assertEqual(solution, want, problem)
            seen.add(want)
        self.assertEqual(seen, {"inside", "on", "outside"})


class CircleConstantForRadius(_Base):
    name, variant = "geo_circle_center_radius_from_equation", "constant_for_radius"

    def test(self):
        for problem, solution in self.samples():
            m = self.search(r"\$x\^2 \+ y\^2 ([+-]) (\d+)x ([+-]) (\d+)y \+ c = 0\$.*radius \$(\d+)\$", problem)
            D = int(m[2]) * (1 if m[1] == "+" else -1)
            E = int(m[4]) * (1 if m[3] == "+" else -1)
            r = int(m[5])
            c = int(solution)
            self.assertEqual(Fraction(D * D + E * E, 4) - c, r * r, problem)


class CircleDiameter(_Base):
    name, variant = "geo_circle_center_radius_from_equation", "diameter"

    def test(self):
        for problem, solution in self.samples():
            _, _, c = circle_equation(self.search(r"circle \$([^$]+)\$\?", problem)[1])
            self.assertEqual(int(solution) ** 2, 4 * c, problem)


class InscribedTangentChord(_Base):
    name, variant = "geo_inscribed_angle", "tangent_chord"

    def test(self):
        for problem, solution in self.samples():
            m = re.search(r"arc they intercept measures \$(\d+)\^", problem)
            if m:
                self.assertEqual(2 * int(solution), int(m[1]), problem)
            else:
                a = int(self.search(r"forming a \$(\d+)\^", problem)[1])
                self.assertEqual(int(solution), 2 * a, problem)


class CircleWholeChord(_Base):
    name, variant = "geo_circle_segments", "whole_chord"

    def test(self):
        for problem, solution in self.samples():
            a, b, c = map(int, self.search(r"segments of \$(\d+)\$ and \$(\d+)\$\. The other has one segment of "
                                           r"length \$(\d+)\$", problem).groups())
            self.assertEqual(c * (int(solution) - c), a * b, problem)


class CircleTangentLength(_Base):
    name, variant = "geo_circle_segments", "tangent_length"

    def test(self):
        for problem, solution in self.samples():
            e, w = map(int, self.search(r"external segment \$(\d+)\$ and total length \$(\d+)\$", problem).groups())
            self.assertGreater(w, e)
            self.assertEqual(int(solution) ** 2, e * w, problem)


class CircleAreaScale(_Base):
    name, variant = "area_of_circle", "scale_radius"

    def test(self):
        for problem, solution in self.samples():
            k = int(self.search(r"multiplied by \$(\d+)\$", problem)[1])
            self.assertAlmostEqual(float(solution), (math.pi * (3 * k) ** 2) / (math.pi * 9), places=9)


class CircleAnnulus(_Base):
    name, variant = "area_of_circle", "annulus"

    def test(self):
        for problem, solution in self.samples():
            r, R = map(int, self.search(r"radii \$(\d+)\$ and \$(\d+)\$", problem).groups())
            self.close(solution, math.pi * R * R - math.pi * r * r, problem)


class CircumferenceWheel(_Base):
    name, variant = "circumference", "wheel_revolutions"

    def test(self):
        for problem, solution in self.samples():
            d, m = map(int, self.search(r"diameter of \$(\d+)\$ cm.*rolling \$(\d+)\$ meters", problem).groups())
            self.close(solution, m * 100 / (math.pi * d), problem)


class CircumferenceSemicircle(_Base):
    name, variant = "circumference", "semicircle_perimeter"

    def test(self):
        for problem, solution in self.samples():
            r = int(self.search(r"radius \$(\d+)\$", problem)[1])
            self.close(solution, 2 * math.pi * r / 2 + 2 * r, problem)


class SectorRadians(_Base):
    name, variant = "sector_area", "radians"

    def test(self):
        for problem, solution in self.samples():
            r, t = self.search(r"radius \$(\d+)\$ and a central angle of \$([\d.]+)\$ radians", problem).groups()
            r, t = int(r), Fraction(t)
            # As a fraction of the whole circle: (t / 2pi) * pi r^2.
            self.close(solution, float(t) / (2 * math.pi) * math.pi * r * r, problem)


class ArcRadians(_Base):
    name, variant = "arc_length", "radians"

    def test(self):
        for problem, solution in self.samples():
            r, t = self.search(r"radius \$(\d+)\$ has a central angle of \$([\d.]+)\$ radians", problem).groups()
            self.close(solution, float(t) / (2 * math.pi) * 2 * math.pi * int(r), problem)


class ArcClockHand(_Base):
    name, variant = "arc_length", "clock_hand"

    def test(self):
        for problem, solution in self.samples():
            length, minutes = map(int, self.search(r"\$(\d+)\$ cm long.*in \$(\d+)\$ minutes", problem).groups())
            self.close(solution, math.radians(6 * minutes) * length, problem)


class TranslateFindVector(_Base):
    name, variant = "geo_translate_point", "find_the_vector"

    def test(self):
        for problem, solution in self.samples():
            (x, y), (x2, y2) = [tuple(map(int, p)) for p in re.findall(r"\((-?\d+), (-?\d+)\)", problem)]
            want = x2 - x if "horizontal" in problem else y2 - y
            self.assertEqual(int(solution), want, problem)


class TranslateTwice(_Base):
    name, variant = "geo_translate_point", "two_translations"

    def test(self):
        for problem, solution in self.samples():
            x, y = map(int, self.search(r"point \$\(" + INT + ", " + INT, problem).groups())
            for a, b in re.findall(r"\\langle (-?\d+), (-?\d+) \\rangle", problem):
                x, y = x + int(a), y + int(b)
            self.assertEqual(pt(solution), (x, y), problem)


class ReflectTwice(_Base):
    name, variant = "geo_reflect_point", "two_reflections"

    def test(self):
        for problem, solution in self.samples():
            x, y = map(int, self.search(r"point \$\(" + INT + ", " + INT, problem).groups())
            for axis in re.findall(r"over the (x|y)-axis", problem):
                x, y = (x, -y) if axis == "x" else (-x, y)
            self.assertEqual(pt(solution), (x, y), problem)


class RotateAboutPoint(_Base):
    name, variant = "geo_rotate_point", "about_a_point"

    def test(self):
        for problem, solution in self.samples():
            (x, y), (cx, cy) = [tuple(map(int, p)) for p in re.findall(r"\((-?\d+), (-?\d+)\)", problem)]
            t = math.radians(int(self.search(r"by \$(\d+)\^", problem)[1]))
            dx, dy = x - cx, y - cy
            want = (round(cx + dx * math.cos(t) - dy * math.sin(t)), round(cy + dx * math.sin(t) + dy * math.cos(t)))
            self.assertEqual(pt(solution), want, problem)


class DilateAboutPoint(_Base):
    name, variant = "geo_dilate_point", "about_a_point"

    def test(self):
        for problem, solution in self.samples():
            (x, y), (cx, cy) = [tuple(map(int, p)) for p in re.findall(r"\((-?\d+), (-?\d+)\)", problem)]
            k = frac(self.search(r"scale factor of \$([\d/]+)\$", problem)[1])
            self.assertEqual(pt(solution), (cx + k * (x - cx), cy + k * (y - cy)), problem)


class DilateImageLength(_Base):
    name, variant = "geo_dilate_point", "image_length"

    def test(self):
        for problem, solution in self.samples():
            length = int(self.search(r"is \$(\d+)\$ units long", problem)[1])
            k = frac(self.search(r"scale factor of \$([\d/]+)\$", problem)[1])
            # Dilate the endpoints (0, 0) and (length, 0) about (3, 4) and measure the image.
            img = [(3 + k * (px - 3), 4 + k * (py - 4)) for px, py in ((0, 0), (length, 0))]
            self.assertEqual(Fraction(solution), abs(img[1][0] - img[0][0]), problem)


def table_counts(problem):
    return {k: int(v) for k, v in re.findall(r"([AB][XY]): (\d+)", problem.replace("&", ""))}


class ConditionalIndependent(_Base):
    name, variant = "geo_conditional_probability_table", "independent"

    def test(self):
        seen = set()
        for problem, solution in self.samples():
            c = table_counts(problem)
            total = sum(c.values())
            independent = Fraction(c["AX"], total) == Fraction(c["AX"] + c["AY"], total) * Fraction(c["AX"] + c["BX"], total)
            self.assertEqual(solution, "yes" if independent else "no", problem)
            seen.add(solution)
        self.assertEqual(seen, {"yes", "no"})


class ConditionalJoint(_Base):
    name, variant = "geo_conditional_probability_table", "joint"

    def test(self):
        for problem, solution in self.samples():
            c = table_counts(problem)
            row, col = self.search(r"P\(([AB]) \\text\{ and \} ([XY])\)", problem).groups()
            self.assertEqual(frac(solution), Fraction(c[row + col], sum(c.values())), problem)


class CompoundAtLeastOneOfN(_Base):
    name, variant = "geo_compound_probability", "at_least_one_of_n"

    def test(self):
        for problem, solution in self.samples():
            p = frac(self.search(r"probability \$([\d/]+)\$", problem)[1])
            n = int(self.search(r"In \$(\d+)\$ attempts", problem)[1])
            total = sum(math.comb(n, k) * p ** k * (1 - p) ** (n - k) for k in range(1, n + 1))
            self.assertEqual(frac(solution), total, problem)


class CompoundAAndNotB(_Base):
    name, variant = "geo_compound_probability", "a_and_not_b"

    def test(self):
        for problem, solution in self.samples():
            pa = frac(self.search(r"\$P\(A\) = ([\d/]+)\$", problem)[1])
            pb = frac(self.search(r"\$P\(B\) = ([\d/]+)\$", problem)[1])
            self.assertEqual(frac(solution), pa - pa * pb, problem)


class ExpectedMissingProbability(_Base):
    name, variant = "geo_expected_value", "missing_probability"

    def test(self):
        for problem, solution in self.samples():
            p1, p2 = map(Fraction, self.search(r"probabilities \$([\d.]+)\$, \$([\d.]+)\$, and \$p\$", problem).groups())
            self.assertEqual(Fraction(solution) + p1 + p2, 1, problem)


class ExpectedRaffle(_Base):
    name, variant = "geo_expected_value", "raffle"

    def test(self):
        for problem, solution in self.samples():
            tickets, price, prize = map(int, self.search(r"sells \$(\d+)\$ tickets for \$(\d+)\$ dollars each, and one "
                                                         r"ticket wins \$(\d+)\$", problem).groups())
            ev = Fraction(1, tickets) * (prize - price) + Fraction(tickets - 1, tickets) * (-price)
            self.assertEqual(Fraction(solution), ev, problem)


class SimilarSideSplitter(_Base):
    name, variant = "geo_similar_triangle_side", "side_splitter"

    def test(self):
        for problem, solution in self.samples():
            ad, db, ae = map(int, self.search(r"\$AD = (\d+)\$, \$DB = (\d+)\$, and \$AE = (\d+)\$", problem).groups())
            ec = Fraction(ae * db, ad)
            # AD/AB = AE/AC (the smaller triangle is similar to the whole).
            self.assertEqual(Fraction(ad, ad + db), ae / (ae + ec))
            self.close(solution, float(ec), problem)


class SimilarScaleFromPerimeters(_Base):
    name, variant = "geo_similar_triangle_side", "scale_from_perimeters"

    def test(self):
        for problem, solution in self.samples():
            p1, p2 = self.search(r"perimeters \$(\d+)\$ and \$([\d.]+)\$", problem).groups()
            self.assertEqual(frac(solution), Fraction(p2) / int(p1), problem)


class ScaleScaledArea(_Base):
    name, variant = "geo_scale_factor_ratio", "scaled_area"

    def test(self):
        for problem, solution in self.samples():
            k = frac(self.search(r"scale factor of \$([\d/]+)\$", problem)[1])
            m = re.search(r"area \$(\d+)\$", problem)
            if m:
                self.assertEqual(Fraction(solution), int(m[1]) * k ** 2, problem)
            else:
                v = int(self.search(r"volume \$(\d+)\$", problem)[1])
                self.assertEqual(Fraction(solution), v * k ** 3, problem)


class RegularPolygonApothem(_Base):
    name, variant = "geo_regular_polygon_area", "apothem_from_area"

    def test(self):
        for problem, solution in self.samples():
            n, side, area = self.search(r"regular (\d+)-sided polygon has sides of length \$(\d+)\$ and an area "
                                        r"of \$([\d.]+)\$", problem).groups()
            self.assertEqual(Fraction(solution) * int(n) * int(side) / 2, Fraction(area), problem)


class CompositeFillTime(_Base):
    name, variant = "geo_composite_solid", "fill_time"

    def test(self):
        for problem, solution in self.samples():
            l, w, d, rate = self.search(r"\$(\d+)\$ m long, \$(\d+)\$ m wide, and \$(\d+)\$ m deep.*at \$([\d.]+)\$",
                                        problem).groups()
            self.assertEqual(Fraction(solution) * Fraction(rate), int(l) * int(w) * int(d), problem)


class NormUnitVector(_Base):
    name, variant = "euclidian_norm", "unit_vector"

    def test(self):
        for problem, solution in self.samples():
            a, b = map(int, self.search(r"as \$\(" + INT + ", " + INT + r"\)\$", problem).groups())
            want = (a if "first" in problem else b) / math.hypot(a, b)
            self.close(solution, want, problem)


class LineXIntercept(_Base):
    name, variant = "equation_of_line_from_two_points", "x_intercept"

    def test(self):
        for problem, solution in self.samples():
            (x1, y1), (x2, y2) = [tuple(map(int, p)) for p in re.findall(r"\((-?\d+), (-?\d+)\)", problem)]
            x0 = frac(solution)
            # (x0, 0) is collinear with the two points.
            self.assertEqual((y2 - y1) * (x0 - x1), (0 - y1) * (x2 - x1), problem)


class LineReceipts(_Base):
    name, variant = "equation_of_line_from_two_points", "receipts"

    def test(self):
        for problem, solution in self.samples():
            c1, h1, c2, h2 = map(int, self.search(r"charged \$(\d+)\$ dollars for a \$(\d+)\$-hour job and \$(\d+)\$ "
                                                  r"dollars for a \$(\d+)\$-hour", problem).groups())
            m, b = map(int, re.fullmatch(r"y = (\d+)x \+ (\d+)", solution).groups())
            self.assertEqual((m * h1 + b, m * h2 + b), (c1, c2), problem)


class PerimeterRegularSide(_Base):
    name, variant = "perimeter_of_polygons", "regular_side"

    def test(self):
        for problem, solution in self.samples():
            n, p = map(int, self.search(r"\$(\d+)\$ sides has a perimeter of \$(\d+)\$", problem).groups())
            self.assertEqual(n * int(solution), p, problem)


class PerimeterFenceGate(_Base):
    name, variant = "perimeter_of_polygons", "fence_with_gate"

    def test(self):
        for problem, solution in self.samples():
            l, w, gate = map(int, self.search(r"is \$(\d+)\$ m by \$(\d+)\$ m.*a \$(\d+)\$ m gate", problem).groups())
            self.assertEqual(int(solution), l + w + l + w - gate, problem)


class TriangleLongestThirdSide(_Base):
    name, variant = "valid_triangle", "longest_third_side"

    def test(self):
        for problem, solution in self.samples():
            a, b = map(int, self.search(r"are \$(\d+)\$ and \$(\d+)\$", problem).groups())
            ok = [c for c in range(1, 200) if a + b > c and a + c > b and b + c > a]
            self.assertEqual(int(solution), max(ok) if "largest" in problem else min(ok), problem)


class PolygonExteriorAngle(_Base):
    name, variant = "angle_regular_polygon", "exterior_angle"

    def test(self):
        for problem, solution in self.samples():
            n = int(self.search(r"with \$(\d+)\$ sides", problem)[1])
            self.close(solution, 180 - (n - 2) * 180 / n, problem)


class PolygonMissingAngle(_Base):
    name, variant = "sum_of_polygon_angles", "missing_angle"

    def test(self):
        for problem, solution in self.samples():
            n = int(self.search(r"with \$(\d+)\$ sides", problem)[1])
            angles = [int(v) for v in re.findall(r"\$(\d+)\^\\circ\$", problem)]
            self.assertEqual(len(angles), n - 1)
            self.assertEqual(sum(angles) + int(solution), (n - 2) * 180, problem)


class PolygonTiles(_Base):
    name, variant = "angle_regular_polygon", "tiles_the_plane"

    def test(self):
        for problem, solution in self.samples():
            n = int(self.search(r"with \$(\d+)\$ sides", problem)[1])
            self.assertEqual(solution, "yes" if n in (3, 4, 6) else "no", problem)


class DotRevenue(_Base):
    name, variant = "vector_dot", "revenue"

    def test(self):
        for problem, solution in self.samples():
            nums = [int(v) for v in re.findall(r"\$(\d+)\$", problem)]
            prices, qty = nums[:3], nums[3:6]
            self.assertEqual(int(solution), sum(p * q for p, q in zip(prices, qty)), problem)


class DotSelf(_Base):
    name, variant = "vector_dot", "self_dot"

    def test(self):
        for problem, solution in self.samples():
            u = [int(v) for v in self.search(r"\\langle ([^\\]+) \\rangle", problem)[1].split(", ")]
            self.assertEqual(int(solution), round(math.hypot(*u) ** 2), problem)


class VectorsAngleDegrees(_Base):
    name, variant = "angle_btw_vectors", "degrees"

    def test(self):
        for problem, solution in self.samples():
            (a, b), (c, d) = [tuple(map(int, p)) for p in re.findall(r"\((-?\d+), (-?\d+)\)", problem)]
            angle = abs(math.degrees(math.atan2(b, a) - math.atan2(d, c)))
            angle = 360 - angle if angle > 180 else angle
            self.close(solution, angle, problem)


class DegreesCoterminal(_Base):
    name, variant = "degree_to_rad", "coterminal"

    def test(self):
        for problem, solution in self.samples():
            deg = int(self.search(r"coterminal with \$" + INT, problem)[1])
            ans = int(solution)
            self.assertTrue(0 <= ans < 360)
            self.assertEqual((deg - ans) % 360, 0, problem)


class RadiansWheel(_Base):
    name, variant = "radian_to_deg", "wheel_turns"

    def test(self):
        for problem, solution in self.samples():
            turns = float(self.search(r"turns \$([\d.]+)\$ revolutions", problem)[1])
            self.close(solution, math.radians(360 * turns), problem)


class ComplexModulusOnly(_Base):
    name, variant = "complex_to_polar", "modulus"

    def test(self):
        for problem, solution in self.samples():
            m = self.search(r"modulus of \$" + INT + r" ([+-]) (\d+)i\$", problem)
            self.close(solution, abs(complex(int(m[1]), int(m[3]) * (1 if m[2] == "+" else -1))), problem)


class FractionRepeatingBlock(_Base):
    name, variant = "fraction_to_decimal", "repeating_block"

    def test(self):
        for problem, solution in self.samples():
            n, d = map(int, self.search(r"decimal for \$(\d+)/(\d+)\$", problem).groups())
            # Long division: find when a remainder first repeats.
            seen, rem, pos = {}, n % d, 0
            while rem and rem not in seen:
                seen[rem] = pos
                rem = rem * 10 % d
                pos += 1
            length = pos - seen[rem] if rem else 0
            self.assertEqual(int(solution), length, problem)


class FahrenheitToCelsius(_Base):
    name, variant = "celsius_to_fahrenheit", "fahrenheit_to_celsius"

    def test(self):
        for problem, solution in self.samples():
            f = int(self.search(r"Convert \$" + INT, problem)[1])
            self.close(solution, (f - 32) / 1.8, problem)


class CubeEdgeFromVolume(_Base):
    name, variant = "volume_cube", "edge_from_volume"

    def test(self):
        for problem, solution in self.samples():
            v = int(self.search(r"volume of \$(\d+)\$", problem)[1])
            self.assertEqual(int(strip_unit(solution)) ** 3, v, problem)


class CubeScaleEdge(_Base):
    name, variant = "volume_cube", "scale_edge"

    def test(self):
        for problem, solution in self.samples():
            v, k = map(int, self.search(r"volume of \$(\d+)\$ cubic meters\. Every edge is made \$(\d+)\$", problem).groups())
            edge = v ** (1 / 3)
            self.close(strip_unit(solution), (k * edge) ** 3, problem)


class CubeEdgeFromArea(_Base):
    name, variant = "surface_area_cube", "edge_from_area"

    def test(self):
        for problem, solution in self.samples():
            a = int(self.search(r"surface area of \$(\d+)\$", problem)[1])
            self.assertEqual(6 * int(strip_unit(solution)) ** 2, a, problem)


class CubePaintCans(_Base):
    name, variant = "surface_area_cube", "paint_cans"

    def test(self):
        for problem, solution in self.samples():
            s_len, cover = map(int, self.search(r"with \$(\d+)\$ m edges.*covers \$(\d+)\$", problem).groups())
            cans = int(solution)
            self.assertGreaterEqual(cans * cover, 6 * s_len ** 2)
            self.assertLess((cans - 1) * cover, 6 * s_len ** 2, problem)


class CuboidMissingDimension(_Base):
    name, variant = "volume_cuboid", "missing_dimension"

    def test(self):
        for problem, solution in self.samples():
            v, l, w = map(int, self.search(r"volume of \$(\d+)\$.*length of \$(\d+)\$ m, and a width of \$(\d+)\$",
                                           problem).groups())
            self.assertEqual(l * w * int(strip_unit(solution)), v, problem)


class CuboidLiters(_Base):
    name, variant = "volume_cuboid", "liters"

    def test(self):
        for problem, solution in self.samples():
            l, w, h = map(int, self.search(r"measures \$(\d+)\$ cm by \$(\d+)\$ cm by \$(\d+)\$ cm", problem).groups())
            self.assertEqual(Fraction(solution) * 1000, l * w * h, problem)


class CuboidAreaMissingDimension(_Base):
    name, variant = "surface_area_cuboid", "missing_dimension"

    def test(self):
        for problem, solution in self.samples():
            a, l, w = map(int, self.search(r"surface area of \$(\d+)\$.*length of \$(\d+)\$ m, and a width of "
                                           r"\$(\d+)\$", problem).groups())
            h = int(strip_unit(solution))
            self.assertEqual(2 * (l * w + l * h + w * h), a, problem)


class CylinderHeightFromVolume(_Base):
    name, variant = "volume_cylinder", "height_from_volume"

    def test(self):
        for problem, solution in self.samples():
            r, k = map(int, self.search(r"radius \$(\d+)\$ m and volume \$(\d+)\\pi\$", problem).groups())
            self.assertEqual(r * r * int(strip_unit(solution)), k, problem)


class CylinderCanLabel(_Base):
    name, variant = "curved_surface_area_cylinder", "can_label"

    def test(self):
        for problem, solution in self.samples():
            d, h = map(int, self.search(r"diameter \$(\d+)\$ m and height \$(\d+)\$ m", problem).groups())
            self.close(strip_unit(solution), 2 * math.pi * (d / 2) * h, problem)


class CylinderOpenTop(_Base):
    name, variant = "surface_area_cylinder", "open_top"

    def test(self):
        for problem, solution in self.samples():
            r, h = map(int, self.search(r"radius \$(\d+)\$ m and height \$(\d+)\$ m", problem).groups())
            full = 2 * math.pi * r * r + 2 * math.pi * r * h
            self.close(strip_unit(solution), full - math.pi * r * r, problem)


class ConeFromCylinder(_Base):
    name, variant = "volume_cone", "from_cylinder"

    def test(self):
        for problem, solution in self.samples():
            v = int(self.search(r"holds \$(\d+)\$", problem)[1])
            self.assertEqual(3 * Fraction(strip_unit(solution)), v, problem)


class ConeLateral(_Base):
    name, variant = "surface_area_cone", "lateral_only"

    def test(self):
        for problem, solution in self.samples():
            r, l = map(int, self.search(r"radius \$(\d+)\$ m and slant height \$(\d+)\$ m", problem).groups())
            total = math.pi * r * r + math.pi * r * l
            self.close(strip_unit(solution), total - math.pi * r * r, problem)


class SphereRadiusFromVolume(_Base):
    name, variant = "volume_sphere", "radius_from_volume"

    def test(self):
        for problem, solution in self.samples():
            m = self.search(r"volume of \$(?:(\d+)|\\frac\{(\d+)\}\{(\d+)\})\\pi\$", problem)
            coef = Fraction(int(m[1])) if m[1] else Fraction(int(m[2]), int(m[3]))
            r = int(strip_unit(solution))
            self.assertEqual(Fraction(4, 3) * r ** 3, coef, problem)


class SphereHowManyFit(_Base):
    name, variant = "volume_sphere", "how_many_fit"

    def test(self):
        for problem, solution in self.samples():
            r, R = map(int, self.search(r"radius \$(\d+)\$ cm have the same total volume as one ball of radius "
                                        r"\$(\d+)\$", problem).groups())
            self.assertEqual(int(solution) * r ** 3, R ** 3, problem)


class HemisphereFromDiameter(_Base):
    name, variant = "volume_hemisphere", "from_diameter"

    def test(self):
        for problem, solution in self.samples():
            d = int(self.search(r"diameter of \$(\d+)\$", problem)[1])
            self.close(strip_unit(solution), 4 / 3 * math.pi * (d / 2) ** 3 / 2, problem)


class SphereRadiusFromArea(_Base):
    name, variant = "surface_area_sphere", "radius_from_area"

    def test(self):
        for problem, solution in self.samples():
            k = int(self.search(r"surface area of \$(\d+)\\pi\$", problem)[1])
            self.assertEqual(4 * int(strip_unit(solution)) ** 2, k, problem)


class PyramidHeightFromVolume(_Base):
    name, variant = "volume_pyramid", "height_from_volume"

    def test(self):
        for problem, solution in self.samples():
            base, vol = self.search(r"base area of \$(\d+)\$ square meters and a volume of \$([\d.]+)\$", problem).groups()
            self.assertEqual(Fraction(int(base) * int(strip_unit(solution)), 3), Fraction(vol), problem)


class PyramidSlantFromArea(_Base):
    name, variant = "surface_area_pyramid", "slant_from_area"

    def test(self):
        for problem, solution in self.samples():
            side, area = map(int, self.search(r"base edges of \$(\d+)\$ m and a total surface area of \$(\d+)\$",
                                              problem).groups())
            slant = int(strip_unit(solution))
            self.assertEqual(side * side + 4 * Fraction(side * slant, 2), area, problem)


class TriangleHeightFromArea(_Base):
    name, variant = "area_of_triangle", "height_from_area"

    def test(self):
        for problem, solution in self.samples():
            area, b = self.search(r"area of \$([\d.]+)\$ square meters and a base of \$(\d+)\$", problem).groups()
            self.assertEqual(Fraction(int(b) * int(strip_unit(solution)), 2), Fraction(area), problem)
