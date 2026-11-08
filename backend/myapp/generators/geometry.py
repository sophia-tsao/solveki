"""Solveki-local geometry / trigonometry generators."""
import random
from math import gcd

from ._registry import register
from ._steps import Steps, tex_frac


@register
def angle_sum():
    r"""Angle Sum

    Given sin/cos/tan of two acute angles from Pythagorean triples, find a
    trig function of their sum as a simplified fraction.
    """
    triples = [
        [3, 4, 5],
        [5, 12, 13],
        [7, 24, 25],
        [8, 15, 17],
        [9, 40, 41],
        [12, 35, 37],
        [20, 21, 29],
    ]
    functions = []
    fractions = []
    triangles = [random.choice(triples), random.choice(triples)]
    for i in range(2):
        functions.append(random.choice(["sin", "cos", "tan"]))
        if functions[i] == "sin":
            fractions.append(f"{triangles[i][0]}/{triangles[i][2]}")
        elif functions[i] == "cos":
            fractions.append(f"{triangles[i][1]}/{triangles[i][2]}")
        else:
            fractions.append(f"{triangles[i][0]}/{triangles[i][1]}")
    ans_func = random.choice(["sin", "cos"])
    if ans_func == "sin":
        numerator = triangles[0][0] * triangles[1][1] + triangles[1][0] * triangles[0][1]
        denominator = triangles[0][2] * triangles[1][2]
    else:
        numerator = triangles[0][1] * triangles[1][1] - triangles[0][0] * triangles[1][0]
        denominator = triangles[0][2] * triangles[1][2]
    g = gcd(numerator, denominator)
    raw_numerator, raw_denominator = numerator, denominator
    numerator //= g
    denominator //= g
    ans = f"{int(numerator)}/{int(denominator)}"
    problem = (
        f"For positive acute angles A and B, it is known that "
        f"$\\{functions[0]} A = {fractions[0]}$ and $\\{functions[1]} B = {fractions[1]}$. "
        f"Find the value of $\\{ans_func}(A+B)$ in the simplest form as a fraction."
    )
    solution = f"${ans}$"

    s = Steps()
    for angle, (opp, adj, hyp), func in zip("AB", triangles, functions):
        s.step(
            rf"Since $\{func} {angle}$ is given, ${angle}$ is an angle in a right triangle "
            rf"with opposite side ${opp}$, adjacent side ${adj}$, and hypotenuse ${hyp}$. "
            "Read off its sine and cosine.",
            rf"\sin {angle} = {tex_frac(opp, hyp)}, \quad \cos {angle} = {tex_frac(adj, hyp)}",
        )
    (a_opp, a_adj, a_hyp), (b_opp, b_adj, b_hyp) = triangles
    if ans_func == "sin":
        s.formula("The angle sum identity for sine", r"\sin(A+B) = \sin A \cos B + \cos A \sin B")
        s.substitute(
            rf"\sin(A+B) = {tex_frac(a_opp, a_hyp)} \cdot {tex_frac(b_adj, b_hyp)} + "
            rf"{tex_frac(a_adj, a_hyp)} \cdot {tex_frac(b_opp, b_hyp)} = {tex_frac(raw_numerator, raw_denominator)}",
            text="Substitute the sines and cosines.",
        )
    else:
        s.formula("The angle sum identity for cosine", r"\cos(A+B) = \cos A \cos B - \sin A \sin B")
        s.substitute(
            rf"\cos(A+B) = {tex_frac(a_adj, a_hyp)} \cdot {tex_frac(b_adj, b_hyp)} - "
            rf"{tex_frac(a_opp, a_hyp)} \cdot {tex_frac(b_opp, b_hyp)} = {tex_frac(raw_numerator, raw_denominator)}",
            text="Substitute the sines and cosines.",
        )
    if g != 1:
        s.step(
            f"Simplify by dividing the numerator and denominator by ${g}$.",
            tex_frac(numerator, denominator),
        )
    s.answer(solution)
    return problem, solution, s.done()
