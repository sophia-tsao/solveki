# Khan Academy ↔ Solveki coverage gaps

Compared on 2026-10-04: the Khan Academy math catalog ([khan_academy_math_catalog.md](khan_academy_math_catalog.md), 29 core courses) against Solveki's 324 practice topics (`seed_topics.py`).

A Khan Academy lesson counts as covered when some Solveki topic drills the same core skill — not merely the same broad area. These calls were made by reading each lesson's videos and, for borderline cases, the Solveki generator source, so treat individual entries as judgment calls rather than exact.

## Summary

- Khan Academy lessons compared (deduplicated by name across courses): **1236**
- Covered by a Solveki topic: **604**
- Not covered (listed below): **632**, including **38** units with no coverage at all
- Solveki topics with no video in Khan Academy's current math courses: **21**

## Contents

- [Solveki topics that Khan Academy doesn't have](#solveki-topics-that-khan-academy-doesnt-have)
- [Khan Academy topics that Solveki doesn't have](#khan-academy-topics-that-solveki-doesnt-have)
  - [2nd grade math](#2nd-grade-math)
  - [3rd grade math](#3rd-grade-math)
  - [4th grade math](#4th-grade-math)
  - [5th grade math](#5th-grade-math)
  - [6th grade math](#6th-grade-math)
  - [7th grade math](#7th-grade-math)
  - [8th grade math](#8th-grade-math)
  - [Basic geometry and measurement](#basic-geometry-and-measurement)
  - [Algebra 1](#algebra-1)
  - [High school geometry](#high-school-geometry)
  - [Algebra 2](#algebra-2)
  - [Integrated math 1](#integrated-math-1)
  - [Integrated math 2](#integrated-math-2)
  - [Integrated math 3](#integrated-math-3)
  - [Trigonometry](#trigonometry)
  - [Precalculus](#precalculus)
  - [Statistics essentials](#statistics-essentials)
  - [AP®︎/College Statistics](#apcollege-statistics)
  - [AP®︎/College Precalculus](#apcollege-precalculus)
  - [AP®︎/College Calculus AB](#apcollege-calculus-ab)
  - [AP®︎/College Calculus BC](#apcollege-calculus-bc)
  - [Multivariable calculus](#multivariable-calculus)
  - [Differential equations](#differential-equations)
  - [College Algebra](#college-algebra)
  - [Linear algebra](#linear-algebra)
  - [Early math review](#early-math-review)
  - [Arithmetic](#arithmetic)
  - [Algebra basics](#algebra-basics)

## Solveki topics that Khan Academy doesn't have

No video in Khan Academy's current math course pages teaches these Solveki topics. Each still has a "Learn more" video, found by searching YouTube.

### On Khan Academy's YouTube channels but not in its current courses (12)

Khan Academy made a video for these, but it is no longer part of the current math courses. Some are older uploads; some are from the Khan Academy India channel.

| Solveki topic | Course | Generator | "Learn more" video used |
|---|---|---|---|
| Fourth Angle of Quadrilateral | Grade 7 | `fourth_angle_of_quadrilateral` | [The sum of interior angles of a quadrilateral](https://www.youtube.com/watch?v=BoQgG_TYAG8) (Khan Academy India - English) |
| Surface area of a cone | Grade 7 | `surface_area_cone` | [Surface area of a cone](https://www.youtube.com/watch?v=9w6qYXatwkM) (Khan Academy) |
| Simple Interest | Grade 7 | `simple_interest` | [Intro to simple interest](https://www.youtube.com/watch?v=Rmol9IzSDXk) (Khan Academy India - English) |
| Percentage error | Grade 7 | `percentage_error` | [Finding percent error](https://www.youtube.com/watch?v=WQLcC5SpbYY) (Khan Academy) |
| Surface area of a sphere | Grade 8 | `surface_area_sphere` | [Surface area of sphere: computation and sense of formula](https://www.youtube.com/watch?v=IZ4DpWYO3kY) (Khan Academy India - English) |
| Sum of Angles of Polygon | Geometry | `sum_of_polygon_angles` | [Sum of interior angles of a polygon](https://www.youtube.com/watch?v=qG3HnRccrQU) (Khan Academy) |
| Angle of a Regular Polygon | Geometry | `angle_regular_polygon` | [Sum of interior angles of a polygon](https://www.youtube.com/watch?v=qG3HnRccrQU) (Khan Academy) |
| Union, Intersection, Difference of Two Sets | Algebra II | `set_operation` | [Intersection and union of sets](https://www.youtube.com/watch?v=jAfNg3ylZAI) (Khan Academy) |
| Rationalize a Denominator Using the Conjugate | Algebra II | `alg2_rationalize_denominator` | [Rationalizing Denominators with Conjugates](https://www.youtube.com/watch?v=ENIUcjdPO54) (Khan Academy) |
| Direct and Inverse Variation | Algebra I | `alg1_variation` | [Direct and inverse variation](https://www.youtube.com/watch?v=92U67CUy9Gc) (Khan Academy) |
| Absolute-Value Inequality | Algebra I | `alg1_abs_value_inequality` | [Absolute value inequalities](https://www.youtube.com/watch?v=iI_2Piwn_og) (Khan Academy) |
| System of Three Equations | Algebra II | `alg2_solve_system_three` | [Systems of three variables](https://www.youtube.com/watch?v=pANZpI9sOYg) (Khan Academy) |

### No Khan Academy video found (9)

Neither the Khan Academy catalog nor a YouTube search turned up a Khan Academy video for these, so the "Learn more" link uses another educational channel.

| Solveki topic | Course | Generator | "Learn more" video used |
|---|---|---|---|
| Sum and Product of the Roots | Algebra I | `alg1_sum_product_roots` | [How To Find The Sum and Product of the Roots of a Quadratic Equation - Algebra](https://www.youtube.com/watch?v=kBSj35rik8w) (The Organic Chemistry Tutor) |
| Area of an Oblique Triangle | Pre-Calculus | `pc_oblique_triangle_area` | [Area Of A Triangle 1/2absinC](https://www.youtube.com/watch?v=hu4t3NuSk2w) (FuseSchool - Global Education) |
| Eliminate the Parameter | Pre-Calculus | `pc_parametric_to_rectangular` | [Parametric Equations - How to Eliminate the Parameter](https://www.youtube.com/watch?v=pvbyMXsDR3A) (Mario's Math Tutoring) |
| Quadratic-Form Trigonometric Equation | Pre-Calculus | `pc_trig_quadratic` | [Solving Trigonometric Equations That Are Quadratic in Form](https://www.youtube.com/watch?v=h8E8N1eARjs) (Study Force) |
| Ordinal Numbers | Grade 1 | `arith_ordinal_number` | [Ordinal Numbers](https://www.youtube.com/watch?v=-IAIrsUIcUo) (Tutoring Hour) |
| Segment Lengths in Circles | Geometry | `geo_circle_segments` | [Circle Theorems involving Secants, Chords, and Tangents](https://www.youtube.com/watch?v=ASZl3SnKwI8) (Mario's Math Tutoring) |
| Odds from Probability | Statistical Reasoning | `stat_odds_probability` | [Converting Probabilities into Odds](https://www.youtube.com/watch?v=N1NWFj2rZcA) (EHB Explains) |
| Half-Angle Formula Values | Pre-Calculus | `pc_half_angle_values` | [Half Angle Formulas & Identities - Evaluating Trigonometric Expressions](https://www.youtube.com/watch?v=9YI69okba3c) (The Organic Chemistry Tutor) |
| Volume of the frustum of a cone | Geometry | `geo_frustum_volume` | [How to Find the Volume of a Frustum](https://www.youtube.com/watch?v=j06P-oKn094) (Cognito) |

## Khan Academy topics that Solveki doesn't have

Grouped by Khan Academy course and unit, in course order. A lesson that appears in several courses is listed once, under the first course that has it, so later courses only show what is new to them. Each lesson links to Khan Academy.

## 2nd grade math

### Place value — 2 of 6 lessons not covered

- [Numbers in standard, word, and expanded form](https://www.khanacademy.org/math/cc-2nd-grade-math/cc-2nd-place-value/x3184e0ec:numbers-in-standard-word-and-expanded-form) — e.g. Expanded form of numbers; Number and word form of a number; Word form and expanded form
- [Regroup whole numbers](https://www.khanacademy.org/math/cc-2nd-grade-math/cc-2nd-place-value/cc-2nd-hundreds) — e.g. Regrouping whole numbers: 675

### Add and subtract within 100 — 1 of 6 lessons not covered

- [Addition and subtraction: missing values](https://www.khanacademy.org/math/cc-2nd-grade-math/cc-2nd-add-subtract-100/cc-2nd-add-sub-miss-value-prob) — e.g. Missing numbers in addition and subtraction

### Add and subtract within 1,000 — 1 of 4 lessons not covered

- [Adding up to four 2-digit numbers](https://www.khanacademy.org/math/cc-2nd-grade-math/cc-2nd-add-subtract-1000/x3184e0ec:adding-up-to-four-2-digit-numbers) — e.g. Adding four two digit numbers; Adding multiple 2-digit numbers word problems

### Measurement — *entire unit not covered*

- [Units of length](https://www.khanacademy.org/math/cc-2nd-grade-math/cc-2nd-measurement-data/x3184e0ec:units-of-length) — e.g. Getting a sense of meters and centimeters; Getting a sense of inches and feet
- [Measure lengths](https://www.khanacademy.org/math/cc-2nd-grade-math/cc-2nd-measurement-data/cc-2nd-measuring-length) — e.g. Measuring in inches; Measuring lengths (cm, m); Measuring lengths in different units
- [Estimate lengths](https://www.khanacademy.org/math/cc-2nd-grade-math/cc-2nd-measurement-data/cc-2nd-compare-estimate-length) — e.g. Estimating lengths
- [Length word problems](https://www.khanacademy.org/math/cc-2nd-grade-math/cc-2nd-measurement-data/cc-2nd-length-word-problems) — e.g. Length word problem example (US Customary); Length word problems

### Data — *entire unit not covered*

- [Picture graphs](https://www.khanacademy.org/math/cc-2nd-grade-math/x3184e0ec:data/cc-2nd-line-plots) — e.g. Making picture graphs and line plots; Picture graphs
- [Bar graphs](https://www.khanacademy.org/math/cc-2nd-grade-math/x3184e0ec:data/cc-2nd-bar-graphs) — e.g. Creating a bar graph; Reading bar graphs: bikes
- [Line plots](https://www.khanacademy.org/math/cc-2nd-grade-math/x3184e0ec:data/cc-2nd-line-plots) — e.g. Making picture graphs and line plots; Read line plots

### Geometry — *entire unit not covered*

- [Shapes](https://www.khanacademy.org/math/cc-2nd-grade-math/x3184e0ec:geometry/cc-2nd-shapes) — e.g. Recognizing shapes; Cousin Fal's shape collection; Shapes and angles
- [Equal parts of shapes](https://www.khanacademy.org/math/cc-2nd-grade-math/x3184e0ec:geometry/cc-2nd-fractions-of-shapes) — e.g. Equal parts of circles and rectangles
- [Partition rectangles](https://www.khanacademy.org/math/cc-2nd-grade-math/x3184e0ec:geometry/cc-2nd-fractions-of-shapes) — e.g. Equal parts of circles and rectangles; Partitioning rectangles

## 3rd grade math

### Intro to multiplication — 1 of 6 lessons not covered

- [Commutative property of multiplication](https://www.khanacademy.org/math/cc-third-grade-math/intro-to-multiplication/imp-properties-of-multiplication) — e.g. Commutative property of multiplication

### Addition, subtraction, and estimation — 3 of 9 lessons not covered

- [Estimate to add multi-digit numbers](https://www.khanacademy.org/math/cc-third-grade-math/imp-addition-and-subtraction/estimate-to-add-multi-digit-numbers) — e.g. Estimating when adding multi-digit numbers
- [Estimate to subtract multi-digit numbers](https://www.khanacademy.org/math/cc-third-grade-math/imp-addition-and-subtraction/estimate-to-subtract-multi-digit-numbers) — e.g. Estimating when subtracting large numbers
- [Addition and subtraction missing value problems](https://www.khanacademy.org/math/cc-third-grade-math/imp-addition-and-subtraction/imp-addition-and-subtraction-missing-value-problems) — e.g. Missing number for 3-digit addition within 1000; Missing number for 3-digit subtraction within 1000

### Understand fractions — 4 of 5 lessons not covered

- [Fractions intro](https://www.khanacademy.org/math/cc-third-grade-math/imp-fractions/imp-fractions-intro) — e.g. Intro to fractions; Cutting shapes into equal parts; Identifying unit fractions word problem
- [Fractions in contexts](https://www.khanacademy.org/math/cc-third-grade-math/imp-fractions/fractions-in-contexts) — e.g. Fractions in contexts
- [What fractions mean](https://www.khanacademy.org/math/cc-third-grade-math/imp-fractions/imp-what-fractions-mean) — e.g. Identifying numerators and denominators; Recognizing fractions; Recognizing fractions greater than 1
- [Fractions and whole numbers](https://www.khanacademy.org/math/cc-third-grade-math/imp-fractions/imp-fractions-and-whole-numbers) — e.g. Representing 1 as a fraction; Relating fractions to 1; Whole numbers as fractions

### Equivalent fractions and comparing fractions — 1 of 3 lessons not covered

- [Comparing fractions of different wholes](https://www.khanacademy.org/math/cc-third-grade-math/equivalent-fractions-and-comparing-fractions/imp-comparing-fractions-of-different-wholes) — e.g. Comparing fractions of different wholes 1; Comparing fractions of different wholes

### More with multiplication and division — 3 of 4 lessons not covered

- [Multiplication and division word problems](https://www.khanacademy.org/math/cc-third-grade-math/imp-multiplication-and-division/multiplication-and-division-word-problems) — e.g. Multiplication word problem: soda party; Division word problem: blueberries
- [Associative property of multiplication](https://www.khanacademy.org/math/cc-third-grade-math/imp-multiplication-and-division/associative-property-of-multiplication) — e.g. Associative property of multiplication; Properties of multiplication; Using associative property to simplify multiplication
- [Multiplying by tens](https://www.khanacademy.org/math/cc-third-grade-math/imp-multiplication-and-division/imp-multiplying-by-tens) — e.g. Multiplying by multiples of 10; Multiplying by tens word problem

### Arithmetic patterns and problem solving — 1 of 4 lessons not covered

- [Estimation word problems](https://www.khanacademy.org/math/cc-third-grade-math/arithmetic-patterns-and-problem-solving/estimation-word-problems) — e.g. 2-step estimation word problems

### Quadrilaterals — *entire unit not covered*

- [Quadrilaterals](https://www.khanacademy.org/math/cc-third-grade-math/quadrilaterals-3rd/imp-quadrilaterals) — e.g. Intro to quadrilaterals

### Area — 3 of 5 lessons not covered

- [Count unit squares to find area](https://www.khanacademy.org/math/cc-third-grade-math/imp-geometry/imp-count-unit-squares-to-find-area) — e.g. Intro to area and unit squares; Measuring rectangles with different unit squares; Creating rectangles with a given area 1
- [Area and the distributive property](https://www.khanacademy.org/math/cc-third-grade-math/imp-geometry/imp-area-and-the-distributive-property) — e.g. Area and the distributive property
- [Decompose figures to find area](https://www.khanacademy.org/math/cc-third-grade-math/imp-geometry/imp-decompose-figures-to-find-area) — e.g. Decomposing shapes to find area: grids ; Decomposing shapes to find area: add; Decomposing shapes to find area: subtract

### Perimeter — 1 of 4 lessons not covered

- [Perimeter of polygons with missing side lengths](https://www.khanacademy.org/math/cc-third-grade-math/3rd-perimeter/perimeter-of-polygons-with-missing-side-lengths) — e.g. Finding perimeter when a side length is missing ; Finding missing side length when given perimeter

### Time — 1 of 3 lessons not covered

- [Time on number line](https://www.khanacademy.org/math/cc-third-grade-math/time/tell-time-on-number-line) — e.g. Telling time with number line

### Measurement — *entire unit not covered*

- [Mass](https://www.khanacademy.org/math/cc-third-grade-math/imp-measurement-and-data/imp-mass) — e.g. Understanding mass (grams and kilograms); Word problems with mass
- [Volume](https://www.khanacademy.org/math/cc-third-grade-math/imp-measurement-and-data/imp-volume) — e.g. Understanding volume (liters); Word problems with volume

### Represent and interpret data — *entire unit not covered*

- [Line plots with fractions](https://www.khanacademy.org/math/cc-third-grade-math/represent-and-interpret-data/imp-line-plots) — e.g. Measuring lengths to nearest 1/4 unit; Graphing data on line plots; Interpreting line plots with fractions

## 4th grade math

### Place value — 3 of 6 lessons not covered

- [Writing whole numbers in expanded form](https://www.khanacademy.org/math/cc-fourth-grade-math/imp-place-value-and-rounding-2/imp-ways-to-write-whole-numbers-expanded-form-and-written-form) — e.g. Writing a number in expanded form
- [Writing whole numbers in written form](https://www.khanacademy.org/math/cc-fourth-grade-math/imp-place-value-and-rounding-2/writing-whole-numbers-in-written-form) — e.g. Writing numbers in words and standard form
- [Regrouping whole numbers](https://www.khanacademy.org/math/cc-fourth-grade-math/imp-place-value-and-rounding-2/imp-regrouping-whole-numbers) — e.g. Regrouping whole number place values; Regrouping numbers into various place values; Adding whole numbers by their place values

### Addition, subtraction, and estimation — 2 of 3 lessons not covered

- [Adding multi-digit numbers](https://www.khanacademy.org/math/cc-fourth-grade-math/imp-addition-and-subtraction-2/imp-adding-multi-digit-numbers) — e.g. Relate place value to standard algorithm for multi-digit addition; Adding multi-digit numbers: 48,029+233,930
- [Subtracting multi-digit numbers](https://www.khanacademy.org/math/cc-fourth-grade-math/imp-addition-and-subtraction-2/imp-subtracting-multi-digit-numbers) — e.g. Relate place value to standard algorithm for multi-digit subtraction; Multi-digit subtraction: 389,002-76,151

### Multiply by 1-digit numbers — 4 of 5 lessons not covered

- [Comparing with multiplication](https://www.khanacademy.org/math/cc-fourth-grade-math/imp-multiplication-and-division-2/imp-comparing-with-multiplication) — e.g. Comparing with multiplication; Comparing with multiplication and addition: giraffe; Comparing with multiplication and addition: money
- [Multi-digit multiplication: place value and area models](https://www.khanacademy.org/math/cc-fourth-grade-math/imp-multiplication-and-division-2/imp-multi-digit-multiplication-place-value-and-area-models) — e.g. Using area model and properties to multiply ; Multiplying with area model: 6 x 7981
- [Estimate products](https://www.khanacademy.org/math/cc-fourth-grade-math/imp-multiplication-and-division-2/estimate-products) — e.g. Estimating with multiplication
- [Multiply with partial products](https://www.khanacademy.org/math/cc-fourth-grade-math/imp-multiplication-and-division-2/multiply-with-partial-products) — e.g. Multiplying 2-digits by 1-digit with partial products; Multiplying 3-digit by 1-digit; Multiplying 3-digit by 1-digit (regrouping)

### Multiply by 2-digit numbers — *entire unit not covered*

- [Multiply by 10s](https://www.khanacademy.org/math/cc-fourth-grade-math/multiplying-by-2-digit-numbers/multiply-by-10s) — e.g. Multiplying 10s
- [Multiply 2-digit numbers with area models](https://www.khanacademy.org/math/cc-fourth-grade-math/multiplying-by-2-digit-numbers/multiply-2-digit-numbers-with-area-models) — e.g. Multiplying with area model: 16 x 27; Multiplying with area model: 78 x 65
- [Estimate products (2-digit numbers)](https://www.khanacademy.org/math/cc-fourth-grade-math/multiplying-by-2-digit-numbers/estimate-products-2-digit-numbers) — e.g. Estimating 2-digit multiplication
- [Multiply 2-digit numbers with partial products](https://www.khanacademy.org/math/cc-fourth-grade-math/multiplying-by-2-digit-numbers/multiply-2-digit-numbers-with-partial-products) — e.g. Multiplying two 2-digit numbers using partial products; Multiplying 2-digit numbers

### Division — 2 of 8 lessons not covered

- [Estimate quotients](https://www.khanacademy.org/math/cc-fourth-grade-math/division/estimate-quotients) — e.g. Estimating quotients
- [Multiplication, division word problems](https://www.khanacademy.org/math/cc-fourth-grade-math/division/mult-division-word-problems) — e.g. Division word problem: field goals; Multiplication word problem: pizza

### Factors, multiples and patterns — 1 of 3 lessons not covered

- [Math patterns](https://www.khanacademy.org/math/cc-fourth-grade-math/imp-factors-multiples-and-patterns/imp-math-patterns) — e.g. Factors and multiples: days of the week; Math patterns: table; Math patterns: toothpicks

### Add and subtract fractions — 6 of 8 lessons not covered

- [Decomposing fractions](https://www.khanacademy.org/math/cc-fourth-grade-math/imp-fractions-2/imp-decomposing-fractions) — e.g. Decomposing a fraction visually; Decomposing a mixed number
- [Adding and subtracting fractions: word problems](https://www.khanacademy.org/math/cc-fourth-grade-math/imp-fractions-2/imp-adding-and-subtracting-fractions-word-problems) — e.g. Fraction word problem: piano; Fraction word problem: pizza; Fraction word problem: spider eyes
- [Adding and subtracting mixed numbers](https://www.khanacademy.org/math/cc-fourth-grade-math/imp-fractions-2/imp-adding-and-subtracting-mixed-numbers) — e.g. Adding mixed numbers with like denominators; Subtracting mixed numbers with like denominators; Mixed number addition with regrouping
- [Adding and subtracting mixed numbers word problems](https://www.khanacademy.org/math/cc-fourth-grade-math/imp-fractions-2/adding-and-subtracting-mixed-numbers-word-problems) — e.g. Fraction word problem: lizard; Subtracting mixed numbers with like denominators word problem
- [Fractions with denominators of 10 and 100](https://www.khanacademy.org/math/cc-fourth-grade-math/imp-fractions-2/imp-fractions-with-denominators-of-10-and-100) — e.g. Visually converting tenths and hundredths; Decomposing hundredths ; Decomposing hundredths on number line

### Multiply fractions — 2 of 4 lessons not covered

- [Multiplying whole numbers and mixed numbers](https://www.khanacademy.org/math/cc-fourth-grade-math/4th-multiply-fractions/imp-multiplying-whole-numbers-and-fractions) — e.g. Multiplying mixed numbers by whole numbers
- [Multiplying whole numbers and fractions word problems](https://www.khanacademy.org/math/cc-fourth-grade-math/4th-multiply-fractions/imp-multiplying-whole-numbers-and-fractions-word-problems) — e.g. Multiplying fractions word problem: milk; Multiplying fractions word problem: movies; Multiplying fractions by whole numbers word problem

### Understand decimals — 3 of 10 lessons not covered

- [Decimals in word form](https://www.khanacademy.org/math/cc-fourth-grade-math/imp-decimals/imp-intro-to-decimals) — e.g. Decimals as words; Relating decimals and fractions in words; Decimal place value
- [Decimals on the number line](https://www.khanacademy.org/math/cc-fourth-grade-math/imp-decimals/imp-decimals-on-the-number-line) — e.g. Graphing tenths from 0 to 1 ; Identifying tenths on a number line; Graphing hundredths from 0 to 0.1
- [Regrouping decimals](https://www.khanacademy.org/math/cc-fourth-grade-math/imp-decimals/imp-decimals-greater-than-one) — e.g. Decimal place value with regrouping

### Plane figures — *entire unit not covered*

- [Types of plane figures](https://www.khanacademy.org/math/geometry/hs-geo-transformations/hs-geo-intro-euclid) — e.g. Terms & labels in geometry; Lines, line segments, & rays
- [Angle introduction](https://www.khanacademy.org/math/cc-seventh-grade-math/cc-7th-geometry/cc-7th-angles) — e.g. Angles: introduction; Naming angles; Identifying an angle
- [Parallel and perpendicular](https://www.khanacademy.org/math/geometry/hs-geo-analytic-geometry/hs-geo-parallel-perpendicular-lines) — e.g. Parallel & perpendicular lines intro; Parallel & perpendicular lines; Drawing parallel line segments
- [Classifying triangles](https://www.khanacademy.org/math/cc-fourth-grade-math/plane-figures/imp-classifying-triangles) — e.g. Classifying triangles ; Classifying triangles by angles; Worked example: Classifying triangles
- [Classifying geometric shapes](https://www.khanacademy.org/math/cc-fourth-grade-math/plane-figures/imp-classifying-geometric-shapes) — e.g. Classifying shapes by line and angles types; Quadrilateral properties; Classifying shapes by lines and angles
- [Line of symmetry](https://www.khanacademy.org/math/geometry/xff63fac4:hs-geo-transformation-properties-and-proofs/hs-geo-symmetry) — e.g. Intro to reflective symmetry; Identifying symmetrical figures

### Measuring angles — 2 of 3 lessons not covered

- [Understanding angle measurement](https://www.khanacademy.org/math/cc-fourth-grade-math/imp-geometry-2/imp-angles-in-circles) — e.g. Angle measurement & circle arcs; Measuring angles with a circular protractor; Angles in circles word problem
- [Measuring angles](https://www.khanacademy.org/math/cc-fourth-grade-math/imp-geometry-2/imp-measuring-angles) — e.g. Measuring angles in degrees; Measuring angles using a protractor; Measuring angles using a protractor 2

### Units of measurement — 4 of 10 lessons not covered

- [Estimating mass](https://www.khanacademy.org/math/cc-fourth-grade-math/imp-measurement-and-data-2/imp-estimating-mass) — e.g. Metric system: units of weight; Choose pounds or ounces to measure weight; U.S. customary units: weight
- [Estimating volume](https://www.khanacademy.org/math/cc-fourth-grade-math/imp-measurement-and-data-2/imp-estimating-volume) — e.g. Metric system: units of volume; U.S. customary units: fluid volume
- [Estimating length](https://www.khanacademy.org/math/cc-fourth-grade-math/imp-measurement-and-data-2/imp-estimating-length) — e.g. Metric system: units of distance; U.S. customary units: distance
- [Conversion word problems](https://www.khanacademy.org/math/cc-fourth-grade-math/imp-measurement-and-data-2/imp-conversion-word-problems) — e.g. Multi-step unit conversion examples (metric); Multi-step unit conversion examples  (U.S. Customary)

## 5th grade math

### Decimal place value — 5 of 7 lessons not covered

- [Decimal place value intro](https://www.khanacademy.org/math/cc-fifth-grade-math/imp-place-value-and-decimals/imp-decimal-place-value-intro) — e.g. Place value with decimals
- [Decimals in expanded form](https://www.khanacademy.org/math/cc-fifth-grade-math/imp-place-value-and-decimals/imp-decimals-in-expanded-form) — e.g. Write decimals in expanded form
- [Decimals in written form](https://www.khanacademy.org/math/cc-fifth-grade-math/imp-place-value-and-decimals/imp-decimals-in-written-form) — e.g. Decimals in written form (hundredths); Decimals in written form (thousandths)
- [Decimals in different forms](https://www.khanacademy.org/math/cc-fifth-grade-math/imp-place-value-and-decimals/decimals-in-different-forms) — e.g. Expressing decimals in multiple forms; Visual understanding of regrouping decimals; Regrouping with decimals

### Add decimals — 1 of 4 lessons not covered

- [Adding decimals intro](https://www.khanacademy.org/math/cc-fifth-grade-math/imp-addition-and-subtraction-3/imp-adding-decimals-intro) — e.g. Estimating decimal addition

### Subtract decimals — 1 of 3 lessons not covered

- [Subtracting decimals intro](https://www.khanacademy.org/math/cc-fifth-grade-math/subtract-decimals/imp-subtracting-decimals-intro) — e.g. Estimating decimal subtraction

### Add and subtract fractions — 2 of 5 lessons not covered

- [Adding and subtracting mixed numbers with unlike denominators](https://www.khanacademy.org/math/cc-fifth-grade-math/imp-fractions-3/imp-adding-and-subtracting-mixed-number-with-unlike-denominators) — e.g. Adding mixed numbers: 19 3/18 + 18 2/3; Subtracting mixed numbers: 7 6/9 - 3 2/5; Adding mixed numbers with regrouping
- [Adding and subtracting fractions with unlike denominators word problems](https://www.khanacademy.org/math/cc-fifth-grade-math/imp-fractions-3/imp-adding-and-subtracting-fractions-with-unlike-denominators-word-problems) — e.g. Adding fractions word problem: paint; Subtracting fractions word problem: tomatoes

### Multi-digit multiplication and division — 3 of 4 lessons not covered

- [Multi-digit multiplication estimation](https://www.khanacademy.org/math/cc-fifth-grade-math/multi-digit-multiplication-and-division/multi-digit-multiplication-estimation) — e.g. Strategies for multiplying multiples of 10, 100 and 1000; Estimating multi-digit multiplication
- [Multi-digit multiplication](https://www.khanacademy.org/math/cc-fifth-grade-math/multi-digit-multiplication-and-division/imp-multi-digit-multiplication) — e.g. Relate multiplication with area models to the standard algorithm; Intro to standard way of multiplying multi-digit numbers; Understanding the standard algorithm for multiplication
- [Multi-digit division estimation](https://www.khanacademy.org/math/cc-fifth-grade-math/multi-digit-multiplication-and-division/multi-digit-division-estimation) — e.g. Strategies for dividing multiples of 10, 100, and 1000; Estimating multi-digit division

### Multiply fractions — 4 of 6 lessons not covered

- [Multiplication as scaling](https://www.khanacademy.org/math/cc-fifth-grade-math/5th-multiply-fractions/imp-multiplication-as-scaling) — e.g. Multiplication as scaling with fractions; Fraction multiplication as scaling examples
- [Multiplying mixed numbers](https://www.khanacademy.org/math/cc-fifth-grade-math/5th-multiply-fractions/imp-multiplying-mixed-numbers) — e.g. Multiplying mixed numbers
- [Area of rectangles with fraction side lengths](https://www.khanacademy.org/math/cc-fifth-grade-math/5th-multiply-fractions/area-of-rectangles-with-fraction-side-lengths) — e.g. Finding area with fractional sides 1; Finding area with fractional sides 2
- [Multiplying fractions word problems](https://www.khanacademy.org/math/cc-fifth-grade-math/5th-multiply-fractions/imp-multiplying-fractions-word-problems) — e.g. Multiplying fractions word problem: muffins; Multiplying fractions word problem: laundry; Multiplying fractions word problem: bike

### Divide fractions — 3 of 5 lessons not covered

- [Fractions as division](https://www.khanacademy.org/math/cc-fifth-grade-math/divide-fractions/imp-fractions-as-division) — e.g. Understanding fractions as division; Creating a fraction through division; Creating mixed numbers with fraction division
- [Relate fraction division to fraction multiplication](https://www.khanacademy.org/math/cc-fifth-grade-math/divide-fractions/relate-fraction-division-to-fraction-multiplication) — e.g. Multiplication and division relationship for fractions
- [Dividing fractions and whole numbers word problems](https://www.khanacademy.org/math/cc-fifth-grade-math/divide-fractions/imp-dividing-fractions-and-whole-numbers-word-problems) — e.g. Fraction division in context; Dividing fractions and whole number word problems

### Divide decimals — 3 of 4 lessons not covered

- [Estimate to divide decimals](https://www.khanacademy.org/math/cc-fifth-grade-math/divide-decimals/estimate-to-divide-decimals) — e.g. Estimating decimal division
- [Divide whole numbers to get a decimal quotient](https://www.khanacademy.org/math/cc-fifth-grade-math/divide-decimals/divide-whole-numbers-to-get-a-decimal-quotient) — e.g. Divide whole numbers with decimal quotients: 5÷2; Divide whole numbers with decimal quotients: 78÷12
- [Divide whole numbers by decimals](https://www.khanacademy.org/math/cc-fifth-grade-math/divide-decimals/divide-whole-numbers-by-decimals) — e.g. Visually dividing a whole number by a decimal; Dividing a whole number by a decimal on a number line; Division strategies for decimal quotients

### Powers of ten — 1 of 5 lessons not covered

- [Comparing decimal place values](https://www.khanacademy.org/math/cc-fifth-grade-math/powers-of-ten/imp-comparing-decimal-place-values) — e.g. Comparing decimal place values

### Volume — 1 of 4 lessons not covered

- [Volume with unit cubes](https://www.khanacademy.org/math/cc-fifth-grade-math/5th-volume/volume-with-unit-cubes) — e.g. Volume intro; Measuring volume with unit cubes

### Coordinate plane — *entire unit not covered*

- [Intro to the coordinate plane](https://www.khanacademy.org/math/cc-fifth-grade-math/imp-geometry-3/imp-intro-to-the-coordinate-plane) — e.g. Introduction to the coordinate plane; Coordinate plane: graphing points
- [Coordinate plane word problems](https://www.khanacademy.org/math/cc-fifth-grade-math/imp-geometry-3/imp-coordinate-plane-word-problems) — e.g. Coordinate plane graphing word problem; Interpreting plotted points

### Algebraic thinking — *entire unit not covered*

- [Writing expressions](https://www.khanacademy.org/math/cc-fifth-grade-math/imp-algebraic-thinking/imp-writing-expressions) — e.g. Constructing numerical expressions; Evaluating expressions with & without parentheses; Translating expressions with parentheses
- [Number patterns](https://www.khanacademy.org/math/cc-fifth-grade-math/imp-algebraic-thinking/imp-number-patterns) — e.g. Graphing patterns on coordinate plane; Interpreting patterns on coordinate plane; Interpreting relationships in ordered pairs

### Converting units of measure — 2 of 5 lessons not covered

- [Converting metric units word problems](https://www.khanacademy.org/math/cc-fifth-grade-math/imp-measurement-and-data-3/converting-metric-units-word-problems) — e.g. Measurement word problem: tea party; Time word problem: Susan's break
- [Converting US Customary units word problems](https://www.khanacademy.org/math/cc-fifth-grade-math/imp-measurement-and-data-3/converting-us-customary-units-word-problems) — e.g. Measurement word problem: running laps; Measurement word problem: elevator; Measurement word problem: blood drive

### Line plots — *entire unit not covered*

- [Graph data on line plots](https://www.khanacademy.org/math/cc-fourth-grade-math/imp-fractions-2/imp-line-plots-with-fractions) — e.g. Making line plots with fractional data
- [Interpret data on line plots](https://www.khanacademy.org/math/cc-fourth-grade-math/imp-fractions-2/imp-line-plots-with-fractions) — e.g. Interpreting line plots with fractions; Reading a line plot with fractions; Line plot distribution: trail mix

### Properties of shapes — *entire unit not covered*

- [Triangles](https://www.khanacademy.org/math/cc-fourth-grade-math/plane-figures/imp-classifying-triangles) — e.g. Classifying triangles ; Classifying triangles by angles

## 6th grade math

### Ratios — 1 of 4 lessons not covered

- [Intro to ratios](https://www.khanacademy.org/math/cc-sixth-grade-math/cc-6th-ratios-prop-topic/intro-to-ratios) — e.g. Intro to ratios; Basic ratios; Part:whole ratios

### Arithmetic with rational numbers — 1 of 8 lessons not covered

- [Adding and subtracting decimals word problems](https://www.khanacademy.org/math/cc-sixth-grade-math/cc-6th-arithmetic-operations/cc-6th-add-sub-decimals-word-problems) — e.g. Adding decimals word problem; Adding & subtracting decimals word problem

### Exponents and order of operations — 1 of 5 lessons not covered

- [Powers of fractions and decimals](https://www.khanacademy.org/math/cc-sixth-grade-math/x0267d782:cc-6th-exponents-and-order-of-operations/x0267d782:powers-of-fractions-and-decimals) — e.g. Exponents of decimals; Powers of fractions

### Negative numbers — 3 of 7 lessons not covered

- [Intro to negative numbers](https://www.khanacademy.org/math/cc-sixth-grade-math/cc-6th-negative-number-topic/cc-6th-neg-num-intro) — e.g. Introduction to negative numbers
- [Negative symbol as opposite](https://www.khanacademy.org/math/cc-sixth-grade-math/cc-6th-negative-number-topic/negative-symbol-as-opposite) — e.g. Negative symbol as opposite; Number opposites
- [Rational numbers on the number line](https://www.khanacademy.org/math/cc-sixth-grade-math/cc-6th-negative-number-topic/cc-6th-neg-dec-frac-number-line) — e.g. Negative decimals on the number line; Decimals & fractions on the number line

### Variables & expressions — 6 of 12 lessons not covered

- [Parts of algebraic expressions](https://www.khanacademy.org/math/algebra/x2f8bb11595b61c86:foundation-algebra/x2f8bb11595b61c86:intro-variables) — e.g. What is a variable?; Terms, factors, & coefficients; Why aren't we using the multiplication sign?
- [Evaluating expressions with multiple variables](https://www.khanacademy.org/math/algebra/x2f8bb11595b61c86:foundation-algebra/x2f8bb11595b61c86:substitute-evaluate-expression) — e.g. Evaluating expressions with two variables; Evaluating expressions with two variables: fractions & decimals
- [Expression value intuition](https://www.khanacademy.org/math/cc-sixth-grade-math/cc-6th-expressions-and-variables/expression-value-intuition) — e.g. Expression value intuition
- [Evaluating expressions word problems](https://www.khanacademy.org/math/cc-sixth-grade-math/cc-6th-expressions-and-variables/cc-7th-evaluating-expressions-word-problems) — e.g. Evaluating expressions with variables: temperature; Evaluating expressions with variables: cubes; Evaluating expressions with variables: exponents
- [Writing algebraic expressions introduction](https://www.khanacademy.org/math/cc-sixth-grade-math/cc-6th-expressions-and-variables/cc-6th-writing-expressions) — e.g. Writing basic expressions with variables; Writing algebraic subtraction expressions; Writing expressions with variables
- [Writing basic algebraic expressions word problems](https://www.khanacademy.org/math/cc-sixth-grade-math/cc-6th-expressions-and-variables/cc-6th-alg-expression-word-problems) — e.g. Writing basic expressions word problems

### Equations & inequalities — 6 of 9 lessons not covered

- [Algebraic equations basics](https://www.khanacademy.org/math/cc-sixth-grade-math/cc-6th-equations-and-inequalities/cc-6th-intro-equations) — e.g. Variables, expressions, & equations; Testing solutions to equations
- [Finding mistakes in one-step equations](https://www.khanacademy.org/math/cc-sixth-grade-math/cc-6th-equations-and-inequalities/pre-algebra-one-step-equation-mistakes) — e.g. Finding mistakes in one-step equations
- [One-step equation word problems](https://www.khanacademy.org/math/cc-sixth-grade-math/cc-6th-equations-and-inequalities/cc-6th-super-yoga) — e.g. Modeling with one-step equations
- [Intro to inequalities with variables](https://www.khanacademy.org/math/cc-sixth-grade-math/cc-6th-equations-and-inequalities/cc-6th-inequalities) — e.g. Testing solutions to inequalities; Plotting inequalities ; Plotting an inequality example
- [Dependent and independent variables](https://www.khanacademy.org/math/cc-sixth-grade-math/cc-6th-equations-and-inequalities/cc-6th-dependent-independent) — e.g. Dependent & independent variables; Dependent & independent variables: graphing
- [Analyzing relationships between variables](https://www.khanacademy.org/math/cc-sixth-grade-math/cc-6th-equations-and-inequalities/x0267d782:cc-6th-analyzing-relationships) — e.g. Writing equations for relationships between quantities; Analyzing relationships between variables

### Plane figures — 2 of 3 lessons not covered

- [Areas of parallelograms](https://www.khanacademy.org/math/cc-sixth-grade-math/x0267d782:cc-6th-plane-figures/cc-6th-parallelogram-area) — e.g. Area of a parallelogram; Finding height of a parallelogram
- [Area of composite figures](https://www.khanacademy.org/math/cc-sixth-grade-math/x0267d782:cc-6th-plane-figures/cc-6th-area) — e.g. Finding area by rearranging parts; Area of composite shapes; Area of quadrilateral with 2 parallel sides

### Coordinate plane — 2 of 3 lessons not covered

- [Four quadrants](https://www.khanacademy.org/math/cc-sixth-grade-math/x0267d782:coordinate-plane/cc-6th-coordinate-plane) — e.g. Points on the coordinate plane examples; Plotting a point (ordered pair); Finding the point not graphed
- [Polygons on the coordinate plane](https://www.khanacademy.org/math/cc-sixth-grade-math/x0267d782:coordinate-plane/cc-6th-quadrilaterals-on-plane) — e.g. Drawing a quadrilateral on the coordinate plane example; Area of a parallelogram on the coordinate plane; Coordinates of a missing vertex

### 3D figures — 3 of 5 lessons not covered

- [Geometric solids (3D shapes)](https://www.khanacademy.org/math/cc-sixth-grade-math/cc-6th-geometry-topic/geometric-solids) — e.g. Counting faces and edges of 3D shapes; Recognizing common 3D shapes
- [Volume with mini cubes](https://www.khanacademy.org/math/cc-sixth-grade-math/cc-6th-geometry-topic/x0267d782:cc-6th-volume-with-mini-cubes) — e.g. Volume with fractional cubes
- [Volume with fractions](https://www.khanacademy.org/math/cc-sixth-grade-math/cc-6th-geometry-topic/cc-6th-volume-with-fractions) — e.g. Volume of a rectangular prism: fractional dimensions; How volume changes from changing dimensions; Volume of a rectangular prism: word problem

### Data and statistics — 6 of 10 lessons not covered

- [Statistical questions](https://www.khanacademy.org/math/cc-sixth-grade-math/cc-6th-data-statistics/cc-6-statistical-questions) — e.g. Statistical questions
- [Dot plots & frequency tables](https://www.khanacademy.org/math/cc-sixth-grade-math/cc-6th-data-statistics/dot-plot) — e.g. Representing data; Frequency tables & dot plots
- [Histograms](https://www.khanacademy.org/math/cc-sixth-grade-math/cc-6th-data-statistics/histograms) — e.g. Creating a histogram; Interpreting a histogram
- [Mean and median challenge problems](https://www.khanacademy.org/math/cc-sixth-grade-math/cc-6th-data-statistics/cc-6th-mean-median-challenge) — e.g. Missing value given the mean; Impact on median & mean: removing an outlier; Impact on median & mean: increasing an outlier
- [Comparing data displays](https://www.khanacademy.org/math/cc-sixth-grade-math/cc-6th-data-statistics/cc-7th-compare-data-displays) — e.g. Comparing dot plots, histograms, and box plots
- [Shape of data distributions](https://www.khanacademy.org/math/cc-sixth-grade-math/cc-6th-data-statistics/cc-6-shape-of-data) — e.g. Shapes of distributions; Clusters, gaps, peaks & outliers

## 7th grade math

### Proportional relationships — 2 of 6 lessons not covered

- [Identifying proportional relationships](https://www.khanacademy.org/math/cc-seventh-grade-math/cc-7th-ratio-proportion/cc-7th-proportional-rel) — e.g. Intro to proportional relationships; Proportional relationships: movie tickets; Proportional relationships: bananas
- [Graphs of proportional relationships](https://www.khanacademy.org/math/cc-seventh-grade-math/cc-7th-ratio-proportion/cc-7th-graphs-proportions) — e.g. Identifying proportional relationships from graphs; Proportional relationships: graphs; Interpreting graphs of proportional relationships

### Rates and percentages — 1 of 3 lessons not covered

- [Rate problems with fractions](https://www.khanacademy.org/math/cc-seventh-grade-math/cc-7th-fractions-decimals/cc-7th-rates) — e.g. Rates with fractions

### Rational numbers: addition and subtraction — 2 of 5 lessons not covered

- [Addition & subtraction word problems with negatives](https://www.khanacademy.org/math/cc-seventh-grade-math/x6b17ba59:rational-numbers-addition-and-subtraction/cc-7th-add-sub-word-problems-w-negatives) — e.g. Interpreting negative number statements; Negative number word problem: temperatures; Negative number word problem: Alaska
- [Properties of addition & subtraction](https://www.khanacademy.org/math/cc-seventh-grade-math/x6b17ba59:rational-numbers-addition-and-subtraction/cc-7th-properties-of-addition-and-subtraction) — e.g. Associative and commutative properties of addition with negatives; Equivalent expressions with negative numbers

### Negative numbers: multiplication and division — 3 of 9 lessons not covered

- [Multiplication & division word problems with negatives](https://www.khanacademy.org/math/cc-seventh-grade-math/cc-7th-negative-numbers-multiply-and-divide/cc-7th-mult-div-neg-word-problems) — e.g. Interpreting multiplication & division of negative numbers
- [Rational number word problems](https://www.khanacademy.org/math/cc-seventh-grade-math/cc-7th-negative-numbers-multiply-and-divide/cc-7th-multistep-word-probs) — e.g. Rational number word problem: school report; Rational number word problem: cosmetics; Rational number word problem: cab
- [Powers with rational bases](https://www.khanacademy.org/math/cc-seventh-grade-math/cc-7th-negative-numbers-multiply-and-divide/x6b17ba59:powers-with-rational-bases) — e.g. Exponents with negative bases; 1 and -1 to different powers

### Expressions, equations, & inequalities — 2 of 8 lessons not covered

- [Interpreting linear expressions](https://www.khanacademy.org/math/cc-seventh-grade-math/cc-7th-variables-expressions/cc-7th-interpreting-lin-exp) — e.g. Interpreting linear expressions: diamonds; Interpreting linear expressions: flowers; Writing expressions word problems
- [Two-step equation word problems](https://www.khanacademy.org/math/cc-seventh-grade-math/cc-7th-variables-expressions/cc-7th-linear-eq-word-probs) — e.g. Equation word problem: super yoga (1 of 2); Equation word problem: super yoga (2 of 2); Two-step equation word problem: computers

### Statistics and probability — 2 of 4 lessons not covered

- [Probability models](https://www.khanacademy.org/math/cc-seventh-grade-math/cc-7th-probability-statistics/cc-7th-theoretical-and-experimental-probability) — e.g. Theoretical and experimental probabilities; Making predictions with probability ; Probability models example: frozen yogurt
- [Comparing and sampling populations](https://www.khanacademy.org/math/cc-seventh-grade-math/cc-7th-probability-statistics/cc-7th-population-sampling) — e.g. Reasonable samples; Comparing distributions with dot plots (example problem)

### Geometry — 2 of 7 lessons not covered

- [Area and circumference challenge problems](https://www.khanacademy.org/math/cc-seventh-grade-math/cc-7th-geometry/cc-7th-area-circ-challenge) — e.g. Finding circumference of a circle when given the area; Area of a shaded region; Impact of increasing the radius
- [Slicing geometric shapes](https://www.khanacademy.org/math/geometry/hs-geo-solids/hs-geo-2d-vs-3d) — e.g. Slicing a rectangular pyramid

## 8th grade math

### Numbers and operations — 3 of 12 lessons not covered

- [Repeating decimals](https://www.khanacademy.org/math/cc-eighth-grade-math/cc-8th-numbers-operations/cc-8th-repeating-decimals) — e.g. Converting a fraction to a repeating decimal; Converting repeating decimals to fractions (part 1 of 2); Converting repeating decimals to fractions (part 2 of 2)
- [Irrational numbers](https://www.khanacademy.org/math/algebra/x2f8bb11595b61c86:irrational-numbers/x2f8bb11595b61c86:irrational-numbers-intro) — e.g. Intro to rational & irrational numbers; Classifying numbers: rational & irrational; Classifying numbers
- [Scientific notation word problems](https://www.khanacademy.org/math/cc-eighth-grade-math/cc-8th-numbers-operations/cc-8th-scientific-notation-word-problems) — e.g. Scientific notation word problem: red blood cells; Scientific notation word problem: U.S. national debt; Scientific notation word problem: speed of light

### Solving equations with one unknown — 2 of 4 lessons not covered

- [Number of solutions to equations](https://www.khanacademy.org/math/algebra/x2f8bb11595b61c86:solve-equations-inequalities/x2f8bb11595b61c86:num-solutions-linear-equations) — e.g. Number of solutions to equations; Worked example: number of solutions to equations; Creating an equation with no solutions
- [Equations word problems](https://www.khanacademy.org/math/cc-eighth-grade-math/cc-8th-solving-equations/linear-equations-word-problems) — e.g. Sums of consecutive integers; Sum of integers challenge

### Linear equations and functions — 7 of 13 lessons not covered

- [Solutions to linear equations](https://www.khanacademy.org/math/algebra/x2f8bb11595b61c86:foundation-algebra/x2f8bb11595b61c86:algebra-overview-history) — e.g. Intro to the coordinate plane; Solutions to 2-variable equations; Worked example: solutions to 2-variable equations
- [Intercepts](https://www.khanacademy.org/math/algebra/x2f8bb11595b61c86:linear-equations-graphs/x2f8bb11595b61c86:x-intercepts-and-y-intercepts) — e.g. Intro to intercepts; x-intercept of a line; Intercepts from an equation
- [Graphing slope-intercept form](https://www.khanacademy.org/math/algebra/x2f8bb11595b61c86:forms-of-linear-equations/x2f8bb11595b61c86:graphing-slope-intercept-equations) — e.g. Graph from slope-intercept equation
- [Linear models](https://www.khanacademy.org/math/cc-eighth-grade-math/cc-8th-linear-equations-functions/8th-linear-functions-modeling) — e.g. Linear graphs word problems; Linear graphs word problem: cats; Linear equations word problems: volcano
- [Constructing linear models for real-world relationships](https://www.khanacademy.org/math/algebra/x2f8bb11595b61c86:linear-equations-graphs/x2f8bb11595b61c86:applying-intercepts-and-slope) — e.g. Linear functions word problem: fuel; Linear functions word problem: pool; Modeling with linear equations: gym membership & lemonade
- [Recognizing functions](https://www.khanacademy.org/math/cc-eighth-grade-math/cc-8th-linear-equations-functions/cc-8th-function-intro) — e.g. Testing if a relationship is a function; Relations and functions; Recognizing functions from graph
- [Linear and nonlinear functions](https://www.khanacademy.org/math/cc-eighth-grade-math/cc-8th-linear-equations-functions/linear-nonlinear-functions-tut) — e.g. Recognizing linear functions; Linear & nonlinear functions: table; Linear & nonlinear functions: word problem

### Systems of equations — 1 of 5 lessons not covered

- [Systems of equations word problems](https://www.khanacademy.org/math/algebra/x2f8bb11595b61c86:systems-of-equations/x2f8bb11595b61c86:systems-of-equations-word-problems) — e.g. Age word problem: Imran; Age word problem: Ben & William; Age word problem: Arman & Diya

### Geometry — 2 of 7 lessons not covered

- [Angles between intersecting lines](https://www.khanacademy.org/math/cc-eighth-grade-math/cc-8th-geometry/cc-8th-angles-between-lines) — e.g. Angles, parallel lines, & transversals; Parallel & perpendicular lines; Missing angles with a transversal

### Geometric transformations — 3 of 7 lessons not covered

- [Transformations intro](https://www.khanacademy.org/math/geometry/hs-geo-transformations/hs-geo-transformations-intro) — e.g. Rigid transformations intro; Dilations intro; Identifying transformations
- [Properties & definitions of transformations](https://www.khanacademy.org/math/geometry/xff63fac4:hs-geo-transformation-properties-and-proofs/hs-geo-rigid-transformations-overview) — e.g. Finding measures using rigid transformations; Rigid transformations: preserved properties; Mapping shapes
- [Congruence and similarity](https://www.khanacademy.org/math/geometry/hs-geo-congruence/hs-geo-trans-and-congruence) — e.g. Congruent shapes & transformations; Non-congruent shapes & transformations; Similar shapes & transformations

### Data and modeling — 2 of 4 lessons not covered

- [Introduction to scatter plots](https://www.khanacademy.org/math/cc-eighth-grade-math/cc-8th-data/cc-8th-scatter-plots) — e.g. Constructing a scatter plot
- [Interpreting scatter plots](https://www.khanacademy.org/math/cc-eighth-grade-math/cc-8th-data/cc-8th-interpreting-scatter-plots) — e.g. Example of direction in scatterplots; Scatter plot: smokers

## Basic geometry and measurement

### Measuring angles — 5 of 6 lessons not covered

- [Parts of plane figures](https://www.khanacademy.org/math/geometry/hs-geo-transformations/hs-geo-intro-euclid) — e.g. Terms & labels in geometry; Lines, line segments, & rays
- [Angle types](https://www.khanacademy.org/math/cc-fourth-grade-math/plane-figures/imp-angle-introduction) — e.g. Identifying an angle; Acute, right, & obtuse angles; Recognizing angles

### Plane figures — *entire unit not covered*

- [Quadrilaterals introduction](https://www.khanacademy.org/math/cc-third-grade-math/quadrilaterals-3rd/imp-quadrilaterals) — e.g. Intro to quadrilaterals
- [Lines of symmetry](https://www.khanacademy.org/math/geometry/xff63fac4:hs-geo-transformation-properties-and-proofs/hs-geo-symmetry) — e.g. Intro to reflective symmetry; Identifying symmetrical figures
- [More on quadrilaterals](https://www.khanacademy.org/math/cc-fourth-grade-math/plane-figures/imp-classifying-geometric-shapes) — e.g. Quadrilateral properties; Kites as a geometric shape; Quadrilateral types

### Coordinate plane — 3 of 4 lessons not covered

- [Points in all four quadrants](https://www.khanacademy.org/math/cc-sixth-grade-math/x0267d782:coordinate-plane/cc-6th-coordinate-plane) — e.g. Points on the coordinate plane examples; Plotting a point (ordered pair); Finding the point not graphed

### Decomposing to find area — 2 of 4 lessons not covered

- [Area of parallelograms](https://www.khanacademy.org/math/cc-sixth-grade-math/x0267d782:cc-6th-plane-figures/cc-6th-parallelogram-area) — e.g. Area of a parallelogram; Finding height of a parallelogram

### Angle relationships — 1 of 4 lessons not covered

- [Parallel lines and transversals](https://www.khanacademy.org/math/cc-eighth-grade-math/cc-8th-geometry/cc-8th-angles-between-lines) — e.g. Angles, parallel lines, & transversals; Parallel & perpendicular lines; Missing angles with a transversal

## Algebra 1

### Algebra foundations — 3 of 6 lessons not covered

- [Overview and history of algebra](https://www.khanacademy.org/math/algebra/x2f8bb11595b61c86:foundation-algebra/x2f8bb11595b61c86:algebra-overview-history) — e.g. Origins of algebra; Abstract-ness; The beauty of algebra
- [Introduction to variables](https://www.khanacademy.org/math/algebra/x2f8bb11595b61c86:foundation-algebra/x2f8bb11595b61c86:intro-variables) — e.g. What is a variable?; Why aren't we using the multiplication sign?; Creativity break: Why is creativity important in STEM jobs?
- [Division by zero](https://www.khanacademy.org/math/algebra/x2f8bb11595b61c86:foundation-algebra/x2f8bb11595b61c86:division-zero) — e.g. Why dividing by zero is undefined; The problem with dividing zero by zero; Undefined & indeterminate expressions

### Solving equations & inequalities — 2 of 6 lessons not covered

- [Analyzing the number of solutions to linear equations](https://www.khanacademy.org/math/algebra/x2f8bb11595b61c86:solve-equations-inequalities/x2f8bb11595b61c86:num-solutions-linear-equations) — e.g. Number of solutions to equations; Worked example: number of solutions to equations; Creating an equation with no solutions
- [Compound inequalities](https://www.khanacademy.org/math/algebra/x2f8bb11595b61c86:solve-equations-inequalities/x2f8bb11595b61c86:compound-inequalities) — e.g. Compound inequalities: OR; Compound inequalities: AND; A compound inequality with no solution

### Working with units — *entire unit not covered*

- [Rate conversion](https://www.khanacademy.org/math/algebra/x2f8bb11595b61c86:working-units/x2f8bb11595b61c86:rate-conversion) — e.g. Intro to dimensional analysis; Same rate with different units; Creativity break: When did you first realize that you liked algebra
- [Appropriate units](https://www.khanacademy.org/math/algebra/x2f8bb11595b61c86:working-units/x2f8bb11595b61c86:appropriate-units) — e.g. Defining appropriate quantities for modeling; Formulas and units: Volume of a pool; Formulas and units: Comparing rates
- [Word problems with multiple units](https://www.khanacademy.org/math/algebra/x2f8bb11595b61c86:working-units/x2f8bb11595b61c86:word-problems-multiple-units) — e.g. Using units to solve problems: Toy factory; Using units to solve problems: Road trip; Using units to solve problems: Drug dosage

### Linear equations & graphs — 5 of 6 lessons not covered

- [Two-variable linear equations intro](https://www.khanacademy.org/math/algebra/x2f8bb11595b61c86:linear-equations-graphs/x2f8bb11595b61c86:two-variable-linear-equations-intro) — e.g. Two-variable linear equations intro; Solutions to 2-variable equations; Worked example: solutions to 2-variable equations
- [Horizontal & vertical lines](https://www.khanacademy.org/math/algebra/x2f8bb11595b61c86:linear-equations-graphs/x2f8bb11595b61c86:horizontal-vertical-lines) — e.g. Slope of a horizontal line; Horizontal & vertical lines
- [x-intercepts and y-intercepts](https://www.khanacademy.org/math/algebra/x2f8bb11595b61c86:linear-equations-graphs/x2f8bb11595b61c86:x-intercepts-and-y-intercepts) — e.g. Intro to intercepts; x-intercept of a line; Intercepts from an equation
- [Applying intercepts and slope](https://www.khanacademy.org/math/algebra/x2f8bb11595b61c86:linear-equations-graphs/x2f8bb11595b61c86:applying-intercepts-and-slope) — e.g. Slope, x-intercept, y-intercept meaning in context; Slope and intercept meaning in context; Slope and intercept meaning from a table
- [Modeling with linear equations and inequalities](https://www.khanacademy.org/math/algebra/x2f8bb11595b61c86:linear-equations-graphs/x2f8bb11595b61c86:modeling-with-linear-equations-and-inequalities) — e.g. Comparing linear rates example; Creativity break: How do you apply creativity in algebra

### Forms of linear equations — 1 of 6 lessons not covered

- [Graphing slope-intercept equations](https://www.khanacademy.org/math/algebra/x2f8bb11595b61c86:forms-of-linear-equations/x2f8bb11595b61c86:graphing-slope-intercept-equations) — e.g. Graph from slope-intercept equation

### Systems of equations — 2 of 6 lessons not covered

- [Equivalent systems of equations](https://www.khanacademy.org/math/algebra/x2f8bb11595b61c86:systems-of-equations/x2f8bb11595b61c86:equivalent-systems-equations) — e.g. Why can we subtract one equation from the other in a system of equations?; Worked example: equivalent systems of equations; Worked example: non-equivalent systems of equations

### Inequalities (systems & graphs) — *entire unit not covered*

- [Checking solutions of two-variable inequalities](https://www.khanacademy.org/math/algebra/x2f8bb11595b61c86:inequalities-systems-graphs/x2f8bb11595b61c86:checking-solutions-of-two-variable-inequalities) — e.g. Testing solutions to inequalities ; Testing solutions to systems of inequalities
- [Graphing two-variable inequalities](https://www.khanacademy.org/math/algebra/x2f8bb11595b61c86:inequalities-systems-graphs/x2f8bb11595b61c86:graphing-two-variable-inequalities) — e.g. Intro to graphing two-variable inequalities; Graphing two-variable inequalities; Two-variable inequalities from their graphs
- [Modeling with linear inequalities](https://www.khanacademy.org/math/algebra/x2f8bb11595b61c86:inequalities-systems-graphs/x2f8bb11595b61c86:modeling-with-linear-inequalities) — e.g. Writing two-variable inequalities word problem; Solving two-variable inequalities word problem; Interpreting two-variable inequalities word problem

### Functions — 6 of 13 lessons not covered

- [Functions and equations](https://www.khanacademy.org/math/algebra/x2f8bb11595b61c86:functions/x2f8bb11595b61c86:functions-and-equations) — e.g. Equations vs. functions; Obtaining a function from an equation
- [Interpreting function notation](https://www.khanacademy.org/math/algebra/x2f8bb11595b61c86:functions/x2f8bb11595b61c86:interpreting-function-notation) — e.g. Function notation word problem: bank; Function notation word problem: beach
- [Maximum and minimum points](https://www.khanacademy.org/math/algebra/x2f8bb11595b61c86:functions/x2f8bb11595b61c86:maximum-and-minimum-points) — e.g. Introducing minimum and maximum points; Worked example: absolute and relative extrema
- [Intervals where a function is positive, negative, increasing, or decreasing](https://www.khanacademy.org/math/algebra/x2f8bb11595b61c86:functions/x2f8bb11595b61c86:intervals-where-a-function-is-positive-negative-increasing-or-decreasing) — e.g. Increasing, decreasing, positive or negative intervals; Worked example: positive & negative intervals
- [Interpreting features of graphs](https://www.khanacademy.org/math/algebra/x2f8bb11595b61c86:functions/x2f8bb11595b61c86:interpreting-features-of-graphs) — e.g. Graph interpretation word problem: temperature; Graph interpretation word problem: basketball; Creativity break: How can people get creative in algebra

### Sequences — 1 of 6 lessons not covered

- [Modeling with sequences](https://www.khanacademy.org/math/algebra/x2f8bb11595b61c86:sequences/x2f8bb11595b61c86:modeling-with-sequences) — e.g. Sequences word problems

### Absolute value & piecewise functions — *entire unit not covered*

- [Graphs of absolute value functions](https://www.khanacademy.org/math/algebra/x2f8bb11595b61c86:absolute-value-piecewise-functions/x2f8bb11595b61c86:graphs-of-absolute-value-functions) — e.g. Shifting absolute value graphs; Scaling & reflecting absolute value functions: equation; Scaling & reflecting absolute value functions: graph
- [Piecewise functions](https://www.khanacademy.org/math/algebra/x2f8bb11595b61c86:absolute-value-piecewise-functions/x2f8bb11595b61c86:piecewise-functions) — e.g. Introduction to piecewise functions; Worked example: evaluating piecewise functions; Worked example: graphing piecewise functions

### Exponential growth & decay — 5 of 7 lessons not covered

- [Exponential vs. linear growth](https://www.khanacademy.org/math/algebra/x2f8bb11595b61c86:exponential-growth-decay/x2f8bb11595b61c86:exponential-vs-linear-growth) — e.g. Intro to exponential functions; Exponential vs. linear growth; Exponential vs. linear  models: verbal
- [Graphs of exponential growth](https://www.khanacademy.org/math/algebra/x2f8bb11595b61c86:exponential-growth-decay/x2f8bb11595b61c86:graphs-of-exponential-growth) — e.g. Exponential function graph; Graphs of exponential growth
- [Exponential vs. linear growth over time](https://www.khanacademy.org/math/algebra/x2f8bb11595b61c86:exponential-growth-decay/x2f8bb11595b61c86:exponential-vs-linear-growth-over-time) — e.g. Exponential vs. linear growth over time
- [Exponential functions from tables & graphs](https://www.khanacademy.org/math/algebra/x2f8bb11595b61c86:exponential-growth-decay/x2f8bb11595b61c86:exponential-functions-from-tables-graphs) — e.g. Writing exponential functions; Writing exponential functions from tables; Writing exponential functions from graphs
- [Exponential vs. linear models](https://www.khanacademy.org/math/algebra/x2f8bb11595b61c86:exponential-growth-decay/x2f8bb11595b61c86:exponential-vs-linear-models) — e.g. Linear vs. exponential growth: from data; Linear vs. exponential growth: from data (example 2)

### Quadratics: Multiplying & factoring — 4 of 9 lessons not covered

- [Introduction to factoring](https://www.khanacademy.org/math/algebra/x2f8bb11595b61c86:quadratics-multiplying-factoring/x2f8bb11595b61c86:intro-factoring) — e.g. Intro to factors & divisibility; Factoring with the distributive property
- [Factoring quadratics by grouping](https://www.khanacademy.org/math/algebra/x2f8bb11595b61c86:quadratics-multiplying-factoring/x2f8bb11595b61c86:factor-quadratics-grouping) — e.g. Intro to grouping; Factoring quadratics by grouping; Factoring quadratics: common factor + grouping
- [Factoring quadratics with difference of squares](https://www.khanacademy.org/math/algebra/x2f8bb11595b61c86:quadratics-multiplying-factoring/x2f8bb11595b61c86:factor-difference-squares) — e.g. Difference of squares intro; Factoring difference of squares: leading coefficient ≠ 1; Factoring difference of squares: analyzing factorization
- [Factoring quadratics with perfect squares](https://www.khanacademy.org/math/algebra/x2f8bb11595b61c86:quadratics-multiplying-factoring/x2f8bb11595b61c86:factor-perfect-squares) — e.g. Perfect square factorization intro; Factoring perfect squares; Identifying perfect square form

### Quadratic functions & equations — 3 of 13 lessons not covered

- [Intro to parabolas](https://www.khanacademy.org/math/algebra/x2f8bb11595b61c86:quadratic-functions-equations/x2f8bb11595b61c86:intro-parabolas) — e.g. Parabolas intro; Interpreting a parabola in context; Interpret a quadratic graph
- [Comparing quadratic functions](https://www.khanacademy.org/math/algebra/x2f8bb11595b61c86:quadratic-functions-equations/x2f8bb11595b61c86:graphing-and-comparing-quadratics) — e.g. Comparing features of quadratic functions; Comparing maximum points of quadratic functions
- [Transforming quadratic functions](https://www.khanacademy.org/math/algebra/x2f8bb11595b61c86:quadratic-functions-equations/x2f8bb11595b61c86:transform-quadratic-functions) — e.g. Intro to parabola transformations; Shifting parabolas; Scaling & reflecting parabolas

### Irrational numbers — *entire unit not covered*

- [Sums and products of rational and irrational numbers](https://www.khanacademy.org/math/algebra/x2f8bb11595b61c86:irrational-numbers/x2f8bb11595b61c86:sums-and-products-of-rational-and-irrational-numbers) — e.g. Proof: sum & product of two rationals is rational; Proof: product of rational & irrational is irrational; Proof: sum of rational & irrational is irrational
- [Proofs concerning irrational numbers](https://www.khanacademy.org/math/algebra/x2f8bb11595b61c86:irrational-numbers/x2f8bb11595b61c86:proofs-concerning-irrational-numbers) — e.g. Proof: √2 is irrational; Proof: square roots of prime numbers are irrational; Proof: there's an irrational number between any two rational numbers

### Creativity in algebra — *entire unit not covered*

- [Creativity in algebra](https://www.khanacademy.org/math/algebra/x2f8bb11595b61c86:algebra-creativity/x2f8bb11595b61c86:creativity-in-algebra) — e.g. Creativity in algebra; Creative algebra at work; The future of creativity in algebra

## High school geometry

### Performing transformations — 2 of 6 lessons not covered

- [Intro to Euclidean geometry](https://www.khanacademy.org/math/geometry/hs-geo-transformations/hs-geo-intro-euclid) — e.g. Euclid as the father of geometry; Terms & labels in geometry; Geometric definitions example
- [Introduction to rigid transformations](https://www.khanacademy.org/math/geometry/hs-geo-transformations/hs-geo-transformations-intro) — e.g. Rigid transformations intro; Dilations intro; Identifying transformations

### Transformation properties and proofs — *entire unit not covered*

- [Rigid transformations overview](https://www.khanacademy.org/math/geometry/xff63fac4:hs-geo-transformation-properties-and-proofs/hs-geo-rigid-transformations-overview) — e.g. Finding measures using rigid transformations; Rigid transformations: preserved properties; Mapping shapes
- [Dilation preserved properties](https://www.khanacademy.org/math/geometry/xff63fac4:hs-geo-transformation-properties-and-proofs/xff63fac4:hs-geo-dilation-preserved-properties) — e.g. Dilations and properties
- [Symmetry](https://www.khanacademy.org/math/geometry/xff63fac4:hs-geo-transformation-properties-and-proofs/hs-geo-symmetry) — e.g. Intro to reflective symmetry; Intro to rotational symmetry; Finding a quadrilateral from its symmetries
- [Proofs with transformations](https://www.khanacademy.org/math/geometry/xff63fac4:hs-geo-transformation-properties-and-proofs/xff63fac4:hs-geo-proofs-with-transformations) — e.g. Proofs with transformations

### Congruence — 6 of 8 lessons not covered

- [Transformations & congruence](https://www.khanacademy.org/math/geometry/hs-geo-congruence/hs-geo-trans-and-congruence) — e.g. Congruent shapes & transformations; Non-congruent shapes & transformations; Segment congruence equivalent to having same length
- [Triangle congruence from transformations](https://www.khanacademy.org/math/geometry/hs-geo-congruence/hs-geo-triangle-congruence) — e.g. Proving the SSS triangle congruence criterion using transformations; Proving the SAS triangle congruence criterion using transformations; Proving the ASA and AAS triangle congruence criteria using transformations
- [Congruent triangles](https://www.khanacademy.org/math/geometry/hs-geo-congruence/xff63fac4:hs-geo-congruent-triangles) — e.g. Triangle congruence postulates/criteria; Determining congruent triangles; Calculating angle measures to verify congruence
- [Theorems concerning quadrilateral properties](https://www.khanacademy.org/math/geometry/hs-geo-congruence/hs-geo-quadrilaterals-theorems) — e.g. Proof: Opposite sides of a parallelogram; Proof: Diagonals of a parallelogram; Proof: Opposite angles of a parallelogram
- [Proofs of general theorems](https://www.khanacademy.org/math/geometry/hs-geo-congruence/hs-geo-triangle-theorems) — e.g. Geometry proof problem: midpoint; Geometry proof problem: congruent segments; Geometry proof problem: squared circle
- [Constructing lines & angles](https://www.khanacademy.org/math/geometry/hs-geo-congruence/hs-geo-bisectors) — e.g. Geometric constructions: congruent angles; Geometric constructions: parallel line; Geometric constructions: perpendicular bisector

### Similarity — 4 of 7 lessons not covered

- [Definitions of similarity](https://www.khanacademy.org/math/geometry/hs-geo-similarity/hs-geo-similarity-definitions) — e.g. Similar shapes & transformations; Rational equations intro
- [Introduction to triangle similarity](https://www.khanacademy.org/math/geometry/hs-geo-similarity/hs-geo-triangle-similarity-intro) — e.g. Intro to triangle similarity; Triangle similarity postulates/criteria; Determining similar triangles
- [Angle bisector theorem](https://www.khanacademy.org/math/geometry/hs-geo-similarity/hs-geo-angle-bisector-theorem) — e.g. Intro to angle bisector theorem; Using the angle bisector theorem
- [Proving relationships using similarity](https://www.khanacademy.org/math/geometry/hs-geo-trig/hs-geo-pythagorean-proofs) — e.g. Pythagorean theorem proof using similarity; Exploring medial triangles; Proof: Parallel lines divide triangle sides proportionally

### Right triangles & trigonometry — 2 of 8 lessons not covered

- [Ratios in right triangles](https://www.khanacademy.org/math/geometry/hs-geo-trig/xff63fac4:hs-geo-trig-ratios-similarity) — e.g. Using similarity to estimate ratio between side lengths; Using right triangle ratios to approximate angle measure
- [Sine & cosine of complementary angles](https://www.khanacademy.org/math/geometry/hs-geo-trig/hs-geo-complementary-angles) — e.g. Sine & cosine of complementary angles; Using complementary angles; Trig word problem: complementary angles

### Analytic geometry — 3 of 5 lessons not covered

- [Dividing line segments](https://www.khanacademy.org/math/geometry/hs-geo-analytic-geometry/hs-geo-dividing-segments) — e.g. Dividing line segments: graphical; Dividing line segments; Proving triangle medians intersect at a point
- [Parallel & perpendicular lines on the coordinate plane](https://www.khanacademy.org/math/geometry/hs-geo-analytic-geometry/hs-geo-parallel-perpendicular-lines) — e.g. Parallel & perpendicular lines intro; Parallel & perpendicular lines from graph; Classifying quadrilaterals on the coordinate plane
- [Equations of parallel & perpendicular lines](https://www.khanacademy.org/math/geometry/hs-geo-analytic-geometry/hs-geo-parallel-perpendicular-eq) — e.g. Parallel lines from equation; Parallel lines from equation (example 2); Parallel lines from equation (example 3)

### Conic sections — 3 of 4 lessons not covered

- [Graphs of circles intro](https://www.khanacademy.org/math/geometry/xff63fac4:hs-geo-conic-sections/alg2-graphs-of-circles-intro) — e.g. Intro to conic sections; Graphing circles from features; Features of a circle from its graph
- [Expanded equation of a circle](https://www.khanacademy.org/math/geometry/xff63fac4:hs-geo-conic-sections/hs-geo-circle-expanded-equation) — e.g. Features of a circle from its expanded equation
- [Focus and directrix of a parabola](https://www.khanacademy.org/math/geometry/xff63fac4:hs-geo-conic-sections/xff63fac4:hs-geo-parabola) — e.g. Intro to focus & directrix; Equation of a parabola from focus & directrix

### Circles — 5 of 13 lessons not covered

- [Arc measure](https://www.khanacademy.org/math/geometry/hs-geo-circles/hs-geo-arc-measures) — e.g. Intro to arc measure; Finding arc measures; Finding arc measures with equations
- [Proofs with inscribed shapes](https://www.khanacademy.org/math/geometry/hs-geo-circles/xff63fac4:hs-geo-proofs-with-inscribed-shapes) — e.g. Proof: Right triangles inscribed in circles; Inscribed quadrilaterals proof; Proof: radius is perpendicular to a chord it bisects
- [Constructing regular polygons inscribed in circles](https://www.khanacademy.org/math/geometry/hs-geo-circles/hs-geo-inscribed-polygons) — e.g. Geometric constructions: circle-inscribed square; Geometric constructions: circle-inscribed equilateral triangle; Geometric constructions: circle-inscribed regular hexagon
- [Constructing circumcircles & incircles](https://www.khanacademy.org/math/geometry/hs-geo-circles/hs-geo-circum-in-circles) — e.g. Geometric constructions: triangle-inscribing circle; Geometric constructions: triangle-circumscribing circle
- [Constructing a line tangent to a circle](https://www.khanacademy.org/math/geometry/hs-geo-circles/hs-geo-constructing-tangents) — e.g. Geometric constructions: circle tangent; Geometric constructions: circle tangent (example 2)

### Solid geometry — 3 of 4 lessons not covered

- [2D vs. 3D objects](https://www.khanacademy.org/math/geometry/hs-geo-solids/hs-geo-2d-vs-3d) — e.g. Dilating in 3D; Slicing a rectangular pyramid; Ways to cross-section a cube
- [Cavalieri's principle and dissection methods](https://www.khanacademy.org/math/geometry/hs-geo-solids/xff63fac4:hs-geo-cavalieri-s-principle) — e.g. Cavalieri's principle in 3D; Volume of pyramids intuition; Volumes of cones intuition
- [Density](https://www.khanacademy.org/math/geometry/hs-geo-solids/hs-geo-density) — e.g. Area density; Volume density

## Algebra 2

### Polynomial arithmetic — 2 of 6 lessons not covered

- [Intro to polynomials](https://www.khanacademy.org/math/algebra/x2f8bb11595b61c86:quadratics-multiplying-factoring/x2f8bb11595b61c86:multiply-monomial-polynomial) — e.g. Polynomials intro; The parts of polynomial expressions
- [Multiplying binomials by polynomials](https://www.khanacademy.org/math/algebra2/x2ec2f6f830c9fb89:poly-arithmetic/x2ec2f6f830c9fb89:bi-by-poly) — e.g. Multiplying binomials by polynomials: area model; Multiplying binomials by polynomials

### Complex numbers — 4 of 6 lessons not covered

- [The imaginary unit i](https://www.khanacademy.org/math/algebra2/x2ec2f6f830c9fb89:complex/x2ec2f6f830c9fb89:imaginary) — e.g. Intro to the imaginary numbers; Simplifying roots of negative numbers; Powers of the imaginary unit
- [Complex numbers introduction](https://www.khanacademy.org/math/algebra2/x2ec2f6f830c9fb89:complex/x2ec2f6f830c9fb89:complex-num) — e.g. Intro to complex numbers; Classifying complex numbers
- [The complex plane](https://www.khanacademy.org/math/algebra2/x2ec2f6f830c9fb89:complex/x2ec2f6f830c9fb89:complex-plane) — e.g. Plotting numbers on the complex plane
- [Quadratic equations with complex solutions](https://www.khanacademy.org/math/algebra2/x2ec2f6f830c9fb89:complex/x2ec2f6f830c9fb89:complex-eq) — e.g. Solving quadratic equations: complex roots

### Polynomial factorization — 4 of 7 lessons not covered

- [Factoring monomials](https://www.khanacademy.org/math/algebra2/x2ec2f6f830c9fb89:poly-factor/x2ec2f6f830c9fb89:mono-factor) — e.g. Introduction to factoring higher degree polynomials; Introduction to factoring higher degree monomials; Which monomial factorization is correct?
- [Taking common factors](https://www.khanacademy.org/math/algebra2/x2ec2f6f830c9fb89:poly-factor/x2ec2f6f830c9fb89:common-factor) — e.g. Taking common factor from binomial; Taking common factor from trinomial; Taking common factor: area model
- [Factoring using structure](https://www.khanacademy.org/math/algebra2/x2ec2f6f830c9fb89:poly-factor/x2ec2f6f830c9fb89:factor-w-structure) — e.g. Identifying quadratic patterns; Factorization with substitution; Factoring using the perfect square pattern
- [Polynomial identities](https://www.khanacademy.org/math/algebra2/x2ec2f6f830c9fb89:poly-factor/x2ec2f6f830c9fb89:poly-identities) — e.g. Polynomial identities introduction; Analyzing polynomial identities; Describing numerical relationships with polynomial identities

### Polynomial division — 1 of 4 lessons not covered

- [Dividing polynomials by x](https://www.khanacademy.org/math/algebra2/x2ec2f6f830c9fb89:poly-div/x2ec2f6f830c9fb89:poly-div-by-x) — e.g. Polynomial division introduction; Dividing polynomials by x (no remainders); Divide polynomials by x (with remainders)

### Polynomial graphs — 1 of 3 lessons not covered

- [Positive and negative intervals of polynomials](https://www.khanacademy.org/math/algebra2/x2ec2f6f830c9fb89:poly-graphs/x2ec2f6f830c9fb89:poly-intervals) — e.g. Positive and negative intervals of polynomials; Multiplicity of zeros of polynomials; Zeros of polynomials (multiplicity)

### Rational exponents and radicals — 2 of 5 lessons not covered

- [Equivalent forms of exponential expressions](https://www.khanacademy.org/math/algebra2/x2ec2f6f830c9fb89:exp/x2ec2f6f830c9fb89:equivalent-exp) — e.g. Rewriting exponential expressions as A⋅Bᵗ; Equivalent forms of exponential expressions
- [Solving exponential equations using properties of exponents](https://www.khanacademy.org/math/algebra2/x2ec2f6f830c9fb89:exp/x2ec2f6f830c9fb89:exp-eq-prop) — e.g. Solving exponential equations using exponent properties; Solving exponential equations using exponent properties (advanced)

### Exponential models — 2 of 3 lessons not covered

- [Interpreting the rate of change of exponential models](https://www.khanacademy.org/math/algebra2/x2ec2f6f830c9fb89:exp-model/x2ec2f6f830c9fb89:exp-change) — e.g. Interpreting change in exponential models; Interpreting time in exponential models
- [Advanced interpretation of exponential models](https://www.khanacademy.org/math/algebra2/x2ec2f6f830c9fb89:exp-model/x2ec2f6f830c9fb89:interpret-exp) — e.g. Interpreting change in exponential models: with manipulation; Interpreting change in exponential models: changing units

### Logarithms — 1 of 6 lessons not covered

- [The constant e and the natural logarithm](https://www.khanacademy.org/math/algebra2/x2ec2f6f830c9fb89:logs/x2ec2f6f830c9fb89:e) — e.g. 𝑒 and compound interest; 𝑒 as a limit; Evaluating natural logarithm with calculator

### Transformations of functions — *entire unit not covered*

- [Shifting functions](https://www.khanacademy.org/math/algebra2/x2ec2f6f830c9fb89:transformations/x2ec2f6f830c9fb89:shift) — e.g. Shifting functions introduction; Shifting functions examples; Graphing shifted functions
- [Reflecting functions](https://www.khanacademy.org/math/algebra2/x2ec2f6f830c9fb89:transformations/x2ec2f6f830c9fb89:reflect) — e.g. Reflecting functions introduction; Reflecting functions: examples
- [Symmetry of functions](https://www.khanacademy.org/math/algebra2/x2ec2f6f830c9fb89:transformations/x2ec2f6f830c9fb89:symmetry) — e.g. Function symmetry introduction; Even and odd functions: Graphs; Even and odd functions: Tables
- [Scaling functions](https://www.khanacademy.org/math/algebra2/x2ec2f6f830c9fb89:transformations/x2ec2f6f830c9fb89:scale) — e.g. Scaling functions introduction; Scaling functions vertically: examples; Scaling functions horizontally: examples
- [Putting it all together](https://www.khanacademy.org/math/algebra2/x2ec2f6f830c9fb89:transformations/x2ec2f6f830c9fb89:trans-all-together) — e.g. Identifying function transformations
- [Graphs of square and cube root functions](https://www.khanacademy.org/math/algebra2/x2ec2f6f830c9fb89:transformations/x2ec2f6f830c9fb89:radical-graphs) — e.g. Graphing square and cube root functions
- [Graphs of exponential functions](https://www.khanacademy.org/math/algebra2/x2ec2f6f830c9fb89:transformations/x2ec2f6f830c9fb89:exp-graphs) — e.g. Transforming exponential graphs; Transforming exponential graphs (example 2); Graphing exponential functions
- [Graphs of logarithmic functions](https://www.khanacademy.org/math/algebra2/x2ec2f6f830c9fb89:transformations/x2ec2f6f830c9fb89:log-graphs) — e.g. Graphical relationship between 2ˣ and log₂(x); Graphing logarithmic functions (example 1); Graphing logarithmic functions (example 2)

### Equations — 3 of 6 lessons not covered

- [Cube-root equations](https://www.khanacademy.org/math/algebra2/x2ec2f6f830c9fb89:eq/x2ec2f6f830c9fb89:cbrt-eq) — e.g. Solving cube-root equations
- [Quadratic systems](https://www.khanacademy.org/math/algebra2/x2ec2f6f830c9fb89:eq/x2ec2f6f830c9fb89:quad-sys) — e.g. Quadratic systems: a line and a parabola; Quadratic systems: a line and a circle; Quadratic system with no solutions
- [Solving equations by graphing](https://www.khanacademy.org/math/algebra2/x2ec2f6f830c9fb89:eq/x2ec2f6f830c9fb89:sol-eq-graph) — e.g. Solving equations by graphing; Solving equations by graphing: intro; Solving equations by graphing: graphing calculator

### Trigonometry — 3 of 9 lessons not covered

- [Graphs of sin(x), cos(x), and tan(x)](https://www.khanacademy.org/math/algebra2/x2ec2f6f830c9fb89:trig/x2ec2f6f830c9fb89:trig-graphs) — e.g. Graph of y=sin(x); Intersection points of y=sin(x) and y=cos(x); Graph of y=tan(x)
- [Graphing sinusoidal functions](https://www.khanacademy.org/math/algebra2/x2ec2f6f830c9fb89:trig/x2ec2f6f830c9fb89:graphing-sinusoid) — e.g. Example: Graphing y=3⋅sin(½⋅x)-2; Example: Graphing y=-cos(π⋅x)+1.5; Sinusoidal function from graph
- [Sinusoidal models](https://www.khanacademy.org/math/algebra2/x2ec2f6f830c9fb89:trig/x2ec2f6f830c9fb89:sinusoidal-models) — e.g. Interpreting trigonometric graphs in context; Trig word problem: modeling daily temperature; Trig word problem: modeling annual temperature

### Modeling — 4 of 5 lessons not covered

- [Modeling with function combination](https://www.khanacademy.org/math/algebra2/x2ec2f6f830c9fb89:modeling/x2ec2f6f830c9fb89:model-comb) — e.g. Modeling with function combination
- [Interpreting features of functions](https://www.khanacademy.org/math/algebra2/x2ec2f6f830c9fb89:modeling/x2ec2f6f830c9fb89:interpreting-features) — e.g. Periodicity of algebraic models; End behavior of algebraic models; Symmetry of algebraic models
- [Modeling with two variables](https://www.khanacademy.org/math/algebra2/x2ec2f6f830c9fb89:modeling/x2ec2f6f830c9fb89:eq-ineq-models) — e.g. Graph labels and scales; Rational equation word problem; Quadratic inequality word problem
- [Modeling with multiple variables](https://www.khanacademy.org/math/algebra2/x2ec2f6f830c9fb89:modeling/x2ec2f6f830c9fb89:modeling-with-multiple-variables) — e.g. Modeling with multiple variables: Pancakes; Modeling with multiple variables: Roller coaster; Modeling with multiple variables: Taco stand

## Integrated math 1

### Scatterplots — 1 of 2 lessons not covered

- [Creating and interpreting scatterplots](https://www.khanacademy.org/math/cc-eighth-grade-math/cc-8th-data/cc-8th-scatter-plots) — e.g. Constructing a scatter plot; Example of direction in scatterplots; Example: Correlation coefficient intuition

### Data distributions — 2 of 4 lessons not covered

- [Displays of distributions](https://www.khanacademy.org/math/cc-sixth-grade-math/cc-6th-data-statistics/dot-plot) — e.g. Frequency tables & dot plots; Creating a histogram; Interpreting a histogram
- [Comparing distributions](https://www.khanacademy.org/math/cc-seventh-grade-math/cc-7th-probability-statistics/cc-7th-population-sampling) — e.g. Comparing distributions with dot plots (example problem)

### Congruence — 6 of 8 lessons not covered

- [Proofs of general theorems that use triangle congruence](https://www.khanacademy.org/math/geometry/hs-geo-congruence/hs-geo-triangle-theorems) — e.g. Geometry proof problem: midpoint; Geometry proof problem: congruent segments; Geometry proof problem: squared circle

## Integrated math 2

### Irrational numbers — *entire unit not covered*

- [Sums & products of rational/irrational numbers](https://www.khanacademy.org/math/algebra/x2f8bb11595b61c86:irrational-numbers/x2f8bb11595b61c86:sums-and-products-of-rational-and-irrational-numbers) — e.g. Proof: sum & product of two rationals is rational; Proof: product of rational & irrational is irrational; Proof: sum of rational & irrational is irrational

### Conic sections — 3 of 5 lessons not covered

- [Introduction to conic sections](https://www.khanacademy.org/math/geometry/xff63fac4:hs-geo-conic-sections/alg2-graphs-of-circles-intro) — e.g. Intro to conic sections
- [Focus & directrix of a parabola](https://www.khanacademy.org/math/geometry/xff63fac4:hs-geo-conic-sections/xff63fac4:hs-geo-parabola) — e.g. Intro to focus & directrix; Equation of a parabola from focus & directrix; Focus & directrix of a parabola from equation

### Probability — 1 of 6 lessons not covered

- [Addition rule for probability](https://www.khanacademy.org/math/precalculus/x9e81a4f98389efdf:prob-comb/x9e81a4f98389efdf:addition-rule-prob-precalc) — e.g. Probability with Venn diagrams; Addition rule for probability

## Integrated math 3

### Study Design — *entire unit not covered*

- [Samples and surveys](https://www.khanacademy.org/math/cc-seventh-grade-math/cc-7th-probability-statistics/cc-7th-population-sampling) — e.g. Reasonable samples
- [Observational studies and experiments](https://www.khanacademy.org/math/math3/x5549cc1686316ba5:study-design/x5549cc1686316ba5:observations) — e.g. Types of statistical studies; Correlation and causality; Appropriate statistical study example

### Rational functions — 4 of 9 lessons not covered

- [Modeling with rational functions](https://www.khanacademy.org/math/precalculus/x9e81a4f98389efdf:rational-functions/x9e81a4f98389efdf:modeling-with-rational-functions) — e.g. Analyzing structure word problem: pet store (1 of 2); Analyzing structure word problem: pet store (2 of 2); Rational equations word problem: combined rates
- [Adding subtracting rational expressions intro](https://www.khanacademy.org/math/precalculus/x9e81a4f98389efdf:rational-functions/x9e81a4f98389efdf:adding-and-subtracting-rational-expressions) — e.g. Adding & subtracting rational expressions: like denominators; Intro to adding rational expressions with unlike denominators; Adding rational expression: unlike denominators
- [Adding subtracting rational expressions (factored)](https://www.khanacademy.org/math/precalculus/x9e81a4f98389efdf:rational-functions/x9e81a4f98389efdf:adding-and-subtracting-rational-expressions) — e.g. Subtracting rational expressions: factored denominators; Least common multiple of polynomials
- [Adding subtracting rational expressions (not factored)](https://www.khanacademy.org/math/precalculus/x9e81a4f98389efdf:rational-functions/x9e81a4f98389efdf:adding-and-subtracting-rational-expressions) — e.g. Subtracting rational expressions

## Trigonometry

### Right triangles & trigonometry — 3 of 6 lessons not covered

- [Sine and cosine of complementary angles](https://www.khanacademy.org/math/trigonometry/trigonometry-right-triangles/sine-and-cosine-of-complementary-angles) — e.g. Intro to the Pythagorean trig identity; Sine & cosine of complementary angles; Using complementary angles
- [The reciprocal trigonometric ratios](https://www.khanacademy.org/math/trigonometry/trigonometry-right-triangles/reciprocal-trig-ratios) — e.g. Finding reciprocal trig ratios; Using reciprocal trig ratios

### Trigonometric functions — 4 of 11 lessons not covered

- [Long live Tau](https://www.khanacademy.org/math/trigonometry/unit-circle-trig-func/long-live-tau) — e.g. Tau versus pi; Pi is (still) wrong

### Trigonometric equations and identities — 2 of 6 lessons not covered

- [Challenging trigonometry problems](https://www.khanacademy.org/math/trigonometry/trig-equations-and-identities/challenge-trig-problems) — e.g. Trig challenge problem: area of a triangle; Trig challenge problem: area of a hexagon; Trig challenge problem: cosine of angle-sum

## Precalculus

### Composite and inverse functions — 4 of 5 lessons not covered

- [Modeling with composite functions](https://www.khanacademy.org/math/precalculus/x9e81a4f98389efdf:composite/x9e81a4f98389efdf:composite-modeling) — e.g. Modeling with composite functions; Modeling with composite functions: skydiving; Meaningfully composing functions
- [Invertible functions](https://www.khanacademy.org/math/precalculus/x9e81a4f98389efdf:composite/x9e81a4f98389efdf:invertible) — e.g. Determining if a function is invertible; Restricting domains of functions to make them invertible
- [Inverse functions in graphs and tables](https://www.khanacademy.org/math/precalculus/x9e81a4f98389efdf:composite/x9e81a4f98389efdf:inverse-functions-in-graphs-and-tables) — e.g. Reading inverse values from a graph; Reading inverse values from a table
- [Verifying inverse functions by composition](https://www.khanacademy.org/math/precalculus/x9e81a4f98389efdf:composite/x9e81a4f98389efdf:verifying-inverse) — e.g. Verifying inverse functions from tables; Using specific values to test for inverses; Verifying inverse functions by composition

### Complex numbers — 5 of 9 lessons not covered

- [Distance and midpoint of complex numbers](https://www.khanacademy.org/math/precalculus/x9e81a4f98389efdf:complex/x9e81a4f98389efdf:complex-distance-midpoint) — e.g. Distance & midpoint of complex numbers
- [Identities with complex numbers](https://www.khanacademy.org/math/precalculus/x9e81a4f98389efdf:complex/x9e81a4f98389efdf:complex-id) — e.g. Complex numbers & sum of squares factorization; Factoring sum of squares; Factoring polynomials using complex numbers
- [Graphically multiplying complex numbers](https://www.khanacademy.org/math/precalculus/x9e81a4f98389efdf:complex/x9e81a4f98389efdf:complex-mul) — e.g. Multiplying complex numbers graphically example: -3i; Multiplying complex numbers graphically example: -1-i
- [The fundamental theorem of algebra](https://www.khanacademy.org/math/precalculus/x9e81a4f98389efdf:complex/x9e81a4f98389efdf:fta) — e.g. The Fundamental theorem of Algebra; Quadratics & the Fundamental Theorem of Algebra ; Number of possible real roots of a polynomial

### Rational functions — 2 of 7 lessons not covered

- [Adding and subtracting rational expressions](https://www.khanacademy.org/math/precalculus/x9e81a4f98389efdf:rational-functions/x9e81a4f98389efdf:adding-and-subtracting-rational-expressions) — e.g. Adding & subtracting rational expressions: like denominators; Intro to adding rational expressions with unlike denominators; Adding rational expression: unlike denominators

### Conic sections — 4 of 6 lessons not covered

- [Foci of an ellipse](https://www.khanacademy.org/math/precalculus/x9e81a4f98389efdf:conics/x9e81a4f98389efdf:ellipse-foci) — e.g. Foci of an ellipse from equation
- [Foci of a hyperbola](https://www.khanacademy.org/math/precalculus/x9e81a4f98389efdf:conics/x9e81a4f98389efdf:hyperb-foci) — e.g. Foci of a hyperbola from equation; Proof of the hyperbola foci formula
- [Hyperbolas not centered at the origin](https://www.khanacademy.org/math/precalculus/x9e81a4f98389efdf:conics/x9e81a4f98389efdf:non-origin-hyperb) — e.g. Equation of a hyperbola not centered at the origin

### Vectors — 6 of 9 lessons not covered

- [Vectors introduction](https://www.khanacademy.org/math/precalculus/x9e81a4f98389efdf:vectors/x9e81a4f98389efdf:vectors-intro) — e.g. Intro to vectors and scalars; Representing quantities with vectors; Interpreting statements about vectors
- [Vector components](https://www.khanacademy.org/math/precalculus/x9e81a4f98389efdf:vectors/x9e81a4f98389efdf:vector-components) — e.g. Introduction to vector components; Finding the components of a vector; Comparing the components of vectors
- [Direction of vectors](https://www.khanacademy.org/math/precalculus/x9e81a4f98389efdf:vectors/x9e81a4f98389efdf:magnitude-direction) — e.g. Direction of vectors from components: 1st & 2nd quadrants; Direction of vectors from components: 3rd & 4th quadrants
- [Vector components from magnitude and direction](https://www.khanacademy.org/math/precalculus/x9e81a4f98389efdf:vectors/x9e81a4f98389efdf:component-form) — e.g. Vector components from magnitude & direction; Vector components from magnitude & direction: word problem
- [Adding vectors in magnitude and direction form](https://www.khanacademy.org/math/precalculus/x9e81a4f98389efdf:vectors/x9e81a4f98389efdf:vec-add-mag-dir) — e.g. Adding vectors in magnitude and direction form
- [Vectors word problems](https://www.khanacademy.org/math/precalculus/x9e81a4f98389efdf:vectors/x9e81a4f98389efdf:vec-models) — e.g. Vector word problem: resultant velocity; Vector word problem: hiking; Vector word problem: resultant force

### Matrices — 11 of 14 lessons not covered

- [Introduction to matrices](https://www.khanacademy.org/math/precalculus/x9e81a4f98389efdf:matrices/x9e81a4f98389efdf:mat-intro) — e.g. Intro to matrices
- [Using matrices to represent data](https://www.khanacademy.org/math/precalculus/x9e81a4f98389efdf:matrices/x9e81a4f98389efdf:model-situations-with-matrices) — e.g. Using matrices to represent data: Networks; Using matrices to represent data: Payoffs
- [Multiplying matrices by scalars](https://www.khanacademy.org/math/precalculus/x9e81a4f98389efdf:matrices/x9e81a4f98389efdf:multiplying-matrices-by-scalars) — e.g. Multiplying matrices by scalars
- [Using matrices to manipulate data](https://www.khanacademy.org/math/precalculus/x9e81a4f98389efdf:matrices/x9e81a4f98389efdf:using-matrices-to-manipulate-data) — e.g. Using matrices to manipulate data: Pet store; Using matrices to manipulate data: Game show
- [Matrices as transformations of the plane](https://www.khanacademy.org/math/precalculus/x9e81a4f98389efdf:matrices/x9e81a4f98389efdf:matrices-as-transformations) — e.g. Matrices as transformations of the plane; Working with matrices as transformations of the plane; Intro to determinant notation and computation
- [Using matrices to transform the plane](https://www.khanacademy.org/math/precalculus/x9e81a4f98389efdf:matrices/x9e81a4f98389efdf:using-matrices-to-transform-the-plane) — e.g. Using matrices to transform the plane: Mapping a vector; Using matrices to transform the plane: Composing matrices
- [Transforming 3D and 4D vectors with matrices](https://www.khanacademy.org/math/precalculus/x9e81a4f98389efdf:matrices/x9e81a4f98389efdf:transforming-3d-and-4d-vectors-with-matrices) — e.g. Using matrices to transform a 4D vector; Composing 3x3 matrices
- [Properties of matrix multiplication](https://www.khanacademy.org/math/precalculus/x9e81a4f98389efdf:matrices/x9e81a4f98389efdf:properties-of-matrix-multiplication) — e.g. Defined matrix operations; Intro to identity matrix; Dimensions of identity matrix
- [Representing systems of equations with matrices](https://www.khanacademy.org/math/precalculus/x9e81a4f98389efdf:matrices/x9e81a4f98389efdf:representing-systems-with-matrices) — e.g. Representing systems of equations with matrices; Representing systems of any number of equations with matrices
- [Introduction to matrix inverses](https://www.khanacademy.org/math/precalculus/x9e81a4f98389efdf:matrices/x9e81a4f98389efdf:intro-to-matrix-inverses) — e.g. Inverse matrix introduction; Invertible matrices and determinants; Invertible matrices and transformations
- [Finding inverses of 2x2 matrices](https://www.khanacademy.org/math/precalculus/x9e81a4f98389efdf:matrices/x9e81a4f98389efdf:practice-finding-inverses-of-2x2-matrices) — e.g. Finding inverses of 2x2 matrices

### Probability and combinatorics — 4 of 9 lessons not covered

- [Venn diagrams and the addition rule](https://www.khanacademy.org/math/precalculus/x9e81a4f98389efdf:prob-comb/x9e81a4f98389efdf:addition-rule-prob-precalc) — e.g. Probability with Venn diagrams; Addition rule for probability
- [Probability distributions introduction](https://www.khanacademy.org/math/precalculus/x9e81a4f98389efdf:prob-comb/x9e81a4f98389efdf:probability-distributions-introduction) — e.g. Constructing a probability distribution for random variable; Valid discrete probability distribution examples; Probability with discrete random variable example
- [Theoretical & empirical probability distributions](https://www.khanacademy.org/math/precalculus/x9e81a4f98389efdf:prob-comb/x9e81a4f98389efdf:theoretical-empirical-probability-distributions) — e.g. Theoretical probability distribution example: tables; Theoretical probability distribution example: multiplication; Probability distributions from empirical data
- [Decisions with probability](https://www.khanacademy.org/math/precalculus/x9e81a4f98389efdf:prob-comb/x9e81a4f98389efdf:decisions-with-probability) — e.g. Using probabilities to make fair decisions example

### Limits and continuity — 12 of 15 lessons not covered

- [Defining limits and using limit notation](https://www.khanacademy.org/math/ap-calculus-ab/ab-limits-new/ab-1-2) — e.g. Introducing limits
- [Estimating limit values from graphs](https://www.khanacademy.org/math/ap-calculus-ab/ab-limits-new/ab-1-3) — e.g. Estimating limit values from graphs; Examining unbounded limits; Estimating one-sided limits from graphs
- [Estimating limit values from tables](https://www.khanacademy.org/math/ap-calculus-ab/ab-limits-new/ab-1-4) — e.g. Approximating limits using tables; Estimating limits from tables; Estimating one-sided limits from tables
- [Determining limits using algebraic properties of limits: limit properties](https://www.khanacademy.org/math/ap-calculus-ab/ab-limits-new/ab-1-5a) — e.g. Introducing properties of limits; Determining limits of combined functions; Determining limits of combined functions: piecewise functions
- [Determining limits using algebraic properties of limits: direct substitution](https://www.khanacademy.org/math/ap-calculus-ab/ab-limits-new/ab-1-5b) — e.g. Finding limits by direct substitution; Examining undefined limits by direct substitution; Determining limits of trigonometric functions
- [Determining limits using the squeeze theorem](https://www.khanacademy.org/math/ap-calculus-ab/ab-limits-new/ab-1-8) — e.g. Introducing the squeeze theorem; Determining the limit of sin(x)/x as x approaches 0; Determining the limit of (1-cos(x))/x as x approaches 0
- [Exploring types of discontinuities](https://www.khanacademy.org/math/ap-calculus-ab/ab-limits-new/ab-1-10) — e.g. Exploring types of discontinuities
- [Defining continuity at a point](https://www.khanacademy.org/math/ap-calculus-ab/ab-limits-new/ab-1-11) — e.g. Exploring continuity at a point; Working an example: Continuity at a point (graphical); Working an example: point where a function is continuous
- [Confirming continuity over an interval](https://www.khanacademy.org/math/ap-calculus-ab/ab-limits-new/ab-1-12) — e.g. Exploring continuity over an interval; Determining if functions are continuous on all real numbers; Determining if functions are continuous at specific x-values
- [Removing discontinuities](https://www.khanacademy.org/math/ap-calculus-ab/ab-limits-new/ab-1-13) — e.g. Removing discontinuities (factoring); Removing discontinuities (rationalization)
- [Connecting infinite limits and vertical asymptotes](https://www.khanacademy.org/math/ap-calculus-ab/ab-limits-new/ab-1-14) — e.g. Introducing infinite limits; Exploring infinite limits and asymptotes; Analyzing unbounded limits: rational function
- [Working with the intermediate value theorem](https://www.khanacademy.org/math/ap-calculus-ab/ab-limits-new/ab-1-16) — e.g. Discovering the intermediate value theorem; Working an example: using the intermediate value theorem; Applying the intermediate value theorem: table

## Statistics essentials

### Displaying a single quantitative variable — 2 of 5 lessons not covered

- [Frequency tables and dot plots](https://www.khanacademy.org/math/cc-sixth-grade-math/cc-6th-data-statistics/dot-plot) — e.g. Frequency tables & dot plots

### Scatterplots — *entire unit not covered*

- [Fitting trend lines to scatterplots](https://www.khanacademy.org/math/ap-statistics/xfb5d8e68:regression-analysis/xfb5d8e68:graphical-representations-between-two-quantitative-variables) — e.g. Bivariate relationship linearity, strength and direction; Estimating the line of best fit exercise; Line of best fit: smoking in 1945
- [Analyzing trend lines in scatterplots](https://www.khanacademy.org/math/ap-statistics/xfb5d8e68:regression-analysis/xfb5d8e68:least-squares-reg) — e.g. Interpreting slope of regression line; Interpreting y-intercept in regression model; Example: Correlation coefficient intuition
- [Residuals](https://www.khanacademy.org/math/probability/xa88397b6:scatterplots/xa88397b6:residuals) — e.g. Introduction to residuals and least-squares regression; Calculating residual example; Residual plots

### Study design — *entire unit not covered*

- [Introduction to planning a study](https://www.khanacademy.org/math/ap-statistics/xfb5d8e68:exploring-one-variable-data-and-collecting-data/xfb5d8e68:introducing-statistics-what-can-we-learn-from-data) — e.g. Identifying a sample and population; Generalizability of survey results example; Types of studies
- [Potential problems with sampling](https://www.khanacademy.org/math/ap-statistics/xfb5d8e68:exploring-one-variable-data-and-collecting-data/xfb5d8e68:potential-problems-with-sampling) — e.g. Examples of bias in surveys; Example of undercoverage introducing bias
- [Sampling methods](https://www.khanacademy.org/math/ap-statistics/xfb5d8e68:exploring-one-variable-data-and-collecting-data/xfb5d8e68:random-sampling) — e.g. Techniques for generating a simple random sample; Techniques for random sampling and avoiding bias; Systematic random sampling
- [Introduction to experimental design](https://www.khanacademy.org/math/probability/xa88397b6:study-design/observational-studies-experiments) — e.g. Introduction to experiment design; Matched pairs experiment design; Correlation and causality
- [Inference and experiments](https://www.khanacademy.org/math/probability/xa88397b6:study-design/xa88397b6:inference-experiments) — e.g. Statistical significance of experiment; Can causality be established from this study?

### Probability — 2 of 7 lessons not covered

- [Probability from simulations](https://www.khanacademy.org/math/ap-statistics/xfb5d8e68:probability-random-variables-and-probability-distributions/xfb5d8e68:estimating-probabilities-using-simulation) — e.g. Experimental versus theoretical probability simulation; Random number list to run experiment; Random numbers for experimental probability

## AP®︎/College Statistics

### Exploring one-variable data and collecting data — 10 of 13 lessons not covered

- [Introducing statistics: what can we learn from data?](https://www.khanacademy.org/math/ap-statistics/xfb5d8e68:exploring-one-variable-data-and-collecting-data/xfb5d8e68:introducing-statistics-what-can-we-learn-from-data) — e.g. Identifying a sample and population; Statistical questions; Statistical and non statistical questions
- [Variables](https://www.khanacademy.org/math/ap-statistics/xfb5d8e68:exploring-one-variable-data-and-collecting-data/xfb5d8e68:variables) — e.g. Identifying individuals, variables and categorical variables in a data set; Classifying discrete and continuous variables
- [Graphical representations for one categorical variable](https://www.khanacademy.org/math/cc-2nd-grade-math/x3184e0ec:data/cc-2nd-bar-graphs) — e.g. Creating a bar graph; Reading bar graphs: movies; Reading bar charts: comparing two sets of data
- [Graphical representations for one quantitative variable](https://www.khanacademy.org/math/cc-sixth-grade-math/cc-6th-data-statistics/histograms) — e.g. Creating a histogram; Interpreting a histogram; Stem-and-leaf plots
- [Descriptions for one quantitative variable distributions](https://www.khanacademy.org/math/ap-statistics/xfb5d8e68:exploring-one-variable-data-and-collecting-data/xfb5d8e68:descriptions-for-one-quantitative-variable-distributions) — e.g. Classifying shapes of distributions; Clusters, gaps, peaks & outliers; Example: Describing a distribution
- [Comparisons of the distributions for one quantitative variable](https://www.khanacademy.org/math/ap-statistics/xfb5d8e68:exploring-one-variable-data-and-collecting-data/xfb5d8e68:comparisons-of-the-distributions-for-one-quantitative-variable) — e.g. Example: Comparing distributions; Comparing distributions using summary statistics; Z-score introduction
- [The investigative question revisited and data collection](https://www.khanacademy.org/math/ap-statistics/xfb5d8e68:exploring-one-variable-data-and-collecting-data/xfb5d8e68:the-investigative-question-revisited-and-data-collection) — e.g. Identifying a census; Types of studies; Worked example identifying experiment
- [Random sampling](https://www.khanacademy.org/math/ap-statistics/xfb5d8e68:exploring-one-variable-data-and-collecting-data/xfb5d8e68:random-sampling) — e.g. Sampling with and without replacement; Techniques for generating a simple random sample; Techniques for random sampling and avoiding bias
- [Experimental design](https://www.khanacademy.org/math/ap-statistics/xfb5d8e68:exploring-one-variable-data-and-collecting-data/xfb5d8e68:experimental-design) — e.g. Introduction to experiment design; Matched pairs experiment design

### Probability, random variables, and probability distributions — 3 of 12 lessons not covered

- [Estimating probabilities using simulation](https://www.khanacademy.org/math/cc-seventh-grade-math/cc-7th-probability-statistics/cc-7th-basic-prob) — e.g. Intro to theoretical probability; Experimental versus theoretical probability simulation; Random number list to run experiment
- [Mutually exclusive events](https://www.khanacademy.org/math/precalculus/x9e81a4f98389efdf:prob-comb/x9e81a4f98389efdf:addition-rule-prob-precalc) — e.g. Probability with Venn diagrams; Addition rule for probability
- [Introduction to random variables and probability distributions](https://www.khanacademy.org/math/precalculus/x9e81a4f98389efdf:prob-comb/x9e81a4f98389efdf:probability-distributions-introduction) — e.g. Constructing a probability distribution for random variable; Valid discrete probability distribution examples; Probability with discrete random variable example

### Inference for categorical data: proportions — 10 of 12 lessons not covered

- [Estimators](https://www.khanacademy.org/math/ap-statistics/xfb5d8e68:inference-for-categorical-data-proportions/xfb5d8e68:estimators) — e.g. Identifying statistics and parameters; Sample statistic bias worked example
- [Sampling distributions for sample proportions](https://www.khanacademy.org/math/ap-statistics/xfb5d8e68:inference-for-categorical-data-proportions/xfb5d8e68:sampling-distributions-for-sample-proportions) — e.g. Sampling distribution of sample proportion part 1; Sampling distribution of sample proportion part 2; Normal conditions for sampling distributions of sample proportions
- [Setting up a test for a population proportion](https://www.khanacademy.org/math/ap-statistics/xfb5d8e68:inference-for-categorical-data-proportions/xfb5d8e68:setting-up-a-test-for-a-population-proportion) — e.g. Idea behind hypothesis testing; Examples of null and alternative hypotheses; Constructing hypotheses for a significance test about a proportion
- [P-values](https://www.khanacademy.org/math/ap-statistics/xfb5d8e68:inference-for-categorical-data-proportions/xfb5d8e68:p-values) — e.g. P-values and significance tests; Comparing P-values to different significance levels; Estimating a P-value from a simulation
- [Potential errors when performing tests](https://www.khanacademy.org/math/ap-statistics/xfb5d8e68:inference-for-categorical-data-proportions/xfb5d8e68:potential-errors-when-performing-tests) — e.g. Introduction to Type I and Type II errors; Examples identifying Type I and Type II errors; Introduction to power in significance tests
- [Sampling distributions for the difference between sample proportions](https://www.khanacademy.org/math/ap-statistics/xfb5d8e68:inference-for-categorical-data-proportions/xfb5d8e68:sampling-distributions-for-the-difference-between-sample-proportions) — e.g. Sampling distribution of the difference in sample proportions; Sampling distribution of the difference in sample proportions: Probability example
- [Constructing a confidence interval for the difference between two population proportions](https://www.khanacademy.org/math/ap-statistics/xfb5d8e68:inference-for-categorical-data-proportions/xfb5d8e68:constructing-a-confidence-interval-for-the-difference-between-two-population-proportions) — e.g. Confidence intervals for the difference between two proportions; Examples identifying conditions for inference on two proportions; Calculating a confidence interval for the difference of proportions
- [Setting up a test for the difference between two population proportions](https://www.khanacademy.org/math/ap-statistics/xfb5d8e68:inference-for-categorical-data-proportions/xfb5d8e68:setting-up-a-test-for-the-difference-between-two-population-proportions) — e.g. Hypothesis test for difference in proportions; Constructing hypotheses for two proportions
- [Carrying out a test for the difference between two population proportions](https://www.khanacademy.org/math/ap-statistics/xfb5d8e68:inference-for-categorical-data-proportions/xfb5d8e68:carrying-out-a-test-for-the-difference-between-two-population-proportions) — e.g. Hypothesis test for difference in proportions example; Comparing P value to significance level for test involving difference of proportions
- [Setting up a chi-square test for homogeneity or independence](https://www.khanacademy.org/math/ap-statistics/xfb5d8e68:inference-for-categorical-data-proportions/xfb5d8e68:setting-up-a-chi-square-test-for-homogeneity-or-independence) — e.g. Introduction to the chi-square test for homogeneity; Chi-square test for association (independence)

### Inference for quantitative data: means — 5 of 8 lessons not covered

- [Setting up a test for a population mean or population mean difference](https://www.khanacademy.org/math/ap-statistics/xfb5d8e68:inference-for-quantitative-data-means/xfb5d8e68:setting-up-a-test-for-a-population-mean-or-population-mean-difference) — e.g. Writing hypotheses for a significance test about a mean; Conditions for a t test about a mean
- [Sampling distributions for the difference between two sample means](https://www.khanacademy.org/math/ap-statistics/xfb5d8e68:inference-for-quantitative-data-means/xfb5d8e68:sampling-distributions-for-the-difference-between-two-sample-means) — e.g. Sampling distribution of the difference in sample means; Sampling distribution of the difference in sample means: Probability example
- [Constructing a confidence interval for the difference between two population means](https://www.khanacademy.org/math/ap-statistics/xfb5d8e68:inference-for-quantitative-data-means/xfb5d8e68:constructing-a-confidence-interval-for-the-difference-between-two-population-means) — e.g. Conditions for inference for difference of means; Constructing t interval for difference of means; Calculating confidence interval for difference of means
- [Setting up a test for the difference between two populations means](https://www.khanacademy.org/math/ap-statistics/xfb5d8e68:inference-for-quantitative-data-means/xfb5d8e68:setting-up-a-test-for-the-difference-between-two-populations-means) — e.g. Hypotheses for a two-sample t test; Example of hypotheses for paired and two-sample t tests
- [Carrying out a test for the difference between two population means](https://www.khanacademy.org/math/ap-statistics/xfb5d8e68:inference-for-quantitative-data-means/xfb5d8e68:carrying-out-a-test-for-the-difference-between-two-population-means) — e.g. Two-sample t test for difference of means; Conclusion for a two-sample t test using a P-value

### Regression analysis — 2 of 4 lessons not covered

- [Graphical representations between two quantitative variables](https://www.khanacademy.org/math/cc-eighth-grade-math/cc-8th-data/cc-8th-scatter-plots) — e.g. Constructing a scatter plot; Example of direction in scatterplots; Bivariate relationship linearity, strength and direction

### Exploring categorical data — 2 of 4 lessons not covered

- [The language of variation: Variables](https://www.khanacademy.org/math/ap-statistics/xfb5d8e68:exploring-one-variable-data-and-collecting-data/xfb5d8e68:variables) — e.g. Identifying individuals, variables and categorical variables in a data set
- [Representing a categorical variable with graphs](https://www.khanacademy.org/math/cc-2nd-grade-math/x3184e0ec:data/cc-2nd-bar-graphs) — e.g. Creating a bar graph; Reading bar graphs: movies; Reading bar charts: comparing two sets of data

### Exploring one-variable quantitative data: Displaying and describing — *entire unit not covered*

- [Representing a quantitative variable with dot plots](https://www.khanacademy.org/math/cc-sixth-grade-math/cc-6th-data-statistics/dot-plot) — e.g. Frequency tables & dot plots
- [Representing a quantitative variable with histograms and stem plots](https://www.khanacademy.org/math/cc-sixth-grade-math/cc-6th-data-statistics/histograms) — e.g. Creating a histogram; Interpreting a histogram; Stem-and-leaf plots
- [Describing the distribution of a quantitative variable](https://www.khanacademy.org/math/ap-statistics/xfb5d8e68:exploring-one-variable-data-and-collecting-data/xfb5d8e68:descriptions-for-one-quantitative-variable-distributions) — e.g. Classifying shapes of distributions; Clusters, gaps, peaks & outliers; Example: Describing a distribution
- [Comparing distributions of a quantitative variable](https://www.khanacademy.org/math/ap-statistics/xfb5d8e68:exploring-one-variable-data-and-collecting-data/xfb5d8e68:comparisons-of-the-distributions-for-one-quantitative-variable) — e.g. Example: Comparing distributions

### Exploring one-variable quantitative data: Summary statistics — 3 of 6 lessons not covered

- [More on mean and median](https://www.khanacademy.org/math/cc-sixth-grade-math/cc-6th-data-statistics/cc-6th-mean-median-challenge) — e.g. Missing value given the mean; Impact on median & mean: increasing an outlier; Impact on median & mean: removing an outlier
- [Effects of linear transformations](https://www.khanacademy.org/math/statistics-probability/modeling-distributions-of-data/effects-of-linear-transformations) — e.g. How parameters change as data is shifted and scaled
- [More on standard deviation (optional)](https://www.khanacademy.org/math/statistics-probability/summarizing-quantitative-data/more-on-standard-deviation) — e.g. Review and intuition why we divide by n-1 for the unbiased sample variance; Why we divide by n - 1 in variance ; Simulation showing bias in sample variance

### Exploring one-variable quantitative data: Percentiles, z-scores, and the normal distribution — 1 of 5 lessons not covered

- [Density curves](https://www.khanacademy.org/math/statistics-probability/modeling-distributions-of-data/density-curve) — e.g. Density Curves; Median, mean and skew from density curves

### Exploring two-variable quantitative data — 3 of 5 lessons not covered

- [Representing the relationship between two quantitative variables](https://www.khanacademy.org/math/cc-eighth-grade-math/cc-8th-data/cc-8th-scatter-plots) — e.g. Constructing a scatter plot; Example of direction in scatterplots; Bivariate relationship linearity, strength and direction
- [Analyzing departures from linearity](https://www.khanacademy.org/math/statistics-probability/describing-relationships-quantitative-data/assessing-the-fit-in-least-squares-regression) — e.g. R-squared or coefficient of determination; Standard deviation of residuals or root mean square deviation (RMSD); Interpreting computer regression data

### Collecting data — *entire unit not covered*

- [Random sampling and data collection](https://www.khanacademy.org/math/ap-statistics/xfb5d8e68:exploring-one-variable-data-and-collecting-data/xfb5d8e68:random-sampling) — e.g. Techniques for generating a simple random sample; Techniques for random sampling and avoiding bias; Systematic random sampling

### Probability — 2 of 4 lessons not covered

- [Mutually exclusive events and unions of events](https://www.khanacademy.org/math/precalculus/x9e81a4f98389efdf:prob-comb/x9e81a4f98389efdf:addition-rule-prob-precalc) — e.g. Probability with Venn diagrams; Addition rule for probability

### Random variables and probability distributions — 5 of 7 lessons not covered

- [Transforming random variables](https://www.khanacademy.org/math/statistics-probability/random-variables-stats-library/transforming-random-variable) — e.g. Impact of transforming (scaling and shifting) random variables; Example: Transforming a discrete random variable
- [Combining random variables](https://www.khanacademy.org/math/statistics-probability/random-variables-stats-library/combine-random-variables) — e.g. Mean of sum and difference of random variables; Variance of sum and difference of random variables; Intuition for why independence matters for variance of sum
- [Parameters for a binomial distribution](https://www.khanacademy.org/math/ap-statistics/xfb5d8e68:probability-random-variables-and-probability-distributions/xfb5d8e68:the-binomial-distribution) — e.g. Expected value of a binomial variable; Variance of a binomial variable; Finding the mean and standard deviation of a binomial random variable
- [The geometric distribution](https://www.khanacademy.org/math/statistics-probability/random-variables-stats-library/random-variables-geometric) — e.g. Geometric random variables introduction; Geometric distribution mean and standard deviation; Probability for a geometric random variable

### Sampling distributions — 4 of 7 lessons not covered

- [Biased and unbiased point estimates](https://www.khanacademy.org/math/ap-statistics/xfb5d8e68:inference-for-categorical-data-proportions/xfb5d8e68:estimators) — e.g. Sample statistic bias worked example
- [Sampling distributions for differences in sample proportions](https://www.khanacademy.org/math/ap-statistics/xfb5d8e68:inference-for-categorical-data-proportions/xfb5d8e68:sampling-distributions-for-the-difference-between-sample-proportions) — e.g. Sampling distribution of the difference in sample proportions; Sampling distribution of the difference in sample proportions: Probability example
- [Sampling distributions for differences in sample means](https://www.khanacademy.org/math/ap-statistics/xfb5d8e68:inference-for-quantitative-data-means/xfb5d8e68:sampling-distributions-for-the-difference-between-two-sample-means) — e.g. Sampling distribution of the difference in sample means; Sampling distribution of the difference in sample means: Probability example

### Inference for categorical data: Proportions — 6 of 9 lessons not covered

- [The idea of significance tests](https://www.khanacademy.org/math/ap-statistics/xfb5d8e68:inference-for-categorical-data-proportions/xfb5d8e68:setting-up-a-test-for-a-population-proportion) — e.g. Idea behind hypothesis testing; Examples of null and alternative hypotheses; P-values and significance tests
- [Concluding a test for a population proportion](https://www.khanacademy.org/math/statistics-probability/significance-tests-one-sample/tests-about-population-proportion) — e.g. Making conclusions in a test about a proportion; Significance test for a proportion free response example; Significance test for a proportion free response (part 2 with correction)
- [Confidence intervals for the difference of two proportions](https://www.khanacademy.org/math/ap-statistics/xfb5d8e68:inference-for-categorical-data-proportions/xfb5d8e68:constructing-a-confidence-interval-for-the-difference-between-two-population-proportions) — e.g. Confidence intervals for the difference between two proportions; Examples identifying conditions for inference on two proportions; Calculating a confidence interval for the difference of proportions
- [Testing for the difference of two population proportions](https://www.khanacademy.org/math/ap-statistics/xfb5d8e68:inference-for-categorical-data-proportions/xfb5d8e68:setting-up-a-test-for-the-difference-between-two-population-proportions) — e.g. Hypothesis test for difference in proportions; Constructing hypotheses for two proportions; Hypothesis test for difference in proportions example

### Inference for quantitative data: Means — 3 of 5 lessons not covered

- [Setting up a test for a population mean](https://www.khanacademy.org/math/ap-statistics/xfb5d8e68:inference-for-quantitative-data-means/xfb5d8e68:setting-up-a-test-for-a-population-mean-or-population-mean-difference) — e.g. Writing hypotheses for a significance test about a mean; Conditions for a t test about a mean
- [Confidence intervals for the difference of two means](https://www.khanacademy.org/math/ap-statistics/xfb5d8e68:inference-for-quantitative-data-means/xfb5d8e68:constructing-a-confidence-interval-for-the-difference-between-two-population-means) — e.g. Conditions for inference for difference of means; Constructing t interval for difference of means; Calculating confidence interval for difference of means
- [Testing for the difference of two population means](https://www.khanacademy.org/math/ap-statistics/xfb5d8e68:inference-for-quantitative-data-means/xfb5d8e68:setting-up-a-test-for-the-difference-between-two-populations-means) — e.g. Hypotheses for a two-sample t test; Example of hypotheses for paired and two-sample t tests; Two-sample t test for difference of means

### Inference for categorical data: Chi-square — *entire unit not covered*

- [Chi-square test for goodness of fit](https://www.khanacademy.org/math/statistics-probability/inference-categorical-data-chi-square-tests/chi-square-goodness-of-fit-tests) — e.g. Chi-square statistic for hypothesis testing; Chi-square goodness-of-fit example
- [Chi square tests for relationships (homogeneity or independence)](https://www.khanacademy.org/math/ap-statistics/xfb5d8e68:inference-for-categorical-data-proportions/xfb5d8e68:setting-up-a-chi-square-test-for-homogeneity-or-independence) — e.g. Introduction to the chi-square test for homogeneity; Chi-square test for association (independence)

### Inference for quantitative data: slopes — *entire unit not covered*

- [Confidence intervals for the slope of a regression model](https://www.khanacademy.org/math/statistics-probability/advanced-regression-inference-transforming/inference-on-slope) — e.g. Introduction to inference about slope in linear regression; Conditions for inference on slope; Confidence interval for the slope of a regression line
- [Testing for the slope of a regression model](https://www.khanacademy.org/math/statistics-probability/advanced-regression-inference-transforming/inference-on-slope) — e.g. Calculating t statistic for slope of regression line; Using a P-value to make conclusions in a test about slope; Using a confidence interval to test slope

### Prepare for the AP®︎ Statistics Exam — *entire unit not covered*

- [Prepare for the exam](https://www.khanacademy.org/math/ap-statistics/xfb5d8e68:prepare-for-the-2022-ap-statistics-exam/prepare-for-ap-stats-exam) — e.g. Significance test for a proportion free response example; Significance test for a proportion free response (part 2 with correction); Free response example: Significance test for a mean

## AP®︎/College Precalculus

### Polynomial and rational functions — 4 of 14 lessons not covered

- [Change in tandem](https://www.khanacademy.org/math/algebra2/x2ec2f6f830c9fb89:poly-graphs/x2ec2f6f830c9fb89:poly-intervals) — e.g. Positive and negative intervals of polynomials; Increasing, decreasing, positive or negative intervals; Worked example: two inputs with the same output (graph)
- [Polynomial functions and rates of change](https://www.khanacademy.org/math/algebra/x2f8bb11595b61c86:quadratics-multiplying-factoring/x2f8bb11595b61c86:multiply-monomial-polynomial) — e.g. Polynomials intro; Introducing minimum and maximum points
- [Transformations of functions](https://www.khanacademy.org/math/ap-precalculus/xe322600f784e4778:polynomial-and-rational-functions/xe322600f784e4778:transformations-of-functions) — e.g. Graph a polynomial with transformations; Writing transformation form equations of polynomials from a graph; Identifying function transformations
- [Function model selection and assumption articulation](https://www.khanacademy.org/math/algebra/x2f8bb11595b61c86:absolute-value-piecewise-functions/x2f8bb11595b61c86:piecewise-functions) — e.g. Introduction to piecewise functions; Worked example: average rate of change from graph; Worked example: average rate of change from table

### Exponential and logarithmic functions — 7 of 12 lessons not covered

- [Exponential functions](https://www.khanacademy.org/math/algebra-1-eureka-squared-aligned/x15446f63b23e2a07:quadratic-functions/x15446f63b23e2a07:using-transformations-to-graph-exponential-functions-bases-between-0-and-1) — e.g. Determining and representing the domain and range of exponential functions; Identifying key features of exponential functions
- [Exponential function manipulation](https://www.khanacademy.org/math/algebra2/x2ec2f6f830c9fb89:exp/x2ec2f6f830c9fb89:equivalent-exp) — e.g. Equivalent forms of exponential expressions
- [Competing function model validation](https://www.khanacademy.org/math/ap-statistics/xfb5d8e68:regression-analysis/xfb5d8e68:resid) — e.g. Introduction to residuals and least squares regression; Analyzing data to model functions
- [Inverse functions](https://www.khanacademy.org/math/precalculus/x9e81a4f98389efdf:composite/x9e81a4f98389efdf:inverse-functions-in-graphs-and-tables) — e.g. Reading inverse values from a graph; Reading inverse values from a table; Determining if a function is invertible
- [Inverses of exponential functions](https://www.khanacademy.org/math/algebra2/x2ec2f6f830c9fb89:logs/x2ec2f6f830c9fb89:log-intro) — e.g. Relationship between exponentials & logarithms: graphs; Relationship between exponentials & logarithms: tables; Relationship between exponentials & logarithms
- [Exponential and logarithmic equations and inequalities](https://www.khanacademy.org/math/college-algebra/xa5dd2923c88e7aa8:logarithms/xa5dd2923c88e7aa8:logarithmic-equations) — e.g. Solving logarithmic equations; Logarithmic equations: variable in the base; Logarithmic equations: variable in the argument
- [Logarithmic function context and data modeling](https://www.khanacademy.org/math/ap-precalculus/xe322600f784e4778:exponential-and-logarithmic-functions/xe322600f784e4778:construct-logarithmic-functions) — e.g. Constructing logarithmic functions from tables

### Trigonometric and polar functions — 6 of 13 lessons not covered

- [Periodic phenomena](https://www.khanacademy.org/math/algebra2/x2ec2f6f830c9fb89:modeling/x2ec2f6f830c9fb89:interpreting-features) — e.g. Periodicity of algebraic models; Exploring the characteristics of periodic functions
- [Sinusoidal function context and data modeling](https://www.khanacademy.org/math/algebra2/x2ec2f6f830c9fb89:trig/x2ec2f6f830c9fb89:graphing-sinusoid) — e.g. Sinusoidal function from graph
- [The tangent function](https://www.khanacademy.org/math/ap-precalculus/xe322600f784e4778:trigonometric-and-polar-functions/xe322600f784e4778:transform-and-describe-tangent-functions) — e.g. Understanding the tangent function
- [The secant, cosecant, and cotangent functions](https://www.khanacademy.org/math/ap-precalculus/xe322600f784e4778:trigonometric-and-polar-functions/xe322600f784e4778:the-secant-cosecant-and-cotangent-functions) — e.g. Identifying the asymptote equations of transformed reciprocal trigonometric functions
- [Polar function graphs](https://www.khanacademy.org/math/ap-precalculus/xe322600f784e4778:trigonometric-and-polar-functions/xe322600f784e4778:graphs-of-polar-functions) — e.g. Graphing polar functions
- [Rates of change in polar functions](https://www.khanacademy.org/math/ap-precalculus/xe322600f784e4778:trigonometric-and-polar-functions/xe322600f784e4778:rates-of-change-in-polar-functions) — e.g. Describing characteristics of polar function graphs; Estimating the value of a polar function with linear approximation

### Functions involving parametric vectors and matrices — 6 of 10 lessons not covered

- [Parametric functions modeling planar motion and rates of change](https://www.khanacademy.org/math/ap-precalculus/xe322600f784e4778:functions-involving-parametric-vectors-and-matrices/xe322600f784e4778:key-features-of-parametric-planar-motion-functionsd) — e.g. Identifying vertical extremum of parametric planar motion functions; Identifying intercepts of parametric planar motion functions; Determining the average rate of change of parametric planar motion functions over a given interval
- [Parametrically defined circles and lines](https://www.khanacademy.org/math/ap-precalculus/xe322600f784e4778:functions-involving-parametric-vectors-and-matrices/xe322600f784e4778:parametrically-defined-circles-and-lines) — e.g. Parametric equations for projectile motion
- [Parameterization of implicitly defined functions](https://www.khanacademy.org/math/ap-precalculus/xe322600f784e4778:functions-involving-parametric-vectors-and-matrices/xe322600f784e4778:parameterization-of-implicitly-defined-functions) — e.g. Parameterizing implicitly defined functions
- [Vectors](https://www.khanacademy.org/math/precalculus/x9e81a4f98389efdf:vectors/x9e81a4f98389efdf:vectors-intro) — e.g. Intro to vectors and scalars; Representing quantities with vectors; Interpreting statements about vectors
- [Linear transformation and matrices](https://www.khanacademy.org/math/linear-algebra/matrix-transformations/linear-transformations) — e.g. Matrix vector products as linear transformations
- [Matrices as functions](https://www.khanacademy.org/math/precalculus/x9e81a4f98389efdf:matrices/x9e81a4f98389efdf:using-matrices-to-manipulate-data) — e.g. Using matrices to manipulate data: Game show; Using matrices to manipulate data: Pet store

## AP®︎/College Calculus AB

### Limits and continuity — 16 of 18 lessons not covered

- [About the Course](https://www.khanacademy.org/math/ap-calculus-ab/ab-limits-new/x2dd7feea:untitled-840) — e.g. Khan Academy in the classroom; Sal interviews the AP Calculus Lead at College Board
- [Define limits and use limit notation](https://www.khanacademy.org/math/ap-calculus-ab/ab-limits-new/ab-1-2) — e.g. Introducing limits
- [Estimate limit values from graphs](https://www.khanacademy.org/math/ap-calculus-ab/ab-limits-new/ab-1-3) — e.g. Estimating limit values from graphs; Examining unbounded limits; Estimating one-sided limits from graphs
- [Estimate limit values from tables](https://www.khanacademy.org/math/ap-calculus-ab/ab-limits-new/ab-1-4) — e.g. Approximating limits using tables; Estimating limits from tables; Estimating one-sided limits from tables
- [Determine limits using algebraic properties of limits: limit properties](https://www.khanacademy.org/math/ap-calculus-ab/ab-limits-new/ab-1-5a) — e.g. Introducing properties of limits; Determining limits of combined functions; Determining limits of combined functions: piecewise functions
- [Determine limits using algebraic properties of limits: direct substitution](https://www.khanacademy.org/math/ap-calculus-ab/ab-limits-new/ab-1-5b) — e.g. Finding limits by direct substitution; Examining undefined limits by direct substitution; Determining limits of trigonometric functions
- [Determine limits using the squeeze theorem](https://www.khanacademy.org/math/ap-calculus-ab/ab-limits-new/ab-1-8) — e.g. Introducing the squeeze theorem; Determining the limit of sin(x)/x as x approaches 0; Determining the limit of (1-cos(x))/x as x approaches 0
- [Explore types of discontinuities](https://www.khanacademy.org/math/ap-calculus-ab/ab-limits-new/ab-1-10) — e.g. Exploring types of discontinuities
- [Define continuity at a point](https://www.khanacademy.org/math/ap-calculus-ab/ab-limits-new/ab-1-11) — e.g. Exploring continuity at a point; Working an example: Continuity at a point (graphical); Working an example: point where a function is continuous
- [Confirm continuity over an interval](https://www.khanacademy.org/math/ap-calculus-ab/ab-limits-new/ab-1-12) — e.g. Exploring continuity over an interval; Determining if functions are continuous on all real numbers; Determining if functions are continuous at specific x-values
- [Remove discontinuities](https://www.khanacademy.org/math/ap-calculus-ab/ab-limits-new/ab-1-13) — e.g. Removing discontinuities (factoring); Removing discontinuities (rationalization)
- [Connect infinite limits and vertical asymptotes](https://www.khanacademy.org/math/ap-calculus-ab/ab-limits-new/ab-1-14) — e.g. Introducing infinite limits; Exploring infinite limits and asymptotes; Analyzing unbounded limits: rational function
- [Connect limits at infinity and horizontal asymptotes](https://www.khanacademy.org/math/ap-calculus-ab/ab-limits-new/ab-1-15) — e.g. Introducing limits at infinity; Exploring functions with same limit at infinity; Determining limits at infinity of quotients (Part 1)
- [Work with the intermediate value theorem](https://www.khanacademy.org/math/ap-calculus-ab/ab-limits-new/ab-1-16) — e.g. Discovering the intermediate value theorem; Working an example: using the intermediate value theorem; Applying the intermediate value theorem: table
- [Optional videos](https://www.khanacademy.org/math/ap-calculus-ab/ab-limits-new/ab-limits-optional) — e.g. Exploring the formal definition of limits Part 1: intuition review; Exploring the formal definition of limits Part 2: building the idea; Exploring the formal definition of limits Part 3: the definition
- [Free response questions: limits and continuity](https://www.khanacademy.org/math/ap-calculus-ab/ab-limits-new/x2dd7feea:limits-and-continuity-free-response-questions) — e.g. Determining continuity: 2011 Calculus AB free response #6a

### Differentiation: definition and basic derivative rules — 7 of 14 lessons not covered

- [Define average and instantaneous rates of change at a point](https://www.khanacademy.org/math/ap-calculus-ab/ab-differentiation-1-new/ab-2-1) — e.g. Connecting Newton, Leibniz, and Usain Bolt; Exploring derivatives as a concept; Connecting secant lines and average rate of change
- [Estimate derivatives of a function at a point](https://www.khanacademy.org/math/ap-calculus-ab/ab-differentiation-1-new/ab-2-3) — e.g. Estimating derivatives
- [Connect differentiability and continuity: determine when derivatives do and do not exist](https://www.khanacademy.org/math/ap-calculus-ab/ab-differentiation-1-new/ab-2-4) — e.g. Exploring differentiability and continuity; Understanding differentiability at a point: graphical; Examining differentiability at a point: algebraic (function is differentiable)
- [Practice to connect derivatives and limits](https://www.khanacademy.org/math/ap-calculus-ab/ab-differentiation-1-new/ab-3-7) — e.g. Finding limits with derivatives
- [Find the derivatives of tangent, cotangent, secant, and/or cosecant functions](https://www.khanacademy.org/math/ap-calculus-ab/ab-differentiation-1-new/ab-2-10) — e.g. Finding derivatives of tan(x) and cot(x); Finding derivatives of sec(x) and csc(x)
- [Free response questions: differentiation definition and basic derivative rules](https://www.khanacademy.org/math/ap-calculus-ab/ab-differentiation-1-new/x2dd7feea:differentiation-definition-and-basic-derivative-rules-free-response-questions) — e.g. Estimating rate of change 2011 AP Calculus AB free response 2a; Writing equation of tangent line AP Calculus AB free response 2011 3a; Estimating rate of change: 2015 AP Calculus AB/BC 3a

### Differentiation: composite, implicit, and inverse functions — 5 of 10 lessons not covered

- [Differentiate inverse functions](https://www.khanacademy.org/math/ap-calculus-ab/ab-differentiation-2-new/ab-3-3) — e.g. Exploring the derivatives of inverse functions; Exploring the derivatives of inverse functions: from equations; Exploring the derivatives of inverse functions: from tables
- [Differentiate inverse trigonometric functions](https://www.khanacademy.org/math/ap-calculus-ab/ab-differentiation-2-new/ab-3-4) — e.g. Determining the derivative of inverse sine; Determining the derivative of inverse cosine; Determining the derivative of inverse tangent
- [Select procedures to calculate derivatives: strategy](https://www.khanacademy.org/math/ap-calculus-ab/ab-differentiation-2-new/ab-3-5a) — e.g. Differentiating functions: Find the error; Manipulating functions before differentiation; Exploring disguised derivatives
- [Select procedures to calculate derivatives: multiple rules](https://www.khanacademy.org/math/ap-calculus-ab/ab-differentiation-2-new/ab-3-5b) — e.g. Differentiating using multiple rules: strategy; Applying the chain rule and product rule; Applying the chain rule twice

### Contextual applications of differentiation — 3 of 9 lessons not covered

- [Interpret the meaning of the derivative in context](https://www.khanacademy.org/math/ap-calculus-ab/ab-diff-contextual-applications-new/ab-4-1) — e.g. Interpreting the meaning of the derivative in context
- [Rates of change in other applied contexts (non-motion problems)](https://www.khanacademy.org/math/ap-calculus-ab/ab-diff-contextual-applications-new/ab-4-3) — e.g. Exploring applied rate of change: forgetfulness; Examining marginal cost and differential calculus

### Analytical applications of differentiation — 7 of 13 lessons not covered

- [Determine intervals on which a function increases or decreases](https://www.khanacademy.org/math/ap-calculus-ab/ab-diff-analytical-applications-new/ab-5-3) — e.g. Finding decreasing interval given the function; Finding increasing interval given the derivative
- [Determine concavity of intervals and find points of inflection: graphical](https://www.khanacademy.org/math/ap-calculus-ab/ab-diff-analytical-applications-new/ab-5-6a) — e.g. Introducing concavity; Analyzing concavity (graphical); Introducing inflection points
- [Use the second derivative test to find extrema](https://www.khanacademy.org/math/ap-calculus-ab/ab-diff-analytical-applications-new/ab-5-7) — e.g. Applying the second derivative test
- [Sketch curves of functions and their derivatives](https://www.khanacademy.org/math/ap-calculus-ab/ab-diff-analytical-applications-new/ab-5-8) — e.g. Sketching a curve with calculus: polynomial; Sketching a curve with calculus: logarithm; Analyzing a function with its derivative
- [Connect a function, its first derivative, and its second derivative](https://www.khanacademy.org/math/ap-calculus-ab/ab-diff-analytical-applications-new/ab-5-9) — e.g. Establishing a calculus-based justification for a function increasing; Justifying a function's features using the first derivative; Identifying inflection points from graphs of function and derivatives
- [Solve optimization problems](https://www.khanacademy.org/math/ap-calculus-ab/ab-diff-analytical-applications-new/ab-5-11) — e.g. Applying optimization: sum of squares; Applying optimization: box volume (Part 1); Applying optimization: box volume (Part 2)
- [Explore behaviors of implicit relations](https://www.khanacademy.org/math/ap-calculus-ab/ab-diff-analytical-applications-new/ab-5-12) — e.g. Determining horizontal tangent to implicit curve; Determining equation of vertical line tangent to curve

### Integration and accumulation of change — 8 of 14 lessons not covered

- [Explore accumulations of change](https://www.khanacademy.org/math/ap-calculus-ab/ab-integration-new/ab-6-1) — e.g. Introducing integral calculus; Introducing definite integrals; Working an example: accumulation of change
- [The fundamental theorem of calculus and accumulation functions](https://www.khanacademy.org/math/ap-calculus-ab/ab-integration-new/ab-6-4) — e.g. Introducing the fundamental theorem of calculus and accumulation functions; Understanding functions defined by definite integrals (accumulation functions); Finding derivative with fundamental theorem of calculus
- [Interpret the behavior of accumulation functions that involve area](https://www.khanacademy.org/math/ap-calculus-ab/ab-integration-new/ab-6-5) — e.g. Interpreting the behavior of accumulation functions
- [Apply properties of definite integrals](https://www.khanacademy.org/math/ap-calculus-ab/ab-integration-new/ab-6-6) — e.g. Understanding definite integrals with a negative value; Finding definite integrals using area formulas; Calculating net area using geometry
- [Find antiderivatives and integrals: basic rules and notation: common indefinite integrals](https://www.khanacademy.org/math/ap-calculus-ab/ab-integration-new/ab-6-8b) — e.g. Determining the indefinite integral of 1/x; Determining the indefinite integrals of sin(x), cos(x), and eˣ
- [Complete the square or use long division to integrate functions](https://www.khanacademy.org/math/ap-calculus-ab/ab-integration-new/ab-6-10) — e.g. Integrating using long division; Integrating using completing the square and the derivative of arctan(x)
- [Free response questions: integration and accumulation of change](https://www.khanacademy.org/math/ap-calculus-ab/ab-integration-new/x2dd7feea:integration-and-accumulation-of-change-free-response-questions) — e.g. Using equations involving integrals: 2011 Calculus AB free response #4a

### Differential equations — 4 of 8 lessons not covered

- [Model situations with differential equations](https://www.khanacademy.org/math/ap-calculus-ab/ab-differential-equations-new/ab-7-1) — e.g. Introducing differential equations; Writing a differential equation
- [Verify solutions for differential equations](https://www.khanacademy.org/math/ap-calculus-ab/ab-differential-equations-new/ab-7-2) — e.g. Verifying solutions to differential equations
- [Sketch slope fields](https://www.khanacademy.org/math/ap-calculus-ab/ab-differential-equations-new/ab-7-3) — e.g. Introducing slope fields; Working an example: equation from slope field; Working an example: slope field from equation
- [Draw conclusion from slope fields](https://www.khanacademy.org/math/ap-calculus-ab/ab-differential-equations-new/ab-7-4) — e.g. Approximating solution curves in slope fields; Working an example: range of solution curve from slope field

### Applications of integration — 7 of 13 lessons not covered

- [Use accumulation functions and definite integrals in applied contexts](https://www.khanacademy.org/math/ap-calculus-ab/ab-applications-of-integration-new/ab-8-3) — e.g. Determining area under rate function gives the net change; Interpreting definite integral as net change; Working examples: interpreting definite integrals in context
- [Find the area between curves expressed as functions of y](https://www.khanacademy.org/math/ap-calculus-ab/ab-applications-of-integration-new/ab-8-5) — e.g. Calculating area between a curve and the 𝘺-axis; Calculating horizontal area between curves
- [Find the area between curves that intersect at more than two points](https://www.khanacademy.org/math/ap-calculus-ab/ab-applications-of-integration-new/ab-8-6) — e.g. Calculating areas between curves with calculator
- [Volumes with cross sections: squares and rectangles](https://www.khanacademy.org/math/ap-calculus-ab/ab-applications-of-integration-new/ab-8-7) — e.g. Introducing volume with cross sections; Determining integral for volume with rectangular cross sections; Exploring volume with cross sections: squares and rectangles (no graph)
- [Volumes with cross sections: triangles and semicircles](https://www.khanacademy.org/math/ap-calculus-ab/ab-applications-of-integration-new/ab-8-8) — e.g. Exploring volume with cross sections: semicircle; Exploring volume with cross sections: triangle
- [Volume with disc method: revolve around other axes](https://www.khanacademy.org/math/ap-calculus-ab/ab-applications-of-integration-new/ab-8-10) — e.g. Using the disc method: rotation around horizontal line; Using the disc method: rotation around vertical line; Calculating integral: disc around vertical line
- [Volume with washer method: revolve around other axes](https://www.khanacademy.org/math/ap-calculus-ab/ab-applications-of-integration-new/ab-8-12) — e.g. Using the washer method: rotating around horizontal line (not x-axis), part 1; Using the washer method: rotating around horizontal line (not x-axis), part 2; Using the washer method: rotating around vertical line (not y-axis), part 1

## AP®︎/College Calculus BC

### Differentiation: definition and basic derivative rules — 6 of 14 lessons not covered

- [Connect differentiability and continuity: determining when derivatives do and do not exist](https://www.khanacademy.org/math/ap-calculus-ab/ab-differentiation-1-new/ab-2-4) — e.g. Exploring differentiability and continuity; Understanding differentiability at a point: graphical; Examining differentiability at a point: algebraic (function is differentiable)

### Differentiation: composite, implicit, and inverse functions — 5 of 10 lessons not covered

- [Select procedures for calculating derivatives: strategy](https://www.khanacademy.org/math/ap-calculus-ab/ab-differentiation-2-new/ab-3-5a) — e.g. Differentiating functions: Find the error; Manipulating functions before differentiation; Exploring disguised derivatives
- [Select procedures for calculating derivatives: multiple rules](https://www.khanacademy.org/math/ap-calculus-ab/ab-differentiation-2-new/ab-3-5b) — e.g. Differentiating using multiple rules: strategy; Applying the chain rule and product rule; Applying the chain rule twice

### Analytical applications of differentiation — 7 of 13 lessons not covered

- [Determine intervals on which a function is increasing or decreasing](https://www.khanacademy.org/math/ap-calculus-ab/ab-diff-analytical-applications-new/ab-5-3) — e.g. Finding decreasing interval given the function; Finding increasing interval given the derivative
- [Determine concavity of intervals and finding points of inflection: graphical](https://www.khanacademy.org/math/ap-calculus-ab/ab-diff-analytical-applications-new/ab-5-6a) — e.g. Introducing concavity; Analyzing concavity (graphical); Introducing inflection points

### Integration and accumulation of change — 8 of 16 lessons not covered

- [Exploring accumulations of change](https://www.khanacademy.org/math/ap-calculus-ab/ab-integration-new/ab-6-1) — e.g. Introducing integral calculus; Introducing definite integrals; Working an example: accumulation of change
- [Interpreting the behavior of accumulation functions involving area](https://www.khanacademy.org/math/ap-calculus-ab/ab-integration-new/ab-6-5) — e.g. Interpreting the behavior of accumulation functions
- [Applying properties of definite integrals](https://www.khanacademy.org/math/ap-calculus-ab/ab-integration-new/ab-6-6) — e.g. Understanding definite integrals with a negative value; Finding definite integrals using area formulas; Evaluating a definite integral over a single point
- [Finding antiderivatives and indefinite integrals: basic rules and notation: common indefinite integrals](https://www.khanacademy.org/math/ap-calculus-ab/ab-integration-new/ab-6-8b) — e.g. Determining the indefinite integral of 1/x; Determining the indefinite integrals of sin(x), cos(x), and eˣ
- [Integrating functions using long division and completing the square](https://www.khanacademy.org/math/ap-calculus-ab/ab-integration-new/ab-6-10) — e.g. Integrating using long division; Integrating using completing the square and the derivative of arctan(x)
- [Evaluating improper integrals](https://www.khanacademy.org/math/ap-calculus-bc/bc-integration-new/bc-6-13) — e.g. Introduction to improper integrals; Divergent improper integral

### Differential equations — 6 of 9 lessons not covered

- [Modeling situations with differential equations](https://www.khanacademy.org/math/ap-calculus-ab/ab-differential-equations-new/ab-7-1) — e.g. Introducing differential equations; Writing a differential equation
- [Verifying solutions for differential equations](https://www.khanacademy.org/math/ap-calculus-ab/ab-differential-equations-new/ab-7-2) — e.g. Verifying solutions to differential equations
- [Sketching slope fields](https://www.khanacademy.org/math/ap-calculus-ab/ab-differential-equations-new/ab-7-3) — e.g. Introducing slope fields; Working an example: equation from slope field; Working an example: slope field from equation
- [Reasoning using slope fields](https://www.khanacademy.org/math/ap-calculus-ab/ab-differential-equations-new/ab-7-4) — e.g. Approximating solution curves in slope fields; Working an example: range of solution curve from slope field
- [Approximating solutions using Euler’s method](https://www.khanacademy.org/math/ap-calculus-bc/bc-differential-equations-new/bc-7-5) — e.g. Euler's method; Worked example: Euler's method
- [Logistic models with differential equations](https://www.khanacademy.org/math/ap-calculus-bc/bc-differential-equations-new/bc-7-9) — e.g. Growth models: introduction; The logistic  growth model; Worked example: Logistic model word problem

### Applications of integration — 7 of 12 lessons not covered

- [Using accumulation functions and definite integrals in applied contexts](https://www.khanacademy.org/math/ap-calculus-ab/ab-applications-of-integration-new/ab-8-3) — e.g. Determining area under rate function gives the net change; Interpreting definite integral as net change; Working examples: interpreting definite integrals in context
- [Finding the area between curves expressed as functions of y](https://www.khanacademy.org/math/ap-calculus-ab/ab-applications-of-integration-new/ab-8-5) — e.g. Calculating area between a curve and the 𝘺-axis; Calculating horizontal area between curves
- [Volume with disc method: revolving around other axes](https://www.khanacademy.org/math/ap-calculus-ab/ab-applications-of-integration-new/ab-8-10) — e.g. Using the disc method: rotation around horizontal line; Using the disc method: rotation around vertical line; Calculating integral: disc around vertical line
- [Volume with washer method: revolving around other axes](https://www.khanacademy.org/math/ap-calculus-ab/ab-applications-of-integration-new/ab-8-12) — e.g. Using the washer method: rotating around horizontal line (not x-axis), part 1; Using the washer method: rotating around horizontal line (not x-axis), part 2; Using the washer method: rotating around vertical line (not y-axis), part 1
- [The arc length of a smooth, planar curve and distance traveled](https://www.khanacademy.org/math/ap-calculus-bc/bc-applications-of-integration-new/bc-8-13) — e.g. Arc length intro; Worked example: arc length

### Parametric equations, polar coordinates, and vector-valued functions — *entire unit not covered*

- [Defining and differentiating parametric equations](https://www.khanacademy.org/math/ap-calculus-bc/bc-advanced-functions-new/bc-9-1) — e.g. Parametric equations intro; Parametric equations differentiation
- [Second derivatives of parametric equations](https://www.khanacademy.org/math/ap-calculus-bc/bc-advanced-functions-new/bc-9-2) — e.g. Second derivatives (parametric functions)
- [Finding arc lengths of curves given by parametric equations](https://www.khanacademy.org/math/ap-calculus-bc/bc-advanced-functions-new/bc-9-3) — e.g. Parametric curve arc length; Worked example: Parametric arc length
- [Defining and differentiating vector-valued functions](https://www.khanacademy.org/math/ap-calculus-bc/bc-advanced-functions-new/bc-9-4) — e.g. Vector-valued functions intro; Vector-valued functions differentiation; Second derivatives (vector-valued functions)
- [Solving motion problems using parametric and vector-valued functions](https://www.khanacademy.org/math/ap-calculus-bc/bc-advanced-functions-new/bc-9-6) — e.g. Planar motion example: acceleration vector; Motion along a curve: finding rate of change; Motion along a curve: finding velocity magnitude
- [Defining polar coordinates and differentiating in polar form](https://www.khanacademy.org/math/ap-calculus-bc/bc-advanced-functions-new/bc-9-7) — e.g. Polar functions derivatives; Worked example: differentiating polar functions
- [Finding the area of a polar region or the area bounded by a single polar curve](https://www.khanacademy.org/math/ap-calculus-bc/bc-advanced-functions-new/bc-9-8) — e.g. Area bounded by polar curves; Worked example: Area enclosed by cardioid
- [Finding the area of the region bounded by two polar curves](https://www.khanacademy.org/math/ap-calculus-bc/bc-advanced-functions-new/bc-9-9) — e.g. Worked example: Area between two polar graphs
- [Calculator-active practice](https://www.khanacademy.org/math/ap-calculus-bc/bc-advanced-functions-new/bc-9-10) — e.g. Evaluating definite integral with calculator

### Infinite sequences and series — 13 of 16 lessons not covered

- [Working with geometric series](https://www.khanacademy.org/math/ap-calculus-bc/bc-series-new/bc-10-2) — e.g. Worked example: convergent geometric series; Worked example: divergent geometric series; Infinite geometric series word problem: bouncing ball
- [The nth-term test for divergence](https://www.khanacademy.org/math/ap-calculus-bc/bc-series-new/bc-10-3) — e.g. nth term divergence test
- [Integral test for convergence](https://www.khanacademy.org/math/ap-calculus-bc/bc-series-new/bc-10-4) — e.g. Integral test; Worked example: Integral test
- [Harmonic series and p-series](https://www.khanacademy.org/math/ap-calculus-bc/bc-series-new/bc-10-5) — e.g. Harmonic series and 𝑝-series; Worked example: p-series
- [Comparison tests for convergence](https://www.khanacademy.org/math/ap-calculus-bc/bc-series-new/bc-10-6) — e.g. Direct comparison test; Worked example: direct comparison test; Limit comparison test
- [Alternating series test for convergence](https://www.khanacademy.org/math/ap-calculus-bc/bc-series-new/bc-10-7) — e.g. Alternating series test; Worked example: alternating series
- [Ratio test for convergence](https://www.khanacademy.org/math/ap-calculus-bc/bc-series-new/bc-10-8) — e.g. Ratio test
- [Determining absolute or conditional convergence](https://www.khanacademy.org/math/ap-calculus-bc/bc-series-new/bc-10-9) — e.g. Conditional & absolute convergence
- [Alternating series error bound](https://www.khanacademy.org/math/ap-calculus-bc/bc-series-new/bc-10-10) — e.g. Alternating series remainder; Worked example: alternating series remainder
- [Lagrange error bound](https://www.khanacademy.org/math/ap-calculus-bc/bc-series-new/bc-10-12) — e.g. Taylor polynomial remainder (part 1); Taylor polynomial remainder (part 2); Worked example: estimating sin(0.4) using Lagrange error bound
- [Radius and interval of convergence of power series](https://www.khanacademy.org/math/ap-calculus-bc/bc-series-new/bc-10-13) — e.g. Power series intro; Worked example: interval of convergence
- [Representing functions as power series](https://www.khanacademy.org/math/ap-calculus-bc/bc-series-new/bc-10-15) — e.g. Integrating power series; Differentiating power series; Finding function from power series by integrating

### AP Calculus BC solved exams — 2 of 4 lessons not covered

- [AP Calculus BC 2015](https://www.khanacademy.org/math/ap-calculus-bc/bc-solved-exams-new/bc-solved-exams-2015-new) — e.g. 2015 AP Calculus BC 2a; 2015 AP Calculus BC 2b; 2015 AP Calculus BC 2c
- [AP Calculus BC 2011](https://www.khanacademy.org/math/ap-calculus-bc/bc-solved-exams-new/bc-solved-exams-2011-new) — e.g. 2011 Calculus BC free response #1a; 2011 Calculus BC free response #1 (b & c); 2011 Calculus BC free response #1d

## Multivariable calculus

### Thinking about multivariable functions — *entire unit not covered*

- [Introduction to multivariable calculus](https://www.khanacademy.org/math/multivariable-calculus/thinking-about-multivariable-function/introduction-to-multivariable-calculus) — e.g. Multivariable functions
- [Visualizing scalar-valued functions](https://www.khanacademy.org/math/multivariable-calculus/thinking-about-multivariable-function/visualizing-scalar-valued-functions) — e.g. Representing points in 3d; Introduction to 3d graphs; Interpreting graphs with slices
- [Visualizing vector-valued functions](https://www.khanacademy.org/math/multivariable-calculus/thinking-about-multivariable-function/visualizing-vector-valued-functions) — e.g. Parametric curves; Parametric surfaces; Vector fields, introduction
- [Transformations](https://www.khanacademy.org/math/multivariable-calculus/thinking-about-multivariable-function/multivariable-transformations) — e.g. Transformations, part 1; Transformations, part 2 ; Transformations, part 3

### Derivatives of multivariable functions — *entire unit not covered*

- [Partial derivatives](https://www.khanacademy.org/math/multivariable-calculus/multivariable-derivatives/partial-derivatives) — e.g. Partial derivatives, introduction; Graphical understanding of partial derivatives; Formal definition of partial derivatives
- [Gradient and directional derivatives](https://www.khanacademy.org/math/multivariable-calculus/multivariable-derivatives/gradient-and-directional-derivatives) — e.g. Gradient; Gradient and graphs; Gradient and contour maps
- [Differentiating parametric curves](https://www.khanacademy.org/math/ap-calculus-bc/bc-advanced-functions-new/bc-9-4) — e.g. Vector-valued functions intro; Vector-valued functions differentiation; Differential of a vector valued function
- [Multivariable chain rule](https://www.khanacademy.org/math/multivariable-calculus/multivariable-derivatives/multivariable-chain-rule) — e.g. Multivariable chain rule; Multivariable chain rule intuition; Vector form of the multivariable chain rule
- [Curvature](https://www.khanacademy.org/math/multivariable-calculus/multivariable-derivatives/curvature) — e.g. Curvature intuition; Curvature formula, part 1; Curvature formula, part 2
- [Partial derivatives of vector-valued functions](https://www.khanacademy.org/math/multivariable-calculus/multivariable-derivatives/partial-derivatives-of-vector-valued-functions) — e.g. Computing the partial derivative of a vector-valued function; Partial derivative of a parametric surface, part 1; Partial derivative of a parametric surface, part 2
- [Divergence](https://www.khanacademy.org/math/multivariable-calculus/multivariable-derivatives/divergence-grant-videos) — e.g. Divergence intuition, part 1; Divergence intuition, part 2; Divergence formula, part 1
- [Curl](https://www.khanacademy.org/math/multivariable-calculus/multivariable-derivatives/curl-grant-videos) — e.g. 2d curl intuition; 2d curl formula; 2d curl example
- [Laplacian](https://www.khanacademy.org/math/multivariable-calculus/multivariable-derivatives/laplacian) — e.g. Laplacian intuition; Laplacian computation example; Explicit Laplacian formula
- [Jacobian](https://www.khanacademy.org/math/multivariable-calculus/multivariable-derivatives/jacobian) — e.g. Jacobian prerequisite knowledge; Local linearity for a multivariable function; The Jacobian matrix

### Applications of multivariable derivatives — *entire unit not covered*

- [Tangent planes and local linearization](https://www.khanacademy.org/math/multivariable-calculus/applications-of-multivariable-derivatives/tangent-planes-and-local-linearization) — e.g. What is a tangent plane; Controlling a plane in space; Computing a tangent plane
- [Quadratic approximations](https://www.khanacademy.org/math/multivariable-calculus/applications-of-multivariable-derivatives/quadratic-approximations) — e.g. What do quadratic approximations look like; Quadratic approximation formula, part 1; Quadratic approximation formula, part 2
- [Optimizing multivariable functions](https://www.khanacademy.org/math/multivariable-calculus/applications-of-multivariable-derivatives/optimizing-multivariable-functions-videos) — e.g. Multivariable maxima and minima; Saddle points; Warm up to the second partial derivative test
- [Lagrange multipliers and constrained optimization](https://www.khanacademy.org/math/multivariable-calculus/applications-of-multivariable-derivatives/lagrange-multipliers-and-constrained-optimization) — e.g. Constrained optimization introduction; Lagrange multipliers, using tangency to solve constrained optimization; Finishing the intro lagrange multiplier example

### Integrating multivariable functions — *entire unit not covered*

- [Line integrals for scalar functions](https://www.khanacademy.org/math/multivariable-calculus/integrating-multivariable-functions/line-integrals) — e.g. Introduction to the line integral; Line integral example 1; Line integral example 2 (part 1)
- [Line integrals in vector fields](https://www.khanacademy.org/math/multivariable-calculus/integrating-multivariable-functions/line-integrals-vectors) — e.g. Line integrals and vector fields; Using a line integral to find work; Parametrization of a reverse path
- [Double integrals](https://www.khanacademy.org/math/multivariable-calculus/integrating-multivariable-functions/double-integrals-topic) — e.g. Double integral 1; Double integrals 2; Double integrals 3
- [Double integrals (articles)](https://www.khanacademy.org/math/multivariable-calculus/integrating-multivariable-functions/double-integrals-a) — e.g. Polar coordinates
- [Triple integrals](https://www.khanacademy.org/math/multivariable-calculus/integrating-multivariable-functions/triple-integrals-topic) — e.g. Triple integrals 1; Triple integrals 2; Triple integrals 3
- [Surface integral preliminaries](https://www.khanacademy.org/math/multivariable-calculus/integrating-multivariable-functions/surface-parametrization) — e.g. Parametrizing a surface, part 1; Determining a position vector-valued function for a parametrization of two parameters; Partial derivatives of vector-valued functions
- [Surface integrals](https://www.khanacademy.org/math/multivariable-calculus/integrating-multivariable-functions/surface-integrals-introduction) — e.g. Introduction to the surface integral; Example of calculating a surface integral part 1; Example of calculating a surface integral part 2
- [Flux in 3D](https://www.khanacademy.org/math/multivariable-calculus/integrating-multivariable-functions/3d-flux) — e.g. Conceptual understanding of flux; Constructing a unit normal vector; Vector representation of a surface integral

### Green's, Stokes', and the divergence theorems — *entire unit not covered*

- [Green's theorem](https://www.khanacademy.org/math/multivariable-calculus/greens-theorem-and-stokes-theorem/greens-theorem) — e.g. Green's theorem proof (part 1); Green's theorem proof (part 2); Green's theorem example 1
- [2D divergence theorem](https://www.khanacademy.org/math/multivariable-calculus/greens-theorem-and-stokes-theorem/2d-divergence-theorem-ddp) — e.g. Constructing a unit normal vector to a curve; 2D divergence theorem; Conceptual clarification for 2D divergence theorem
- [Stokes' theorem](https://www.khanacademy.org/math/multivariable-calculus/greens-theorem-and-stokes-theorem/stokes-theorem) — e.g. Stokes' theorem intuition; Green's and Stokes' theorem relationship; Orienting boundary with surface
- [3D divergence theorem](https://www.khanacademy.org/math/multivariable-calculus/greens-theorem-and-stokes-theorem/divergence-theorem) — e.g. 3D divergence theorem intuition; Divergence theorem example 1; Explanation of example 1
- [Proof of Stokes' theorem](https://www.khanacademy.org/math/multivariable-calculus/greens-theorem-and-stokes-theorem/stokes-proof) — e.g. Stokes' theorem proof part 1; Stokes' theorem proof part 2; Stokes' theorem proof part 3
- [Types of regions in three dimensions](https://www.khanacademy.org/math/multivariable-calculus/greens-theorem-and-stokes-theorem/region-types-3d) — e.g. Type I regions in three dimensions; Type II regions in three dimensions; Type III regions in three dimensions
- [Divergence theorem proof](https://www.khanacademy.org/math/multivariable-calculus/greens-theorem-and-stokes-theorem/divergence-theorem-proof) — e.g. Divergence theorem proof (part 1); Divergence theorem proof (part 2); Divergence theorem proof (part 3)

## Differential equations

### First order differential equations — 6 of 8 lessons not covered

- [Intro to differential equations](https://www.khanacademy.org/math/ap-calculus-ab/ab-differential-equations-new/ab-7-1) — e.g. Introducing differential equations; Writing a differential equation; Worked example: linear solution to differential equation
- [Slope fields](https://www.khanacademy.org/math/ap-calculus-ab/ab-differential-equations-new/ab-7-3) — e.g. Introducing slope fields; Working an example: equation from slope field; Working an example: slope field from equation
- [Euler's Method](https://www.khanacademy.org/math/ap-calculus-bc/bc-differential-equations-new/bc-7-5) — e.g. Euler's method; Worked example: Euler's method
- [Logistic models](https://www.khanacademy.org/math/ap-calculus-bc/bc-differential-equations-new/bc-7-9) — e.g. Growth models: introduction; The logistic  growth model; Logistic equations (Part 1)
- [Exact equations and integrating factors](https://www.khanacademy.org/math/differential-equations/first-order-differential-equations/exact-equations) — e.g. Exact equations intuition 1 (proofy); Exact equations intuition 2 (proofy); Exact equations example 1
- [Homogeneous equations](https://www.khanacademy.org/math/differential-equations/first-order-differential-equations/homogeneous-equations) — e.g. First order homogenous equations; First order homogeneous equations 2

### Second order linear equations — *entire unit not covered*

- [Linear homogeneous equations](https://www.khanacademy.org/math/differential-equations/second-order-differential-equations/linear-homogeneous-2nd-order) — e.g. 2nd order linear homogeneous differential equations 1; 2nd order linear homogeneous differential equations 2; 2nd order linear homogeneous differential equations 3
- [Complex and repeated roots of characteristic equation](https://www.khanacademy.org/math/differential-equations/second-order-differential-equations/complex-roots-characteristic-equation) — e.g. Complex roots of the characteristic equations 1; Complex roots of the characteristic equations 2; Complex roots of the characteristic equations 3
- [Method of undetermined coefficients](https://www.khanacademy.org/math/differential-equations/second-order-differential-equations/undetermined-coefficients) — e.g. Undetermined coefficients 1; Undetermined coefficients 2; Undetermined coefficients 3

### Laplace transform — *entire unit not covered*

- [Laplace transform](https://www.khanacademy.org/math/differential-equations/laplace-transform/laplace-transform-tutorial) — e.g. Laplace transform 1; Laplace transform 2; L{sin(at)} - transform of sin(at)
- [Properties of the Laplace transform](https://www.khanacademy.org/math/differential-equations/laplace-transform/properties-of-laplace-transform) — e.g. Laplace as linear operator and Laplace of derivatives; Laplace transform of cos t and polynomials; "Shifting" transform by multiplying function by exponential
- [Laplace transform to solve a differential equation](https://www.khanacademy.org/math/differential-equations/laplace-transform/laplace-transform-to-solve-differential-equation) — e.g. Laplace transform to solve an equation; Laplace transform solves an equation 2; Using the Laplace transform to solve a nonhomogeneous eq
- [The convolution integral](https://www.khanacademy.org/math/differential-equations/laplace-transform/convolution-integral) — e.g. Introduction to the convolution; The convolution and the Laplace transform; Using the convolution theorem to solve an initial value prob

## College Algebra

### Exponents and radicals — 1 of 7 lessons not covered

- [Graphing exponential growth and decay](https://www.khanacademy.org/math/algebra/x2f8bb11595b61c86:exponential-growth-decay/x2f8bb11595b61c86:exponential-decay) — e.g. Graphing exponential growth & decay

### Quadratic functions and equations — 1 of 5 lessons not covered

- [Quadratic models](https://www.khanacademy.org/math/algebra/x2f8bb11595b61c86:inequalities-systems-graphs/x2f8bb11595b61c86:modeling-with-linear-inequalities) — e.g. Creativity break: What can we do to expand our creative skills?; Interpret quadratic models: Factored form; Interpret quadratic models: Vertex form

### Advanced equations — 1 of 4 lessons not covered

- [Modeling with rational expressions](https://www.khanacademy.org/math/precalculus/x9e81a4f98389efdf:rational-functions/x9e81a4f98389efdf:modeling-with-rational-functions) — e.g. Combining mixtures example; Rational equation word problem; Rational equations word problem: combined rates (example 2)

### Graphs and forms of linear equations — 4 of 8 lessons not covered

- [Graphing from slope](https://www.khanacademy.org/math/algebra/x2f8bb11595b61c86:linear-equations-graphs/x2f8bb11595b61c86:slope) — e.g. Graphing a line given point and slope
- [Horizontal and vertical lines](https://www.khanacademy.org/math/algebra/x2f8bb11595b61c86:linear-equations-graphs/x2f8bb11595b61c86:horizontal-vertical-lines) — e.g. Slope of a horizontal line; Horizontal & vertical lines
- [Equations of parallel and perpendicular lines](https://www.khanacademy.org/math/geometry/hs-geo-analytic-geometry/hs-geo-parallel-perpendicular-eq) — e.g. Parallel lines from equation; Parallel lines from equation (example 2); Parallel lines from equation (example 3)

### Logarithms — 3 of 7 lessons not covered

- [Logarithmic equations](https://www.khanacademy.org/math/college-algebra/xa5dd2923c88e7aa8:logarithms/xa5dd2923c88e7aa8:logarithmic-equations) — e.g. Solving logarithmic equations; Solving real world logarithmic equations

## Linear algebra

### Vectors and spaces — 6 of 7 lessons not covered

- [Linear combinations and spans](https://www.khanacademy.org/math/linear-algebra/vectors-and-spaces/linear-combinations) — e.g. Linear combinations and span
- [Linear dependence and independence](https://www.khanacademy.org/math/linear-algebra/vectors-and-spaces/linear-independence) — e.g. Introduction to linear independence; More on linear independence; Span and linear independence example
- [Subspaces and the basis for a subspace](https://www.khanacademy.org/math/linear-algebra/vectors-and-spaces/subspace-basis) — e.g. Linear subspaces; Basis of a subspace
- [Matrices for solving systems by elimination](https://www.khanacademy.org/math/linear-algebra/vectors-and-spaces/matrices-elimination) — e.g. Solving a system of 3 equations and 4 variables using matrix row-echelon form; Solving linear systems with matrices; Using matrix row-echelon form in order to show a linear system has no solutions
- [Null space and column space](https://www.khanacademy.org/math/linear-algebra/vectors-and-spaces/null-column-space) — e.g. Matrix vector products; Introduction to the null space of a matrix; Null space 2: Calculating the null space of a matrix

### Matrix transformations — 5 of 7 lessons not covered

- [Functions and linear transformations](https://www.khanacademy.org/math/linear-algebra/matrix-transformations/linear-transformations) — e.g. A more formal understanding of functions; Vector transformations; Linear transformations
- [Linear transformation examples](https://www.khanacademy.org/math/linear-algebra/matrix-transformations/lin-trans-examples) — e.g. Linear transformation examples: Scaling and reflections; Linear transformation examples: Rotations in R2; Rotation in R3 around the x-axis
- [Inverse functions and transformations](https://www.khanacademy.org/math/linear-algebra/matrix-transformations/inverse-transformations) — e.g. Introduction to the inverse of a function; Proof: Invertibility implies a unique solution to f(x)=y; Surjective (onto) and injective (one-to-one) functions
- [More determinant depth](https://www.khanacademy.org/math/linear-algebra/matrix-transformations/determinant-depth) — e.g. Determinant when row multiplied by scalar; (correction) scalar multiplication of row; Determinant when row is added
- [Transpose of a matrix](https://www.khanacademy.org/math/linear-algebra/matrix-transformations/matrix-transpose) — e.g. Transpose of a matrix; Determinant of transpose; Transpose of a matrix product

### Alternate coordinate systems (bases) — 4 of 5 lessons not covered

- [Orthogonal complements](https://www.khanacademy.org/math/linear-algebra/alternate-bases/othogonal-complements) — e.g. Orthogonal complements; dim(v) + dim(orthogonal complement of v) = n; Representing vectors in rn using subspace members
- [Change of basis](https://www.khanacademy.org/math/linear-algebra/alternate-bases/change-of-basis) — e.g. Coordinates with respect to a basis; Change of basis matrix; Invertible change of basis matrix
- [Orthonormal bases and the Gram-Schmidt process](https://www.khanacademy.org/math/linear-algebra/alternate-bases/orthonormal-basis) — e.g. Introduction to orthonormal bases; Coordinates with respect to orthonormal bases; Projections onto subspaces with orthonormal bases
- [Eigen-everything](https://www.khanacademy.org/math/linear-algebra/alternate-bases/eigen-everything) — e.g. Introduction to eigenvalues and eigenvectors; Proof of formula for determining eigenvalues; Example solving for the eigenvalues of a 2x2 matrix

## Early math review

### Counting — 2 of 4 lessons not covered

- [Counting](https://www.khanacademy.org/math/cc-kindergarten-math/cc-kindergarten-counting/kindergarten-counting) — e.g. Counting with small numbers; Counting in order
- [Counting objects](https://www.khanacademy.org/math/cc-kindergarten-math/cc-kindergarten-counting/kindergarten-count-object-topic) — e.g. Counting in pictures; Counting objects 1; Counting objects 2

### Addition and subtraction intro — 3 of 6 lessons not covered

- [Making small numbers](https://www.khanacademy.org/math/cc-kindergarten-math/cc-kindergarten-add-subtract/kindergarten-make-10) — e.g. Making 5
- [Making 10](https://www.khanacademy.org/math/cc-kindergarten-math/cc-kindergarten-add-subtract/kindergarten-making-5-9) — e.g. Getting to 10 by filling boxes; Adding to 10
- [Relate addition and subtraction](https://www.khanacademy.org/math/cc-1st-grade-math/cc-1st-add-subtract/cc-1st-add-subtract-10) — e.g. Relating addition and subtraction

### Addition and subtraction within 20 — 2 of 7 lessons not covered

- [Equal sign](https://www.khanacademy.org/math/cc-1st-grade-math/cc-1st-add-subtract/cc-1st-equal-sign) — e.g. Equal sign
- [Missing number within 20](https://www.khanacademy.org/math/cc-2nd-grade-math/cc-2nd-add-subtract-100/cc-2nd-add-sub-miss-value-prob) — e.g. Missing numbers in addition and subtraction

### Addition and subtraction within 100 — 2 of 11 lessons not covered

- [Word problems within 100](https://www.khanacademy.org/math/cc-2nd-grade-math/cc-2nd-add-subtract-100/cc-2nd-more-fewer-100) — e.g. Adding and subtracting on number line word problems; Adding two digit numbers on a number line; Subtraction word problem: tennis balls

### Measurement and data — 7 of 9 lessons not covered

- [Length and size](https://www.khanacademy.org/math/cc-1st-grade-math/cc-1st-measurement-geometry/copy-of-cc-early-math-length-intro) — e.g. Ordering by length
- [Measuring length](https://www.khanacademy.org/math/cc-2nd-grade-math/cc-2nd-measurement-data/x3184e0ec:units-of-length) — e.g. Getting a sense of meters and centimeters; Getting a sense of inches and feet; Measuring in inches
- [Comparing and estimating length](https://www.khanacademy.org/math/early-math/cc-early-math-measure-data-topic/cc-early-math-compare-estimate-length) — e.g. Comparing lengths; Estimating lengths

### Geometry — *entire unit not covered*

- [Basic shapes](https://www.khanacademy.org/math/cc-2nd-grade-math/x3184e0ec:geometry/cc-2nd-shapes) — e.g. Cousin Fal's shape collection; Recognizing shapes; Relative position
- [Properties of shapes](https://www.khanacademy.org/math/cc-2nd-grade-math/x3184e0ec:geometry/cc-2nd-shapes) — e.g. Cousin Fal's shape collection; Recognizing shapes; Shapes and angles
- [Composing shapes](https://www.khanacademy.org/math/cc-kindergarten-math/cc-kindergarten-geometry/kindergarten-composing-shapes) — e.g. Composing shapes
- [Fractions of shapes](https://www.khanacademy.org/math/cc-1st-grade-math/cc-1st-measurement-geometry/cc-1st-fractions-of-shapes) — e.g. Halves and fourths; Equal parts of circles and rectangles; Partitioning rectangles

## Arithmetic

### Add and subtract through 1,000,000 — 2 of 5 lessons not covered

- [Adding within 1,000,000](https://www.khanacademy.org/math/cc-fourth-grade-math/imp-addition-and-subtraction-2/imp-adding-multi-digit-numbers) — e.g. Relate place value to standard algorithm for multi-digit addition; Adding multi-digit numbers: 48,029+233,930
- [Subtracting within 1,000,000](https://www.khanacademy.org/math/cc-fourth-grade-math/imp-addition-and-subtraction-2/imp-subtracting-multi-digit-numbers) — e.g. Relate place value to standard algorithm for multi-digit subtraction; Multi-digit subtraction: 389,002-76,151

### Multiply and divide multi-digit numbers — 3 of 4 lessons not covered

- [Multiply with multiples of 10, 100, and 1,000](https://www.khanacademy.org/math/cc-fifth-grade-math/multi-digit-multiplication-and-division/multi-digit-multiplication-estimation) — e.g. Strategies for multiplying multiples of 10, 100 and 1000
- [Divide with multiples of 10, 100, and 1,000](https://www.khanacademy.org/math/cc-fifth-grade-math/multi-digit-multiplication-and-division/multi-digit-division-estimation) — e.g. Strategies for dividing multiples of 10, 100, and 1000

## Algebra basics

### Algebraic expressions — 2 of 7 lessons not covered

- [Writing algebraic expressions](https://www.khanacademy.org/math/cc-sixth-grade-math/cc-6th-expressions-and-variables/cc-6th-writing-expressions) — e.g. Writing basic expressions with variables; Writing expressions with variables; Writing expressions with variables & parentheses

### Graphing lines and slope — 4 of 8 lessons not covered

- [Coordinate plane](https://www.khanacademy.org/math/cc-sixth-grade-math/x0267d782:coordinate-plane/cc-6th-coordinate-plane) — e.g. Quadrants of the coordinate plane; Points and quadrants example

### Quadratics and polynomials — 1 of 9 lessons not covered

- [Factoring polynomials by taking common factors](https://www.khanacademy.org/math/algebra/x2f8bb11595b61c86:quadratics-multiplying-factoring/x2f8bb11595b61c86:intro-factoring) — e.g. Factoring with the distributive property; Taking common factor from binomial; Taking common factor from trinomial

### Equations and geometry — 2 of 5 lessons not covered

- [Equations & geometry](https://www.khanacademy.org/math/algebra-basics/alg-basics-equations-and-geometry/equations-geometry) — e.g. Equation practice with segment addition; Equation practice with midpoints; Equation practice with vertical angles
- [Triangle similarity intro](https://www.khanacademy.org/math/geometry/hs-geo-similarity/hs-geo-triangle-similarity-intro) — e.g. Intro to triangle similarity; Triangle similarity postulates/criteria; Determining similar triangles
