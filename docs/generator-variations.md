# Problem-generator variations

This is a proposal for extra question variations for every seeded Solveki topic. Each variation tests the same concept in a genuinely different way: reverse reasoning, a different representation, a context, hidden information, constraints, structure or a parameter. Changing the numbers or the wording doesn't count.

**How variations are served.** A variation is served inside its topic's existing generator, which picks a variant at random. The current question is kept as the `classic` variant. No new topics are added, so spaced-repetition grading stays per concept. The mechanics are in `backend/myapp/generators/_variants.py`.

**Status.** A ★ marks the variant to build first for its topic. All six phases have been built, with ★ variants first and a math test for each variant. About 640 variants live in the `*_variants.py` modules, one module per subject area. Not every non-★ idea below is built. In particular, many non-★ AP Precalculus and Calculus items are still open, and some catalogue items were left out because they would have needed a second topic's skill or a non-typeable answer. To see what a topic serves, run `python manage.py preview_steps <generator> --all-variants`.

## Hard constraints every variation must satisfy

- **Grading.** `myapp/answers.py` checks answers by equivalence, with these rules:
  - Equal numbers match, so 0.5 = 1/2 and 42.0 = 42.
  - A fraction matches a rounded decimal if it rounds to it, so 1/3 = 0.333.
  - Unreduced fractions are always wrong (6/8 is not accepted for 3/4).
  - Whitespace and letter case are ignored.

  Everything else must match as text. So a generator's solution stays in one canonical `_format` form, with fractions reduced, and these rules apply:
  - Prefer variations whose answer is **a single number** (int, `a/b`, or a decimal rounded to 3dp).
  - Use the existing `(x, y)` / `y = mx + b` / ASCII-inequality forms only when the concept needs them.
  - Never introduce a new list or word format.
- **Every non-integer answer** gets a format sentence in the problem. Use the `_format.py` helpers (`num`, `frac`, `frac_from`, `pair`). See the typeable-solution rules: no `\frac`/`\sqrt` in solutions.
- **One topic per question.** A variation tests only its own topic's concept. It may take several steps of that same skill, but it never needs a skill that belongs to a different seeded topic. For example, a cone-volume variant doesn't make the student find the height with Pythagoras, and a log-product-rule variant doesn't also need the quotient rule. This keeps SRS grading honest: a miss is attributed to the right topic.
- **Uniqueness.** Puzzle and constraint variants (e.g. "5 coins worth 41¢, how many dimes?") are built by picking the answer first and generating the givens from it. Random givens can produce a puzzle with no answer, several answers, or an ugly non-integer answer. The generator then brute-forces a check that exactly one answer works, and resamples if not.
- **No pictures.** Problems render as KaTeX over `$…$` segments.
  - "Graph" means the graph's features stated in words: intercepts, points, "rises 3 for every 4", a number-line description.
  - A "table" is a KaTeX `\begin{array}`. `ap_precalc_functions._table` already does this, and its tests parse it.
- **Steps.** 2–6 steps, using the variant's own numbers, ending with `s.answer(solution)`. Use rf-strings and `\%`.

## Variation archetypes (tags used in the catalogue)

| Tag | Meaning |
|---|---|
| REV | Reverse: given the result, find an input, parameter or original |
| MISS | Missing piece in an equation, table or diagram |
| CTX | Word problem / real context, including interpreting the answer (e.g. rounding a quotient up) |
| TAB | Information given as a table |
| GRAPH | Graph or number line described in words (points, intercepts, shading) |
| STR | Structure: use a relationship instead of brute computation (SAT "find 4x+6") |
| PARAM | For what k does a property hold (no solution, perpendicular, factor, …) |
| HID | Hidden information: a needed quantity is implied, not stated |
| CON | Multiple constraints pin down the answer |
| COUNT | How many solutions / integers / outcomes satisfy it |
| CMP | Compare two situations and report a value |
| EST | Bound or estimate (e.g. between which consecutive integers) |
| ERR | Misconception check (e.g. how much greater is 3^4 than 3·4) |

★ marks the highest-value variant for a topic: build it first in its phase.


## Catalogue

Each line is `[TAG] description — example → answer form`. The topic's existing question stays as the "classic" variant.

### Arithmetic facts (`lib_arith_gen.py`)

**addition**
- ★[MISS] Missing addend: $27+\square=42$ → int
- [MISS] Missing digit with regrouping: $2\square+15=42$ → digit
- [STR] Compensation: $27+15=30+\square$ → int
- [CTX] Start-unknown story: "Some birds were in a tree, 15 more came, now there are 42. How many were there at first?" → int

**subtraction**
- ★[STR] Constant difference: $42-18=44-\square$ → int
- [MISS] $\square-18=24$ and $42-\square=24$ → int
- [CTX] Compare story: "Ann has 42 cards, Ben has 18. How many more does Ann have?" → int
- [MISS] Missing digit: $4\square-18=24$ → digit

**multiplication**
- ★[STR] Distributive split: $7\times14=7\times10+7\times\square$ → int
- [STR] Doubling: "If $6\times8=48$, what is $12\times8$?" → int
- [CON] "I am a multiple of 7 between 30 and 40." → int
- [CTX] Area or equal groups: "4 shelves hold 9 books each" → int

**division**
- ★[CTX] Interpret the remainder: "45 students, vans hold 8. How many vans are needed?" → int (rounds up)
- [CTX] Quotative vs partitive: "42 cookies in bags of 6: how many bags?" / "shared among 6: how many each?" → int
- [REV] "What number divided by 6 is 7?" → int
- [STR] Fact family: "$6\times7=42$, so $42\div\square=6$" → int

**absolute_difference**
- ★[GRAPH] Number line: "points at −9 and 6. How far apart are they?" → int
- [CTX] Temperature: "low −9°, high 6°: how many degrees warmer?" → int
- [CON] "Two numbers are 15 apart. One is −9 and the other is positive. What is the other?" → int

**exponentiation**
- ★[REV] $3^{\square}=81$ → int; and $\square^4=81$ (positive base) → int
- [ERR] "How much greater is $3^4$ than $3\times4$?" → int
- [STR] Change of base: $4^3=2^{\square}$ → int
- [CTX] Doubling: "1 cell doubles every hour. How many after 6 hours?" → int

**square**
- ★[ERR] Sign and order: evaluate $-7^2$ vs $(-7)^2$ (ask one) → int
- [STR] Consecutive squares: $17^2=16^2+\square$ → int
- [CTX] "A square patio has 12 tiles per side. How many tiles?" → int

**square_root**
- ★[ERR] $\sqrt{36}+\sqrt{64}-\sqrt{36+64}$ → int (roots don't add)
- [REV] $\sqrt{n}=12$, find $n$ → int
- [CTX] "A square has area 144. Find its side." → int
- [EST] "$\sqrt{90}$ lies between which consecutive integers? Enter the smaller." → int

**cube_root**
- ★[CTX] "A cube has volume 2744 cm³. Find its edge." → int
- [REV] $\sqrt[3]{n}=14$ → int
- Negative input: $\sqrt[3]{-125}$ → int
- [STR] $\sqrt[3]{8\cdot27}$ → int

**lcm**
- ★[CTX] "Buses leave every 8 and 12 minutes, both at 9:00. In how many minutes do they next leave together?" → int
- [CTX] "Hot dogs come in 10s and buns in 8s. What is the fewest hot dogs that match buns exactly?" → int
- [CON] "Smallest number over 100 divisible by both 6 and 8" → int
- [STR] "LCM of n and 2n" / "LCM of two different primes" → int

**greatest_common_divisor**
- ★[CTX] "36 roses and 24 tulips into identical bouquets with nothing left over. What is the most bouquets?" → int
- [CTX] "Largest square tile that exactly covers a 24×36 floor" → int (side)
- [STR] "GCD of n and n + 1" → 1; "GCD of 3k and 5k" → k → int

**prime_factors**
- ★[STR] "Smallest whole number to multiply 72 by to get a perfect square" → int
- [REV] "$n=2^3\cdot3^2\cdot5$. Find n." → int
- [COUNT] "How many distinct prime factors does 360 have?" / "What is the largest prime factor of 330?" → int

**is_prime / is_composite**
- [CON] "Smallest prime greater than 90" → int
- [COUNT] "How many primes are between 20 and 40?" → int
- [CON] "Smallest odd composite number greater than 85" → int
- [STR] "Can n square tiles form only one rectangle? Answer yes or no." (prime ⇔ yes) → yes/no

**compare_fractions**
- ★[CON] "Find the whole number n with $\frac12<\frac n8<\frac34$" (generated so exactly one n works) → int
- [STR] "Which is greater, 5/9 or 4/7? Enter the greater fraction." → a/b
- [CTX] "Ana ate 3/8 of a pizza and Bo ate 2/5 of a same-size pizza. How much more did the bigger eater eat?" → a/b

**factorial**
- ★[STR] $\frac{10!}{8!}$ → int
- [REV] $n!=720$ → int
- [CTX] "How many ways can 5 books be arranged on a shelf?" → int
- [COUNT] (stretch) "How many trailing zeros does 25! have?" → int

### Arithmetic, Grades 1–5 (`arithmetic.py`)

**arith_place_value**
- ★[STR] Unusual regrouping: "4 thousands + 17 hundreds + 3 ones" → int
- [REV] Build from digits: "4 thousands, 7 hundreds, 3 tens, 8 ones" → int
- [STR] "How many tens in all are in 4738?" → 473
- [CMP] "In 7474, the first 7 is how many times the second 7?" → 100
- [CON] "Largest 4-digit number using 3, 8, 1, 5 once each" → int

**arith_rounding**
- ★[REV] "A whole number rounds to 4700 (nearest hundred). What is the smallest it could be?" (or largest) → int
- [COUNT] "How many whole numbers round to 50 to the nearest ten?" → 10
- [CTX] "Estimate 438 + 271 by rounding each to the nearest hundred" → int

**arith_add_fractions / arith_subtract_fractions / arith_add_unlike_fractions**
- ★[MISS] $\frac12+\frac{\square}{6}=\frac56$ → int (numerator)
- [REV] "What must be added to 3/8 to make 1?" → a/b
- [CON] $\frac12+\frac1n=\frac56$, find n → int
- [CTX] "Ran 1/3 mile then 1/4 mile. How far in all?" / "How much farther?" → a/b
- [GRAPH] Number-line distance between two fractions → a/b

**arith_compare_decimals**
- ★[CON] "A 2-decimal number between 3.4 and 3.5 whose hundredths digit is 7" → decimal
- [CTX] "Race times 12.45 s, 12.5 s, 12.405 s. What is the winning time?" → decimal
- [ERR] "Which is greater, 0.5 or 0.45?" (longer isn't bigger) → decimal

**arith_add_decimals / arith_subtract_decimals**
- ★[MISS] $12.5+\square=15.75$ → decimal
- [CTX] "Change from $20 after buying $7.35 and $4.80" → 2dp
- [GRAPH] Number-line distance between two decimals → decimal

**arith_multiply_decimals**
- ★[STR] "Given $25\times32=800$, find $2.5\times0.32$" → decimal
- [CTX] Price per pound × pounds; rectangle with decimal sides → decimal
- [ERR] $0.4\times0.3$ (decimal places) → decimal

**arith_divide_decimals**
- ★[STR] "Given $105\div7=15$, find $10.5\div0.7$" → int
- [REV] $\square\times0.7=10.5$ → decimal
- [CTX] Unit price: "$10.50 for 7 pens. What is the price of one?" → 2dp

**arith_order_of_operations**
- ★[CON] "Put + and × in $2\ \square\ 3\ \square\ 4$ (one of each). What is the largest result?" → int
- [MISS] $3+\square\times2=11$ → int
- [CTX] "3 packs of 4 pencils plus 2 loose pencils" → int
- [ERR] "Working left to right gives 14 for $3+4\times2$. What is the correct value?" → int

**arith_nth_multiple**
- ★[REV] "84 is which multiple of 7?" → int
- [COUNT] "How many multiples of 7 are from 1 to 100?" → int
- [CON] "Smallest multiple of 7 greater than 100" → int

**arith_powers_of_ten**
- ★[REV] $34\times10^{\square}=34000$ → int
- [CMP] "5000 is how many times 50?" → int
- [CTX] "37 boxes of 100 pencils" / "4500 cm in m" → int or decimal

**arith_length_conversion / arith_metric_unit_conversion**
- ★[CTX] "A 5 ft ribbon is cut into 4-inch pieces. How many pieces?" → int
- [STR] Mixed units: "2 m 35 cm is how many cm?" → int
- [CMP] "How much longer is 2 yd than 70 in, in inches?" → int
- [CTX] "Each batch needs 750 mL. How many full batches from a 3 L bottle?" → int

**arith_minutes_to_hours**
- ★[REV] "2 hr 15 min is how many minutes?" → int
- [CTX] "1 hr 45 min + 50 min, in minutes" → int
- [CMP] "How much longer is 150 min than 2 hr 20 min?" → int

**arith_elapsed_time**
- ★[REV] Start unknown: "A movie ended at 6:10 and lasted 1 hr 25 min. When did it start?" → H:MM
- [REV] Duration unknown: "3:40 to 5:15, in minutes" → int
- [CTX] Schedule: three activities back to back from 1:20. When does the last one end? → H:MM
- [CTX] Across noon: "10:50 a.m. to 1:20 p.m., in minutes" → int

**arith_money**
- ★[MISS] "Has $9.25 and needs $12.00. How much more?" → 2dp
- [CON] "Buys as many $1.75 items as possible with $10. How much is left?" → 2dp
- [CTX] Change from $20 → 2dp

**arith_area_of_rectangle**
- ★[REV] Area and length given, find width → int
- [STR] L-shape split into two rectangles → int
- [STR] "Double both sides. How many times larger is the area?" → 4

**arith_compare_numbers / arith_compare_three_digit**
- ★[CON] "Smallest digit for □ that makes $4\square7>459$ true" → digit
- [CON] "Largest 3-digit number from the digits 4, 7, 2" → int
- [STR] "What number is 10 more / 100 less than 472?" → int
- [STR] "3 tens 14 ones vs 4 tens 2 ones: type the greater number" → int

**arith_missing_number_sequence**
- ★[REV] Missing *first* term → int
- Decreasing sequences; [STR] "What is the rule? (the amount added each time)" → int
- [MISS] Two missing terms: enter the larger one → int

**arith_even_or_odd**
- ★[STR] "Is the sum of 37 and 48 even or odd?" / the product → word
- [CTX] "Can 17 children pair up with no one left over? yes/no" → yes/no
- [COUNT] "How many even numbers are between 11 and 25?" → int

**arith_ordinal_number**
- ★[HID] "In a line of 12, Sam is 5th from the front. Which position is he from the back?" → ordinal (8th)
- [COUNT] "How many people stand between the 3rd and the 9th?" → int

**arith_word_problem_within_20 / arith_two_step_word_problem**
- ★Change-unknown and start-unknown stories: "had 6, now has 13, how many did she get?" → int
- [CMP] Compare stories: "Ben has 6 fewer than Ann's 13" → int
- Two-step with mixed operations (×then−, ÷then+) → int
- [REV] Unknown start in a two-step story → int

**arith_add_subtract_within_1000**
- ★[STR] $472+318=470+\square$ → int
- [MISS] Missing digit → digit
- [REV] $\square-318=154$ → int

**arith_tell_time_five_min**
- ★"Quarter to 4" / "20 minutes before 5" → H:MM
- [GRAPH] "Minute hand on the 7, hour hand between 2 and 3" → H:MM
**arith_count_money_value**
- ★[CON] "Fewest coins that make 68¢" → int
- [CON] "5 coins are worth 41¢. How many are dimes?" (resampled until unique) → int
- [CTX] Change from $1 → 2dp

**arith_array_repeated_addition**
- ★[REV] "24 chairs in 4 equal rows. How many per row?" → int
- [STR] $5+5+5+5=\square\times5$ → int
- [CTX] "An array of 3 rows of 7, then 2 more rows are added" → int

**arith_equivalent_fraction**
- ★[CTX] Fraction of a set: "3/4 of a 12-slice pizza is how many slices?" → int
- Missing denominator: $\frac23=\frac{8}{\square}$ → int
- [STR] "Simplest form of 18/24" → a/b

**arith_missing_factor**
- ★[STR] Equality: $6\times\square=3\times14$ → int
- $\square\div6=7$ → int
- [CTX] "How many boxes of 6 make 42?" → int

**arith_fraction_on_number_line**
- ★[REV] "0 to 1 is cut into 8 parts. Which tick shows 3/4?" → int
- Beyond 1: "0 to 2 in 6 parts, 4th tick" → a/b
- [CTX] "Distance between two ticks" → a/b

**arith_fraction_times_whole**
- ★[REV] "2/3 of a number is 12. Find the number." → int
- [CTX] "3/4 of 20 students" → int
- [STR] $4\times\frac23=\square\times\frac13$ → int

**arith_mixed_to_improper**
- ★Reverse: "17/5 lies between which two whole numbers? Enter the smaller." → int
- [CTX] "7/4 cups: how many full cups?" → int

**arith_long_division_remainder**
- ★[CTX] Interpret the remainder. Each story asks for one int: how many vans (round up), how many full bags (round down), how many left over (the remainder).
- [REV] "A number ÷ 6 = 7 R 5. Find the number." → int

**arith_angle_addition**
- ★[STR] "BD bisects ∠ABC = 130°. Find ∠ABD." → int
- [REV] Find the whole angle from its parts → int

**arith_factor_pairs_count**
- ★[CTX] "How many different rectangles can 24 square tiles make?" → int
- [REV] "Smallest number with exactly 3 factor pairs" → int
- [STR] "How many factors does 36 have?" (perfect squares have an odd count) → int

**arith_round_decimal**
- ★[REV] "Smallest 2-decimal number that rounds to 3.5" → decimal
- [COUNT] "How many 2-decimal numbers round to 3.5?" → 10
- [CTX] Round money to the nearest dollar → int

### Pre-algebra (`prealgebra.py`, `lib_fractions_gen.py`, `lib_powers_gen.py`)

**pre_unit_rate**
- ★[CMP] Better buy: "12 oz for $3.00 or 20 oz for $4.40. What is the unit price of the better buy?" → 2dp
- [GRAPH] "A line through (0, 0) and (4, 10). What is the unit rate?" → decimal
- [TAB] Distance/time table → rate
- Complex fractions: "2/3 mile in 1/4 hour, in mph" → a/b
- [REV] "At 40 mph, how far in 2.5 h?" → int

**pre_equivalent_ratio**
- ★[HID] Part-part-whole: "Boys:girls is 2:3 and there are 30 students. How many girls?" → int
- [CON] "Ratio 3:5, and the difference is 14. Find the larger quantity." → int
- [TAB] Ratio table with a missing entry → int
- [CTX] Recipe scaling → int or a/b

**pre_solve_proportion**
- ★Unknown in a binomial: $\frac{x+1}{4}=\frac68$ → int or a/b
- Unknown in the denominator: $\frac4x=\frac69$ → a/b
- [CTX] Scale or recipe → int

**pre_integer_operations / pre_rational_operations**
- ★[CON] "Two integers have sum −2 and product −15. Find the larger one." → int
- [CTX] Elevation, temperature, debt (signed change) → int or a/b
- [MISS] $(-6)+\square=4$ → int
- [GRAPH] "Start at −3, move 8 left then 5 right" → int

**pre_absolute_value**
- ★[GRAPH] Distance between −7 and 3 on a number line → int
- [REV] "|x| = 5 and x < 0" → int
- [ERR] $|-7|-|3|$ vs $|-7-3|$ (ask one) → int
- [CTX] "How far is 47 from the target 52?" → int

**pre_one_step_inequality / pre_multi_step_inequality / alg1_linear_inequality_solve**
- ★[COUNT] "Greatest integer solution of $3x<20$" / "smallest integer solution" → int
- [CTX] Budget: "$20 + 0.5x \le 45$. What is the most minutes?" → int
- [GRAPH] "Closed circle at 5, shaded left. Write the inequality." → ASCII inequality
- [COUNT] "How many positive integers satisfy $-3<2x+1\le9$?" → int

**pre_scientific_notation_ops / product_of_scientific_notations**
- ★[CMP] "How many times greater is $6\times10^8$ than $2\times10^5$?" → int or m*10^e
- [REV] $(\square\times10^3)(2\times10^4)=8\times10^7$ → number
- [STR] "Write $45\times10^3$ in scientific notation" → m*10^e
- [CTX] Distances or populations → m*10^e

**pre_integer_exponent_rules / alg1_product_of_powers / quotient_of_power_same_base / power_of_powers**
- ★[STR] Different bases: $8^2\cdot4^3=2^{\square}$ → int
- [MISS] $2^3\cdot2^{\square}=2^{10}$; $(a^{\square})^3\cdot a^2=a^{14}$ → int
- [STR] Zero exponent: $a^5/a^5$; evaluate $2^{-3}\cdot2^5$ → int
- [CTX] "$10^9$ bytes split into $10^6$-byte files is $10^{\square}$ files" → int

**quotient_of_power_same_power / alg1_power_of_product**
- ★[STR] $\frac{12^3}{4^3}$ → 27 (evaluate the base first)
- [MISS] $(3x^2)^{\square}=81x^8$ → int
- [STR] "Coefficient of $(2x)^3$" → int

**pre_constant_of_proportionality**
- ★[TAB] Table → k (a/b)
- [GRAPH] "Line through the origin and (4, 10)" → k
- [REV] "k = 3.5 and y = 21. Find x." → int
- [CTX] Read k from $y=3.5x$ in a context → decimal

**pre_evaluate_function**
- ★[TAB] f given as a table: $f(2)+f(3)$; "for which x is f(x) = 9?" → int
- [REV] $f(x)=11$, find x → int
- [CTX] $C(n)=5n+12$ → int

**pre_slope_from_two_points**
- ★[PARAM] "(1, k) and (4, 10) lie on a line of slope 2. Find k." → int
- [TAB] Table of values → a/b
- [GRAPH] "Rises 3 for every 4 to the right" → a/b
- [CTX] Cost vs items → rate

**pre_linear_function_value**
- ★[REV] Given y, find x → int or a/b
- [TAB] Find m and b from a table, then predict → int
- [CTX] Taxi fare → 2dp

**pre_mean_absolute_deviation**
- ★[STR] "Add 5 to every value. What is the new MAD?" / "Double every value" → decimal
- [CMP] "Which of two classes' scores is more spread out? Enter that class's MAD." → decimal
- [CTX] Daily temperatures → decimal

**pre_range / pre_mode**
- ★[MISS] "The range is 15 and the minimum is 4. Find the maximum." / "3, 5, 5, 7, x has modes 5 and 7. Find x." → int
- [STR] Add 10 to every value: new range → int
- [TAB] Frequency table → int

**pre_interquartile_range**
- ★[GRAPH] Box plot described in words → IQR int
- [CON] "Q1 = 10, Q3 = 16. Using the 1.5·IQR rule, what is the smallest upper outlier?" → int
- [TAB] Frequency table → int

**pre_approximate_irrational**
- ★[COUNT] "How many integers lie strictly between $\sqrt{20}$ and $\sqrt{90}$?" → int
- [EST] Between consecutive integers: enter the smaller → int
- [REV] "Largest integer n with $\sqrt n<7.5$" → int

**pre_area_of_trapezoid**
- ★[REV] Area and both bases given, find the height (or area, height and one base, find the other base) → int or decimal
- [GRAPH] Vertex coordinates → area
- [STR] Rectangle plus triangle decomposition → int

**pre_convert_fdp**
- ★[CTX] "18 of 24 students. What percent is that?" → %
- [STR] Repeating decimals: "0.333… as a fraction" → a/b
- Percents over 100: 1.25 → % ; 0.5% → decimal

**pre_evaluate_expression**
- ★[STR] "If $2x+3=11$, what is $4x+6$?" (no solving needed) → int
- Two variables → int
- [REV] Value given, find x → int
- [CTX] Area or temperature formula → int or decimal

**pre_distributive_property**
- ★[REV] Factor out the GCF: $6x+15=\square(2x+5)$ → int
- [MISS] $3(2x+\square)=6x+15$ → int
- [STR] Mental math: $7\times98=7(100-2)$ → int

**pre_order_rational**
- ★[CON] "Which value lies between −1/2 and −1/4?" (one of the listed values) → value as shown
- "Enter the least" / "Enter the value closest to 0" → value as shown

**pre_coordinate_distance**
- ★[REV] "The point 7 units above (2, 3)" → (x, y)
- [STR] Reflect over the x-axis: distance between a point and its image → int

**pre_two_step_equation / pre_multi_step_equation / basic_algebra**
- ★[STR] "If $3x+4=19$, find $6x-1$" → int
- [CTX] "Think of a number, double it, add 3, get 19" → int
- [CTX] Consecutive integers: "three consecutive integers sum to 51. Find the largest." → int
- ★[PARAM] "For what k does $3(x-2)=3x+k$ have infinitely many solutions?" → int
- Fractional coefficient: $\frac x3+4=7$ → int

**pre_percent_change**
- ★[REV] "After a 25% increase it is 100. What was the original?" → number
- ★[STR] Successive changes: "+20% then −20%. What is the net % change?" → signed %
- [REV] "Percent change and new value given. Find the old value." → number

**pre_discount_tax_tip**
- ★[REV] "Sale price $36 after 25% off. Find the original price." → $
- [CTX] Discount then tax → $
- [CMP] "20% off or $10 off a $45 item: what is the lower price?" → $
- Two successive discounts → $

**pre_scale_length**
- ★[REV] Find the scale from a map length and an actual length → int
- [CTX] Model car at 1:24 → number

**pre_compound_probability**
- ★[CMP] "At least one" via the complement → a/b
- Without replacement → a/b
- [REV] "P(red from A) = 1/3 and P(both) = 1/12. Find P(red from B)." → a/b
- [COUNT] Size of the sample space → int

**pre_variables_both_sides**
- ★[CTX] Break-even: "Plan A $20 + 5x, Plan B $35 + 2x. At how many months are they equal?" → int
- [PARAM] "$ax+5=3x+b$ has no solution. Find a." → int
- [STR] "If $5x+2=3x+8$, find $x+1$" → int

**pre_slope_intercept_form**
- ★[REV] "$Ax+2y=8$ has slope −3. Find A." → int
- [STR] x-intercept only / y-intercept only → int or a/b

**pre_line_from_slope_point**
- ★Parallel or perpendicular to a given line, through a point → y = mx + b
- [TAB] Table → y = mx + b
- [CTX] "Starts at 12 and rises 3 per hour" → y = mx + b
- [STR] y-intercept only → number

**pre_compare_functions**
- ★Table vs words-graph: which has the greater initial value → A/B
- [CTX] Two savings plans → A/B or number

**pre_system_solution_count**
- ★[PARAM] "For what k does the system have no solution?" → int
- [GRAPH] Lines described by slope and intercept → word
- [PARAM] "For what k are there infinitely many solutions?" → int

**combine_like_terms**
- ★[STR] "Coefficient of x after simplifying $3(x+2)-2(x-5)+4x$" → int
- [MISS] $4x^2+\square x^2=9x^2$ → int
- [CTX] Perimeter of a shape with algebraic sides → expression

**common_factors / factors** (list answers stay classic)
- ★[COUNT] "How many factors does n have?" → int
- [CON] "Largest common factor less than the GCD" / "the sum of all factors" → int

**fraction_multiplication / divide_fractions**
- ★[CTX] Quotative division: "How many 3/4-cup servings are in 6 cups?" → int
- [CTX] "1/2 of 2/3 of a garden" → a/b
- [REV] $\frac23\cdot\square=\frac{8}{15}$ → a/b
- [STR] "Is the quotient of 6 ÷ 3/4 more or less than 6? Enter the quotient." → int

### Algebra I (`algebra1.py`, `lib_algebra_extra_gen.py`, `lib_powers_gen.py`, `algebra.py`)

**Shared 2×2-system pool** (`system_of_equations`, `linear_equations`, `alg1_solve_system`, `alg2_solve_system_matrix`, `intersection_of_two_lines`). Each topic keeps its classic variant and draws from this pool:
- ★[STR] Find $x+y$ without solving: $3x+2y=17$, $2x+3y=13$ → int
- ★[PARAM] "For what k does $kx+3y=5$, $4x+6y=7$ have no solution?" → int
- [CTX] Tickets, coins, mixtures → int
- [REV] "The solution is (2, −1). In $ax+3y=5$, find a." → int
- [HID] One line given by two points → (x, y)
- [TAB] One relationship given as a table → (x, y)

**expanding / alg1_multiply_binomials**
- ★[REV] "$(2x+3)(x+k)=2x^2+11x+12$. Find k." → int
- [STR] "Coefficient of x in $(2x-1)(3x+4)$" → int
- [STR] Difference of squares: $51\times49$ via $(50+1)(50-1)$ → int
- [CTX] Rectangle with sides $x+3$ and $x+5$: area expression → polynomial

**factoring**
- ★[COUNT] "For how many integers b is $x^2+bx+12$ factorable over the integers?" → int
- [REV] "$x^2+bx-48=(x+8)(x-6)$. Find b." → int
- [STR] "Larger root of $x^2+2x-48=0$" → int
- [CTX] "A rectangle has area $x^2+8x+15$ and one side $x+3$. Find the other side." → expression

**quadratic_equation**
- ★[REV] "One root of $x^2-5x+c=0$ is 3. Find the other root." → int
- [PARAM] "k that gives a double root" → int or a/b
- [CTX] "Time for a projectile to hit the ground" → 3dp
- [CON] Positive root only → number

**vertex_form**
- ★[CON] "Vertex (3, 4) and passes through (5, 12). Find a." → int
- [STR] Max or min value only → int
- [CTX] Maximum height of a projectile → number

**aroc_over_interval**
- ★[TAB] Table → a/b
- [PARAM] "AROC of $x^2$ on [1, b] is 7. Find b." → int
- [CTX] Average speed from a distance function → number

**alg1_absolute_value_equation**
- ★[PARAM] "$|x-4|=k$ has exactly one solution. Find k." → 0
- [COUNT] Number of solutions (c > 0, = 0, < 0) → int
- [STR] "Sum of the solutions of $|2x+3|=7$" → int
- [CTX] Tolerance: "50 ± 0.2 mm. What is the smallest acceptable length?" → decimal

**alg1_exponential_growth_decay**
- ★[HID] "Doubles every 4 years. What is the yearly growth factor?" → 3dp
- [TAB] Growth factor from a table → number
- [CTX] Half-life: "fraction left after 3 half-lives" → a/b
- [REV] "Rate from start and end over 1 period" → %

**alg1_evaluate_exponential**
- ★[REV] $3\cdot2^x=48$ → int
- [STR] $f(x+1)/f(x)$ → b; f(0) → a

**alg1_domain_of_function**
- ★[COUNT] "Smallest integer in the domain of $\sqrt{2x-5}$" → int
- [CTX] "Tickets cost $5 and the budget is $40. What is the largest sensible input?" → int
- [COUNT] "How many integers from −5 to 5 are not in the domain of $\frac{1}{x^2-4}$?" → int

**alg1_discriminant**
- ★[PARAM] "Largest integer c giving two real roots of $x^2+6x+c$" → int
- [PARAM] "k giving exactly one root" → number
- [GRAPH] "How many x-intercepts?" → int
- [CTX] "Does the ball reach 30 m? yes/no" → yes/no

**alg1_axis_of_symmetry**
- ★[HID] "A parabola passes through (−1, 5) and (7, 5). Find the axis." → x = 3
- [STR] From factored form $a(x-2)(x+6)$ → x = −2
- [PARAM] "The axis of $x^2+bx+1$ is x = 3. Find b." → int
- [TAB] Table with symmetric y-values → x = h

**alg1_sum_product_roots**
- ★[STR] "Sum of the reciprocals of the roots" / "sum of their squares, $s^2-2p$" → a/b
- [REV] "The roots sum to 7 and multiply to 10. Find c in $x^2+bx+c$." → int
- [PARAM] (stretch) "One root is twice the other. Find c." → int

**alg1_complete_the_square**
- ★[MISS] "$x^2+10x+\square$ is a perfect square" → int
- [STR] "Minimum value of $x^2+6x+4$" → int
- Solve by completing the square: the larger root → number

**alg1_literal_equation**
- ★[STR] "In $d=rt$, t doubles while d stays fixed. r is multiplied by what?" → a/b
- [CTX] Use the rearranged formula: "P = 30 and l = 9. Find w." → number
- Temperature, simple-interest or other formulas → number

**alg1_point_slope_form**
- ★[STR] "y-intercept of $y-3=2(x+1)$" → int
- [REV] "A point on the line has x = 5. Find its y." → int
- [TAB] Table → point-slope form

**alg1_variation**
- ★[STR] "y varies inversely with x. x triples. y is multiplied by what?" → a/b
- [TAB] Decide direct or inverse from a table, then predict → number
- [CTX] Workers/days, or Boyle's law → number
- (stretch) Combined variation $y\propto x/z^2$ → number

**alg1_simplify_rational**
- ★[MISS] $\frac{x^2+5x+6}{x+2}=x+\square$ → int
- [STR] "x-value of the hole" → int

**alg1_abs_value_inequality**
- ★[REV] "Write $-2<x<8$ as $|x-c|<r$. Find c." (or r) → int
- [COUNT] Integer solutions → int
- [CTX] "Within 3° of 70°: what is the lowest temperature?" → int

**alg1_simplify_radical**
- ★[STR] $\sqrt8+\sqrt{18}=\square\sqrt2$ → int
- [MISS] $\sqrt{72}=6\sqrt{\square}$ → int
- [REV] $3\sqrt5=\sqrt n$ → int

**alg1_negative_exponent**
- ★[STR] $\frac{1}{32}=2^{\square}$ → int
- $(2/3)^{-2}$ → a/b
- [CTX] "$10^{-3}$ m in mm" → int

### Algebra II (`algebra2.py`, `lib_algebra_extra_gen.py`, `lib_seqstats_gen.py`)

**alg2_evaluate_polynomial**
- ★[STR] "Sum of the coefficients" = p(1); "constant term" = p(0) → int
- [PARAM] "$p(x)=x^3+kx-4$ and p(2) = 10. Find k." → int
- [CTX] Volume of a box as a function of the cut → int

**alg2_polynomial_division**
- ★[PARAM] "Dividing by x − 2 leaves remainder 3. Find k." → int
- Ask one number only: "constant term of the quotient" / "the remainder" → int
- [CTX] "A box's volume is V(x) and one dimension is x + 2. Find the other dimensions' product." → polynomial

**alg2_remainder_theorem**
- ★[PARAM] "k so that x − 2 is a factor" → int
- ★[CON] (SAT-hard) "p has remainder 5 at x = 1 and 3 at x = −1. Find a." (two conditions) → int
- Divisor $2x-1$: the remainder is $p(1/2)$ → a/b
- "Is x + 3 a factor? yes/no" → yes/no

**alg2_build_polynomial_from_roots**
- ★[GRAPH] "x-intercepts 1, 2, −3 and y-intercept 12. Find the leading coefficient." → int
- [STR] One coefficient only (constant term / $x^2$ coefficient) → int
- Multiplicity: "double root at 2, single root at −1: constant term" → int

**alg2_add_complex**
- ★[CON] "$(a+3i)-(2-bi)=5+7i$. Find a + b." → int
- [MISS] $(3+2i)+z=5-i$ → a+bi
- [STR] "z plus its conjugate" → int

**multiply_complex_numbers**
- ★[PARAM] "$(2+i)(k+3i)$ is real. Find k." → int
- [STR] $(a+bi)(a-bi)$ → int
- [STR] Powers of i: $i^{23}$ → -i

**alg2_rational_exponent**
- ★[REV] $x^{2/3}=16$ → int
- Negative: $8^{-2/3}$ → a/b
- [STR] "$\sqrt[3]{x^2}=x^{\square}$" → a/b

**alg2_solve_radical_equation**
- ★Extraneous root: $\sqrt{x+7}=x+1$ → int (only the valid root)
- [COUNT] Number of real solutions → int
- Cube-root equations → int
- [CTX] Pendulum $T=2\pi\sqrt{L/9.8}$, solve for L → 3dp

**alg2_solve_exponential_log**
- ★[STR] "$2^x=5$. Find $2^{x+2}$." → 20 (no logs needed)
- Common base: $3^{x+1}=27^{x-1}$ → int; $4^x=32$ → a/b
- [CTX] Doubling time → 3dp

**alg2_evaluate_log / log**
- ★[REV] "$\log_b81=4$. Find b." / "$\log_2x=5$. Find x." → int
- Fractional and negative values: $\log_2\frac18$, $\log_48$ → int or a/b
- [EST] "$\log_250$ lies between which consecutive integers? Enter the smaller." → int

**alg2_log_product_rule / alg2_log_quotient_rule / alg2_log_power_rule**
Each topic uses only its own rule:
- Product: ★[REV] "$\log_bx=3$ and $\log_b(xy)=5$. Find $\log_by$." → int; [STR] condense $\log_68+\log_627$ (= 3) → int
- Quotient: ★[REV] "$\log_b(x/y)=1$ and $\log_bx=4$. Find $\log_by$." → int; [STR] condense $\log_354-\log_32$ (= 3) → int
- Power: ★[PARAM] "$\log_b(x^k)=12$ and $\log_bx=3$. Find k." → int; [STR] $\log_2\sqrt[3]{x}$ given $\log_2x$ → a/b

**alg2_log_change_of_base**
- ★[STR] Chain: $\log_23\cdot\log_38$ → int
- Exact: $\log_48$ → a/b
- [STR] "$\log_ab=2$. Find $\log_ba$." → a/b

**alg2_rationalize_denominator / alg2_radical_equation_conjugate**
- ★[HID] "$\sqrt{x+13}-\sqrt{x+6}=1$. Find $\sqrt{x+13}+\sqrt{x+6}$." → int (conjugate product)
- "$\frac{6}{\sqrt5-\sqrt2}=a(\sqrt5+\sqrt2)$. Find a." → int

**alg2_inverse_linear_function / alg2_inverse_nonlinear**
- ★[TAB] "f(2) = 7, so $f^{-1}(7)$ =" from a table → int
- [STR] Slope of the inverse → a/b; $f(f^{-1}(5))$ → 5
- Restricted quadratic: $f(x)=(x-2)^2+1$, x ≥ 2: find $f^{-1}(10)$ → int
- [CTX] Inverse of °C → °F → number

**alg2_function_composition**
- ★[TAB] Composition from f and g tables → int
- [REV] "$f(g(x))=11$. Solve for x." → int
- [PARAM] "$f(x)=2x+k$ and $f(g(1))=9$. Find k." → int
- Decomposition: "$h=(3x+1)^2=f(g(x))$ with $f=x^2$. Find g(2)." → int

**alg2_solve_rational_equation / alg2_rational_expression_ops**
- ★Extraneous roots: $\frac{x}{x-2}=\frac{2}{x-2}+3$ → int or "no solution"
- [CTX] Work rate: "A takes 3 h and B takes 6 h. How long together?" → number
- [CTX] Round-trip average speed → number
- Add or subtract, then evaluate at a point → a/b

**alg2_complex_division / alg2_complex_modulus**
- ★[STR] "|z| = 3 and |w| = 5. Find |zw|." / $|z^3|$ → int
- [REV] "$|a+4i|=5$ and a > 0. Find a." → int
- [GRAPH] Distance between two complex numbers → number
- Real part only of a quotient → a/b

**alg2_rational_root_list**
- ★[COUNT] Number of candidates → int
- "Is 3/2 a possible rational root? yes/no" → yes/no
- [STR] "Largest possible rational root" → int or a/b

**alg2_solve_system_three**
- ★[STR] Add the equations to get x + y + z directly → int
- [CTX] Three ticket types → int
- [REV] Solution given, find a coefficient → int

**alg2_matrix_operation**
- ★[STR] Non-commutativity: "entry (1,1) of AB − BA" → int
- [MISS] "A + X = B: an entry of X" → int
- [CTX] Price matrix × quantity → int

**int_matrix_22_determinant**
- ★[PARAM] "k making A singular" → int
- [STR] $\det(2A)=4\det A$ → int
- [GRAPH] Parallelogram area as |det| → int

**alg2_solve_polynomial_factoring**
- ★[COUNT] Real solutions of a biquadratic ($x^4-5x^2+4$ vs $x^4-3x^2-4$) → int
- [STR] Factor by grouping: the largest root → int
- [PARAM] "One root is 2. Find k, then the largest root." → int
- [STR] Sum of the roots → int

**alg2_conic_equation**
- ★[REV] From the equation: focal distance $c$ ($c^2=a^2-b^2$) → 3dp or int
- [STR] Slope of a hyperbola's asymptote → a/b
- [CON] "An ellipse through a point with one semi-axis known. Find the other." → int

**alg2_polynomial_end_behavior**
- ★[GRAPH] "Rises at both ends with 4 x-intercepts. Minimum degree?" → int
- [STR] "Maximum number of turning points" → int

**alg2_z_score / stat_z_score** (shared pool)
- ★[CMP] "Two students on different tests. Enter the higher z-score." → 3dp
- [REV] Value from z → number; σ from x, μ and z → number
- [CTX] Which is more unusual → number

**alg2_empirical_rule**
- ★[STR] "Percent above μ + σ" → 16; "between μ − 2σ and μ + σ" → 81.5
- [CTX] "Out of 1000, how many between …?" → int
- [REV] "95% lie between 40 and 60. Find σ." → int

**arithmetic_progression_term / arithmetic_progression_sum / geometric_progression**
- ★[HID] "$a_3=11$ and $a_8=31$. Find $a_{20}$." → int
- [REV] "Which term is 99?" → int; "how many terms in 7, 11, …, 99?" → int
- [CTX] Theater rows; salary increases → int
- [STR] Sum of the first n odd numbers = $n^2$ → int
- [REV] Sum given, find n → int
- Geometric: the ratio from two non-adjacent terms; a missing middle term (geometric mean) → int or a/b

**combinations / permutation**
- ★[REV] Handshakes: "45 handshakes. How many people?" → int
- [CON] Restrictions: committees with at least one X; two people must sit together → int
- [STR] $\binom{n}{r}=\binom{n}{n-r}$: "$\binom{20}{17}$" → int
- Repeated letters: arrangements of "LEVEL" → int

**set_operation** (classic list answer stays)
- ★[COUNT] Inclusion–exclusion: "30 students, 18 take art, 15 music, 7 both. How many take neither?" → int
- [MISS] Missing Venn region from totals → int
- (stretch) Three sets → int

**confidence_interval**
- ★[REV] "Interval (46.2, 53.8). Find the margin of error." / "the mean" → decimal
- [STR] "n is quadrupled. The margin of error is multiplied by what?" → a/b

### Geometry (`geometry_hs.py`, `lib_geometry_gen.py`, `lib_angles_gen.py`, `geometry.py`)

**geo_right_triangle_side**
- ★[REV] Find the angle from two sides (inverse trig) → degrees, 3dp
- [STR] "In a right triangle sin A = 0.6. Find cos B." → decimal
- [CTX] Angle of elevation, ladder, shadow → 3dp
- (stretch) [HID] Two observation points → 3dp

**geo_solve_right_triangle_pythag / pythagorean_theorem**
- ★[HID] Isosceles triangle height from its sides → int or 3dp
- [HID] Space diagonal of a box → 3dp
- [CTX] TV diagonal; ladder against a wall → number
- Converse: "Is a triangle with sides 9, 12, 15 right? yes/no" → yes/no

**geo_special_right_triangle**
- ★[CTX] Diagonal of a square; height of an equilateral triangle; side of a hexagon → 3dp
- [REV] Find the leg from the hypotenuse → 3dp

**geo_circle_equation_from_center_radius**
- ★[HID] From the endpoints of a diameter → equation
- [HID] Center and a point on the circle → equation
- [PARAM] "Is (5, 1) inside, on, or outside?" → word

**geo_circle_center_radius_from_equation**
- ★General form: "$x^2+y^2-4x+6y-3=0$. Find the radius." → int
- [PARAM] "$x^2+y^2+6x-8y+k=0$ has radius 3. Find k." → int
- [STR] Diameter from the equation → int

**geo_translate_point / geo_reflect_point / geo_rotate_point / geo_dilate_point**
- ★[REV] Pre-image from the image → (x, y)
- [REV] "Translation vector taking P to P′: enter the horizontal shift" → int
- Same-type composition: two translations; two reflections; two rotations → (x, y)
- Non-origin centers: rotate about (1, 2); dilate about (2, −1) → (x, y)
- [STR] "Length of the image segment" (isometry vs dilation) → number

**geo_inscribed_angle**
- ★[STR] Angle subtending a diameter; two inscribed angles on the same arc → int
- Cyclic quadrilateral: opposite angles → int
- Tangent–chord angle → int

**geo_conditional_probability_table**
- ★[MISS] Missing cell from the totals, then the probability → a/b
- [STR] "Are A and X independent? yes/no" → yes/no
- Joint vs marginal vs conditional (ask the one not usually asked) → a/b

**geo_compound_probability**
- ★[REV] "P(A or B) and P(A) given, independent. Find P(B)." → a/b
- "At least one of n events" → a/b; P(A and not B) → a/b

**geo_expected_value**
- ★[CTX] Fair game: "price that makes the game fair" → 2dp
- [MISS] Missing probability; missing value for a given E(X) → number
- [CTX] Insurance or raffle → 2dp

**geo_similar_triangle_side**
- ★[CTX] Shadows: "a 6 ft person casts a 4 ft shadow" → number
- [STR] Side-splitter (a line parallel to one side) → number
- [REV] Scale factor from perimeters → a/b
- (stretch) Geometric mean from the altitude to the hypotenuse → number

**geo_scale_factor_ratio**
- ★[REV] "Area ratio 9/16. What is the ratio of lengths?" / "Volume ratio 8/27. What is the ratio of areas?" → a/b
- [STR] "Small area 20 and k = 3. Large area?" → int
- [CTX] Model volumes → number

**geo_circle_segments**
- ★Secant–secant → number
- [REV] Tangent length → number
- [REV] "A whole chord from its segments" → int

**geo_regular_polygon_area**
- ★[STR] Hexagon as 6 equilateral triangles → 3dp
- [REV] Apothem from the area and the perimeter → number

**geo_composite_solid / geo_frustum_volume**
- ★[STR] Hollow solids (pipe = outer − inner); frustum = big cone − small cone → 3dp
- [CTX] "A pool fills at r per minute. How long?" → number
- [REV] Missing height → number

**geo_polygon_area_vertices**
- ★[REV] "Triangle (0, 0), (6, 0), (2, k) with area 15 and k > 0. Find k." → int
- [STR] Trapezoid from its vertices → number

**area_of_circle / circumference / area_of_circle_given_center_and_point**
- ★[HID] "A circle centered at (3, −5) is tangent to the x-axis. Find its area." → 3dp
- [REV] Radius from the area or circumference → number
- [STR] Radius doubled: the area factor → 4
- [CTX] Circumference: wheel revolutions to travel a distance → number
- Annulus; semicircle perimeter → 3dp

**sector_area / arc_length**
- ★[REV] Central angle from the sector area (or the arc) → number
- Radians: $s=r\theta$, $A=\frac12r^2\theta$ → number
- [CTX] Path of a clock-hand tip; sprinkler coverage → 3dp

**distance_two_points / midpoint_of_two_points / euclidian_norm**
- ★[REV] "Distance from (1, 2) to (4, k) is 5, with k > 2. Find k." → int
- ★[REV] Endpoint from the midpoint → (x, y)
- Norm: unknown component given the norm → int; unit-vector component → 3dp

**equation_of_line_from_two_points**
- ★[PARAM] "(1, 2), (3, 8), (5, k) are collinear. Find k." → int
- [TAB] Table → line; [STR] x-intercept only → a/b
- [CTX] Cost line from two receipts → y = mx + b

**perimeter_of_polygons**
- ★[REV] Missing side from the perimeter → int
- [REV] Regular polygon side from the perimeter → int
- [CTX] Fencing with a gate → int

**valid_triangle**
- ★[COUNT] "How many integer third sides are possible with sides 7 and 10?" → int
- [CON] Largest or smallest possible integer third side → int

**angle_regular_polygon / sum_of_polygon_angles**
- ★[REV] "n from an interior angle of 150°" / "n from an angle sum of 1440°" → int
- Exterior and central angles → number
- [MISS] Missing angle of an irregular polygon → int
- "Does a regular n-gon tile the plane? yes/no" → yes/no

**complementary_and_supplementary_angle / third_angle_of_triangle / fourth_angle_of_quadrilateral**
- Complementary/supplementary: ★[STR] "The complement of an angle is 40°. What is its supplement?" → int; [STR] "The supplement minus the complement" → 90
- Third angle: ★Isosceles base angles from the vertex angle (and the reverse); [STR] exterior angle theorem → int
- Fourth angle: ★Consecutive or opposite angles of a parallelogram; kite with equal opposite angles → int

**vector_dot**
- ★[PARAM] "k making $\langle 2,k\rangle\perp\langle 3,-6\rangle$" → int
- [STR] $u\cdot u$ for a given u → int; [CTX] Revenue as price·quantity → int

**angle_btw_vectors**
- ★[REV] Dot product from the magnitudes and the angle → number
- Angle in degrees → 3dp
- [STR] "Parallel, opposite or perpendicular vectors: the angle" → 0, π or π/2 as 3dp

**degree_to_rad / radian_to_deg**
- ★Exact form: "$150^\circ=k\pi$. Find k." → a/b
- [CTX] Wheel rotation in radians → 3dp
- Coterminal angle in [0, 360) → int

**complex_to_polar**
- ★Quadrant-aware argument (negative real part) → degrees
- Modulus only → number

**angle_sum**
- ★tan(A + B) from the triples → a/b
- [REV] Given sin(A + B), find cos B → a/b

**trig_differentiation**
- ★Value of the derivative at a special angle (e.g. $\frac{d}{dx}\tan x$ at π/4) → int
- [REV] "Where on [0, π) is the derivative of sin x equal to 0?" → as kπ, enter k → a/b

**fraction_to_decimal**
- ★[STR] "Does n/d terminate? yes/no" → yes/no
- [COUNT] Length of the repeating block → int
- [REV] Decimal → fraction → a/b

**celsius_to_fahrenheit**
- ★[STR] "Which temperature is the same in °C and °F?" → −40
- [STR] "A change of 10°C is a change of how many °F?" → 18
- [REV] F → C → decimal

### Solids (`lib_solids_gen.py`)

Pattern for every solid. Each topic gets the applicable subset:
- ★[REV] Find a dimension from the volume or surface area.
- [STR] Scaling: double r or s, and the volume factor is 8 (or the area factor is 4).
- [CTX] Paint, wrapping, tank capacity in liters, fill time.

Topic-specific:
- **volume_cube / surface_area_cube**: ★[REV] "Surface area 150. Find the edge." / "Volume 343. Find the edge." → int
- **volume_cuboid / surface_area_cuboid**: ★[REV] Missing dimension; [COUNT] "How many 2×2×2 cubes fit?" → int
- **volume_cylinder / curved_surface_area_cylinder / surface_area_cylinder**: ★[REV] Height from the volume; can label = curved area; open-top surface area → 3dp
- **volume_cone / surface_area_cone**: ★[STR] "A cylinder holds 90 cm³. What does a cone with the same base and height hold?" → int; lateral area only → 3dp
- **volume_sphere / volume_hemisphere / surface_area_sphere**: ★[REV] Radius from the volume; hemisphere total surface area = $3\pi r^2$; [CTX] how many balls of radius 1 equal one of radius 3 → int
- **volume_pyramid / surface_area_pyramid**: ★[REV] Height from the volume; base side from the surface area (slant height given) → number
- **area_of_triangle**: ★Coordinates; base–height; isosceles; [REV] height from the area → number

### Statistics, probability, finance (`statistics_gen.py`, `lib_seqstats_gen.py`, `lib_finance_gen.py`, `lib_fractions_gen.py`)

**mean_median / data_summary**
- ★[MISS] "What score on the 5th test makes the mean 85?" → int
- [STR] Add a constant: SD unchanged; multiply: SD scales → number
- [TAB] Median from a frequency table → number
- Single-quantity asks (variance only / SD only) → 3dp

**stat_five_number_summary**
- ★[GRAPH] Read a box plot from words, then compute the IQR or range → int
- One entry only (Q3) → number
- [TAB] Frequency table → number

**stat_correlation_coefficient**
- ★[STR] "r = 0.8 for (x, y). Find r for (x, −2y + 3)." → −0.8
- $r^2$ as a percent of variation explained → number

**stat_regression_line**
- ★[STR] "The line passes through $(\bar x,\bar y)$. With slope 2.5 and means 4 and 20, find the intercept." → number
- [CTX] Predict; residual of a given point → 3dp

**stat_margin_of_error / stat_standard_error_mean / stat_sample_proportion_ci**
- ★[REV] "Smallest n giving E ≤ 0.03" → int (ceiling)
- [STR] "n quadrupled: E is multiplied by what?" → 1/2
- [REV] E and $\hat p$ from the interval endpoints → 3dp
- From counts: "312 of 600 said yes" → interval

**stat_relative_frequency**
- ★[REV] "Relative frequency 0.35 out of 80. Find the count." → int
- Two-way joint relative frequency → a/b

**stat_normal_probability / stat_percentile_rank**
- ★[REV] Inverse normal: "the score at the 90th percentile" → 3dp
- [CTX] "Out of 500, how many fall between …?" → int
- [REV] "Value at the given percentile rank" → number

**stat_test_statistic**
- ★"Reject H₀ at α = 0.05 (two-sided)? yes/no" → yes/no
- [REV] "What sample mean gives z = 2?" → number

**stat_discrete_variance / geo_expected_value**
- ★[STR] Var(2X + 3) = 4 Var(X) → number
- [MISS] Missing probability → decimal; SD → 3dp

**stat_counting_probability / dice_sum_probability**
- ★[STR] "Which sum is most likely with 2 dice?" → 7
- [COUNT] Number of outcomes for a sum → int
- "At least one red" via the complement → a/b
- Difference of two dice → a/b

**stat_odds_probability**
- ★[REV] Odds → probability → a/b
- Odds against → a:b

**binomial_distribution**
- ★"At least one / at most two" → 3dp
- [STR] Expected count np → number
- [REV] "n from the mean and p" → int

**conditional_probability**
- ★[HID] Bayes from rates: "1% have it, the test is 95% accurate…" → 3dp
- Two-way table version → 3dp

**percentage / percentage_difference / percentage_error**
- ★[REV] "18% of x is 13.14. Find x." / "a is what percent of b?" → number
- [CTX] Tip or test scores → number
- [REV] "Observed value from the percent error and the exact value" (two answers, so ask for the larger) → number

**simple_interest / compound_interest**
- ★[REV] Rate, time or principal from the others → number
- Monthly compounding → 2dp
- [COUNT] "First whole year the balance exceeds $2000" → int

**profit_loss_percent**
- ★[REV] Selling price from the cost and the profit %; cost from the selling price → 2dp
- [CTX] "Marked up 40%, then sold at 20% off. What is the profit %?" → number

### Precalculus (`precalculus.py`)

**pc_law_of_sines**
- ★[COUNT] Ambiguous case: "How many triangles have a = 7, b = 10, A = 35°?" → 0/1/2
- [REV] Find an angle (acute) → 3dp
- [CTX] Surveying a river width → 3dp

**pc_law_of_cosines_side**
- ★[REV] Angle from SSS → 3dp
- [CTX] Navigation: two ships diverging → 3dp
- [STR] "Is a triangle with sides 5, 7, 10 obtuse? yes/no" → yes/no

**pc_oblique_triangle_area**
- ★[REV] Missing side from the area → number
- SSS with Heron → 3dp
- [REV] Acute angle from the area → 3dp

**pc_inverse_trig**
- ★[STR] Range restriction: $\arcsin(\sin150^\circ)$ → 30
- Composition: $\sin(\arccos\frac35)$ → a/b
- Radians as kπ: enter k → a/b

**pc_double_angle / pc_half_angle_values / pc_sum_difference_values**
- ★[STR] Recognize the identity: $2\sin15^\circ\cos15^\circ$; $\cos80\cos20+\sin80\sin20$ → a/b
- Quadrant signs: "sin x = 3/5 with x in QII. Find sin 2x." → a/b
- [REV] "cos 2x = 7/25. Find $\sin^2x$." → a/b
- Exact half-angle from a triple → a/b

**pc_solve_trig_equation / pc_trig_quadratic**
- ★[COUNT] "How many solutions does sin 2x = 1/2 have on [0°, 360°)?" → int
- [STR] Sum of all solutions → int
- Identity substitution: $2\cos^2x+\sin x=1$ → list of degrees (classic format)
- Multiple angle: "$\tan 3x=1$ on [0°, 180°): the smallest solution" → int

**pc_polar_to_rectangular / pc_rectangular_to_polar**
- ★Negative r; QIII angles → (x, y)
- [STR] "Give another polar form of (4, 30°) with r < 0: enter θ in [0, 360)" → int

**pc_finite_geometric_sum / pc_sigma_arithmetic_sum / pc_recursive_sequence_term**
- ★[REV] n from the sum; the upper limit of a sigma sum → int
- [CTX] Salary with 5% raises: total over 10 years → 2dp
- ★[STR] Long-run value: "$a_n=0.5a_{n-1}+10$. What does it approach?" → 20
- [REV] $a_1$ from $a_4$ → int

**pc_sequence_limit**
- ★Unequal degrees: the limit is 0 → int
- [CTX] Long-run average cost $C(n)/n$ → number

**pc_vector_add / pc_orthogonal_projection**
- ★[CTX] Boat in a current: ground speed (magnitude of the resultant) → 3dp
- [REV] "Solve u + v = w for v" → (x, y)
- [CON] Linear combination: "$au+bv=w$. Find a." → int
- Projection: the vector-projection component; zero projection ⇒ find k → number

**pc_parametric_to_rectangular**
- ★[STR] Slope only; y-intercept only → number
- Quadratic parameter: $x=t+1$, $y=t^2$ → equation

**pc_unit_circle_point / _sin / _cos / _tan / pc_reciprocal_trig_values**
- ★[HID] "sin θ = 3/5 with θ in QII. Find cos θ." → a/b
- Large coterminal angles: sin 1110° → number
- [REV] "The angle in [0, 2π) with cos θ = −1/2 and sin θ < 0, as kπ: enter k" → a/b
- [REV] "sec θ = 2 with θ in QIV. Find sin θ." → 3dp

**pc_simplify_trig_identity**
- ★[STR] (SAT-hard) "sin x − cos x = 1/2. Find sin x cos x." → 3/8
- Evaluate the simplified form at an angle → number

**Rational-function family** (`pc_rational_vertical_asymptotes`, `_zeros`, `_holes`, `_horizontal_asymptote`, `_slant_asymptote`, `_y_intercept`, `pc_rational_inequality`). Each topic gets its own ★:
- VA ★[PARAM] "$\frac{x-1}{x^2+bx+10}$ has a VA at x = 2. Find b." → int; [COUNT] number of VAs → int
- Zeros ★[COUNT] "How many zeros?" when one cancels as a hole → int
- Holes ★[PARAM] "$\frac{x^2+kx-6}{x-2}$ has a hole. Find k." (then its y-value) → int
- HA ★[PARAM] "HA y = 3 for $\frac{kx^2+1}{x^2-4}$" → int; [STR] "Where does f cross its HA?" → number
- Slant: [STR] "y-intercept of the slant asymptote" → int
- y-intercept: [REV] "f(0) = 2. Find a." → int
- Inequality: ★[COUNT] "How many integers satisfy $\frac{x-1}{x+2}\le0$?" → int

**pc_sinusoid_features**
- ★[REV] Max 11 and min 3 → amplitude and midline (ask one) → int
- [TAB] One period as a table → the period → int
- [STR] Maximum value of $3\sin(2x)+5$ → int

**pc_binomial_term**
- ★Constant term of $(x+\frac1x)^6$ → int
- [STR] Sum of the coefficients = $(a+b)^n$ → int
- [REV] "The coefficient of $x^2$ in $(1+kx)^5$ is 90. Find k > 0." → int

**pc_de_moivre**
- ★[STR] "Smallest positive n with $z^n$ real" → int
- Argument of $z^n$ in [0, 360) → int
- Modulus of each cube root → 3dp

**pc_partial_fractions**
- ★[STR] A + B → int
- Three linear factors: one coefficient → int or a/b

**pc_polar_rectangular_equation**
- ★[STR] "Radius of $r=6\sin\theta$" → 3; the center → (x, y)

### AP Precalculus (`ap_precalc_functions.py`, `ap_precalc_matrices.py`, `ap_precalc_trig.py`)

- **pc_change_in_tandem**: ★[TAB] Give f's average rates of change and ask about concavity; [GRAPH] Features described in words → words
- **pc_second_differences**: ★[MISS] Missing middle table entry → int; [PARAM] "The second difference is 6, so a = ?" → int
- **pc_degree_from_differences**: ★[STR] Leading coefficient = $\Delta^n/n!$ → int or a/b; next table value → int
- **pc_complex_conjugate_zeros**: ★[COUNT] "Degree 5 with 2 nonreal zeros. Maximum number of real zeros?" → int; [REV] "Minimum degree given zeros 2, 1 + i and 3i" → int
- **pc_even_odd_function**: ★[MISS] "f is odd and f(3) = 7. Find f(−3)." → int; [PARAM] "k making $x^4+kx^3+2$ even" → 0; [STR] "$f(x)+f(-x)$ for odd f" → 0
- **pc_function_transformation**: ★[REV] Pre-image point → (x, y); [STR] New maximum value or new zero after a transformation → number
- **pc_identify_model**: ★[STR] "The table is exponential. What is the constant ratio?" (or linear: the constant difference) → number
- **pc_quadratic_model_predict**: ★[STR] Time of the maximum → number; [REV] "When does it reach a given value?" (later time) → number
- **pc_exponential_from_two_points**: ★[CTX] Half-life from two measurements → 3dp; percent rate → number
- **pc_rewrite_exponential**: ★[CTX] Monthly factor from an annual rate → 3dp; [CMP] effective rates → number
- **pc_residual**: ★[REV] Actual value from the residual → number
- **pc_inverse_exponential**: ★[CTX] "Time to reach a value" → number; [TAB] → int
- **pc_log_function_features**: ★[REV] "Find a so that f passes through (5, 3)" → int; [TAB] → number
- **pc_solve_log_equation**: ★[COUNT] Number of valid solutions → int; mixed bases → int
- **pc_exp_log_inequality**: ★[COUNT] Smallest integer solution → int; [CTX] "When does it first exceed …?" → int
- **pc_log_model_context**: ★[CMP] "Magnitude 7 vs 5. How many times stronger?" → 100; [REV] intensity from dB → m*10^e
- **pc_semilog_model**: ★[CTX] Predict y from the semi-log line → 3dp; growth factor from the slope → 3dp
- **pc_periodic_values**: ★Negative inputs (f(−13)); [STR] sum of one period's values times k → int
- **pc_sinusoidal_model**: ★[REV] First time the height reaches h → 3dp
- **pc_sinusoid_transformations**: ★[REV] Find the dilation factor from a stated new period or amplitude → number
- **pc_tangent_features**: ★[COUNT] Vertical asymptotes in an interval → int
- **pc_trig_inequality**: ★[STR] "Total length (in degrees) of the solution set" → int
- **pc_polar_graph_features**: ★[COUNT] "How many times does $r=2\sin3\theta$ pass through the pole on [0, π)?" → int; θ at the maximum r → number
- **pc_polar_rate_of_change**: ★[CMP] Which interval has the faster average rate (enter its rate) → 3dp
- **pc_parametric_position**: ★[REV] "t when the particle is at (7, 6)" → int; [CON] "t when it crosses the x-axis" → int
- **pc_parametric_rate_of_change**: ★[STR] Average speed (distance/time) for a linear motion → 3dp
- **pc_parametric_circle_line**: ★[REV] "Find r so one revolution takes 2π" / "the segment's direction vector component" → int
- **pc_implicit_curve_points**: ★[COUNT] "How many points on the curve have x = 3?" → int
- **pc_parametrize_ellipse**: ★[REV] Semi-axes from the parametrization → equation coefficient → int
- **pc_classify_conic**: ★[PARAM] "k making $kx^2+4y^2-8x=5$ a circle" → int; [STR] sign of $B^2-4AC$ → word
- **pc_vector_valued_function**: ★[REV] "t when the x-component equals 9" → int; average velocity vector component → number
- **pc_inverse_matrix_entry**: ★[PARAM] "k making A non-invertible" → int; [STR] $\det(A^{-1})$ → a/b; [REV] "An entry of A, given $A^{-1}$" → int
- **pc_matrix_transform_point**: ★[REV] Pre-image → (x, y); [REV] "a matrix entry from a given mapping" → int
- **pc_matrix_composition**: ★[STR] "Do AB and BA send (1, 0) to the same point? Enter the x-coordinate of AB(1,0) − BA(1,0)" → int
- **pc_markov_transition**: ★[STR] Steady-state count → int; [REV] "How many were at A last week?" → int

### Calculus (`calculus.py`, `lib_algebra_extra_gen.py`, `lib_seqstats_gen.py`)

**calc_limit_rational / calc_limit_conjugate / pc_sequence_limit**
- ★[PARAM] "$\lim_{x\to2}\frac{x^2+kx-6}{x-2}$ exists. Find the limit." (k is hidden) → int
- [TAB] Limit from a table approaching the point → number
- Limits at infinity; $\sqrt{x^2+ax}-x\to a/2$ → a/b

**calc_derivative_polynomial / power_rule_differentiation**
- ★[REV] "Where is the tangent horizontal?" / "Where does f′(x) = 5?" → number
- Slope at a point → int

**calc_product_rule / calc_quotient_rule / calc_chain_rule**
- ★[TAB] AP-style table of f, g, f′, g′: $(fg)'(2)$, $(f/g)'(2)$, $(f\circ g)'(2)$ → int or a/b
- [CTX] Marginal average cost → number

**calc_derivative_exp_log_trig**
- ★[REV] "Where is f′ = 0?" for $3e^{2x}-6x$ (no product rule needed) → int
- [TAB] With $e^{g(x)}$ → number

**calc_higher_order_derivative**
- ★[STR] $\frac{d^5}{dx^5}x^5$ → 120; acceleration from position → int

**calc_tangent_line**
- ★[STR] Linear approximation: $f(2.1)\approx$ → 3dp
- [PARAM] "The tangent at x = a passes through the origin. Find a > 0." → int
- [REV] "The point where the tangent has slope m" → x

**calc_extrema**
- ★[CTX] Optimization: open-top box, fencing against a wall → number
- Absolute max on a closed interval (check the endpoints) → int
- [PARAM] "k making x = 2 a critical point" → int

**calc_inflection_point / calc_concavity_interval**
- ★[PARAM] "k for an inflection at x = 1" → int
- [TAB] Sign of f″ from a table → x
- y-coordinate of the inflection point → number

**calc_definite_integral_poly / definite_integral**
- ★[STR] Properties: "$\int_1^5f=7$, $\int_1^3f=2$, so $\int_3^5(2f+1)$ =" → int
- [GRAPH] Area under a piecewise-linear graph described by its vertices → number
- [PARAM] "$\int_0^kx\,dx=8$. Find k." → int

**calc_indefinite_integral_poly / power_rule_integration**
- ★Initial value: "F′ = …, F(0) = 3. Find F(2)." → int or a/b

**calc_usub_integral**
- ★[STR] "Rewrite with u-limits: what is the upper u-limit?" → int; indefinite, then evaluate → a/b

**calc_area_between_curves**
- ★[HID] Find the intersections first (they aren't given) → a/b
- [PARAM] "The line y = k splits the area in half" (stretch) → 3dp

**calc_average_value**
- ★[REV] "c where f(c) equals the average value" → 3dp
- [CTX] Average temperature over a day → number

**calc_riemann_sum / calc_trapezoidal_rule**
- ★[TAB] Unequal subintervals from a table (AP-style) → number
- Midpoint sum → number
- [STR] "f is increasing: is a left sum an over- or under-estimate?" → word

**calc_implicit_differentiation**
- ★[HID] "At the point with x = 3 and y > 0" (y must be found) → a/b
- Points with a horizontal tangent: the x-value → number

**calc_particle_motion**
- ★Total distance vs displacement → number
- "Speeding up at t = 1? yes/no" → yes/no
- [TAB] Velocity table → displacement estimate → number

**calc_volume_revolution**
- ★Square cross-sections → a/b
- Revolve about the y-axis (shells or washers) → kπ

**calc_lhopital**
- ★∞/∞ forms; [PARAM] "k making $\lim\frac{\sin kx}{x}=5$" → int

**calc_limit_definition_derivative**
- ★[STR] Recognize the limit: $\lim_{h\to0}\frac{(2+h)^3-8}{h}$ → 12

**calc_integration_by_parts**
- ★Repeated: $\int_0^1x^2e^x\,dx$ → 3dp

**calc_related_rates**
- ★New contexts: cone filling, shadow length, balloon → number

**calc_mvt_find_c**
- ★Rolle's theorem; [TAB] "Must f′ = 2 somewhere on (1, 4) given the table? yes/no" → yes/no

**calc_separable_ode**
- ★[REV] k from two measurements → 3dp
- "Time to reach a value"; Newton's cooling → 3dp

**calc_taylor_coefficient**
- ★[REV] $f^{(n)}(0)=n!\,c_n$ → int
- Substitution: the coefficient of $x^3$ in $e^{2x}$ → a/b
- Approximate $e^{0.1}$ with a degree-2 polynomial → 3dp

---

