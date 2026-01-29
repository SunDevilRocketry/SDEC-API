import math

def make_safe_number(num: float | int | None) -> float | int | None:
    if num is None: return None
    if isinstance(num, float) and math.isnan(num): return None
    return num