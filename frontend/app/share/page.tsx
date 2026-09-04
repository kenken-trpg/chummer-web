"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import CharacterSheet, { type SheetLayout } from "@/components/CharacterSheet";
import { LocaleSwitch } from "@/components/LocaleSwitch";
import { api } from "@/lib/api";
import { readShareValue, decodeShare, ShareError, shareErrorMessage } from "@/lib/character/share";
import { useSheetLayout } from "@/lib/character/useSheetLayout";
import { usePrintSheet } from "@/lib/character/usePrintSheet";
import { useUiText } from "@/lib/i18n";
import { makeTr } from "@/lib/ui-strings";
import type { Catalog, Character } from "@/lib/types";

/**
 * The receiving half of a share link (see `lib/character/share.ts`). The
 * payload rides in the fragment, so this route is a plain static page — the
 * server never sees the character. Read-only by construction: it renders
 * `CharacterSheet`, never the editor, and the only mutation offered is
 * "adopt", which reissues an id and hands the visitor a copy of their own.
 */
export default function SharePage() {
  const router = useRouter();
  const { ui, locale } = useUiText();
  const [sheetLayout, setSheetLayout] = useSheetLayout();
  const printSheet = usePrintSheet(sheetLayout, setSheetLayout);
  const [state, setState] = useState<{
    character: Character;
    catalog: Catalog;
  } | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [adopting, setAdopting] = useState(false);

  useEffect(() => {
    let live = true;
    (async () => {
      try {
        const value = readShareValue(window.location.hash);
        if (!value) throw new ShareError("empty");
        const payload = await decodeShare(value);
        // the stateless service validates the payload and returns `derived`
        const [catalog, character] = await Promise.all([api.catalog(), api.preview(payload)]);
        if (live) setState({ catalog, character });
      } catch (e) {
        if (live) setError(shareErrorMessage(e, ui, "share.err.load"));
      }
    })();
    return () => {
      live = false;
    };
    // mount-only: the fragment is fixed for the life of the page
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function adopt() {
    if (!state || adopting) return;
    setAdopting(true);
    try {
      const mine = await api.import({ ...state.character, id: undefined, derived: undefined });
      try {
        localStorage.setItem("lastCharacterId", mine.id);
      } catch {}
      router.push("/");
    } catch (e) {
      setError(shareErrorMessage(e, ui, "share.err.adopt"));
      setAdopting(false);
    }
  }

  if (error) {
    return (
      <div className="main">
        <p className="errors">{error}</p>
        <p>
          <Link className="btn" href="/">
            {ui("share.mine")}
          </Link>
        </p>
      </div>
    );
  }
  if (!state) return <div className="main">{ui("share.loading")}</div>;

  const tr = makeTr(state.catalog, locale);

  return (
    <div className="app sheet-mode">
      <main className="main">
        <header className="no-print">
          <div className="topline">
            <h1>CHUMMER WEB</h1>
            <LocaleSwitch />
          </div>
          <div className="share-banner">
            <strong>{ui("share.title")}</strong>
            <span className="muted">{ui("share.note")}</span>
          </div>

          <div className="toolbar">
            <button className="btn primary" onClick={() => void adopt()} disabled={adopting}>
              {adopting ? ui("share.adopting") : ui("share.adopt")}
            </button>
            <Link className="btn" href="/">
              {ui("share.mine")}
            </Link>
            <select
              className="btn"
              value={sheetLayout}
              onChange={(e) => setSheetLayout(e.target.value as SheetLayout)}
              title={ui("share.layout")}
              aria-label={ui("share.layout")}
            >
              <option value="standard">{ui("sheet.layout.standard")}</option>
              <option value="compact">{ui("sheet.layout.compact")}</option>
              <option value="text">{ui("sheet.layout.text")}</option>
              <option value="print">{ui("sheet.layout.print")}</option>
            </select>
            <button className="btn" onClick={printSheet}>
              {ui("share.print")}
            </button>
          </div>
        </header>

        <CharacterSheet
          character={state.character}
          catalog={state.catalog}
          tr={tr}
          layout={sheetLayout}
        />
      </main>
    </div>
  );
}
