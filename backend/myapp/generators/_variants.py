"""Several question types ("variants") behind one topic's generator.

A topic is served by one registered generator. To ask its concept in more than
one way, the generator becomes a dispatcher that picks one variant at random;
its original body stays as the ``classic`` variant::

    @register
    @with_variants
    def pre_two_step_equation(max_a=9):          # body unchanged: "classic"
        ...

    @pre_two_step_equation.variant("scaled_expression")
    def _pre_two_step_scaled_expression(max_a=9):
        ...

The dispatcher keeps the generator contract: it's callable with no arguments
and returns ``(problem, solution, steps)``. ``variant="name"`` forces one variant
(for tests and ``preview_steps``); other keyword arguments are the tunable
``*_min``/``*_max`` params, forwarded only to variants that accept them. The
pick uses the global ``random``, so ``random.seed`` still makes runs repeatable.

Variant functions are private and not registered: they're never a topic's
generator on their own. See docs/generator-variations.md for what each topic's
variants should ask.
"""
import functools
import inspect
import random

CLASSIC = "classic"
# The familiar question stays the most common one: each new variant is weight 1.
CLASSIC_WEIGHT = 2


def _accepted(fn, params):
    """The subset of `params` that `fn`'s signature accepts."""
    signature = inspect.signature(fn)
    if any(p.kind is p.VAR_KEYWORD for p in signature.parameters.values()):
        return params
    return {k: v for k, v in params.items() if k in signature.parameters}


def with_variants(fn):
    """Turn generator `fn` into a dispatcher whose ``classic`` variant is `fn`."""
    variants = {CLASSIC: (fn, CLASSIC_WEIGHT)}

    @functools.wraps(fn)
    def dispatcher(*, variant=None, **params):
        if variant is None:
            if len(variants) == 1:
                variant = CLASSIC
            else:
                names = list(variants)
                weights = [variants[name][1] for name in names]
                variant = random.choices(names, weights)[0]
        chosen, _ = variants[variant]  # KeyError for an unknown variant
        return chosen(**_accepted(chosen, params))

    def add_variant(name, weight=1):
        """Decorator: add the decorated function as variant `name`."""
        if name in variants:
            raise ValueError(f"Duplicate variant {name!r} for {fn.__name__}")
        if weight <= 0:
            raise ValueError(f"Variant {name!r} needs a positive weight")

        def decorate(variant_fn):
            variants[name] = (variant_fn, weight)
            return variant_fn
        return decorate

    dispatcher.variants = variants
    dispatcher.variant = add_variant
    return dispatcher


def iter_variants(generator):
    """``(label, callable)`` for every variant of `generator`.

    A plain generator yields ``("", generator)``; a dispatcher yields
    ``("[name]", callable forcing that variant)`` for each of its variants.
    """
    variants = getattr(generator, "variants", None)
    if not variants:
        return [("", generator)]
    return [(f"[{name}]", functools.partial(generator, variant=name)) for name in variants]


def classic(generator):
    """`generator` pinned to its original question, for tests written against it."""
    if getattr(generator, "variants", None):
        return functools.partial(generator, variant=CLASSIC)
    return generator
