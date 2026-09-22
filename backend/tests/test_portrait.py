"""`portrait` is rendered as an <img src>, so the models only keep an inline
raster image — whatever route the value came in by (patch, JSON import, a
shared link)."""

from __future__ import annotations

import pytest

from app.models import CharacterPatch, CharacterState, Priorities, clean_portrait

_PNG = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="


@pytest.mark.parametrize(
    "value",
    [_PNG, "data:image/jpeg;base64,/9j/4AAQ", "data:image/gif;base64,R0lGODlh", "data:image/webp;base64,UklGRg==", ""],
)
def test_a_raster_data_uri_or_nothing_is_kept(value: str) -> None:
    assert clean_portrait(value) == value


@pytest.mark.parametrize(
    "value",
    [
        # a third-party fetch from every viewer of the character
        "https://tracker.example/pixel.png",
        "//tracker.example/pixel.png",
        "javascript:alert(1)",
        "data:image/svg+xml;base64,PHN2Zz48L3N2Zz4=",
        "data:text/html;base64,PGgxPmhpPC9oMT4=",
        # not base64, so not something FileReader or Chummer would have written
        'data:image/png;base64,AAAA" onerror="alert(1)',
        "data:image/png,rawbytes",
    ],
)
def test_anything_else_is_dropped(value: str) -> None:
    assert clean_portrait(value) == ""


def _state(portrait: str) -> CharacterState:
    return CharacterState(id="p", name="p", metatype="Human", attributes={}, priorities=Priorities(), portrait=portrait)


def test_the_models_clean_the_field() -> None:
    assert _state("https://tracker.example/p.png").portrait == ""
    assert _state(_PNG).portrait == _PNG
    assert CharacterPatch(portrait="https://tracker.example/p.png").portrait == ""
    # a patch that does not touch the portrait must not clear it
    assert CharacterPatch().portrait is None


def test_a_portrait_over_the_editor_limit_is_dropped() -> None:
    from app.models._common import MAX_PORTRAIT_CHARS

    head = "data:image/png;base64,"
    fits = head + "A" * (MAX_PORTRAIT_CHARS - len(head))
    assert clean_portrait(fits) == fits
    assert clean_portrait(fits + "AAAA") == ""


def test_an_oversized_mugshot_is_dropped_on_import_with_a_warning() -> None:
    from app.chummer_import import chum5_to_state

    body = "A" * 4_100_000
    raw = f"<character><name>Big</name><mugshots><mugshot>{body}</mugshot></mugshots></character>".encode()
    state, warnings = chum5_to_state(raw)
    assert not state.get("portrait")
    assert "engine.import.portraitDropped" in [w["key"] for w in warnings]


def _png(tag: str) -> str:
    return "iVBORw0KGgo" + tag


def test_three_mugshots_are_imported_main_one_first_and_a_fourth_is_left_out() -> None:
    from app.chummer_import import chum5_to_state

    shots = "".join(f"<mugshot>{_png(t)}</mugshot>" for t in ("AA", "BB", "CC", "DD"))
    raw = f"<character><name>Many</name><mainmugshotindex>2</mainmugshotindex><mugshots>{shots}</mugshots></character>"
    state, _ = chum5_to_state(raw.encode())
    assert state["portrait"] == f"data:image/png;base64,{_png('CC')}"
    assert state["extra_portraits"] == [f"data:image/png;base64,{_png(t)}" for t in ("AA", "BB")]


def test_all_three_portraits_are_exported_as_mugshots_main_one_first() -> None:
    import xml.etree.ElementTree as ET

    from app.characters import import_character
    from app.chummer_export import state_to_chum5
    from tests.test_chummer_export import _rich_state

    pics = [f"data:image/png;base64,{_png(t)}" for t in ("AA", "BB", "CC")]
    state = _rich_state().model_copy(update={"portrait": pics[0], "extra_portraits": pics[1:]})
    root = ET.fromstring(state_to_chum5(import_character(state)))
    assert root.findtext("mainmugshotindex") == "0"
    assert [m.text for m in root.findall("./mugshots/mugshot")] == [_png(t) for t in ("AA", "BB", "CC")]


def test_extra_portraits_keep_only_clean_images_and_at_most_two() -> None:
    ok = f"data:image/png;base64,{_png('AA')}"
    patch = CharacterPatch(extra_portraits=[ok, "https://example.com/x.png", ok, ok])
    assert patch.extra_portraits == [ok, ok]
