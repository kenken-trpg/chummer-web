from __future__ import annotations

from fastapi import Body, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .chummer_import import chum5_to_state
from .models import CharacterCreate, CharacterPatch
from .store import (
    create_character,
    delete_character,
    export_character,
    get_character,
    import_character,
    list_characters,
    public_catalog,
    update_character,
)

app = FastAPI(
    title="Chummer Web",
    description="Unofficial Shadowrun 5e character creator. Not affiliated with Catalyst Game Labs.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health() -> dict:
    return {"ok": True}


@app.get("/api/catalog")
def catalog_endpoint() -> dict:
    try:
        return public_catalog()
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@app.post("/api/characters")
def create(payload: CharacterCreate | None = None) -> dict:
    return create_character(payload).model_dump()


@app.get("/api/characters")
def roster() -> list[dict]:
    return list_characters()


@app.delete("/api/characters/{cid}")
def delete(cid: str) -> dict:
    delete_character(cid)
    return {"ok": True}


@app.get("/api/characters/{cid}")
def read(cid: str) -> dict:
    try:
        return get_character(cid).model_dump()
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="character not found") from exc


@app.patch("/api/characters/{cid}")
def patch(cid: str, payload: CharacterPatch) -> dict:
    try:
        return update_character(cid, payload).model_dump()
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="character not found") from exc
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/api/characters/{cid}/export")
def export_json(cid: str) -> dict:
    try:
        return export_character(cid)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="character not found") from exc


@app.post("/api/characters/import")
def import_json(payload: dict) -> dict:
    try:
        return import_character(payload).model_dump()
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/characters/import-chummer")
def import_chummer(body: bytes = Body(..., media_type="application/octet-stream")) -> dict:
    """Import a Chummer5a .chum5 / .chum5lz save. Returns the character plus a
    list of things that could not be mapped."""
    try:
        state, warnings = chum5_to_state(body)
        state.pop("_warnings", None)
        char = import_character(state)
        return {"character": char.model_dump(), "warnings": warnings}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=f"取り込みに失敗しました: {exc}") from exc
