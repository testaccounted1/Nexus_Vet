"""Unit tests for va_math against known VA combined ratings table values."""
import sys
sys.path.insert(0, "/home/claude/nexus")
from va_math import Rating, combine

def check(ratings, expected_rounded, name):
    res = combine(ratings)
    status = "PASS" if res.rounded == expected_rounded else "FAIL"
    print(f"[{status}] {name}: exact={res.exact:.1f} rounded={res.rounded} "
          f"(expected {expected_rounded})")
    return status == "PASS"

ok = True
# Classic examples from the VA combined ratings table (38 CFR 4.25)
ok &= check([Rating(50), Rating(30)], 70, "50+30 -> 65 -> 70")
ok &= check([Rating(40), Rating(20)], 50, "40+20 -> 52 -> 50")
ok &= check([Rating(60), Rating(40), Rating(20)], 80, "60+40+20 -> 81 -> 80")
ok &= check([Rating(70), Rating(50), Rating(30)], 90, "70+50+30 -> 90")
ok &= check([Rating(10), Rating(10)], 20, "10+10 -> 19 -> 20")
ok &= check([Rating(20), Rating(10)], 30, "20+10 -> 28 -> 30")
ok &= check([Rating(100)], 100, "single 100")
ok &= check([Rating(0), Rating(0)], 0, "zeros")
# Bilateral: 30% right knee + 20% left knee -> combine: 30+20*0.7=44,
# factor 4.4 -> 48.4; then e.g. with 50% PTSD: 50 + 48.4*0.5 = 74 -> 70
ok &= check(
    [Rating(50, "PTSD"),
     Rating(30, "right knee", bilateral=True),
     Rating(20, "left knee", bilateral=True)],
    70, "bilateral knees + PTSD")
# Stacking many small ratings shows diminishing returns
ok &= check([Rating(10)] * 5, 40, "five 10s -> 41 -> 40")

print("\nALL PASS" if ok else "\nSOME FAILURES")
sys.exit(0 if ok else 1)
