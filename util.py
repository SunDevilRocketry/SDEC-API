# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2025 Sun Devil Rocketry

import math

def make_safe_number(num: float | int | None) -> float | int | None:
    if num is None: return None
    if isinstance(num, float) and math.isnan(num): return None
    if math.isinf(num): return 999999
    return num