"""Solveki-local problem generators.

These extend the stock ``mathgenerator`` library with generators we maintain
ourselves. ``_make_problem_for_topic`` resolves a name here first, then falls back to
``mathgenerator``.

To add a generator: write a function returning ``(problem, solution)`` in the
appropriate category module and decorate it with ``@register``. Then import
that module below so its registration runs. The contract test in
``test_generators.py`` automatically covers every registered generator.

A generator should also return a step-by-step explanation as a third value,
``(problem, solution, steps)``, built with ``_steps.Steps``. A student sees it
after missing both attempts, so write it like a Khan Academy / DeltaMath
worked example:

- 2-6 steps, one action each, using the problem's actual numbers.
- Name the formula or rule before using it.
- Round only at the very end, in both the answer and the steps. Compute with
  exact values and keep intermediates exact (a fraction, a root, a multiple
  of pi, or the full terminating decimal). A value shown with ``\\approx`` is
  for reading only: the next step uses the unrounded value or expression,
  never the rounded number.
- Round the answer with ``_format.num`` straight from the unrounded value
  (never ``round()`` it first): ``num`` also records the truncated form, so a
  student who truncates to the stated place (2.666 for 8/3) is marked correct.
- End on the final value in the form the student must type it (e.g.
  "Rounded to the nearest thousandth, the answer is $12.566$.").
- Special branches (e.g. "no solution") get their own steps explaining why.

Preview the wording with ``python manage.py preview_steps <generator_name>``.
"""
from ._registry import LOCAL_GENERATORS, register  # noqa: F401

# Import each category module for its @register side effects. Add new modules
# here as you create them (e.g. calculus, geometry).
from . import (  # noqa: F401,E402
    algebra,
    algebra1,
    algebra2,
    ap_precalc_functions,
    ap_precalc_matrices,
    ap_precalc_trig,
    arithmetic,
    calculus,
    geometry,
    geometry_hs,
    prealgebra,
    precalculus,
    sets_gen,
    statistics_gen,
)

# Local overrides of broken stock ``mathgenerator`` generators. Each module
# registers generators whose names match a library generator, so they take
# precedence in ``_make_problem_for_topic`` (which resolves LOCAL_GENERATORS
# first). They fix untypeable answers, missing format/rounding instructions,
# broken rendering, and outright wrong answers in the library versions.
from . import (  # noqa: F401,E402
    lib_algebra_extra_gen,
    lib_angles_gen,
    lib_arith_gen,
    lib_finance_gen,
    lib_fractions_gen,
    lib_geometry_gen,
    lib_powers_gen,
    lib_seqstats_gen,
    lib_solids_gen,
)

# Extra question types ("variants") for existing topics. Each module attaches
# variants to the dispatchers in its matching category module.
from . import (  # noqa: F401,E402
    prealgebra_variants,
    algebra1_variants,
    geometry_variants,
    statistics_variants,
    algebra2_variants,
    precalculus_variants,
    ap_precalc_variants,
    calculus_variants,
    arithmetic_variants,
)

__all__ = ["LOCAL_GENERATORS", "register"]
