"""
NEXUS — VA Combined Ratings Math Engine
=======================================
Implements the VA's combined ratings methodology (38 CFR 4.25) and the
bilateral factor (38 CFR 4.26).

How VA math actually works (the part everyone gets wrong):
  Ratings are NOT added. Each rating is applied to the *remaining*
  efficiency. A 50% + 30% veteran is not 80%: the 30% applies to the
  50% of capacity that remains, yielding 50 + (30% of 50) = 65,
  which rounds to a 70% combined rating.

Bilateral factor (38 CFR 4.26):
  When disabilities affect both arms, both legs, or paired skeletal
  muscles, those ratings are combined first, then 10% of that combined
  value is added before combining with the remaining ratings.

This module is pure stdlib and fully unit-testable.
"""

from dataclasses import dataclass, field


VALID_RATINGS = set(range(0, 101, 10))


@dataclass
class Rating:
    percent: int
    label: str = ""
    bilateral: bool = False  # part of a bilateral pair (38 CFR 4.26)

    def __post_init__(self):
        if self.percent not in VALID_RATINGS:
            raise ValueError(
                f"VA ratings are in 10% increments (0-100); got {self.percent}"
            )


@dataclass
class CombinedResult:
    exact: float                 # combined value before final rounding
    rounded: int                 # final combined rating (nearest 10)
    bilateral_factor: float      # value added by the bilateral factor (0 if n/a)
    steps: list = field(default_factory=list)  # human-readable explanation


def _combine_pair(a: float, b: float) -> float:
    """Combine two values per the VA combined ratings table logic.

    combined = a + b * (100 - a) / 100, rounded to the nearest whole
    number at each step (matching the integer table in 38 CFR 4.25).
    """
    raw = a + b * (100.0 - a) / 100.0
    return float(round(raw))


def _round_to_nearest_ten(value: float) -> int:
    """Final rounding per 38 CFR 4.25: nearest 10, with 5 rounding up."""
    return int((value + 5) // 10 * 10)


def combine(ratings: list[Rating]) -> CombinedResult:
    """Combine a list of ratings, applying the bilateral factor if any
    ratings are marked bilateral. Returns the result with step-by-step
    explanation suitable for display to the veteran.
    """
    if not ratings:
        return CombinedResult(0.0, 0, 0.0, ["No ratings entered."])

    steps: list[str] = []
    bilateral = sorted(
        (r for r in ratings if r.bilateral), key=lambda r: -r.percent
    )
    others = sorted(
        (r for r in ratings if not r.bilateral), key=lambda r: -r.percent
    )

    pool: list[float] = []
    bilateral_factor = 0.0

    if len(bilateral) >= 2:
        combined_bi = float(bilateral[0].percent)
        steps.append(f"Bilateral group starts at {bilateral[0].percent}%"
                     f" ({bilateral[0].label or 'bilateral #1'}).")
        for r in bilateral[1:]:
            new = _combine_pair(combined_bi, r.percent)
            steps.append(
                f"Combine {combined_bi:.0f} with {r.percent}"
                f" ({r.label or 'bilateral'}): {combined_bi:.0f} + "
                f"{r.percent} x {(100 - combined_bi) / 100:.2f} = {new:.0f}"
            )
            combined_bi = new
        bilateral_factor = round(combined_bi * 0.10, 1)
        with_factor = combined_bi + bilateral_factor
        steps.append(
            f"Bilateral factor (38 CFR 4.26): {combined_bi:.0f} + 10% "
            f"({bilateral_factor:.1f}) = {with_factor:.1f}"
        )
        pool.append(with_factor)
    elif len(bilateral) == 1:
        # A single rating can't form a bilateral pair; treat normally.
        steps.append(
            "Only one rating marked bilateral — the bilateral factor "
            "requires a pair (both arms / both legs / paired muscles), "
            "so it is treated as a normal rating."
        )
        others.append(bilateral[0])
        others.sort(key=lambda r: -r.percent)

    pool.extend(float(r.percent) for r in others)
    pool.sort(reverse=True)

    combined = pool[0]
    if not steps or len(pool) > 1:
        steps.append(f"Start with the highest value: {combined:.1f}")
    for value in pool[1:]:
        new = _combine_pair(combined, value)
        steps.append(
            f"Combine {combined:.1f} with {value:.1f}: "
            f"{combined:.1f} + {value:.1f} x {(100 - combined) / 100:.2f}"
            f" = {new:.0f}"
        )
        combined = new

    rounded = _round_to_nearest_ten(combined)
    steps.append(
        f"Final: {combined:.1f} rounds to the nearest 10 -> "
        f"combined rating of {rounded}%."
    )
    return CombinedResult(combined, rounded, bilateral_factor, steps)
