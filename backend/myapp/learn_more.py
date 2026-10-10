"""Default "Learn more" video links for each topic.

Every practice card offers a "Learn more" link to a video that teaches its
topic. The link the card shows is ``Topic.learn_more_url`` in the database, which
admins can change from the Django admin. This module holds the curated
*defaults*: ``LEARN_MORE_VIDEOS`` maps a topic's stable ``generator_name`` to the
YouTube ID of a video that teaches it — a Khan Academy video wherever one exists
(matched from the Khan Academy catalog in docs/khan_academy_math_catalog.md).

seed_topics writes these defaults into topics whose link is still blank, so new
topics get a link and an admin's edits are never overwritten. test_learn_more
guards that every seeded topic has a default.
"""

# generator_name -> YouTube video ID; the comment is the video's title.
LEARN_MORE_VIDEOS = {
    # Grade 1
    "addition": "fsTD_jqseBA",  # Intro to addition
    "subtraction": "AO9bHbUdg-M",  # Intro to subtraction
    "arith_place_value": "wx2gI8iwMCA",  # Intro to place value
    "arith_compare_numbers": "nFsQA2Zvy1o",  # Greater than and less than symbols
    "arith_missing_number_sequence": "1AqkBdCBm9o",  # Missing numbers between 0 and 120
    "arith_even_or_odd": "vZ9nrNpScu4",  # Understanding even and odd numbers visually
    "arith_ordinal_number": "-IAIrsUIcUo",  # Ordinal Numbers (Tutoring Hour)
    "arith_word_problem_within_20": "SfgD7Sm08ns",  # Addition and subtraction word problems: gorillas
    # Grade 2
    "arith_minutes_to_hours": "DLno3b-Xsmo",  # Converting units: minutes to hours
    "arith_elapsed_time": "PCPmpPV9KR0",  # Time differences example
    "arith_money": "AVSaip4ZQ7U",  # Mia's Mighty Magic Shop—Solving Money Word Problems (MightyOwl)
    "arith_add_subtract_within_1000": "d3109sV6izY",  # Adding 3-digit numbers (no regrouping)
    "arith_tell_time_five_min": "NjJFJ7ge_qk",  # Telling time (labeled clock)
    "arith_count_money_value": "pJ8KwRztfF0",  # Counting American coins
    "arith_array_repeated_addition": "IRjLEJWVtLQ",  # Adding with arrays
    "arith_compare_three_digit": "9Jg5S7F2SMQ",  # Comparing whole numbers
    # Grade 3
    "multiplication": "NVhA7avdTAw",  # Introduction to multiplication
    "division": "mGvunan-I-Q",  # Division as equal groups
    "perimeter_of_polygons": "sJmLjUj_h68",  # Perimeter of a shape
    "arith_rounding": "jvp0mtr1kFM",  # Rounding to nearest 10 and 100
    "arith_area_of_rectangle": "mu3HHCdYYtY",  # Transitioning from unit squares to area formula
    "arith_equivalent_fraction": "-YpEkExjq2E",  # Creating equivalent fractions
    "arith_missing_factor": "TqAtt3g6Tkc",  # Unknowns with multiplication and division
    "arith_fraction_on_number_line": "Z0WsfO-RI8Y",  # Fractions on a number line
    "arith_two_step_word_problem": "sG2FX1ikNKQ",  # Setting up 2-step word problems
    # Grade 4
    "compare_fractions": "zRjLZROI7wc",  # Comparing fractions 1 (unlike denominators)
    "fraction_to_decimal": "4LvGU1a9Z5Q",  # Rewriting fractions as decimals
    "is_prime": "mIStB5X4U8M",  # Prime numbers
    "is_composite": "3h4UK62Qrbo",  # Recognizing prime and composite numbers
    "factors": "vcn2ruTOwFo",  # Finding factors of a number
    "arith_add_fractions": "zkJ1gOrYhEg",  # Adding fractions with unlike denominators introduction
    "arith_subtract_fractions": "SMshimc16LM",  # Subtracting fractions with unlike denominators introduction
    "arith_compare_decimals": "EX9CdUAMpgE",  # Comparing decimals (tenths and hundredths)
    "arith_add_decimals": "6NBkb98nFOM",  # Adding decimals with ones, tenths and hundredths
    "arith_subtract_decimals": "o31cLUkS23E",  # Subtracting decimals: 9.57-8.09
    "arith_nth_multiple": "U5L_aaQ6pYQ",  # Identifying multiples
    "arith_fraction_times_whole": "4PlkCiEXBQI",  # Multiplying unit fractions and whole numbers
    "arith_mixed_to_improper": "xkg7370cpjs",  # Writing mixed numbers as improper fractions
    "arith_long_division_remainder": "NcADzGz3bSI",  # Long division with remainders: 2292÷4
    "arith_angle_addition": "M7NVKImDqGg",  # Decomposing an angle
    "arith_factor_pairs_count": "KcKOM7Degu0",  # Understanding factor pairs
    # Grade 5
    "fraction_multiplication": "CTKMK1ZGLuk",  # Multiplying 2 fractions: 5/6 x 2/3
    "divide_fractions": "tnkPY4UqJ44",  # Dividing fractions: 3/5 ÷ 1/2
    "volume_cube": "ZqzAOZ9pP9Q",  # Volume of triangular prism & cube
    "volume_cuboid": "I9efKVtLCf4",  # Volume of a rectangular prism
    "arith_multiply_decimals": "005032IwRME",  # Understanding decimal multiplication
    "arith_order_of_operations": "eoYThjIAhOc",  # Order of operations introduction
    "arith_powers_of_ten": "Xvsqv2oO2ac",  # Introduction to powers of 10
    "arith_length_conversion": "9iulv2QvKwo",  # Converting metric units of length
    "arith_add_unlike_fractions": "zkJ1gOrYhEg",  # Adding fractions with unlike denominators introduction
    "arith_round_decimal": "_MIn3zFkEcc",  # Worked example: Rounding decimals to nearest tenth
    "arith_metric_unit_conversion": "mI84WDfhuYA",  # Converting units: metric distance
    "arith_divide_decimals": "bIRwzhhBzEU",  # Dividing a decimal by a whole number example
    # Grade 6
    "absolute_difference": "t4xOkpP8FgE",  # Absolute value as distance between numbers
    "exponentiation": "XZRQhkii0h0",  # Intro to exponents
    "square": "XZRQhkii0h0",  # Intro to exponents
    "percentage": "-lUEWEEpmIo",  # Percent of a whole number
    "greatest_common_divisor": "jFd-6EPfnec",  # Greatest common factor explained
    "lcm": "znmPfDfsir8",  # Least common multiple
    "prime_factors": "ZKKDTfHcsG0",  # Prime factorization
    "common_factors": "bLTfBvkrfsM",  # Greatest common factor examples
    "combine_like_terms": "CLWpkv6ccpA",  # Intro to combining like terms
    "area_of_triangle": "7N5orPxUoGo",  # Finding area of triangles
    "surface_area_cube": "1iSBNSYhvIU",  # Surface area of a box (cuboid)
    "surface_area_cuboid": "1iSBNSYhvIU",  # Surface area of a box (cuboid)
    "mean_median": "h8EYEJ32oQ8",  # Statistics intro: Mean, median, & mode
    "pre_unit_rate": "fpjXtpg_isc",  # Rate problems
    "pre_equivalent_ratio": "eb-GHXCqkhQ",  # Equivalent ratios
    "pre_integer_operations": "NQSN00zL5gg",  # Adding & subtracting negative numbers
    "pre_rational_operations": "nhJ60MCLeCU",  # Adding and subtracting fractions with negatives
    "pre_absolute_value": "r6hS_8nm1jM",  # Absolute value examples
    "pre_one_step_inequality": "PNXozoJWsWc",  # One-step inequalities examples
    "pre_mean_absolute_deviation": "GdIkEngwGNU",  # Mean absolute deviation (MAD)
    "pre_interquartile_range": "qLYYHWYr8xI",  # Interquartile range (IQR)
    "pre_range": "7DtWXEPB_AI",  # Finding the range and mid-range
    "pre_mode": "h8EYEJ32oQ8",  # Statistics intro: Mean, median, & mode
    "pre_convert_fdp": "-gB1y-PMWfs",  # Converting percents to decimals & fractions example
    "pre_evaluate_expression": "AJNDeVt9UOo",  # Evaluating an expression with one variable
    "pre_distributive_property": "Jp25LHI9wII",  # Distributive property with variables
    "pre_order_rational": "i1i2_9wg6N8",  # Ordering rational numbers
    "pre_coordinate_distance": "PC_FoyewoIs",  # Coordinate plane word problem examples
    "pre_area_of_trapezoid": "uEIoh8uWs1U",  # Area of quadrilateral with 2 parallel sides
    # Grade 7
    "basic_algebra": "_y_Q3_B2Vh8",  # Intro to two-step equations
    "complementary_and_supplementary_angle": "BTnAlNSgNsY",  # Complementary & supplementary angles
    "third_angle_of_triangle": "6s1CI3uuhko",  # Angles in a triangle sum to 180° proof
    "fourth_angle_of_quadrilateral": "BoQgG_TYAG8",  # The sum of interior angles of a quadrilateral (Khan Academy India - English)
    "area_of_circle": "ZyOhRgnFmIY",  # Area of a circle
    "circumference": "jyLRpr2P0MQ",  # Radius, diameter, circumference & π
    "area_of_circle_given_center_and_point": "ZyOhRgnFmIY",  # Area of a circle
    "surface_area_cone": "9w6qYXatwkM",  # Surface area of a cone
    "surface_area_cylinder": "gL3HxBQyeg0",  # Cylinder volume & surface area
    "curved_surface_area_cylinder": "gL3HxBQyeg0",  # Cylinder volume & surface area
    "surface_area_pyramid": "ODNCH3gSKdA",  # Surface area word problem example
    "simple_interest": "Rmol9IzSDXk",  # Intro to simple interest (Khan Academy India - English)
    "profit_loss_percent": "74XuR3vPvME",  # Finding profit percent (Khan Academy India - English)
    "celsius_to_fahrenheit": "tC1SfxRvtmM",  # Evaluating expressions with variables: temperature
    "percentage_difference": "95euqZnC2KU",  # Percentage Change and Percentage Difference (Meaghan Woodland)
    "percentage_error": "WQLcC5SpbYY",  # Finding percent error
    "dice_sum_probability": "hA8VmhkKEJo",  # Theoretical probability distribution example: tables
    "pre_solve_proportion": "GO5ajwbFqVQ",  # Worked example: Solving proportions
    "pre_multi_step_inequality": "xOxvyeSl0uA",  # Multi-step inequalities
    "pre_constant_of_proportionality": "rj7DweP8e58",  # Identifying the constant of proportionality from equation
    "pre_two_step_equation": "_y_Q3_B2Vh8",  # Intro to two-step equations
    "pre_multi_step_equation": "YZBStgZGyDY",  # Equations with parentheses
    "pre_percent_change": "e1Cd0XL5OEs",  # Percent word problem: magic club
    "pre_discount_tax_tip": "jb_RwR_Eso4",  # Percent word problems: tax and discount
    "pre_scale_length": "XUOPGqKGbjk",  # Scale drawings
    "pre_compound_probability": "6zWPgvEMVlE",  # Probability of a compound event
    # Grade 8
    "square_root": "mbc3_e5lWw0",  # Intro to square roots
    "cube_root": "87_qIofPwhg",  # Intro to cube roots
    "product_of_scientific_notations": "xxAFh-qHPPA",  # Multiplying in scientific notation example
    "pythagorean_theorem": "AA6RfgP-AHU",  # Intro to the Pythagorean theorem
    "volume_cylinder": "gL3HxBQyeg0",  # Cylinder volume & surface area
    "volume_cone": "hC6zx9WAiC4",  # Volume of a cone
    "volume_sphere": "IelS2vg7JO8",  # Volume of a sphere
    "volume_hemisphere": "IelS2vg7JO8",  # Volume of a sphere
    "surface_area_sphere": "IZ4DpWYO3kY",  # Surface area of sphere: computation and sense of formula (Khan Academy India - English)
    "system_of_equations": "uzyd_mIJaoc",  # Systems of equations with substitution: 2y=x+7 & x=y-4
    "linear_equations": "vA-55wZtLeE",  # Solving systems of equations by elimination
    "pre_scientific_notation_ops": "497oIjqRPco",  # Multiplying & dividing in scientific notation
    "pre_integer_exponent_rules": "CZ5ne_mX5_I",  # Multiplying & dividing powers (integer exponents)
    "pre_evaluate_function": "Id6UovYjd-M",  # Worked example: Evaluating functions from equation
    "pre_slope_from_two_points": "WkspBxrzuZo",  # Worked example: slope from two points
    "pre_linear_function_value": "IL3UCuXrUzE",  # Intro to slope-intercept form
    "pre_approximate_irrational": "Lh7NMBPFVZw",  # Approximating square roots
    "geo_translate_point": "SxxzfojT1Pw",  # Translating points
    "geo_reflect_point": "F77xiSlCehI",  # Reflecting points
    "geo_rotate_point": "0NYbQPcdxg8",  # Rotating points
    "geo_dilate_point": "N0_HfmxdbCg",  # Dilating points
    "pre_variables_both_sides": "f15zA0PhSek",  # Intro to equations with variables on both sides
    "pre_slope_intercept_form": "V6Xynlqc_tc",  # Converting to slope-intercept form
    "pre_line_from_slope_point": "AqFwKecNaTk",  # Slope-intercept equation from slope & point
    "pre_compare_functions": "fZO-JylMFqY",  # Comparing linear functions: equation vs. graph
    "pre_system_solution_count": "ogEddosP1G8",  # Number of solutions to a system of equations algebraically
    # Algebra I
    "power_of_powers": "SwqOrUWzDY8",  # Exponent properties with parentheses
    "quotient_of_power_same_base": "AR1uqNbjM5s",  # Exponent properties with quotients
    "quotient_of_power_same_power": "dC1ojsMi1yU",  # Powers of products & quotients (integer exponents)
    "surds_comparison": "KibTbfkoPTs",  # Comparing irrational numbers with radicals
    "expanding": "Xy8NKUoyy98",  # Multiplying binomials intro
    "factoring": "D3a8NnpQ2vU",  # Factoring quadratics as (x+a)(x+b)
    "quadratic_equation": "i7idZfS8t8w",  # The quadratic formula
    "intersection_of_two_lines": "5a6zpfl50go",  # Systems of equations with graphing
    "equation_of_line_from_two_points": "XMJ72mtMn4Y",  # Slope-intercept equation from two points
    "compound_interest": "Rm6UdfRs3gw",  # Compound interest introduction
    "arithmetic_progression_sum": "cYw4MFWsB6c",  # Arithmetic series intro
    "arithmetic_progression_term": "ViLt2WI0XSg",  # Explicit formulas for arithmetic sequences
    "geometric_progression": "pXo0bG4iAyg",  # Intro to geometric sequences
    "vertex_form": "_QqhuLixNEk",  # Vertex form introduction
    "alg1_absolute_value_equation": "6KrKv4Z-aH4",  # Solving absolute value equations
    "alg1_product_of_powers": "zM_p7tfWvLU",  # Exponent properties with products
    "alg1_power_of_product": "dC1ojsMi1yU",  # Powers of products & quotients (integer exponents)
    "alg1_negative_exponent": "JnpqlXN9Whw",  # Negative exponents
    "alg1_exponential_growth_decay": "x9a73iHv06U",  # Constructing exponential models: percent change
    "alg1_evaluate_exponential": "ccyZpjKvJV8",  # Evaluating expressions like 5x² & ⅓(6)ˣ
    "alg1_domain_of_function": "4ZWbeESjv4M",  # Examples finding the domain of functions
    "alg1_discriminant": "XUvKjC21fYU",  # Using the quadratic formula: number of solutions
    "alg1_axis_of_symmetry": "dfoXtodyiIA",  # Vertex & axis of symmetry of a parabola
    "alg1_sum_product_roots": "kBSj35rik8w",  # How To Find The Sum and Product of the Roots of a Quadratic Equation - Algebra (The Organic Chemistry Tutor)
    "alg1_linear_inequality_solve": "SgKBBUFaGb4",  # Inequalities with variables on both sides
    "alg1_complete_the_square": "bNQY0z76M5A",  # Completing the square
    "alg1_literal_equation": "BR5yFOt0zao",  # Manipulating formulas: temperature
    "alg1_point_slope_form": "K_OI9LA54AA",  # Intro to point-slope form
    "alg1_multiply_binomials": "Xy8NKUoyy98",  # Multiplying binomials intro
    "alg1_solve_system": "NPXTkj75-AM",  # Systems of equations with elimination: x-4y=-18 & -x+3y=11
    "alg1_variation": "92U67CUy9Gc",  # Direct and inverse variation
    "alg1_simplify_rational": "7Uos1ED3KHI",  # Reducing rational expressions to lowest terms
    "alg1_abs_value_inequality": "iI_2Piwn_og",  # Absolute value inequalities
    "alg1_simplify_radical": "cw3mp8oNASk",  # Simplifying square roots
    # Geometry
    "distance_two_points": "nyZuite17Pc",  # Distance formula
    "midpoint_of_two_points": "Ez_-RwV9WVo",  # Midpoint formula
    "arc_length": "tVcasOt55Lc",  # Arc length from subtended angle
    "sector_area": "u8JFdwmBvvQ",  # Area of a sector
    "degree_to_rad": "O3jvUZ8wvZs",  # Degrees to radians
    "radian_to_deg": "z0-1gBy1ykE",  # Radians to degrees
    "sum_of_polygon_angles": "qG3HnRccrQU",  # Sum of interior angles of a polygon
    "angle_regular_polygon": "qG3HnRccrQU",  # Sum of interior angles of a polygon
    "valid_triangle": "KlKYvbigBqs",  # Triangle inequality theorem
    "volume_pyramid": "fD52yzLF8DA",  # Volume of pyramids intuition
    "geo_right_triangle_side": "l5VbdqRjTXc",  # Solving for a side in right triangles with trigonometry
    "geo_solve_right_triangle_pythag": "AA6RfgP-AHU",  # Intro to the Pythagorean theorem
    "geo_circle_equation_from_center_radius": "iX5UgArMyiI",  # Writing standard equation of a circle
    "geo_circle_center_radius_from_equation": "JvDpYlyKkNU",  # Features of a circle from its standard equation
    "geo_inscribed_angle": "aNi1-zeEps8",  # Inscribed angles
    "geo_conditional_probability_table": "pIfpHdGVwLU",  # Conditional probability and independence
    "geo_compound_probability": "xSc4oLA9e8o",  # Compound probability of independent events
    "geo_expected_value": "qafPcWNUiM8",  # Mean (expected value) of a discrete random variable
    "geo_special_right_triangle": "SFL4stapeUs",  # Special right triangles proof (part 1)
    "geo_similar_triangle_side": "R-6CAr_zEEk",  # Solving similar triangles
    "geo_scale_factor_ratio": "h-qwno7n5F4",  # Scale factors and area
    "geo_circle_segments": "ASZl3SnKwI8",  # Circle Theorems involving Secants, Chords, and Tangents (Mario's Math Tutoring)
    "geo_regular_polygon_area": "LrxZMdQ6tiw",  # Area of a regular hexagon
    "geo_composite_solid": "dp3my9MnmOM",  # Applying volume of solids
    "geo_polygon_area_vertices": "FSWPX0XB7a0",  # GEO: POLYGON AREA (SHOELACE METHOD) (Virtual Math)
    "geo_frustum_volume": "j06P-oKn094",  # How to Find the Volume of a Frustum (Cognito)
    # Algebra II
    "log": "Z5myJ8dg_rM",  # Intro to logarithms
    "multiply_complex_numbers": "cWn6g8Qqvs4",  # Multiplying complex numbers
    "aroc_over_interval": "neZeuTgEoMA",  # Finding average rate of change of polynomials
    "factorial": "HGoZfzz6dU0",  # Zero factorial or  0!
    "combinations": "iKy-d5_erhI",  # Intro to combinations
    "permutation": "DROZVHObeko",  # Permutation formula
    "set_operation": "jAfNg3ylZAI",  # Intersection and union of sets
    "alg2_evaluate_polynomial": "Id6UovYjd-M",  # Worked example: Evaluating functions from equation
    "alg2_polynomial_division": "FXgV9ySNusc",  # Intro to long division of polynomials
    "alg2_remainder_theorem": "MwG6QD352yc",  # Intro to the Polynomial Remainder Theorem
    "alg2_build_polynomial_from_roots": "CtqwiX4wHEY",  # Zeros of polynomials: matching equation to zeros
    "alg2_add_complex": "SfbjqVyQljk",  # Adding complex numbers
    "alg2_rational_exponent": "lZfXc4nHooo",  # Intro to rational exponents
    "alg2_solve_radical_equation": "pFFoAGIEyJc",  # Solving square-root equations: one solution
    "alg2_solve_exponential_log": "R443Db-wJ5o",  # Solving exponential equations using logarithms: base-10
    "alg2_evaluate_log": "Z5myJ8dg_rM",  # Intro to logarithms
    "alg2_inverse_linear_function": "wSiamij_i_k",  # Finding inverse functions: linear
    "alg2_z_score": "5S-Zfa-vOXs",  # Z-score introduction
    "alg2_empirical_rule": "OhRr26AfFBU",  # Normal distribution problems: Empirical rule
    "alg2_log_product_rule": "pkGrXzakRFs",  # Using the logarithmic product rule
    "alg2_log_quotient_rule": "yEAxG_D1HDw",  # Proof of the logarithm quotient and power rules
    "alg2_log_power_rule": "Pb9V374iOas",  # Using the logarithmic power rule
    "alg2_log_change_of_base": "OkFdDqW9xxM",  # Evaluating logarithms: change of base rule
    "alg2_rationalize_denominator": "ENIUcjdPO54",  # Rationalizing Denominators with Conjugates
    "alg2_radical_equation_conjugate": "c0jONsjJ_eU",  # Solve Radical Equations with 2 Square Roots (Mario's Math Tutoring)
    "alg2_function_composition": "wUNWjd4bMmw",  # Intro to composing functions
    "alg2_solve_rational_equation": "McOMtxI_Jzs",  # Equations with rational expressions
    "alg2_rational_expression_ops": "f-wz_ZzSDdg",  # Multiplying rational expressions
    "alg2_complex_division": "Z8j5RDOibV4",  # Dividing complex numbers
    "alg2_complex_modulus": "yvzyC4VBpUU",  # Absolute value of complex numbers
    "alg2_inverse_nonlinear": "YI30Ecfl4tc",  # Finding inverses of rational functions
    "alg2_rational_root_list": "Y9fwl_qocJc",  # Applying the rational root theorem
    "alg2_solve_system_three": "pANZpI9sOYg",  # Systems of three variables
    "alg2_solve_polynomial_factoring": "SONskIMkYdU",  # Zeros of polynomials (with factoring): common factor
    "alg2_conic_equation": "iX5UgArMyiI",  # Writing standard equation of a circle
    "alg2_polynomial_end_behavior": "tZKzaF28sOk",  # Intro to end behavior of polynomials
    # Statistical Reasoning
    "data_summary": "iHXdzfF7UEs",  # Sample variance
    "conditional_probability": "pIfpHdGVwLU",  # Conditional probability and independence
    "binomial_distribution": "Ctytn4a6zjw",  # Binomial probability example
    "confidence_interval": "6G3jMjAqNqM",  # Example constructing a t interval for a mean
    "stat_five_number_summary": "09Cx7xuIXig",  # Constructing a box plot
    "stat_z_score": "5S-Zfa-vOXs",  # Z-score introduction
    "stat_correlation_coefficient": "u4ugaNo6v1Q",  # Calculating correlation coefficient r
    "stat_regression_line": "FGesqq22TCM",  # Calculating the equation of a regression line
    "stat_margin_of_error": "hlM7zdf7zwU",  # Confidence intervals and margin of error
    "stat_standard_error_mean": "J1twbrHel3o",  # Standard error of the mean
    "stat_sample_proportion_ci": "sjG9Ns_8x6c",  # Example constructing and interpreting a confidence interval for p
    "stat_relative_frequency": "xQSTwehQdCc",  # Creating a relative frequency table for one categorical variable
    "stat_normal_probability": "uwhV0TAPmWc",  # Standard normal table for proportion between values
    "stat_test_statistic": "DfpFfIdwcIo",  # Calculating a z statistic in a test about a proportion
    "stat_discrete_variance": "2egl_5c8i-g",  # Variance and standard deviation of a discrete random variable
    "stat_percentile_rank": "Ngyt8Q5tWkU",  # Calculating percentile
    "stat_counting_probability": "Xqfcy1rqMbI",  # Probability using combinations
    "stat_odds_probability": "N1NWFj2rZcA",  # Converting Probabilities into Odds (EHB Explains)
    # Pre-Calculus
    "angle_btw_vectors": "5AWob_z74Ks",  # Defining the angle between vectors
    "angle_sum": "h0SNEO25vIw",  # Using the cosine angle addition identity
    "vector_dot": "WNuIhXo39_k",  # Vector dot product and vector length
    "euclidian_norm": "qMZnsj4ZO9g",  # Vector magnitude from components
    "complex_to_polar": "8RasCV_Lggg",  # Polar & rectangular forms of complex numbers
    "pc_law_of_sines": "VjmFKle7xIw",  # Solving for a side with the law of sines
    "pc_law_of_cosines_side": "ZElOxG7_m3c",  # Solving for a side with the law of cosines
    "pc_oblique_triangle_area": "hu4t3NuSk2w",  # Area Of A Triangle 1/2absinC (FuseSchool - Global Education)
    "pc_inverse_trig": "JGU74wbZMLg",  # Intro to arcsine
    "pc_double_angle": "a70-dYvDJZY",  # Trig angle addition identities
    "pc_solve_trig_equation": "NC7iWEQ9Kug",  # Solving sinusoidal equations of the form sin(x)=d
    "pc_polar_to_rectangular": "LWje358QRkU",  # Converting polar and rectangular coordinates
    "pc_rectangular_to_polar": "LWje358QRkU",  # Converting polar and rectangular coordinates
    "pc_finite_geometric_sum": "Cf0-6ngH2gs",  # Finite geometric series formula
    "pc_sigma_arithmetic_sum": "RM644gFKo_g",  # Worked example: arithmetic series (sigma notation)
    "pc_sequence_limit": "muqyereWEh4",  # Worked example: sequence convergence/divergence
    "pc_vector_add": "VgqsM-XdBD0",  # Adding & subtracting vectors
    "pc_parametric_to_rectangular": "pvbyMXsDR3A",  # Parametric Equations - How to Eliminate the Parameter (Mario's Math Tutoring)
    "pc_unit_circle_point": "1m9p9iubMLU",  # Unit circle
    "pc_unit_circle_sin": "ROG5LyuP-yo",  # Evaluating trigonometric angles in standard position
    "pc_unit_circle_cos": "ROG5LyuP-yo",  # Evaluating trigonometric angles in standard position
    "pc_unit_circle_tan": "ROG5LyuP-yo",  # Evaluating trigonometric angles in standard position
    "pc_trig_quadratic": "h8E8N1eARjs",  # Solving Trigonometric Equations That Are Quadratic in Form (Study Force)
    "pc_rational_vertical_asymptotes": "X8B4Fi7wadc",  # Analyzing vertical asymptotes of rational functions
    "pc_rational_zeros": "TX_mx3qULpw",  # Graphs of rational functions: zeros
    "pc_rational_holes": "qoMimDT7D8w",  # Discontinuities of rational functions
    "pc_rational_horizontal_asymptote": "UfY72qdxnvk",  # Analyzing horizontal asymptotes of rational functions
    "pc_rational_slant_asymptote": "aYRquz4FsKk",  # Finding oblique asymptotes of a rational function
    "pc_rational_y_intercept": "YElHmwdbkzQ",  # Graphs of rational functions: y-intercept
    "pc_rational_inequality": "JfXMsEi2S-s",  # Solving rational inequalities by testing intervals in terms of a constant
    "pc_sinusoid_features": "s4cLM0l1gd4",  # Features of sinusoidal functions
    "pc_sum_difference_values": "2RbKfRfzD-M",  # Finding trig values using angle addition identities
    "pc_half_angle_values": "9YI69okba3c",  # Half Angle Formulas & Identities - Evaluating Trigonometric Expressions (The Organic Chemistry Tutor)
    "pc_binomial_term": "iPwrDWQ7hPc",  # Intro to the Binomial Theorem
    "pc_de_moivre": "VZmnLQ3CMbE",  # Taking and visualizing powers of a complex number
    "pc_simplify_trig_identity": "soIt2TwV6Xk",  # Using the Pythagorean trig identity
    "pc_recursive_sequence_term": "Kjli0Gunkds",  # Evaluating sequences in recursive form
    "pc_partial_fractions": "Mt92Ozs7aJg",  # Integration with partial fractions
    "pc_polar_rectangular_equation": "7Xoub1BHb6o",  # Converting Polar Equations to Rectangular Equations (Mario's Math Tutoring)
    "pc_orthogonal_projection": "27vT-NWuw0M",  # Introduction to projections
    # AP Calculus
    "int_matrix_22_determinant": "ZAkmBOCiNqU",  # Intro to determinant notation and computation
    "power_rule_differentiation": "bRZmfc1YFsQ",  # Exploring the power rule
    "power_rule_integration": "QxbJsg-Vdms",  # Determining the reverse power rule
    "definite_integral": "auOcNZFKfo0",  # Evaluating definite integrals: reverse power rule
    "trig_differentiation": "UwFlrPNf5ZE",  # Exploring derivatives of sin(x) and cos(x)
    "alg2_solve_system_matrix": "NPXTkj75-AM",  # Systems of equations with elimination: x-4y=-18 & -x+3y=11
    "calc_limit_rational": "EAa3J_nDkoI",  # Determining limits by factoring
    "calc_limit_conjugate": "yVWxxQ7SMOw",  # Determining limits by rationalizing
    "calc_derivative_polynomial": "-CTaxKTzbEI",  # Differentiating polynomials
    "calc_product_rule": "SQUSh1LNjIo",  # Working an example: Product rule with table
    "calc_quotient_rule": "ZAElYVh5DXU",  # Working an example: Quotient rule with table
    "calc_chain_rule": "bLKTkM-w5ps",  # Working an example: Chain rule with table
    "calc_derivative_exp_log_trig": "Iur13MNO0Ro",  # Working an example: Derivatives of sin(x) and cos(x)
    "calc_higher_order_derivative": "WC5VYKI807Q",  # Exploring second derivatives
    "calc_tangent_line": "j9FDoYNxZlw",  # Finding equations of tangents to polynomials
    "calc_extrema": "lFQ4kMcODzU",  # Finding relative extrema (first derivative test)
    "calc_inflection_point": "RoxefQ_Qgm8",  # Analyzing inflection points (algebraic)
    "calc_definite_integral_poly": "auOcNZFKfo0",  # Evaluating definite integrals: reverse power rule
    "calc_indefinite_integral_poly": "YwR_82jgJ_Q",  # Exploring indefinite integrals: sums and multiples
    "calc_usub_integral": "paNqHnR3-aM",  # Using 𝘶-substitution: definite integrals
    "calc_area_between_curves": "wQXYtsyfbqg",  # Calculating the area between curves
    "calc_average_value": "0rzL08BHr5c",  # Calculating average value of function over interval
    "calc_riemann_sum": "dEAk0BHBYCM",  # Introducing Riemann approximations
    "alg2_matrix_operation": "kT4Mp9EdVqs",  # Intro to matrix multiplication
    "calc_implicit_differentiation": "mSVrqKZDRF4",  # Exploring implicit differentiation
    "calc_particle_motion": "b4w0xmuOiQo",  # Working an example: Motion problems with derivatives
    "calc_volume_revolution": "btGaOTXxXs8",  # Using the disc method around x-axis
    "calc_lhopital": "PdSzruR5OeE",  # Introducing L'Hôpital's rule
    "calc_limit_definition_derivative": "HEH_oKNLgUU",  # Finding the derivative of x² at any point using the formal definition
    "calc_integration_by_parts": "dh__n9FVKA0",  # Integration by parts intro
    "calc_related_rates": "kQF9pOqmS0U",  # Introducing related rates
    "calc_mvt_find_c": "S_YIUXy-WFM",  # Applying the mean value theorem example: polynomial
    "calc_trapezoidal_rule": "1p0NHR5w0Lc",  # Approximating area using trapezoidal sums
    "calc_separable_ode": "DL-ozRGDlkY",  # Introducing separable equations
    "calc_concavity_interval": "72L_N7AtCRE",  # Analyzing concavity (algebraic)
    "calc_taylor_coefficient": "RRYh4cqv6ZQ",  # Worked example: coefficient in Maclaurin polynomial
}


def default_learn_more_url(generator_name):
    """The curated default "Learn more" URL for a generator, or "" if none."""
    video_id = LEARN_MORE_VIDEOS.get(generator_name) if generator_name else None
    if not video_id:
        return ""
    return f"https://www.youtube.com/watch?v={video_id}"
