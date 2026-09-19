"""The books a Japanese verification pass can run over — see docs/plans/translation-plan.md.

Phase 5 started as one pass over Run & Gun with the Japanese edition on the
desk. Three more books are reachable, but not the same way: RF, SG and DT have
no Japanese edition at all. What exists is the *Shadowrun Codex*, a Japanese
compendium that reprints a large part of their content, so it is a translation
source rather than a translation of any one book.

That difference is what `page_is_ja` records. For RG the page number Chummer
stores is also the page in the Japanese edition (checked against the book,
2026-09-05), so the worksheet sorted by page runs in the same order as the
reader's hands. For a Codex-sourced book the page is the *English* book's, and
the reader has to look the term up in the Codex's own index — so the worksheet
says so once, up front, rather than implying an order the book will not follow.

Adding a book here is the whole registration: `make_ja_worksheet.py`,
`import_ja_worksheet.py`, `tests/test_book_coverage.py` and
`import_ja_from_refs.py` all read this table.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Book:
    """One book's pass: where its names come from and where its answers go."""

    code: str
    """The value Chummer writes in a `<source>` tag, e.g. "RG"."""

    title: str
    """The English title, for messages."""

    ja_source: str
    """The printed book a reader answers from — not always a translation of `title`."""

    slug: str
    """Filename infix: `<slug>-worksheet.tsv`, `ja_curated_<slug>.py`."""

    table: str
    """The name of the translated table in that module, e.g. "RG"."""

    page_is_ja: bool
    """Whether the catalog's page number also locates the term in `ja_source`."""

    buckets: tuple[str, ...]
    """Catalog sections in the order to work through them; the rest sort last."""

    @property
    def module(self) -> str:
        return f"ja_curated_{self.slug}"

    @property
    def skipped_table(self) -> str:
        return f"{self.table}_UNVERIFIED"

    def bucket_rank(self, bucket: str) -> int:
        return self.buckets.index(bucket) if bucket in self.buckets else len(self.buckets)


BOOKS: dict[str, Book] = {
    "RG": Book(
        code="RG",
        title="Run & Gun",
        ja_source="ラン＆ガン (Japanese edition)",
        slug="rg",
        table="RG",
        page_is_ja=True,
        # batch order from the plan: most-visible first
        buckets=(
            "martial_arts",
            "martial_art_techniques",
            "qualities",
            "armor",
            "armor_mods",
            "weapons",
            "weapon_accessories",
            "gear",
            "commlinks",
            "category",
        ),
    ),
    "RF": Book(
        code="RF",
        title="Run Faster",
        ja_source="シャドウラン・コデックス",
        slug="rf",
        table="RF",
        page_is_ja=False,
        # the character-building end first: a metatype or quality is picked by
        # everyone who opens the app, a lifestyle quality by almost nobody
        buckets=(
            "metatypes",
            "all_metatypes",
            "qualities",
            "gear",
            "armor",
            "weapons",
            "lifestyles",
            "lifestyle_qualities",
            "critter_powers",
            "category",
        ),
    ),
    "SG": Book(
        code="SG",
        title="Street Grimoire",
        ja_source="シャドウラン・コデックス",
        slug="sg",
        table="SG",
        page_is_ja=False,
        # a tradition and a mentor are chosen once and shown everywhere after
        buckets=(
            "traditions",
            "mentors",
            "magic_arts",
            "metamagics",
            "spells",
            "powers",
            "spirits",
            "critter_powers",
            "enhancements",
            "qualities",
            "gear",
            "category",
        ),
    ),
    "DT": Book(
        code="DT",
        title="Data Trails",
        ja_source="シャドウラン・コデックス",
        slug="dt",
        table="DT",
        page_is_ja=False,
        buckets=(
            "cyberdecks",
            "programs",
            "apps",
            "complex_forms",
            "echoes",
            "commlinks",
            "qualities",
            "gear",
            "category",
        ),
    ),
}


def book(code: str) -> Book:
    """-> the registered book, or raise with the list of codes that exist."""
    try:
        return BOOKS[code.upper()]
    except KeyError:
        raise SystemExit(f"unknown book {code!r} — registered: {', '.join(sorted(BOOKS))}") from None
