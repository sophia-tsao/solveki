import random

from django.test import SimpleTestCase

from myapp.generators import LOCAL_GENERATORS
from myapp.generators._variants import CLASSIC, iter_variants, with_variants


def _make():
    """A throwaway dispatcher with one extra variant (never registered)."""
    @with_variants
    def gen(max_n=5):
        return f"classic {max_n}", "1", []

    @gen.variant("other")
    def _other():
        return "other", "2", []

    return gen


class WithVariantsTests(SimpleTestCase):
    def test_no_argument_call_still_works(self):
        problem, solution, steps = _make()()
        self.assertIn(solution, {"1", "2"})

    def test_variant_can_be_forced(self):
        gen = _make()
        self.assertEqual(gen(variant=CLASSIC)[0], "classic 5")
        self.assertEqual(gen(variant="other")[0], "other")

    def test_params_reach_only_variants_that_accept_them(self):
        gen = _make()
        self.assertEqual(gen(variant=CLASSIC, max_n=9)[0], "classic 9")
        self.assertEqual(gen(variant="other", max_n=9)[0], "other")

    def test_unknown_variant_raises(self):
        with self.assertRaises(KeyError):
            _make()(variant="bogus")

    def test_duplicate_or_weightless_variant_rejected(self):
        gen = _make()
        with self.assertRaises(ValueError):
            gen.variant("other")
        with self.assertRaises(ValueError):
            gen.variant("free", weight=0)

    def test_random_pick_reaches_every_variant_and_is_seedable(self):
        gen = _make()
        random.seed(0)
        first = [gen()[0] for _ in range(200)]
        random.seed(0)
        self.assertEqual(first, [gen()[0] for _ in range(200)])
        self.assertEqual(set(first), {"classic 5", "other"})

    def test_classic_only_dispatcher_draws_no_randomness(self):
        @with_variants
        def solo():
            return "p", "s", []
        random.seed(0)
        solo()
        after = random.random()
        random.seed(0)
        self.assertEqual(after, random.random())

    def test_iter_variants(self):
        gen = _make()
        labels = [label for label, _ in iter_variants(gen)]
        self.assertEqual(labels, ["[classic]", "[other]"])
        plain = LOCAL_GENERATORS["addition"]
        if not hasattr(plain, "variants"):
            self.assertEqual(iter_variants(plain), [("", plain)])


class RegisteredVariantsTests(SimpleTestCase):
    def test_variant_functions_are_not_registered_generators(self):
        registered = set(map(id, LOCAL_GENERATORS.values()))
        for name, gen in LOCAL_GENERATORS.items():
            for variant, (fn, weight) in getattr(gen, "variants", {}).items():
                with self.subTest(generator=name, variant=variant):
                    self.assertGreater(weight, 0)
                    if variant != CLASSIC:
                        self.assertNotIn(id(fn), registered)
