"""
Static IRS reference data: §6621 quarterly rates, max tax rates, filing deadlines.

DATA VERIFICATION NOTE: All rates must be cross-checked against IRS IRB publications
before production use. Sources: IRS Rev. Ruls published quarterly in the IRB.
"""
from datetime import date
from decimal import Decimal
from typing import NamedTuple


class RateEntry(NamedTuple):
    year: int
    quarter: int          # 1–4
    rate: Decimal         # e.g. Decimal("0.07") = 7%
    effective_from: date
    effective_to: date


# §6621(a)(2) underpayment rates — non-corporate taxpayers — 1987 Q1 through 2026 Q1
# Format: (year, quarter, rate_pct)
# Source: IRS IRB Rev. Ruls. Verify each entry before production.
_RAW_6621 = [
    # year  Q  rate%
    (1987,  1, "0.09"),
    (1987,  2, "0.09"),
    (1987,  3, "0.09"),
    (1987,  4, "0.10"),
    (1988,  1, "0.11"),
    (1988,  2, "0.10"),
    (1988,  3, "0.10"),
    (1988,  4, "0.11"),
    (1989,  1, "0.11"),
    (1989,  2, "0.12"),
    (1989,  3, "0.12"),
    (1989,  4, "0.11"),
    (1990,  1, "0.11"),
    (1990,  2, "0.11"),
    (1990,  3, "0.11"),
    (1990,  4, "0.11"),
    (1991,  1, "0.11"),
    (1991,  2, "0.10"),
    (1991,  3, "0.10"),
    (1991,  4, "0.10"),
    (1992,  1, "0.09"),
    (1992,  2, "0.08"),
    (1992,  3, "0.08"),
    (1992,  4, "0.07"),
    (1993,  1, "0.07"),
    (1993,  2, "0.07"),
    (1993,  3, "0.07"),
    (1993,  4, "0.07"),
    (1994,  1, "0.07"),
    (1994,  2, "0.07"),
    (1994,  3, "0.08"),
    (1994,  4, "0.08"),
    (1995,  1, "0.09"),
    (1995,  2, "0.09"),
    (1995,  3, "0.09"),
    (1995,  4, "0.09"),
    (1996,  1, "0.09"),
    (1996,  2, "0.08"),
    (1996,  3, "0.09"),
    (1996,  4, "0.09"),
    (1997,  1, "0.09"),
    (1997,  2, "0.09"),
    (1997,  3, "0.09"),
    (1997,  4, "0.09"),
    (1998,  1, "0.09"),
    (1998,  2, "0.08"),
    (1998,  3, "0.08"),
    (1998,  4, "0.08"),
    (1999,  1, "0.07"),
    (1999,  2, "0.08"),
    (1999,  3, "0.08"),
    (1999,  4, "0.08"),
    (2000,  1, "0.08"),
    (2000,  2, "0.09"),
    (2000,  3, "0.09"),
    (2000,  4, "0.09"),
    (2001,  1, "0.09"),
    (2001,  2, "0.08"),
    (2001,  3, "0.07"),
    (2001,  4, "0.07"),
    (2002,  1, "0.06"),
    (2002,  2, "0.06"),
    (2002,  3, "0.06"),
    (2002,  4, "0.06"),
    (2003,  1, "0.05"),
    (2003,  2, "0.05"),
    (2003,  3, "0.05"),
    (2003,  4, "0.04"),
    (2004,  1, "0.04"),
    (2004,  2, "0.05"),
    (2004,  3, "0.04"),
    (2004,  4, "0.05"),
    (2005,  1, "0.05"),
    (2005,  2, "0.06"),
    (2005,  3, "0.06"),
    (2005,  4, "0.07"),
    (2006,  1, "0.07"),
    (2006,  2, "0.07"),
    (2006,  3, "0.08"),
    (2006,  4, "0.08"),
    (2007,  1, "0.08"),
    (2007,  2, "0.08"),
    (2007,  3, "0.08"),
    (2007,  4, "0.08"),
    (2008,  1, "0.07"),
    (2008,  2, "0.06"),
    (2008,  3, "0.05"),
    (2008,  4, "0.06"),
    (2009,  1, "0.05"),
    (2009,  2, "0.04"),
    (2009,  3, "0.04"),
    (2009,  4, "0.04"),
    (2010,  1, "0.04"),
    (2010,  2, "0.04"),
    (2010,  3, "0.04"),
    (2010,  4, "0.04"),
    (2011,  1, "0.04"),
    (2011,  2, "0.04"),
    (2011,  3, "0.04"),
    (2011,  4, "0.03"),
    (2012,  1, "0.03"),
    (2012,  2, "0.03"),
    (2012,  3, "0.03"),
    (2012,  4, "0.03"),
    (2013,  1, "0.03"),
    (2013,  2, "0.03"),
    (2013,  3, "0.03"),
    (2013,  4, "0.03"),
    (2014,  1, "0.03"),
    (2014,  2, "0.03"),
    (2014,  3, "0.03"),
    (2014,  4, "0.03"),
    (2015,  1, "0.03"),
    (2015,  2, "0.03"),
    (2015,  3, "0.03"),
    (2015,  4, "0.03"),
    (2016,  1, "0.03"),
    (2016,  2, "0.04"),
    (2016,  3, "0.04"),
    (2016,  4, "0.04"),
    (2017,  1, "0.04"),
    (2017,  2, "0.04"),
    (2017,  3, "0.04"),
    (2017,  4, "0.04"),
    (2018,  1, "0.04"),
    (2018,  2, "0.05"),
    (2018,  3, "0.05"),
    (2018,  4, "0.05"),
    (2019,  1, "0.06"),
    (2019,  2, "0.06"),
    (2019,  3, "0.05"),
    (2019,  4, "0.05"),
    (2020,  1, "0.05"),
    (2020,  2, "0.03"),  # COVID-era Fed rate cut
    (2020,  3, "0.03"),
    (2020,  4, "0.03"),
    (2021,  1, "0.03"),
    (2021,  2, "0.03"),
    (2021,  3, "0.03"),
    (2021,  4, "0.03"),
    (2022,  1, "0.03"),
    (2022,  2, "0.04"),  # Fed began hiking March 2022
    (2022,  3, "0.05"),
    (2022,  4, "0.06"),
    (2023,  1, "0.07"),
    (2023,  2, "0.07"),
    (2023,  3, "0.07"),
    (2023,  4, "0.08"),
    (2024,  1, "0.08"),
    (2024,  2, "0.08"),
    (2024,  3, "0.08"),
    (2024,  4, "0.08"),
    (2025,  1, "0.07"),
    (2025,  2, "0.07"),
    (2025,  3, "0.07"),
    (2025,  4, "0.07"),
    (2026,  1, "0.07"),
]

# Quarter-to-date-range mapping
_QUARTER_DATES = {
    1: ((1, 1), (3, 31)),
    2: ((4, 1), (6, 30)),
    3: ((7, 1), (9, 30)),
    4: ((10, 1), (12, 31)),
}


def _build_rate_table() -> list[RateEntry]:
    entries = []
    for year, quarter, rate_str in _RAW_6621:
        (m_start, d_start), (m_end, d_end) = _QUARTER_DATES[quarter]
        entries.append(RateEntry(
            year=year,
            quarter=quarter,
            rate=Decimal(rate_str),
            effective_from=date(year, m_start, d_start),
            effective_to=date(year, m_end, d_end),
        ))
    return entries


IRS_6621_RATES: list[RateEntry] = _build_rate_table()

# Index for O(1) lookup: (year, quarter) -> rate
_RATE_INDEX: dict[tuple[int, int], Decimal] = {
    (e.year, e.quarter): e.rate for e in IRS_6621_RATES
}


def get_6621_rate(year: int, quarter: int) -> Decimal:
    """Return the §6621 underpayment rate for a given year/quarter."""
    key = (year, quarter)
    if key not in _RATE_INDEX:
        raise ValueError(f"No §6621 rate found for {year} Q{quarter}. Update tax_constants.py.")
    return _RATE_INDEX[key]


def quarter_for_date(d: date) -> int:
    return (d.month - 1) // 3 + 1


# ── Max ordinary income tax rates (IRC §1291(c)(2)) ─────────────────────────
# Each entry covers a range of years. Source: IRC §1 rate schedules.
_MAX_TAX_RATE_TABLE: dict[int, Decimal] = {}

_RAW_MAX_RATES = [
    (1987, 1987, "0.386"),
    (1988, 1990, "0.280"),
    (1991, 1992, "0.310"),
    (1993, 2000, "0.396"),
    (2001, 2002, "0.386"),
    (2003, 2012, "0.350"),
    (2013, 2017, "0.396"),
    (2018, 2099, "0.370"),
]

for _start, _end, _rate in _RAW_MAX_RATES:
    for _y in range(_start, _end + 1):
        _MAX_TAX_RATE_TABLE[_y] = Decimal(_rate)


def get_max_tax_rate(year: int) -> Decimal:
    """Return the historical maximum ordinary income tax rate for a given year."""
    if year not in _MAX_TAX_RATE_TABLE:
        raise ValueError(f"No max tax rate for year {year}. Update tax_constants.py.")
    return _MAX_TAX_RATE_TABLE[year]


# ── §7503 Adjusted filing deadlines ─────────────────────────────────────────
# Statutory date is April 15 of the following year (for calendar-year taxpayers).
# Adjusted for weekends and special COVID extensions.
# Source: IRC §7503, Notice 2020-23, Notice 2021-21.
_FILING_DEADLINES: dict[int, date] = {
    # tax_year: actual_due_date
    1987: date(1988, 4, 18),   # weekend shift
    1988: date(1989, 4, 18),   # weekend shift
    1989: date(1990, 4, 17),   # weekend shift
    1990: date(1991, 4, 15),
    1991: date(1992, 4, 15),
    1992: date(1993, 4, 15),
    1993: date(1994, 4, 15),
    1994: date(1995, 4, 17),   # weekend shift
    1995: date(1996, 4, 15),
    1996: date(1997, 4, 15),
    1997: date(1998, 4, 15),
    1998: date(1999, 4, 15),
    1999: date(2000, 4, 18),   # weekend shift
    2000: date(2001, 4, 16),   # weekend shift
    2001: date(2002, 4, 15),
    2002: date(2003, 4, 15),
    2003: date(2004, 4, 15),
    2004: date(2005, 4, 15),
    2005: date(2006, 4, 17),   # weekend shift
    2006: date(2007, 4, 17),   # weekend shift
    2007: date(2008, 4, 15),
    2008: date(2009, 4, 15),
    2009: date(2010, 4, 15),
    2010: date(2011, 4, 18),   # weekend shift
    2011: date(2012, 4, 17),   # weekend shift
    2012: date(2013, 4, 15),
    2013: date(2014, 4, 15),
    2014: date(2015, 4, 15),
    2015: date(2016, 4, 18),   # weekend shift
    2016: date(2017, 4, 18),   # weekend shift
    2017: date(2018, 4, 17),   # weekend shift
    2018: date(2019, 4, 15),
    2019: date(2020, 7, 15),   # COVID — Notice 2020-23
    2020: date(2021, 5, 17),   # COVID — Notice 2021-21
    2021: date(2022, 4, 18),   # weekend shift
    2022: date(2023, 4, 18),   # weekend shift
    2023: date(2024, 4, 15),
    2024: date(2025, 4, 15),
    2025: date(2026, 4, 15),
}


def get_filing_deadline(tax_year: int) -> date:
    """
    IRC §1291(c)(3)(B): due date = unextended filing deadline (§7503 adjusted).
    Does NOT include filing extensions (Form 4868).
    """
    if tax_year not in _FILING_DEADLINES:
        raise ValueError(
            f"No filing deadline configured for tax year {tax_year}. "
            "Update tax_constants.py."
        )
    return _FILING_DEADLINES[tax_year]
