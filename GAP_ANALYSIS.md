# Solveki Math-Topic Coverage Gap Analysis

_Comparison of Solveki's current auto-generated topic coverage against the standard scope-and-sequence of **Khan Academy**, **IXL**, and **DeltaMath**._

This report only lists topics that are (a) commonly tested at the given level, (b) amenable to an auto-generated problem with a **single typeable answer** (no free-form proofs, graph-drawing, or essay answers), and (c) **genuinely absent** from Solveki's current topic list (verified against `seed_courses.py` + `seed_topics.py`).

Topics that require the student to *draw* a graph, *construct* a figure, or *write a proof* are noted as poor fits and generally excluded or marked Low.

---

## Summary — Top 10 Highest-Impact Gaps

| # | Topic | Course / Grade | Covered by | Priority |
|---|-------|----------------|------------|----------|
| 1 | Completing the Square | Algebra I | Khan, IXL, DeltaMath | High |
| 2 | Solve Equations with Variables on Both Sides | Grade 8 | Khan, IXL, DeltaMath | High |
| 3 | Two-Step & Multi-Step Linear Equations | Grade 7 | Khan, IXL, DeltaMath | High |
| 4 | Percent Applications (Discount, Tax, Tip, % Change) | Grade 7 | Khan, IXL, DeltaMath | High |
| 5 | Slope-Intercept Form (identify / convert from standard) | Grade 8 / Algebra I | Khan, IXL, DeltaMath | High |
| 6 | Function Composition | Algebra II | Khan, IXL, DeltaMath | High |
| 7 | Special Right Triangles (30-60-90, 45-45-90) | Geometry | Khan, IXL, DeltaMath | High |
| 8 | Operations with / Solving Rational Expressions & Equations | Algebra II | Khan, IXL, DeltaMath | High |
| 9 | Convert Between Fractions, Decimals & Percents | Grade 6 | Khan, IXL, DeltaMath | High |
| 10 | Implicit Differentiation | AP Calculus | Khan, DeltaMath | High |

Runner-ups just outside the top 10: Normal-Distribution Probability via z-table (Statistical Reasoning), Amplitude/Period/Phase Shift of a Sinusoid (Pre-Calculus), and Multiply Binomials / FOIL-adjacent polynomial multiplication (Algebra I).

---

## Grade 1

Current coverage: Addition, Subtraction, Place Value.

| Topic | Covered by | Auto-gen fit | Priority |
|-------|------------|--------------|----------|
| Compare Numbers (>, <, =) | Khan, IXL, DeltaMath | Great fit — output a single symbol/number | High |
| Skip Counting / Missing Number in Sequence | Khan, IXL | Great fit — single number answer | Medium |
| Even or Odd | IXL, Khan | Great fit — one-word/binary answer | Medium |
| Ordinal Numbers (1st, 2nd, …) | IXL | Good fit | Low |
| Word Problems: Add/Subtract within 20 | Khan, IXL | Good fit if templated with numeric answer | Medium |

## Grade 2

Current coverage: Minutes-to-hours conversion, Elapsed Time, Add/Subtract Money.

| Topic | Covered by | Auto-gen fit | Priority |
|-------|------------|--------------|----------|
| Add/Subtract within 1000 (with regrouping) | Khan, IXL, DeltaMath | Great fit | High |
| Tell Time to the Nearest 5 Minutes | Khan, IXL | Good fit (answer as HH:MM) | Medium |
| Count Coin/Bill Value | Khan, IXL | Good fit — single money value | Medium |
| Arrays / Repeated Addition | Khan, IXL | Good fit — single product | Medium |
| Compare 3-Digit Numbers | IXL | Great fit | Low |

## Grade 3

Current coverage: Multiplication, Division, Perimeter of Polygons, Rounding, Area of a Rectangle.

| Topic | Covered by | Auto-gen fit | Priority |
|-------|------------|--------------|----------|
| Equivalent Fractions | Khan, IXL, DeltaMath | Great fit — fill the missing numerator/denominator | High |
| Multiplication/Division Fact Families (missing factor) | Khan, IXL | Great fit — single number | Medium |
| Fractions on a Number Line | Khan, IXL | Fit if answered as a fraction value; drawing version is poor fit | Medium |
| Two-Step Word Problems | Khan, IXL | Good fit if templated | Medium |
| Elapsed Time (word-problem form) | Khan, IXL | Already partly covered at G2; skip | Low |

## Grade 4

Current coverage: Compare Fractions, Fraction↔Decimal, Prime/Composite, Factors, Add/Subtract Fractions, Compare/Add/Subtract Decimals, Nth Multiple.

| Topic | Covered by | Auto-gen fit | Priority |
|-------|------------|--------------|----------|
| Multiply a Fraction by a Whole Number | Khan, IXL, DeltaMath | Great fit | High |
| Mixed Number ↔ Improper Fraction | Khan, IXL, DeltaMath | Great fit | High |
| Long Division with Remainder | Khan, IXL | Great fit — answer quotient + remainder | Medium |
| Factor Pairs of a Number | IXL | Good fit — but overlaps existing "Factors" | Low |
| Angle Measurement (degrees, additive) | Khan, IXL | Good fit — single number | Medium |

## Grade 5

Current coverage: Fraction Mult/Div, Volume of cube/cuboid, Multiply Decimals, Order of Operations, Powers of Ten, Length Conversion.

| Topic | Covered by | Auto-gen fit | Priority |
|-------|------------|--------------|----------|
| Add/Subtract Fractions with **Unlike** Denominators | Khan, IXL, DeltaMath | Great fit (current G4 add/subtract likely like-denominator) | High |
| Round Decimals | Khan, IXL | Great fit | Medium |
| Unit Conversion (mass, capacity, time) | Khan, IXL | Great fit — generalize existing length conversion | Medium |
| Divide with Decimals | Khan, IXL, DeltaMath | Great fit | Medium |
| Coordinate-Plane Plotting | Khan, IXL | Poor fit — requires graphing; skip | Low |

## Grade 6

Current coverage: Absolute difference, Exponentiation, Square, Percentage, GCD, LCM, Prime/Common Factors, Combine Like Terms, Areas, Surface areas, Mean/Median, Unit Rate, Equivalent Ratios, Signed Int/Fraction Ops, Absolute Value Expr, One-Step Inequality, MAD, IQR, Range.

| Topic | Covered by | Auto-gen fit | Priority |
|-------|------------|--------------|----------|
| Convert Between Fractions, Decimals & Percents | Khan, IXL, DeltaMath | Great fit — single value answer | High |
| Evaluate an Algebraic Expression by Substitution | Khan, IXL, DeltaMath | Great fit (distinct from later "Evaluate a Function") | High |
| Distributive Property (expand a(b+c)) | Khan, IXL, DeltaMath | Great fit — expression answer | Medium |
| Order Rational Numbers (least→greatest) | Khan, IXL | Good fit — answer as ordered list | Medium |
| Ratio Tables (complete the missing value) | Khan, IXL | Great fit — overlaps Equivalent Ratios; Low | Low |
| Coordinate-Plane Distance (same row/column) | Khan, IXL | Good fit — single number | Low |

## Grade 7

Current coverage: Basic Algebra, angle relations, circle area/circumference, surface areas, Simple Interest, Profit/Loss %, C→F, % difference/error, dice probability, Solve a Proportion, Multi-Step Inequality, Constant of Proportionality.

| Topic | Covered by | Auto-gen fit | Priority |
|-------|------------|--------------|----------|
| Two-Step & Multi-Step Linear Equations | Khan, IXL, DeltaMath | Great fit — the core 7th-grade algebra skill; "Basic Algebra" is vaguer | High |
| Percent Increase / Decrease (% change) | Khan, IXL, DeltaMath | Great fit — single % answer | High |
| Discount, Markup, Tax & Tip | Khan, IXL, DeltaMath | Great fit — single money/% answer | High |
| Add/Subtract/Multiply/Divide Rational Numbers (mixed signs) | Khan, IXL | Good fit — partly covered by G6 signed ops; Medium | Medium |
| Scale Drawings / Scale Factor Length | Khan, IXL | Good fit — single length | Medium |
| Probability of Compound Events (fractions) | Khan, IXL | Good fit — single fraction | Medium |

## Grade 8

Current coverage: Roots, scientific notation, Pythagorean, volumes, System of equations, Linear Equations, exponent rules, Evaluate a Function, Slope from Two Points, Linear Function Value, transformations of a point.

| Topic | Covered by | Auto-gen fit | Priority |
|-------|------------|--------------|----------|
| Solve Equations with Variables on Both Sides | Khan, IXL, DeltaMath | Great fit — single value; also flag one/none/infinite solutions | High |
| Slope-Intercept Form: identify slope & y-intercept, and convert from standard form | Khan, IXL, DeltaMath | Great fit — single values / equation string | High |
| Equation of a Line from Slope & a Point | Khan, IXL, DeltaMath | Great fit — equation answer | Medium |
| Compare Two Functions (rate of change / value) | Khan, IXL | Good fit — single number/comparison | Medium |
| Solutions of a Linear System (one / none / infinite, by inspection) | Khan, IXL | Good fit — categorical answer | Medium |

## Algebra I

Current coverage: simplify roots, exponent rules, expanding, factoring, quadratic equation, vertex form, line equations, compound interest, AP/GP, absolute value equation, exponential growth/decay, domain, discriminant, axis of symmetry, sum/product of roots, linear inequality.

| Topic | Covered by | Auto-gen fit | Priority |
|-------|------------|--------------|----------|
| Completing the Square | Khan, IXL, DeltaMath | Great fit — answer vertex form or roots | High |
| Solve a Literal Equation (solve for a variable) | Khan, IXL, DeltaMath | Great fit — expression answer | High |
| Point-Slope Form of a Line | Khan, IXL, DeltaMath | Great fit — equation answer | High |
| Multiply Polynomials / Binomials (beyond current "Expanding") | Khan, IXL, DeltaMath | Great fit — polynomial answer; broaden current expanding generator | Medium |
| Solve a System by Substitution / Elimination (show ordered pair) | Khan, IXL, DeltaMath | Good fit — overlaps "Intersection of two lines"; Medium | Medium |
| Direct & Inverse Variation (find k or a value) | Khan, IXL | Great fit — single value | Medium |
| Simplify a Rational Expression | Khan, IXL, DeltaMath | Good fit — expression answer | Medium |
| Solve Absolute-Value Inequalities | Khan, IXL, DeltaMath | Good fit — interval/compound answer | Medium |
| Recursive vs Explicit Sequence Formula | Khan, IXL | Good fit — overlaps AP/GP; Low | Low |

## Geometry

Current coverage: distance, midpoint, arc length, sector area, deg↔rad, polygon angles, valid triangle, volume pyramid/frustum, right-triangle trig & Pythagorean, circle equations, inscribed angle, two-way-table & compound probability, expected value.

| Topic | Covered by | Auto-gen fit | Priority |
|-------|------------|--------------|----------|
| Special Right Triangles (30-60-90, 45-45-90) | Khan, IXL, DeltaMath | Great fit — single side length | High |
| Similar Triangles: Find a Missing Side | Khan, IXL, DeltaMath | Great fit — single length | High |
| Scale Factor → Ratio of Areas / Volumes | Khan, IXL, DeltaMath | Great fit — single ratio/number | Medium |
| Segment Lengths in Circles (chord-chord, secant-secant, tangent) | Khan (some), DeltaMath | Great fit — single length; DeltaMath staple | Medium |
| Area of a Regular Polygon (apothem) | Khan, IXL | Great fit — single number | Medium |
| Surface Area / Volume of Composite Solids | IXL, DeltaMath | Good fit — single number | Medium |
| Coordinate Geometry: Area/Perimeter of a Polygon from Vertices | Khan, IXL | Good fit — single number | Low |
| Two-Column Proofs | Khan, DeltaMath | Poor fit — free-form proof; exclude | Low |

## Algebra II

Current coverage: log basics + log rules, complex arithmetic (add/sub/mult), determinant, ARoC, factorial/combos/perms, polynomial eval/division/remainder, build-from-roots, rational exponents, radical equations, exponential-log equations, inverse of linear function, z-score, empirical rule, 2x2 system, set operations, rationalize denominator.

| Topic | Covered by | Auto-gen fit | Priority |
|-------|------------|--------------|----------|
| Function Composition (f∘g)(x) or at a point | Khan, IXL, DeltaMath | Great fit — expression or single value | High |
| Solve a Rational Equation | Khan, IXL, DeltaMath | Great fit — single value(s) | High |
| Multiply / Divide / Add / Subtract Rational Expressions | Khan, IXL, DeltaMath | Great fit — expression answer | High |
| Complex Number Division | Khan, IXL, DeltaMath | Great fit — a+bi answer (complements existing add/mult) | Medium |
| Modulus of a Complex Number | Khan, IXL | Great fit — single value | Medium |
| Inverse of a Non-Linear Function | Khan, IXL, DeltaMath | Good fit — expression answer (extends existing linear inverse) | Medium |
| Rational Root Theorem (list possible roots) | Khan, DeltaMath | Good fit — list answer | Medium |
| Solve a System of Three Equations | Khan, IXL, DeltaMath | Good fit — ordered triple | Medium |
| Matrix Multiplication / Addition (2x2) | Khan, IXL | Great fit — extends existing determinant generator | Medium |
| Solve a Polynomial Equation by Factoring (degree ≥ 3) | Khan, DeltaMath | Good fit — root list | Medium |
| Conic Sections: Ellipse/Hyperbola Equation from Features | Khan, DeltaMath | Good fit if answer is the equation string | Low |
| End Behavior of a Polynomial | Khan, IXL | Good fit — categorical answer | Low |

## Statistical Reasoning

Current coverage: mean/SD/variance, conditional probability, binomial distribution, confidence interval, five-number summary, z-score, correlation coefficient, regression line, margin of error, standard error, sample-proportion CI, relative frequency.

| Topic | Covered by | Auto-gen fit | Priority |
|-------|------------|--------------|----------|
| Normal Distribution Probability (z-score → probability via table) | Khan, IXL, DeltaMath | Great fit — single probability | High |
| Test Statistic for a Mean / Proportion (z or t) | Khan, DeltaMath | Great fit — single value | Medium |
| Expected Value & Variance of a Discrete Random Variable | Khan, IXL | Good fit — variance extends existing expected-value work | Medium |
| Percentile Rank of a Value | Khan, IXL | Good fit — single value | Medium |
| Combinations/Permutations → Probability | Khan, IXL | Good fit — single fraction (uses existing combo/perm generators) | Medium |
| Odds from Probability (and vice versa) | IXL | Great fit — single ratio | Low |
| Hypothesis Test Conclusion / p-value Interpretation | Khan, DeltaMath | Poor fit — requires interpretive/written conclusion; Low | Low |

## Pre-Calculus

Current coverage: angle sum, vector ops (dot, norm, angle, projection, 2D add), complex↔polar, laws of sines/cosines, oblique-triangle area, inverse trig, double-angle, solve trig eq (+ quadratic-form), polar↔rectangular, geometric/sigma sums, sequence limit, eliminate parameter, unit-circle values, rational-function features (asymptotes/holes/zeros/intercepts), rational inequality.

| Topic | Covered by | Auto-gen fit | Priority |
|-------|------------|--------------|----------|
| Amplitude, Period & Phase Shift of a Sinusoid | Khan, IXL, DeltaMath | Great fit — single values | High |
| Sum & Difference Formula Values (sin/cos/tan) | Khan, IXL, DeltaMath | Great fit — exact value (extends double-angle) | Medium |
| Half-Angle Formula Values | Khan, DeltaMath | Great fit — exact value | Medium |
| Binomial Theorem — Specific Term / Coefficient | Khan, IXL, DeltaMath | Great fit — single coefficient | Medium |
| De Moivre's Theorem (power of a complex number) | Khan, DeltaMath | Great fit — single complex value | Medium |
| Simplify Using Trig Identities | Khan, DeltaMath | Good fit — expression answer | Medium |
| Recursive Sequence: Find the Nth Term | Khan, IXL | Good fit — single value | Low |
| Partial Fraction Decomposition (find coefficients) | Khan, DeltaMath | Good fit — coefficient values | Low |
| Convert Polar Equation ↔ Rectangular Equation | Khan | Good fit — equation string | Low |

## AP Calculus

Current coverage: power-rule diff/int, definite integral of quadratic/poly, trig diff, limits (rational/conjugate), poly derivative, product/quotient/chain rule at a point, exp/log/trig derivatives, higher-order derivative, tangent line, critical points/extrema, inflection point, indefinite integral, u-sub integral, area between curves, average value, Riemann sum.

| Topic | Covered by | Auto-gen fit | Priority |
|-------|------------|--------------|----------|
| Implicit Differentiation (dy/dx at a point) | Khan, DeltaMath | Great fit — single value | High |
| Particle Motion (position/velocity/acceleration) | Khan, DeltaMath | Great fit — single value | High |
| Volume of a Solid of Revolution (Disk/Washer) | Khan, DeltaMath | Great fit — single volume | Medium |
| L'Hopital's Rule | Khan, DeltaMath | Great fit — single limit value | Medium |
| Derivative Using the Limit Definition | Khan, DeltaMath | Good fit — expression/value answer | Medium |
| Integration by Parts | Khan, DeltaMath | Great fit — single value/expression | Medium |
| Related Rates | Khan, DeltaMath | Good fit — single rate value (needs careful templating) | Medium |
| Mean Value Theorem (find c) | Khan, DeltaMath | Great fit — single value | Medium |
| Trapezoidal Rule Approximation | Khan, DeltaMath | Great fit — single value (extends Riemann sum) | Medium |
| Separable Differential Equation (solve / evaluate) | Khan, DeltaMath | Good fit — expression or single value | Medium |
| Second Derivative Test / Concavity Interval | Khan, DeltaMath | Good fit — categorical/interval answer | Low |
| Taylor / Maclaurin Polynomial Coefficient (BC) | Khan, DeltaMath | Good fit — single coefficient | Low |
| Slope Fields | Khan, DeltaMath | Poor fit — requires graphing; exclude | Low |

---

## Cross-Cutting Observations

- **Equation-solving progression is thin in the middle grades.** Solveki jumps from "Basic Algebra" (G7) and "Linear Equations" (G8) to advanced Algebra I topics, but lacks the explicit, heavily-tested rungs competitors drill: two-step equations, variables on both sides, and literal equations. These are among the highest-yield additions.
- **Rational expressions/equations are almost entirely absent** across Algebra I → Algebra II, despite being a DeltaMath and IXL core strand.
- **Function operations** (composition, general inverse) are a notable Algebra II gap — Solveki has only "Inverse of a Linear Function".
- **Percent applications** (tax/tip/discount/markup, percent change) are a Grade 7 staple missing entirely, even though Solveki has percentage, simple interest, and profit/loss.
- **Poor-fit exclusions** (graphing, proofs, interpretation) were deliberately down-ranked: coordinate plotting, scatter plots, two-column proofs, slope fields, and hypothesis-test conclusions.
