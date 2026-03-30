"""Convert per-period amounts into a monthly equivalent for budgeting totals."""

from __future__ import annotations

from app.models.financial import RecurrenceFrequency


def amount_to_monthly(amount: float, frequency: RecurrenceFrequency | str | None) -> float:
    """
    Map a recurring amount to an approximate monthly figure.

    * ``NONE`` — amount is already expressed as a monthly budget line.
    * ``DAILY`` — amount is paid/received each day.
    * ``WEEKLY`` — amount is paid/received each week.
    * ``FORTNIGHTLY`` — every two weeks (26 periods per year).
    * ``MONTHLY`` — one payment per month.
    * ``YEARLY`` — annual amount spread across 12 months.
    """
    if amount is None or amount <= 0:
        return 0.0
    if frequency is None:
        freq = RecurrenceFrequency.MONTHLY
    elif isinstance(frequency, str):
        try:
            freq = RecurrenceFrequency(frequency)
        except ValueError:
            freq = RecurrenceFrequency.MONTHLY
    else:
        freq = frequency

    if freq == RecurrenceFrequency.NONE:
        return float(amount)
    if freq == RecurrenceFrequency.DAILY:
        return float(amount) * 365 / 12
    if freq == RecurrenceFrequency.WEEKLY:
        return float(amount) * 52 / 12
    if freq == RecurrenceFrequency.FORTNIGHTLY:
        return float(amount) * 26 / 12
    if freq == RecurrenceFrequency.MONTHLY:
        return float(amount)
    if freq == RecurrenceFrequency.YEARLY:
        return float(amount) / 12
    return float(amount)
