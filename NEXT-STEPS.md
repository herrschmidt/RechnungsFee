# Nächste Schritte: ELSTER-Export (Issue #360)

> Lokal per `.git/info/exclude` ignoriert; liegt nur im Fork-Branch `elster-test-material`
> (nicht im PR-Branch). Stand: 2026-10-20.

## Stand

- **PR eingereicht: [#460](https://github.com/nicolettas-muggelbude/RechnungsFee/pull/460)**
  (2026-10-20, offen) – UStVA-XML + ZM-CSV, 11 Commits, `Closes #360`,
  Squash-Merge empfohlen. Kommentar an die Maintainerin in #360:
  <https://github.com/nicolettas-muggelbude/RechnungsFee/issues/360#issuecomment-6262359173>
  (inkl. Angebot Fix-PRs #456/#458 und Rückfrage zur Migration bei #456).
- Branch `feature/elster-export` @ `abfc6064`, auf `main` (4db78d00);
  Upstream-`main` unverändert (Stand 2026-10-20), kein Rebase nötig gewesen.
- Gates vor dem PR: volle Suite 517 grün, `tsc -b` + ESLint sauber.
- **Fork:** <https://github.com/herrschmidt/RechnungsFee>. Remotes je Rechner
  verschieden: hier (Windows, `C:\Users\Martin\dev\RechnungsFee`) ist `origin`
  = Fork, kein Upstream-Remote; auf dem ursprünglichen Rechner `fork` = Fork,
  `origin` = Upstream. Gepusht: `feature/elster-export` (PR-Branch) und
  `elster-test-material` (= PR-Branch-Stand + diese Notiz + `.elster-test/`,
  **nie als PR**).
- Account `herrschmidt` hat im Upstream nur **READ** → PRs aus dem Fork
  (`gh pr create -R nicolettas-muggelbude/RechnungsFee --head herrschmidt:<branch>`).

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
| [#456](https://github.com/nicolettas-muggelbude/RechnungsFee/issues/456) | ZM: EU-B2B-Dienstleistungen fehlen, stornierte §13b-Einkäufe erscheinen | Nein mehr – als bekannte Einschränkung im PR |
| [#457](https://github.com/nicolettas-muggelbude/RechnungsFee/issues/457) | KZ 87 als „Ausfuhr“ beschriftet (richtig: KZ 43) | Nein (Kz87 nie im XML) |
| [#458](https://github.com/nicolettas-muggelbude/RechnungsFee/issues/458) | ig. Lieferungen aus Rechnungszahlungen fehlen in KZ 41 | Nein – als bekannte Einschränkung im PR (im Upload-Test bestätigt) |

## Entscheidung für den PR (2026-10-20, ersetzt die alte Regel)

- **Ein PR mit UStVA-XML + ZM-CSV.** #456 und #458 sind vorbestehende
  Rechenfehler, die Seite/PDF genauso betreffen; die Exporte serialisieren nur.
  Beide werden in `docs/04-ustva.md` und der PR-Beschreibung als bekannte
  Einschränkungen genannt. (Alte Regel „ZM-CSV nur nach #456-Fix“ verworfen –
  sonst müsste wegen #458 konsequenterweise auch die UStVA-XML warten.)
- **Fix-PRs für #456/#458 erst nach Merge des Export-PRs** und nach Rückmeldung
  der Maintainerin: Beide berühren `api/zm.py` bzw. die Berechnung (Konflikt-
  und Rebase-Risiko bei gestapelten PRs), #456 hat eine offene Designfrage
  (Migration von Altbuchungen vor #372), und die Maintainerin fixt solche
  Issues oft selbst. Danach erneuter Upload-Test für ZM-Art „S“ und Kz41.

## Upload-Test in Mein ELSTER (durchgeführt 2026-10-20)

**Ergebnis: beide Dateien ohne Fehler importiert, die berechneten Werte
unverändert übernommen – nichts abgesendet.** Verifiziert sind Format und
Übernahme, nicht die Berechnung: Die Test-Rechnung RE-250007 (ig. Lieferung,
1.500 €) steht in der ZM, fehlt aber als Kz41 in der UStVA (`kz_41 = 0.00`,
genau #458). Getestet mit ad-hoc-Testdaten (Q1/2025, BW-Firma
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

### Windows (Git Bash) – Stolpersteine

- Datenverzeichnis ist `%APPDATA%\RechnungsFee` (nicht `HOME`) → isolieren mit
  `APPDATA='C:\tmp\rf-elster-test'` statt `HOME=…` (Windows-Pfad angeben). Auf diesem Rechner liegt dort
  seit 2026-10-20 nur die Test-DB dieses Laufs (Profil `Standard`) – vor einer
  echten Installation der App löschen.
- venv-Pfade: `.venv/Scripts/python` statt `.venv/bin/…`.
- `seed_testdaten.py` braucht `PYTHONIOENCODING=utf-8` (Box-Zeichen) und
  bricht bei den Bar-Journalbuchungen ab, wenn kein Kassenanfangsbestand
  gesetzt ist (`POST /api/setup/kassenbestand`).
- `git show <ref>:<pfad>` braucht `MSYS_NO_PATHCONV=1`.
- `CLAUDE.md`/`claude.md` kollidieren (case-insensitives Dateisystem) →
  `CLAUDE.md` erscheint dauerhaft als geändert; **nie mit committen**.

## Nach dem Merge von #460

1. Fix-PRs für #456 (nach Antwort der Maintainerin zur Migration) und #458,
   jeweils eigener Branch von aktuellem `main`.
2. Erneuter Upload-Test: ZM-Art „S“ und Kz41.
3. Danach `NEXT-STEPS.md`, `.elster-test/` und den Fork-Branch
   `elster-test-material` löschen.
