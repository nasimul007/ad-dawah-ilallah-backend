import re
def validate_page_range(page_range: str, page_limit: int = None) -> bool:
    """
    Validates a printer page range string.

    Supported syntax:
        - Single page:        "5"
        - Range:              "3-7"
        - Open-ended start:   "5-"   (page 5 to last)
        - Open-ended end:     "-5"   (page 1 to 5)
        - Multiple parts:     "1,3-5,8,10-"  (comma-separated mix)

    Spaces are ignored.

    Args:
        page_range:  The page range string to validate.
        page_limit:  Optional. Total number of pages in the document.
                     When provided, all explicit page numbers must be <= page_limit.
                     Must be a positive integer; 0, negative, float, bool, or
                     non-int values cause the function to return False.

    Returns:
        True  — syntax is valid and all numbers are within bounds (if limit given).
        False — invalid syntax, out-of-bounds page, or bad page_limit argument.
    """

    # ── Validate page_limit itself ────────────────────────────────────────────
    if page_limit is not None:
        # bool is a subclass of int in Python, so reject it explicitly
        if not isinstance(page_limit, int) or isinstance(page_limit, bool):
            return False
        if page_limit < 1:
            return False

    # ── Validate input type ───────────────────────────────────────────────────
    if not isinstance(page_range, str):
        return False

    # Strip all whitespace
    s = page_range.replace(" ", "").replace("\t", "")

    if not s:
        return False

    # ── Token pattern ─────────────────────────────────────────────────────────
    # Groups:  1,2 = n-m   |   3 = n-   |   4 = -m   |   5 = n
    token_pattern = re.compile(
        r'^(\d+)-(\d+)$'   # n-m  (bounded range)
        r'|^(\d+)-$'       # n-   (open-ended to last page)
        r'|^-(\d+)$'       # -m   (open-ended from first page)
        r'|^(\d+)$'        # n    (single page)
    )

    tokens = s.split(",")

    for token in tokens:
        # Empty segment e.g. "1,,3" or leading/trailing comma
        if not token:
            return False

        match = token_pattern.match(token)
        if not match:
            return False

        g1, g2, g3, g4, g5 = (match.group(i) for i in range(1, 6))

        if g1 is not None:
            # ── n-m ──────────────────────────────────────────────────────────
            n, m = int(g1), int(g2)
            if n < 1 or m < 1:
                return False
            if n > m:                               # reversed range
                return False
            if page_limit is not None:
                if n > page_limit or m > page_limit:
                    return False

        elif g3 is not None:
            # ── n- ───────────────────────────────────────────────────────────
            n = int(g3)
            if n < 1:
                return False
            if page_limit is not None and n > page_limit:
                return False

        elif g4 is not None:
            # ── -m ───────────────────────────────────────────────────────────
            m = int(g4)
            if m < 1:
                return False
            if page_limit is not None and m > page_limit:
                return False

        else:
            # ── n ────────────────────────────────────────────────────────────
            n = int(g5)
            if n < 1:
                return False
            if page_limit is not None and n > page_limit:
                return False

    return True