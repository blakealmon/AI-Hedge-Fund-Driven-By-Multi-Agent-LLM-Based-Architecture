from typing import List, Tuple


def render_resizing_report(date_str: str, changes: List[Tuple[str, int, int]]) -> str:
    lines = []
    lines.append(f"Resizing Report - {date_str}")
    lines.append("")
    lines.append("Ticker | Prev Qty | New Qty | Delta")
    lines.append("--- | ---:| ---:| ---:")
    for ticker, prev_qty, new_qty in changes:
        delta = new_qty - prev_qty
        lines.append(f"{ticker} | {prev_qty} | {new_qty} | {delta}")
    return "\n".join(lines)


