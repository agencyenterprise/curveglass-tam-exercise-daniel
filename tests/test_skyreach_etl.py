import csv
from pathlib import Path

import pytest

from etl.skyreach import transform

SRC = Path(__file__).parent.parent / "etl" / "incoming" / "skyreach_export_2026-10-27.csv"


@pytest.fixture(scope="module")
def out():
    with open(SRC, newline="") as fh:
        return transform(list(csv.DictReader(fh)))


def flight(flights, no):
    return [f for f in flights if f["flight_no"] == no]


def test_flight_no_includes_airline(out):
    flights, _, _ = out
    assert {f["airline"] for f in flights} == {"SR"}
    assert flight(flights, "SR211")


@pytest.mark.parametrize("no, segment, market", [
    ("SR210", "FLN-GRU", "FLN-GRU"),
    ("SR211", "GRU-FLN", "FLN-GRU"),
    ("SR306", "EZE-FLN", "EZE-FLN"),
    ("SR413", "CNF-FLN", "CNF-FLN"),
])
def test_segment_and_market(out, no, segment, market):
    flights, _, _ = out
    f = flight(flights, no)[0]
    assert (f["segment"], f["market"]) == (segment, market)


def test_departure_split_into_date_and_time(out):
    flights, _, _ = out
    f = flight(flights, "SR305")[0]
    assert (f["dep_date"], f["dep_time_local"]) == ("2026-11-14", "23:50")


def test_capacity_is_int(out):
    flights, _, _ = out
    assert flight(flights, "SR413")[0]["capacity"] == 118


def test_fare_in_major_units(out):
    _, snaps, _ = out
    s = [s for s in snaps if s["flight_no"] == "SR210"][0]
    assert s["avg_fare"] == pytest.approx(389.90)


def test_snapshot_fields(out):
    _, snaps, _ = out
    s = [s for s in snaps if s["flight_no"] == "SR211"][0]
    assert s["snapshot_date"] == "2026-10-27"
    assert s["seats_sold"] == 120
    assert s["dep_date"] == "2026-11-14"


def test_economy_only_and_no_duplicates(out):
    flights, snaps, _ = out
    assert len(flight(flights, "SR210")) == 1
    assert len([s for s in snaps if s["flight_no"] == "SR210"]) == 1
    assert all(f["capacity"] != 12 for f in flights)


def test_zero_capacity_rejected(out):
    flights, _, rejects = out
    assert not flight(flights, "SR412")
    assert len(rejects) == 1 and rejects[0]["row"]["flight"] == "412"


def test_counts(out):
    flights, snaps, rejects = out
    assert (len(flights), len(snaps), len(rejects)) == (5, 5, 1)
