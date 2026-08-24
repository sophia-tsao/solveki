"""Category taxonomy and pure selection/seeding logic for the diagnostic test.

The diagnostic solves the onboarding "cold start": a new user faces ~340 topics
with no idea which to pick. A few profile questions plus a handful of real
generated problems infer the user's level per math *category*, and this module
turns that into (a) which courses of each category to select and (b) how to seed
each selected topic's SM-2 schedule.

Kept free of Django models and HTTP so the level-inference and seeding rules can
be unit-tested in isolation (mirrors how ``myapp.srs`` is structured). The view
layer (``myapp.views.diagnostic``) resolves these course names to ``Topic`` rows,
generates calibration problems, and writes ``UserTopicSelection`` / ``TopicReview``.
"""

from . import srs

# Each category is an ordered (by grade) list of course names drawn verbatim from
# seed_courses.CURRICULUM. A topic's category comes from its course; grade_level
# supplies the within-category level ramp. Authored here rather than as a DB field
# so adding the feature needs no migration and no fragile generator-module guessing.
DIAGNOSTIC_CATEGORIES = [
    {"key": "elementary", "label": "Elementary Math",
     "courses": ["Grade 1", "Grade 2", "Grade 3", "Grade 4", "Grade 5"]},
    {"key": "middle", "label": "Middle School Math",
     "courses": ["Grade 6", "Grade 7", "Grade 8"]},
    {"key": "algebra", "label": "Algebra",
     "courses": ["Algebra I", "Algebra II"]},
    {"key": "geometry", "label": "Geometry",
     "courses": ["Geometry"]},
    {"key": "statistics", "label": "Statistics & Probability",
     "courses": ["Statistical Reasoning"]},
    {"key": "precalculus", "label": "Pre-Calculus",
     "courses": ["Pre-Calculus"]},
    {"key": "calculus", "label": "Calculus",
     "courses": ["AP Calculus"]},
]

# Curriculum order of course names, flattened from the categories low->high. Used
# to break grade-level ties in the course dropdown: Statistical Reasoning,
# Pre-Calculus and AP Calculus are all grade 12, and plain alphabetical order
# would list AP Calculus before Pre-Calculus. Following the taxonomy keeps the
# pedagogical sequence (… Pre-Calculus, then AP Calculus).
_COURSE_ORDER = {
    name: i
    for i, name in enumerate(n for cat in DIAGNOSTIC_CATEGORIES for n in cat["courses"])
}


def course_sort_key(course_name, grade_level):
    """Sort key for listing courses: by grade, then curriculum order, then name.

    Courses absent from the taxonomy fall back to name order within their grade.
    """
    return (grade_level, _COURSE_ORDER.get(course_name, len(_COURSE_ORDER)), course_name)

def category_of_course_name(course_name):
    """Return the category key a course belongs to, or None if it's uncategorized."""
    for cat in DIAGNOSTIC_CATEGORIES:
        if course_name in cat["courses"]:
            return cat["key"]
    return None


# SM-2 seed state per band, chosen so each topic lands in its dashboard mastery
# bucket (see ``intervalLevel`` in Dashboard.jsx): New (interval <= 1), Learning
# (2-5), Familiar (6-20), Proficient (>= 21). "new" and "learning" are seeded with
# explicit intervals because SM-2's interval sequence jumps 1 -> 6 and so can't
# land in the 2-5 "Learning" range; "familiar" and "proficient" replay real grade
# sequences through the scheduler for authentic ease/interval/repetitions.
_BAND_EXPLICIT = {
    "new": (srs.INITIAL_EASE, 0, 0),       # unseen, due today (New)
    "learning": (srs.INITIAL_EASE, 3, 1),  # coming back in a few days (Learning)
}
_BAND_SEQUENCES = {
    "familiar": [5, 5],          # -> interval 6  (Familiar)
    "proficient": [5, 5, 5, 5],  # -> interval ~49 (Proficient)
}


def seed_state_for_band(band):
    """Return the SM-2 (ease, interval, repetitions) for a seeding band.

    New/Learning use explicit intervals; Familiar/Proficient are computed by
    replaying the band's quality sequence through the real scheduler, so those
    numbers are authentic algorithm output rather than hand-typed.
    """
    if band in _BAND_EXPLICIT:
        return _BAND_EXPLICIT[band]
    ease, interval, reps = srs.INITIAL_EASE, 0, 0
    for quality in _BAND_SEQUENCES[band]:
        ease, interval, reps = srs.update(ease, interval, reps, quality)
    return ease, interval, reps


# Blend of the diagnostic's calibration outcomes into a single 0..1 score, used to
# pick one mastery band for the current course's already-learned (earlier) units.
_OUTCOME_SCORE = {"correct_first": 1.0, "correct_second": 0.5, "incorrect": 0.0}


def aggregate_learned_band(outcomes):
    """Pick the mastery band for the current course's earlier (already-learned)
    units from the diagnostic results.

    `outcomes` is the list of calibration outcome strings. The default is
    "learning"; acing the problems bumps those units up to "familiar", while
    mostly missing them drops them to "new" (needs frequent practice). The unit
    the student is *currently* on is always seeded "new" by the caller — this only
    governs the units behind it.
    """
    scores = [_OUTCOME_SCORE[o] for o in outcomes if o in _OUTCOME_SCORE]
    if not scores:
        return "learning"
    avg = sum(scores) / len(scores)
    if avg >= 0.8:
        return "familiar"
    if avg < 0.4:
        return "new"
    return "learning"


# Georgia-curriculum unit taxonomy. Each course maps to an ordered list of units
# (following the unit structure of Georgia's K-12 Mathematics course sequence);
# each unit lists the exact topic names (from ``seed_courses.CURRICULUM``) that
# belong to it. The unit the student reports they're "currently learning" is the
# learning frontier: every topic in that unit and the units before it counts as
# already learned. Authored here (rather than as a DB field) so the mapping needs
# no migration; a completeness test asserts every course topic lands in exactly
# one unit so the taxonomy can't silently drift from the curriculum.
COURSE_UNITS = {
    "Grade 1": [
        {"key": "g1-u1", "name": "Number Sense & Place Value", "topics": [
            "Place Value", "Compare Numbers", "Missing Number in a Sequence",
            "Even or Odd", "Ordinal Numbers"]},
        {"key": "g1-u2", "name": "Addition & Subtraction within 20", "topics": [
            "Addition of two numbers", "Subtraction of two numbers",
            "Add and Subtract Word Problem within 20"]},
    ],
    "Grade 2": [
        {"key": "g2-u1", "name": "Place Value within 1000", "topics": [
            "Add and Subtract within 1000", "Compare 3-Digit Numbers"]},
        {"key": "g2-u2", "name": "Money & Time", "topics": [
            "Convert minutes to hours and minutes", "Elapsed Time",
            "Add and Subtract Money", "Tell Time to the Nearest 5 Minutes",
            "Count Money Value"]},
        {"key": "g2-u3", "name": "Foundations of Multiplication", "topics": [
            "Arrays and Repeated Addition"]},
    ],
    "Grade 3": [
        {"key": "g3-u1", "name": "Multiplication & Division", "topics": [
            "Multiplication", "Division", "Missing Factor"]},
        {"key": "g3-u2", "name": "Fractions", "topics": [
            "Equivalent Fractions", "Fraction on a Number Line"]},
        {"key": "g3-u3", "name": "Measurement & Geometry", "topics": [
            "Perimeter of Polygons", "Area of a Rectangle", "Rounding"]},
        {"key": "g3-u4", "name": "Problem Solving", "topics": [
            "Two-Step Word Problem"]},
    ],
    "Grade 4": [
        {"key": "g4-u1", "name": "Factors & Multiples", "topics": [
            "Is Prime", "Is Composite", "Factors of a number",
            "Nth Multiple of a Number", "Factor Pairs Count"]},
        {"key": "g4-u2", "name": "Fractions", "topics": [
            "Compare Fractions", "Add Fractions", "Subtract Fractions",
            "Multiply a Fraction by a Whole Number", "Mixed and Improper Fractions"]},
        {"key": "g4-u3", "name": "Decimals", "topics": [
            "Fraction to Decimal", "Compare Decimals", "Add Decimals",
            "Subtract Decimals"]},
        {"key": "g4-u4", "name": "Operations & Geometry", "topics": [
            "Long Division with Remainder", "Angle Addition"]},
    ],
    "Grade 5": [
        {"key": "g5-u1", "name": "Operations & Expressions", "topics": [
            "Order of Operations", "Powers of Ten"]},
        {"key": "g5-u2", "name": "Fractions", "topics": [
            "Fraction Multiplication", "Divide Fractions",
            "Add and Subtract Unlike Denominators"]},
        {"key": "g5-u3", "name": "Decimals", "topics": [
            "Multiply Decimals", "Round Decimals", "Divide Decimals"]},
        {"key": "g5-u4", "name": "Measurement & Volume", "topics": [
            "Volume of a cube", "Volume of a cuboid", "Length Unit Conversion",
            "Metric Unit Conversion"]},
    ],
    "Grade 6": [
        {"key": "g6-u1", "name": "The Number System", "topics": [
            "Absolute difference between two numbers",
            "Greatest Common Divisor of N Numbers ( GCD / HCF )",
            "LCM (Least Common Multiple)", "Prime Factors", "Common Factors",
            "Signed Integer Operations", "Signed Fraction Operations",
            "Absolute Value Expression", "Order Rational Numbers",
            "Coordinate Distance"]},
        {"key": "g6-u2", "name": "Ratios & Proportional Relationships", "topics": [
            "Percentage of a number", "Unit Rate", "Equivalent Ratios",
            "Convert Between Fractions, Decimals, and Percents"]},
        {"key": "g6-u3", "name": "Expressions & Equations", "topics": [
            "Exponentiation", "Square", "Combine Like Terms",
            "Evaluate an Algebraic Expression", "Distributive Property",
            "One-Step Inequality"]},
        {"key": "g6-u4", "name": "Geometry", "topics": [
            "Area of Triangle", "Area of Trapezoid", "Surface area of a cube",
            "Surface area of a cuboid"]},
        {"key": "g6-u5", "name": "Statistics", "topics": [
            "Mean and Median", "Mean Absolute Deviation", "Interquartile Range",
            "Range of a Data Set", "Mode of a Data Set"]},
    ],
    "Grade 7": [
        {"key": "g7-u1", "name": "Proportional Relationships", "topics": [
            "Solve a Proportion", "Constant of Proportionality",
            "Scale Factor Length"]},
        {"key": "g7-u2", "name": "Percent Applications", "topics": [
            "Simple Interest", "Profit or Loss Percent",
            "Percentage difference between two numbers", "Percentage error",
            "Percent Increase or Decrease", "Discount, Tax, and Tip"]},
        {"key": "g7-u3", "name": "Expressions & Equations", "topics": [
            "Basic Algebra", "Two-Step Equation", "Multi-Step Equation",
            "Multi-Step Inequality", "Celsius to Fahrenheit"]},
        {"key": "g7-u4", "name": "Geometry", "topics": [
            "Complementary and Supplementary Angle", "Third Angle of Triangle",
            "Fourth Angle of Quadrilateral", "Area of Circle",
            "Circumference of Circle",
            "Area of Circle given center and a point on circle",
            "Surface area of a cone", "Surface area of a cylinder",
            "Curved surface area of a cylinder", "Surface area of a pyramid"]},
        {"key": "g7-u5", "name": "Probability", "topics": [
            "Probability of a certain sum appearing on faces of dice",
            "Probability of Compound Events"]},
    ],
    "Grade 8": [
        {"key": "g8-u1", "name": "Real Numbers, Exponents & Scientific Notation",
         "topics": [
            "Square Root", "Cube Root", "Approximate an Irrational Square Root",
            "Product of scientific notations", "Scientific Notation Operations",
            "Integer Exponent Rules"]},
        {"key": "g8-u2", "name": "Linear Equations & Systems", "topics": [
            "Linear Equations", "Variables on Both Sides",
            "Solve a System of Equations in R^2",
            "Number of Solutions of a Linear System", "Slope from Two Points",
            "Slope-Intercept Form from Standard Form", "Line from Slope and a Point"]},
        {"key": "g8-u3", "name": "Functions", "topics": [
            "Evaluate a Function", "Linear Function Value", "Compare Two Functions"]},
        {"key": "g8-u4", "name": "Geometry & Transformations", "topics": [
            "Pythagorean Theorem", "Translate a Point", "Reflect a Point",
            "Rotate a Point", "Dilate a Point", "Volume of a cylinder",
            "Volume of a cone", "Volume of a sphere", "Volume of a hemisphere",
            "Surface area of a sphere"]},
    ],
    "Algebra I": [
        {"key": "alg1-u1", "name": "Expressions & Exponent Rules", "topics": [
            "Simplify Square Root", "Comparing Surds", "Power of Powers",
            "Quotient of Powers with Same Base", "Quotient of Powers with Same Power",
            "Product of Powers with the Same Base", "Power of a Product",
            "Negative Exponents"]},
        {"key": "alg1-u2", "name": "Linear Equations & Inequalities", "topics": [
            "Solve a Literal Equation", "Absolute Value Equation",
            "Solve a Linear Inequality", "Absolute-Value Inequality",
            "Equation of Line from Two Points", "Point-Slope Form",
            "Intersection of two lines", "Solve a System of Equations",
            "Direct and Inverse Variation"]},
        {"key": "alg1-u3", "name": "Quadratic Functions", "topics": [
            "Expanding Factored Binomial", "Multiply Binomials",
            "Factoring Quadratic", "Quadratic Equation",
            "Vertex of a Quadratic in Vertex Form", "Axis of Symmetry of a Parabola",
            "Completing the Square", "Discriminant and Number of Real Roots",
            "Sum and Product of the Roots"]},
        {"key": "alg1-u4", "name": "Exponential Functions & Sequences", "topics": [
            "Evaluate an Exponential Function", "Exponential Growth and Decay",
            "Compound Interest", "Arithmetic Progression Term",
            "Arithmetic Progression Sum", "Geometric Progression"]},
        {"key": "alg1-u5", "name": "Functions & Rational Expressions", "topics": [
            "Domain of a Function", "Simplify a Rational Expression"]},
    ],
    "Geometry": [
        {"key": "geo-u1", "name": "Coordinate Geometry", "topics": [
            "Distance between 2 points", "Midpoint of two points",
            "Polygon Area from Vertices"]},
        {"key": "geo-u2", "name": "Congruence, Similarity & Polygons", "topics": [
            "Sum of Angles of Polygon", "Angle of a Regular Polygon",
            "Valid Triangle", "Similar Triangles Missing Side",
            "Scale Factor to Area or Volume Ratio", "Area of a Regular Polygon"]},
        {"key": "geo-u3", "name": "Right Triangle Trigonometry", "topics": [
            "Right Triangle Side with Trigonometry",
            "Right Triangle Side with the Pythagorean Theorem",
            "Special Right Triangles", "Degrees to Radians", "Radians to Degrees"]},
        {"key": "geo-u4", "name": "Circles & Volume", "topics": [
            "Arc length of Angle", "Area of a Sector", "Inscribed Angle Theorem",
            "Segment Lengths in Circles",
            "Equation of a Circle from Center and Radius",
            "Center and Radius from a Circle Equation", "Volume of a pyramid",
            "Volume of the frustum of a cone", "Composite Solid Volume"]},
        {"key": "geo-u5", "name": "Probability", "topics": [
            "Conditional Probability from a Two-Way Table",
            "Compound Probability of Independent Events",
            "Expected Value of a Discrete Distribution"]},
    ],
    "Algebra II": [
        {"key": "alg2-u1", "name": "Complex Numbers & Matrices", "topics": [
            "Add and Subtract Complex Numbers", "Multiplication of 2 complex numbers",
            "Complex Number Division", "Modulus of a Complex Number",
            "Determinant to 2x2 Matrix", "Matrix Operation (2x2)",
            "System of Three Equations", "Solve a 2x2 Linear System"]},
        {"key": "alg2-u2", "name": "Polynomial Functions", "topics": [
            "Evaluate a Polynomial", "Polynomial Division by a Linear Factor",
            "Remainder Theorem", "Rational Root Theorem",
            "Build a Polynomial from Its Roots", "Solve a Polynomial by Factoring",
            "End Behavior of a Polynomial", "Average Rate of Change over Interval",
            "Conic Equation from Features"]},
        {"key": "alg2-u3", "name": "Rational & Radical Functions", "topics": [
            "Rational Exponents", "Solve a Radical Equation",
            "Rationalize a Denominator Using the Conjugate",
            "Solve a Radical Equation Using the Conjugate", "Solve a Rational Equation",
            "Rational Expression Operations"]},
        {"key": "alg2-u4", "name": "Exponential & Logarithmic Functions", "topics": [
            "Logarithm", "Evaluate a Logarithm", "Logarithm Product Rule",
            "Logarithm Quotient Rule", "Logarithm Power Rule", "Change of Base Formula",
            "Solve an Exponential Equation with Logarithms"]},
        {"key": "alg2-u5", "name": "Functions & Sets", "topics": [
            "Function Composition", "Inverse of a Linear Function",
            "Inverse of a Non-Linear Function",
            "Union, Intersection, Difference of Two Sets"]},
        {"key": "alg2-u6", "name": "Counting & Statistics", "topics": [
            "Factorial", "Combinations of Objects", "Permutations",
            "Z-Score of a Data Value", "Empirical Rule (68-95-99.7)"]},
    ],
    "Statistical Reasoning": [
        {"key": "stat-u1", "name": "Descriptive Statistics", "topics": [
            "Mean, Standard Deviation and Variance", "Five-Number Summary", "Z-Score",
            "Percentile Rank", "Relative Frequency", "Correlation Coefficient",
            "Least-Squares Regression Line"]},
        {"key": "stat-u2", "name": "Probability", "topics": [
            "Conditional Probability", "Counting to Probability",
            "Odds from Probability", "Expected Value and Variance"]},
        {"key": "stat-u3", "name": "Probability Distributions", "topics": [
            "Binomial distribution", "Normal Distribution Probability"]},
        {"key": "stat-u4", "name": "Statistical Inference", "topics": [
            "Confidence interval For sample S", "Margin of Error",
            "Standard Error of the Mean", "Sample Proportion Confidence Interval",
            "Test Statistic for a Mean or Proportion"]},
    ],
    "Pre-Calculus": [
        {"key": "precalc-u1", "name": "Trigonometric Functions & the Unit Circle",
         "topics": [
            "Coordinates on the Unit Circle", "Sine on the Unit Circle",
            "Cosine on the Unit Circle", "Tangent on the Unit Circle",
            "Inverse Trigonometric Values", "Sinusoid Features"]},
        {"key": "precalc-u2", "name": "Trigonometric Identities & Equations",
         "topics": [
            "Angle Sum", "Double-Angle Values", "Half-Angle Formula Values",
            "Sum and Difference Formula Values", "Simplify Using Trig Identities",
            "Solve a Trigonometric Equation", "Quadratic-Form Trigonometric Equation"]},
        {"key": "precalc-u3", "name": "Triangle Trigonometry", "topics": [
            "Law of Sines", "Law of Cosines", "Area of an Oblique Triangle"]},
        {"key": "precalc-u4", "name": "Vectors & Complex Numbers", "topics": [
            "Vector Operations (2D)", "Angle between 2 vectors",
            "Dot product of 2 vectors", "Orthogonal Projection",
            "Euclidian norm or L2 norm of a vector", "Complex to polar form",
            "De Moivre's Theorem"]},
        {"key": "precalc-u5", "name": "Polar & Parametric", "topics": [
            "Polar to Rectangular Coordinates", "Rectangular to Polar Coordinates",
            "Polar and Rectangular Equation Conversion", "Eliminate the Parameter"]},
        {"key": "precalc-u6", "name": "Rational Functions", "topics": [
            "Vertical Asymptotes of a Rational Function",
            "Zeros of a Rational Function", "Holes of a Rational Function",
            "Horizontal Asymptote of a Rational Function",
            "Slant Asymptote of a Rational Function",
            "Y-Intercept of a Rational Function", "Rational Inequality",
            "Partial Fraction Decomposition"]},
        {"key": "precalc-u7", "name": "Sequences & Series", "topics": [
            "Finite Geometric Series Sum", "Sigma-Notation Arithmetic Sum",
            "Recursive Sequence Nth Term", "Limit of a Rational Sequence",
            "Binomial Theorem Term"]},
    ],
    "AP Calculus": [
        {"key": "calc-u1", "name": "Limits & Continuity", "topics": [
            "Limit of a Rational Function", "Limit Using the Conjugate",
            "L'Hopital's Rule"]},
        {"key": "calc-u2", "name": "Differentiation", "topics": [
            "Derivative Using the Limit Definition", "Power Rule Differentiation",
            "Derivative of a Polynomial", "Trigonometric Differentiation",
            "Derivative of Exponential, Log, or Trig Function",
            "Product Rule at a Point", "Quotient Rule at a Point",
            "Chain Rule at a Point", "Higher-Order Derivative at a Point",
            "Implicit Differentiation"]},
        {"key": "calc-u3", "name": "Applications of Derivatives", "topics": [
            "Tangent Line to a Polynomial", "Critical Points and Extrema",
            "Inflection Point of a Cubic", "Concavity Interval",
            "Mean Value Theorem", "Particle Motion", "Related Rates"]},
        {"key": "calc-u4", "name": "Integration", "topics": [
            "Power Rule Integration", "Indefinite Integral of a Polynomial",
            "Definite Integral of a Polynomial",
            "Definite Integral of Quadratic Equation",
            "Definite Integral by u-Substitution", "Integration by Parts",
            "Riemann Sum", "Trapezoidal Rule"]},
        {"key": "calc-u5", "name": "Applications of Integration", "topics": [
            "Area Between Curves", "Average Value of a Function",
            "Volume of a Solid of Revolution", "Separable Differential Equation"]},
        {"key": "calc-u6", "name": "Series", "topics": [
            "Taylor/Maclaurin Coefficient"]},
    ],
}


def units_for_course(course_name):
    """Ordered list of unit dicts (``{"key", "name", "topics"}``) for a course.

    Returns ``[]`` for a course with no authored units, so callers degrade to
    "whole course" behavior rather than raising.
    """
    return COURSE_UNITS.get(course_name, [])


# Per course, each topic name -> its position in the course's flattened unit
# order (unit 1's topics, then unit 2's, …). Lets topics be listed in curriculum
# unit order regardless of the order they were inserted / their database id.
_TOPIC_ORDER = {
    course_name: {
        topic_name: i
        for i, topic_name in enumerate(t for u in units for t in u["topics"])
    }
    for course_name, units in COURSE_UNITS.items()
}


def topic_order_key(course_name, topic_name):
    """Sort key placing a topic in its course's unit order.

    Topics outside the taxonomy (or in an uncatalogued course) sort after the
    known ones, then by name, so any stray still renders deterministically.
    """
    order = _TOPIC_ORDER.get(course_name, {})
    return (order.get(topic_name, len(order)), topic_name)


def learned_unit_topic_names(course_name, unit_key):
    """Topic names in the units up to and including ``unit_key`` (a set).

    Units are ordered pedagogically, so the reported current unit is the learning
    frontier: every topic in it and the earlier units counts as already learned.
    If ``unit_key`` isn't found (or the course has no authored units), returns all
    the course's unit topics — treating the whole course as learned — so the
    current course is never left empty for want of a match.
    """
    names = set()
    for unit in units_for_course(course_name):
        names.update(unit["topics"])
        if unit["key"] == unit_key:
            return names
    return names


def current_unit_topic_names(course_name, unit_key):
    """Topic names in just the reported current unit (a set).

    Empty if the unit isn't found (or none authored) — the caller then treats the
    whole learned set as earlier units, so no topic is wrongly marked "new".
    """
    for unit in units_for_course(course_name):
        if unit["key"] == unit_key:
            return set(unit["topics"])
    return set()
