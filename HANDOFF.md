# Handoff: Review ELSTER-Export (Issue #360)

**Branch:** `feature/elster-export` — Review-Objekt: `git diff main...feature/elster-export`

## Kontext

Issue #360 (auftraggeberseitig bestätigt durch Maintainer-Kommentar vom
2026-10-19): UStVA als XML-Nutzdaten-Datei für den Upload in Mein ELSTER +
Zusammenfassende Meldung (ZM) als CSV-Meldeliste. **Nicht im Scope:** ERiC,
Hersteller-ID, Zertifikat, Direktübermittlung.

Implementierung in 4 Commits: Steuernummer-Converter + `GET /api/ustva/xml`,
`GET /api/zm/csv`, Frontend-Download-Buttons, Review-Pass + Doku.

## Aufgabe des Reviews

**Adversarial:** nicht prüfen ob der Code zur Spec passt, sondern ob die
Format-Annahmen stimmen. Die gefährlichsten Fehler sind die, wo Code *und*
Spec dieselbe falsche Annahme teilen → Quellen selbst heranziehen (unten),
nicht nur die Spec.

## Primärquellen (unabhängig heranziehen!)

- UStVA-Upload, offizielle Hilfe:
  <https://www.elster.de/eportal/helpGlobal?themaGlobal=ustva_upload>
  — Root `<Anmeldungssteuern>` (Nutzdaten-only, kein `<Elster>`-Envelope),
  ISO-8859-15, `Kz83` füllt das Steuerfeld, Feld-Ausschlussliste inkl. `Kz09`.
- ZM-Meldelisten-Import, offizielle Hilfe:
  <https://www.elster.de/eportal/helpGlobal?themaGlobal=zmdo_import_eop>
  — Schnittstelle v3.0 (`#v3.0`/`#ve3.2.1` Header), UTF-8, Komma-getrennt,
  max. 1500 Meldezeilen, Feldliste + Beispiel-CSV.
- XSD (öffentlicher Mirror, Version 2013):
  `geierlein/geierlein` Repo → `chrome/content/lib/elster/usta_201301.xsd`
  — `allg_StNrSType` = `\d{4}0\d{8}`, `Zeitraum`-Enum 01–12/41–44, Kz-Typen
  (Ganzzahl vs. `.dd`), `Kz83` + `Kz09` pflichtig.
- Steuernummer-Umrechnung je Bundesland + Testvektoren:
  <https://de.wikipedia.org/wiki/Steuernummer> (Bundesschema-Tabelle).
- Referenz-Implementierungen zum Struktur-Diffen: `NicolasSteinhaus/Numera`
  (`UstVaXmlWriter.cs`, `SteuernummerConverter.cs` inkl. Tests), Microsoft
  BCApps `UstvaXMLFileWriter.Codeunit.al`, `Stunkymonkey/viking`, Forum-
  Thread 425731 (funktionierender Upload-Aufbau).

## Angriffsliste — gezielt bohren

1. **Kz09 = `00000`** (Platzhalter): XSD-Pflicht, Upload ignoriert laut
   Hilfe. Frage: gibt es Belege dass Mein ELSTER den Wert doch validiert?
2. **ZM `D→S`-Mapping**: internes `D` = §13b-Dienstleistung, ELSTER-`D` =
   Dreiecksgeschäft. Prüfen ob das interne Kennzeichen wirklich immer
   „Dienstleistung" meint (`api/zm.py::_kennzeichen`) und ob echte
   Dreiecksgeschäfte im Datenmodell vorkommen können.
3. **Kz83 vs. `kz_83`**: ELSTERs Kz83 ist die Zahllast (aus
   `_elster_rundung`), intern heißt `kz_83` die 19%-Steuer. Mapping korrekt?
4. **Steuernummer-Converter** (`utils/elster.py`): Bundesland-Tabelle,
   Prepend-States (BB/HE/MV/SL/SN/ST/TH), 13-stelliger Passthrough mit
   `\d{4}0\d{8}`, Hessen ohne führende 0. Alle 16 Wikipedia-Vektoren in
   `tests/test_elster_steuernummer.py`.
5. **`version`/`xmlns` = Jahr des Zeitraums** (nicht aktuelles Jahr):
   korrekt für rückwirkende Anmeldungen? Schema-Annahme.
6. **Leere `Unternehmer`-Felder werden weggelassen** (XSD `minLength=1`) —
   aber `Name`/`Vorname` optional im Schema? Gegen XSD prüfen.
7. **ISO-8859-15 mit `xmlcharrefreplace`**: nicht darstellbare Zeichen →
   `&#NNN;`-Entities. Valide, aber stimmt die Annahme dass ELSTER sie
   auflöst statt ablehnt?
8. **Rundung**: Bemessungsgrundlagen volle Euro (`_elster_rundung`),
   Steuer/Vorsteuer centgenau. Kz84/Kz85-Sonderfall (§13b: Basis gerundet,
   Steuer original — Issue #428) im XML korrekt abgebildet?
9. **1500-Zeilen-Limit ZM-CSV** wird nicht geprüft — bewusste Entscheidung,
   aber: sollte bei >1500 nicht mindestens ein 422 statt einer still
   unvollständigen Datei kommen?
10. **Zeitraum-Mapping**: `YYYY-QN` → 41–44, `YYYY-MM` → 01–12 — gegen
    `_zeitraum_grenzen` und XSD-Enum abgleichen.
11. **Tests**: sabotagefest? (`pytest tests/test_elster_*.py` — im Zweifel
    eine Annahme im Code brechen und prüfen dass ein Test fällt.)
12. **`Dateiendungen/Header**: `Content-Disposition: attachment`,
    `application/xml` bzw. `text/csv; charset=utf-8` — ZM-Encoding muss
    UTF-8 sein (ISO-8859-15 wurde von BZSt abgeschafft).

## Reproduzieren

```bash
cd src/backend
.venv/bin/python -m pytest tests/test_elster_*.py -x -q   # 64 Tests
.venv/bin/python -m pytest tests/ -x -q                   # Vollsuite
# Probe-XML erzeugen (Beispiel):
.venv/bin/python - <<'EOF'
from utils.elster import build_ustva_xml, steuernummer_elster13
from decimal import Decimal
class U: firmenname="Muster GmbH"; vorname="Max"; nachname="Mustermann"; \
    strasse="Musterweg"; hausnummer="12"; plz="12345"; ort="Musterstadt"; \
    email=None; telefon=None
print(build_ustva_xml(zeitraum="2026-Q3",
    steuernummer13=steuernummer_elster13("151/815/08154","BY"),
    unternehmen=U(), kz_werte={"81":Decimal("150000"),"83":Decimal("28500")}).decode("iso-8859-15"))
EOF
```

## Bewusst NICHT geprüft (Restrisiko)

- Kein Probe-Upload in Mein ELSTER erfolgt → der ist die finale Validierung.
- Nur 2013er-XSD öffentlich verfügbar; aktuelle Jahresversionen könnten
  zusätzliche Pflichtfelder haben (Hilfeseite nennt ERiC-Docpaket als
  Quelle, das ist registrierungspflichtig).
