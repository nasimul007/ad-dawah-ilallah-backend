import math
import re


# ─────────────────────────────────────────────────────────────────────────────
# Rate Card  (Tk per printed page)
# Keys: (color: 'B_W'|'COLOR', sides: 'SINGLE_SIDED'|'DOUBLE_SIDED', tier: 0|1|2)
# Tiers: 0 = 0–10%,  1 = 10–50%,  2 = 50–100%  ink coverage
# ─────────────────────────────────────────────────────────────────────────────
RATE_CARD = {
    ("B_W",   "SINGLE_SIDED"): (2.0, 4.0, 6.0),
    ("B_W",   "DOUBLE_SIDED"): (1.5, 3.5, 5.5),
    ("COLOR", "SINGLE_SIDED"): (3.0, 5.0, 8.0),
    ("COLOR", "DOUBLE_SIDED"): (2.5, 4.5, 7.5),
}


def _coverage_tier(coverage_pct: float) -> int:
    """Map ink coverage percentage to rate tier index (0, 1, or 2)."""
    if coverage_pct <= 10.0:
        return 0
    elif coverage_pct <= 50.0:
        return 1
    else:
        return 2


def _count_pages_in_range(page_range: str, total_pages: int) -> int:
    """
    Parse a validated page range string and return the total number of
    pages it selects.  Open-ended tokens (e.g. '5-') resolve against
    total_pages.

    Assumes the range string has already been validated by validate_page_range().
    """
    s = page_range.replace(" ", "")
    selected = set()

    for token in s.split(","):
        # n-m
        m = re.match(r'^(\d+)-(\d+)$', token)
        if m:
            n, end = int(m.group(1)), int(m.group(2))
            selected.update(range(n, min(end, total_pages) + 1))
            continue

        # n-  (open-ended to last page)
        m = re.match(r'^(\d+)-$', token)
        if m:
            n = int(m.group(1))
            selected.update(range(n, total_pages + 1))
            continue

        # -m  (open-ended from first page)
        m = re.match(r'^-(\d+)$', token)
        if m:
            end = int(m.group(1))
            selected.update(range(1, min(end, total_pages) + 1))
            continue

        # plain n
        m = re.match(r'^(\d+)$', token)
        if m:
            n = int(m.group(1))
            if 1 <= n <= total_pages:
                selected.add(n)

    return len(selected)


def calculate_print_cost(
    *,
    total_pages: int,
    copies: int,
    sides: str,             # 'SINGLE_SIDED' | 'DOUBLE_SIDED'
    print_color: str,       # 'B_W' | 'COLOR'
    print_pages: str,       # 'ALL' | 'CUSTOM'
    pages_per_slide: int,   # 1 | 2 | 4 | 8 | 16
    page_range: str = None, # required when print_pages == 'CUSTOM'
    coverage_pct: float = None,  # ink coverage 0–100; None → assume worst tier (50–100%)
) -> float:
    """
    Calculate the printing cost (in Tk) for a single Print record.

    Args:
        total_pages:    Total pages in the uploaded PDF.
        copies:         Number of copies to print.
        sides:          'SINGLE_SIDED' or 'DOUBLE_SIDED'.
        print_color:    'B_W' or 'COLOR'.
        print_pages:    'ALL' to print everything, 'CUSTOM' to use page_range.
        pages_per_slide: How many document pages are laid out on one printed side
                         (N-up printing).  Accepted: 1, 2, 4, 8, 16.
        page_range:     Page range string (e.g. '1-5,8,10-').
                        Required when print_pages == 'CUSTOM'.
        coverage_pct:   Ink/toner coverage as a percentage (0–100).
                        Obtained from the area-calculation function.
                        If None (file type doesn't support area analysis),
                        the highest-cost tier (>50%) is assumed conservatively.

    Returns:
        Total cost as a float (Tk).

    Raises:
        ValueError: on invalid / missing arguments.
    """

    # ── Input guards ──────────────────────────────────────────────────────────
    if total_pages < 1:
        raise ValueError(f"total_pages must be >= 1, got {total_pages}")
    if copies < 1:
        raise ValueError(f"copies must be >= 1, got {copies}")
    if sides not in ("SINGLE_SIDED", "DOUBLE_SIDED"):
        raise ValueError(f"Invalid sides value: {sides!r}")
    if print_color not in ("B_W", "COLOR"):
        raise ValueError(f"Invalid print_color value: {print_color!r}")
    if print_pages not in ("ALL", "CUSTOM"):
        raise ValueError(f"Invalid print_pages value: {print_pages!r}")
    if pages_per_slide not in (1, 2, 4, 8, 16):
        raise ValueError(f"Invalid pages_per_slide value: {pages_per_slide!r}")
    if print_pages == "CUSTOM" and not page_range:
        raise ValueError("page_range is required when print_pages is 'CUSTOM'")

    # ── Step 1: Determine logical page count ──────────────────────────────────
    if print_pages == "ALL":
        logical_pages = total_pages
    else:  # CUSTOM
        logical_pages = _count_pages_in_range(page_range, total_pages)
        if logical_pages == 0:
            return 0.0  # empty/invalid range → no cost

    # ── Step 2: N-up  →  number of physical printed sides ────────────────────
    # e.g. 10 pages at 4-up = ceil(10/4) = 3 physical sides
    physical_sides = math.ceil(logical_pages / pages_per_slide)

    # ── Step 3: Coverage tier ─────────────────────────────────────────────────
    if coverage_pct is None:
        # File type doesn't support area analysis → assume worst case
        tier = 2
    else:
        coverage_pct = max(0.0, min(100.0, coverage_pct))  # clamp to [0, 100]
        tier = _coverage_tier(coverage_pct)

    # ── Step 4: Per-page rate ─────────────────────────────────────────────────
    rate_per_page = RATE_CARD[(print_color, sides)][tier]

    # ── Step 5: Total cost ────────────────────────────────────────────────────
    # physical_sides is the number of pages that go through the printer per copy
    total_cost = physical_sides * rate_per_page * copies

    return total_cost


# ─────────────────────────────────────────────────────────────────────────────
# Integration helper — mirrors how it's called inside the create() view
# ─────────────────────────────────────────────────────────────────────────────
def get_print_cost_from_data(p_data: dict, total_pages: int, coverage_pct: float = None) -> float:
    """
    Convenience wrapper that accepts a p_data dict (as received in the create
    view) and returns the calculated cost.

    Usage inside the create() view:
        coverage_pct, _ = calculate_area(*process_pdf(file_obj)) if pdf else (None, None)
        cost = get_print_cost_from_data(p_data, total_pages, coverage_pct)

    Then pass cost to Print.objects.create(..., cost=cost)
    """
    return calculate_print_cost(
        total_pages=total_pages,
        copies=int(p_data.get("copies", 1)),
        sides=p_data.get("sides", "SINGLE_SIDED"),
        print_color=p_data.get("print_color", "B_W"),
        print_pages=p_data.get("print_pages", "ALL"),
        pages_per_slide=int(p_data.get("pages_per_slide", 1)),
        page_range=p_data.get("page_range"),
        coverage_pct=coverage_pct,
    )
