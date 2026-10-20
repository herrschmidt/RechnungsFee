# Nächste Schritte: ELSTER-Export (Issue #360)

> Lokal per `.git/info/exclude` ignoriert; liegt nur im Fork-Branch `elster-test-material`
> (nicht im PR-Branch). Stand: 2026-10-20.

## Stand

- Branch `feature/elster-export`, 10 Commits auf `main` (4db78d00)
  – zuletzt `25073184` (ZM-Button „ELSTER-CSV“) und die Doku zum
  Upload-Test. Upstream-`main` hat seitdem keine neuen Commits (Stand
  2026-10-20).
- **Fork:** <https://github.com/herrschmidt/RechnungsFee> (lokal Remote `fork`,
  `origin` = Upstream). Gepusht: `feature/elster-export` (PR-Branch) und
  `elster-test-material` (= PR-Branch + diese Notiz + `.elster-test/`, **nie als PR**).
- Adversarial Review erledigt, Fixes committet (`cf23e5c2`, `65d7ca01`).
  Tests: 517 grün (volle Suite), `tsc -b` sauber.
- Account `herrschmidt` hat im Upstream nur **READ** → PR aus dem Fork:
  `gh pr create -R nicolettas-muggelbude/RechnungsFee --head herrschmidt:feature/elster-export`.
- `HANDOFF.md` wurde in `7b0de578` angelegt und in `65d7ca01` wieder gelöscht –
  beim PR auf Squash-Merge hinweisen oder vorher zusammenfassen.

### Auf einem anderen Rechner

```bash
git clone https://github.com/herrschmidt/RechnungsFee.git && cd RechnungsFee
git switch elster-test-material   # enthält NEXT-STEPS.md + .elster-test/
```

Änderungen am Code immer auf `feature/elster-export` committen, nicht auf
`elster-test-material`.

## Offene Issues (Upstream, von uns angelegt)

| Issue | Inhalt | Blocker? |
|---|---|---|
| [#456](https://github.com/nicolettas-muggelbude/RechnungsFee/issues/456) | ZM: EU-B2B-Dienstleistungen fehlen, stornierte §13b-Einkäufe erscheinen | **Ja für ZM-CSV** |
| [#457](https://github.com/nicolettas-muggelbude/RechnungsFee/issues/457) | KZ 87 als „Ausfuhr“ beschriftet (richtig: KZ 43) | Nein (Kz87 nie im XML) |
| [#458](https://github.com/nicolettas-muggelbude/RechnungsFee/issues/458) | ig. Lieferungen aus Rechnungszahlungen fehlen in KZ 41 | Offen – XML enthält dann kein Kz41 |

## Entscheidungsregel für den PR

- **#456 vor den Upload-Tests gefixt** → gesamten PR einreichen (UStVA-XML + ZM-CSV).
- **Sonst** → PR nur mit UStVA-XML. Die ZM-CSV steckt in `93390b50` (Backend +
  Tests) sowie im ZM-Teil von `9df8ca40`, `cf23e5c2` (ZMPage, `downloadZmCsv`,
  `build_zm_csv`) und in `docs/04-ustva.md` → herauslösen.
- **#458** noch entscheiden: entweder abwarten oder im PR als bekannte
  Einschränkung nennen (Fehler besteht schon vorher, betrifft auch Anzeigehilfe/PDF).

## Upload-Test in Mein ELSTER (durchgeführt 2026-10-20)

**Ergebnis: beide Dateien ohne Fehler importiert, Werte korrekt übernommen –
nichts abgesendet.** Getestet mit ad-hoc-Testdaten (Q1/2025, BW-Firma
`93/815/08152` → `2893081508152`, AT-Kunde `ATU12345675`), Dateien in
`.elster-test/`: `UStVA_2025-Q1_ELSTER.xml`, `ZM_2025-Q1_ELSTER.csv`.

- **UStVA-XML:** Formular befüllt ohne Fehlermeldung. Kz81 2500 → ELSTER
  rechnete selbst 475 € (19 %), Kz66 11,40, Kz83 463,60, Zeitraum
  I. Kalendervierteljahr 2025, Steuernummer in Landesformat angezeigt.
  Prüfmodus: keine Fehler.
- **ZM-CSV:** eine Meldezeile `ATU12345675, 1.500 €, Innergemeinschaftliche
  Lieferung` übernommen, Prüfmodus ohne Fehler. Nur Art „L" upload-getestet;
  „S" (§13b-Dienstleistung) deckt der Test nicht ab – hängt ohnehin an #456.
- **Lernpunkt USt-IdNr.:** ELSTERs Plausi-Prüfung prüft Format + Prüfziffer
  offline. `ATU12345678` → Hinweis „unschlüssig"; mit korrekter Prüfziffer
  (`ATU12345675`, Luhn-basiert) ohne Hinweis akzeptiert. Für Testdaten also
  prüfziffergültige IDs verwenden.

Nachfolgend das ursprüngliche Testsetup mit den kanonischen Q3/2026-Dateien
(für Wiederholungstests, z. B. nach Rebase oder #456-Fix).

Nur hochladen, prüfen, **abbrechen – nie absenden**. Fiktive Testdaten.

Fertige Dateien liegen in `.elster-test/` (erzeugt mit HEAD `65d7ca01`):
- `UStVA_2026-Q3_ELSTER.xml` → Formular *Umsatzsteuer-Voranmeldung 2026*, XML-Upload
- `ZM_2026-Q3_ELSTER.csv` → ZM-Formular, CSV-Import

Erwartete Werte UStVA Q3/2026: Kz81 1235 · Kz86 300 · Kz84 500 · Kz85 95,00 ·
Kz66 19,00 · Kz67 95,00 · **Kz83 236,65** (ELSTER rechnet nach – keine
Abweichungsmeldung erwartet). Name „Test & Söhne Gärtnerei GmbH“ mit Umlauten
korrekt? Kz41 fehlt (bekannt, #458). Hinweise zu Steuernummer/Finanzamt
(Beispiel-Steuernummer 133/8150/8159) bzw. zur Test-USt-IdNr. sind
Testdaten-bedingt.

Erwartet ZM: eine Zeile `FR40303265045,2000,L` (#456 betrifft nur Art „S“).

### Testumgebung neu aufsetzen (falls über die App klicken)

Isoliert über eigenes HOME – echte Daten unter `~/.local/share/RechnungsFee`
bleiben unberührt.

```bash
# Terminal 1 – Backend mit Wegwerf-Daten
cd src/backend && HOME=/tmp/rf-elster-test .venv/bin/uvicorn main:app --port 8002
# Terminal 2 – Frontend (http://localhost:5173, Routen /ustva und /zm)
cd src/frontend && npm run dev
# Terminal 3 – Testdaten einspielen (idempotent, nur echte HTTP-Endpunkte)
python3 .elster-test/seed.py
```

In der App **Q3 / 2026** wählen (voreingestellt ist das laufende Quartal).
Bei Remote-Zugriff: Port 5173 weiterleiten oder die fertigen Dateien oben nutzen.

## Vor dem PR

1. Auf aktuellen Upstream-`main` rebasen, volle Suite + `tsc -b` laufen lassen.
2. PR-Beschreibung: kein ERiC/Zertifikat; Kz09-Platzhalter `00000` (laut
   ELSTER-Hilfe beim Upload ignoriert); kein `<Unternehmer>`-Block; manuelle
   Felder → XML ausgeblendet; geprüft gegen Jahresdokumentation UStVA 2026
   (ERiC 43.4); Ergebnis des Upload-Tests; Verweise auf #456/#457/#458.
3. Danach `NEXT-STEPS.md`, `.elster-test/` und den Fork-Branch
   `elster-test-material` löschen.
