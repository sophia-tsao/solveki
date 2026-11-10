import random

from django.core.management.base import BaseCommand, CommandError

from myapp.generators import LOCAL_GENERATORS
from myapp.views.problems import _make_problem_for_topic


class _Topic:
    """Just enough of a Topic for `_make_problem_for_topic`."""
    id = None

    def __init__(self, generator_name):
        self.generator_name = generator_name


class Command(BaseCommand):
    help = (
        "Print sample problems from a generator with their step-by-step "
        "explanations, exactly as a card would serve them. For reviewing wording."
    )

    def add_arguments(self, parser):
        parser.add_argument("generator_name")
        parser.add_argument("--n", type=int, default=3, help="number of samples")
        parser.add_argument("--seed", type=int, default=None)
        parser.add_argument("--variant", default=None, help="only this question type")
        parser.add_argument(
            "--all-variants", action="store_true", help="n samples of every question type",
        )

    def handle(self, generator_name, n, seed, variant, all_variants, **options):
        if seed is not None:
            random.seed(seed)
        variants = getattr(LOCAL_GENERATORS.get(generator_name), "variants", None) or {}
        if variant is not None and variant not in variants:
            raise CommandError(f"{generator_name!r} has no variant {variant!r}")
        names = (list(variants) or [None]) if all_variants else [variant]
        for name in names:
            if all_variants and name is not None:
                self.stdout.write(f"===== Variant: {name} =====")
            self._samples(generator_name, n, name)

    def _samples(self, generator_name, n, variant):
        for i in range(n):
            made = _make_problem_for_topic(_Topic(generator_name), variant=variant)
            if made is None:
                raise CommandError(f"No generator named {generator_name!r}")
            self.stdout.write(f"--- Sample {i + 1} ---")
            self.stdout.write(f"Problem:  {made['problem']}")
            self.stdout.write(f"Solution: {made['solution']}")
            if not made["steps"]:
                self.stdout.write("(no steps)")
            for number, step in enumerate(made["steps"], 1):
                self.stdout.write(f"  {number}. {step['text']}")
                if step["math"]:
                    self.stdout.write(f"       {step['math']}")
            self.stdout.write("")
