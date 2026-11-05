"""A career character's karma and nuyen: the earning and spending rows of
`<expenses>` and the balance they leave."""

from __future__ import annotations

import copy
import uuid
import xml.etree.ElementTree as ET  # the Element type only — parsing goes through parse_untrusted
from typing import Any

from ..data_loader import CatalogDict
from ..data_loader._xml import _int, _text
from ..models._common import clamp_input_ints
from ..models.career import DEBT_PAYMENT_REASON
from ..notices import Notice
from ._common import _is_uuid


def _spend_log_from_expenses(root: ET.Element) -> list[dict[str, Any]]:
    """What the save's `<expenses>` spent, as rows with negative amounts.

    History only: what it bought is priced from the character itself, so
    counting these as well would charge for everything twice. They say where
    the balance went, which the adjustment alone cannot.
    """
    out: list[dict[str, Any]] = []
    for el in root.findall("./expenses/expense"):
        amount = _int(el.find("amount"))
        kind = _text(el.find("type")).lower()
        if amount >= 0 or kind not in ("karma", "nuyen") or _is_debt_payment(el):
            continue
        out.append(
            {
                "id": str(uuid.uuid4()),
                "label": _text(el.find("reason")),
                "karma": amount if kind == "karma" else 0,
                "nuyen": amount if kind == "nuyen" else 0,
            }
        )
    return out


def _is_debt_payment(el: ET.Element) -> bool:
    return (
        _text(el.find("type")).lower() == "nuyen"
        and _int(el.find("amount")) < 0
        and _text(el.find("reason")) == DEBT_PAYMENT_REASON
    )


def _debt_payments_from_expenses(root: ET.Element) -> list[dict[str, Any]]:
    """The payments towards In Debt: spent nuyen, counted again on import.

    Unlike the rest of what a save spent, nothing else in the character
    prices these, so they are counted rather than kept as history — and
    the debt left comes back as saved.
    """
    return [
        {
            "id": key if _is_uuid(key := _text(el.find("guid"))) else str(uuid.uuid4()),
            "nuyen": -_int(el.find("amount")),
        }
        for el in root.findall("./expenses/expense")
        if _is_debt_payment(el)
    ]


def _reward_log_from_expenses(root: ET.Element) -> list[dict[str, Any]] | None:
    """`<expenses>` back into reward rows, or `None` when there are none.

    Only what was earned counts — a positive amount that is not a refund.
    Rows this app wrote carry `<rewardid>`, which joins a karma row to the
    nuyen row of the same reward; any other row is a reward of its own.
    """
    rows = root.findall("./expenses/expense")
    if not rows:
        return None
    log: dict[str, dict[str, Any]] = {}
    for el in rows:
        amount = _int(el.find("amount"))
        kind = _text(el.find("type")).lower()
        if amount <= 0 or kind not in ("karma", "nuyen") or _text(el.find("refund")).lower() == "true":
            continue
        key = _text(el.find("rewardid")) or _text(el.find("guid")) or str(uuid.uuid4())
        row = log.setdefault(
            key,
            {
                "id": key if _is_uuid(key) else str(uuid.uuid4()),
                "label": _text(el.find("reason")),
                "karma": 0,
                "nuyen": 0,
            },
        )
        row[kind] += amount
    return list(log.values())


def _import_balance(root: ET.Element, cat: CatalogDict, st: dict[str, Any], warn: list[Notice]) -> None:
    """A career character's money, from the balance Chummer saved.

    Chummer keeps `<karma>` and `<nuyen>` as what is left to spend
    (`Character.Karma` / `Nuyen`) and `<expenses>` as the history. This app
    keeps what was earned — the earning rows of that history, which are also
    what Street Cred counts (`CareerKarma`) — and works the balance out. What
    that leaves apart from the saved balance (rent paid, purchases at their
    own prices) is kept as an adjustment, so the balance comes back as saved.
    """
    if not st.get("career"):
        return
    # read before the v2 return below: its fields predate the payments, and
    # the adjustment it restores was worked out with them counted
    payments = _debt_payments_from_expenses(root)
    if payments:
        st["debt_payments"] = payments
    if root.find("lifemoduleskillstate") is not None:
        # v2 restores the exact baseline, reward ledger and adjustments. The
        # standard projection was verified by the life-module reader already.
        return
    from ..engine import compute
    from ..models import CharacterState

    log = _reward_log_from_expenses(root) or []
    if log:
        st["reward_log"] = log
    spent = _spend_log_from_expenses(root)
    if spent:
        st["expense_log"] = spent
    st["karma_earned"] = sum(row["karma"] for row in log)
    st["nuyen_earned"] = sum(row["nuyen"] for row in log)
    # clamped here as well as on the way out of the read: this validates the
    # state mid-read, before the caller ever sees it.
    bare = clamp_input_ints(copy.deepcopy({k: v for k, v in st.items() if not k.startswith("_")}))
    derived = compute(CharacterState.model_validate(bare)).derived
    try:
        nuyen_balance = round(float(_text(root.find("nuyen")) or 0))
    except ValueError:
        nuyen_balance = 0
    st["karma_adjust"] = _int(root.find("karma")) - int((derived.get("karma") or {}).get("remaining") or 0)
    st["nuyen_adjust"] = nuyen_balance - int(derived.get("nuyen") or 0)
