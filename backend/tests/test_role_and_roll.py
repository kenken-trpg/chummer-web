"""Role&Roll: magazine issues reprinting English-supplement items in Japanese
(backend/app/data_loader/role_and_roll.py, scripts/rr_resolve.py)."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from app.catalog_view import public_catalog
from app.data_loader import role_and_roll as rr
from scripts import rr_resolve

WANTED = "1e3d8aff-c31c-41f9-8c62-e3332cac79fa"  # RF, also in the Codex
SPEED_DEMON = "5bcfc0fc-1e46-4ba9-a48c-7b623e9ab8db"  # R5


BASE = rr.Entry(
    line=2,
    url="",
    vol=215,
    page="88",
    source="R5",
    category="資質",
    ja="スピードデーモン",
    english="",
    note="",
    ids=(SPEED_DEMON,),
)


def _entry(**kw) -> rr.Entry:
    return replace(BASE, **kw)


def _find(node, id_):
    return [row for row in rr._rows(node) if row["id"] == id_]


def test_one_book_per_issue_none_of_them_chummers():
    codes = [book["code"] for book in rr.books()]
    assert codes[0] == "RR213" and codes[-1] == "RR241" and len(codes) == 29
    assert all(book["group"] == "RR" for book in rr.books())
    assert not set(codes) & {book["code"] for book in public_catalog()["books"]}


def test_the_shipped_entries_have_no_problems():
    # the hand-typed file: a typo in an id or a vol. fails here, not on screen
    assert rr.problems(rr.load(), public_catalog()) == []


def test_a_wrong_header_is_refused(tmp_path: Path):
    path = tmp_path / "entries.tsv"
    path.write_text("URL\tvol.\t和訳名\n", encoding="utf-8")
    with pytest.raises(ValueError, match="header"):
        rr.load(path)


def test_load_and_save_round_trip(tmp_path: Path):
    path = tmp_path / "entries.tsv"
    rows = [_entry(), _entry(line=3, vol=216, ids=(), note="要確認")]
    rr.save(rows, path)
    assert rr.load(path) == rows
    # "vol.215" and short rows are read too
    path.write_text("\t".join(rr.COLUMNS) + "\n\tVol.215\t9\n", encoding="utf-8")
    assert rr.load(path)[0].vol == 215


def test_stamp_adds_the_issue_beside_the_codex():
    catalog = public_catalog()
    names = rr.stamp(catalog, [_entry(source="RF", ja="お尋ね者", ids=(WANTED,))])
    assert names == {"RR215": {"Wanted": "お尋ね者"}}
    for row in _find(catalog, WANTED):
        assert row["also_in"] == [
            {"source": "SRCX", "page": "200"},
            {"source": "RR215", "page": "88"},
        ]
    # the issue's name is per book: the global table still has the Codex's
    assert catalog["translations"]["Wanted"] == "賞金首"


def test_a_row_without_an_id_changes_nothing():
    catalog = public_catalog()
    assert rr.stamp(catalog, [_entry(ids=())]) == {}
    assert all("also_in" not in row for row in _find(catalog, SPEED_DEMON))


@pytest.mark.parametrize(
    ("entry", "message"),
    [
        (_entry(vol=300), "vol. must be"),
        (_entry(vol=None), "vol. must be"),
        (_entry(ja=""), "和訳名 is empty"),
        (_entry(source="No Such Book"), "unknown 出典原書"),
        (_entry(ids=("not-an-id",)), "no catalog entry"),
        (_entry(source="CF"), "is from R5, not CF"),
        (_entry(english="Chaser"), "not 'Chaser'"),
    ],
)
def test_problems(entry: rr.Entry, message: str):
    (problem,) = rr.problems([entry], public_catalog())
    assert message in problem


def test_problems_across_rows():
    rows = [
        _entry(url="https://a"),
        _entry(line=3, url="https://b", ids=()),
        _entry(line=4),
    ]
    assert rr.problems(rows, public_catalog()) == [
        "line 3: vol.215 has another URL on an earlier line",
        "line 4: Speed Demon is listed twice in vol.215",
    ]


def test_candidates_by_book_category_and_name():
    catalog = public_catalog()
    hits = rr.candidates(_entry(english="speed demon", ids=()), catalog)
    assert [row["id"] for _, row in hits] == [SPEED_DEMON]
    # one name, several Chrome Flesh entries: all of them
    tattoos = _entry(source="Chrome Flesh", category="サイバーウェア", english="Nanotattoos")
    assert len(rr.candidates(tattoos, catalog)) > 1
    # no English: the book's entries of that 分類
    rows = rr.candidates(_entry(ids=()), catalog)
    assert all(section == "qualities" and row["source"] == "R5" for section, row in rows)


def test_resolve_fills_ids_from_the_english_name(tmp_path: Path, capsys):
    path = tmp_path / "entries.tsv"
    rr.save([_entry(ids=(), english="Speed Demon"), _entry(line=3, vol=216, ids=())], path)
    assert rr_resolve.main(["--file", str(path), "--write", "--limit", "1"]) == 0
    first, second = rr.load(path)
    assert first.ids == (SPEED_DEMON,) and second.ids == ()
    out = capsys.readouterr().out
    assert "no English name" in out and "1 row(s) with ids, 1 without" in out


def test_the_catalog_carries_names_per_issue_but_not_the_codex_ones(monkeypatch):
    rows = [
        _entry(),
        _entry(line=3, source="RF", ja="お尋ね者", ids=(WANTED,)),
    ]
    monkeypatch.setattr(rr, "load", lambda path=rr.DATA: rows)
    catalog = public_catalog()
    # Wanted keeps the Codex's 賞金首 everywhere; the issue still lists the page
    assert catalog["book_translations"] == {"RR215": {"Speed Demon": "スピードデーモン"}}
    assert {"source": "RR215", "page": "88"} in _find(catalog, WANTED)[0]["also_in"]
    assert "RR215" not in {book["code"] for book in catalog["books"]}
