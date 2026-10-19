"""ELSTER-Export-Utilities (Stufe 1: Datei-Upload in Mein ELSTER, kein ERiC).

Enthält:
- steuernummer_elster13(): Umrechnung der Landes-Steuernummer ins 13-stellige
  Bundesschema (BUFA-Nr. + "0" + Bezirk + Unterscheidungsnr. + Prüfziffer,
  Schema \d{4}0\d{8} lt. ELSTER-XSD allg_StNrSType).

Quellen: ELSTER-Hilfe themaGlobal=ustva_upload / zmdo_import_eop,
Bundesland-Umrechnungstabelle de.wikipedia.org/wiki/Steuernummer,
ERiC-Schemata (geierlein: usta_201301.xsd), digitalservicebund/erica.
"""

import re
from datetime import date
from decimal import Decimal
from xml.sax.saxutils import escape

# BUFA-Präfix je Bundesland (erste 4 Stellen = Landespräfix + Finanzamtsnummer).
# Länder mit "prepend": im Landesformat steht der Finanzamtsnummer eine
# Ziffer voran (z. B. HE "0FF/…", TH "151/…"), die vor dem Präfix entfällt;
# beide Schreibweisen werden akzeptiert.
_LAND_TABELLE: dict[str, tuple[str, bool]] = {
    "BW": ("28", False),
    "BY": ("9", False),
    "BE": ("11", False),
    "BB": ("30", True),
    "HB": ("24", False),
    "HH": ("22", False),
    "HE": ("26", True),
    "MV": ("40", True),
    "NI": ("23", False),
    "NW": ("5", False),
    "RP": ("27", False),
    "SL": ("10", True),
    "SN": ("32", True),
    "ST": ("31", True),
    "SH": ("21", False),
    "TH": ("41", True),
}

_TRENNER = re.compile(r"[\s/\-.]+")
_STNR_13 = re.compile(r"\d{4}0\d{8}")


class ElsterExportFehler(ValueError):
    """Export kann nicht erzeugt werden (für 422-Antworten)."""


class SteuernummerFehler(ElsterExportFehler):
    """Ungültige oder nicht umrechenbare Steuernummer."""


def steuernummer_elster13(steuernummer: str | None, bundesland: str | None) -> str:
    r"""Rechnet die Landes-Steuernummer in das 13-stellige ELSTER-Format um.

    Akzeptiert die Schreibweisen der Länder ("93/815/08152", "181-815-08155",
    "133/8150/8159") sowie bereits konvertierte 13-stellige Nummern
    (durchgereicht, wenn sie dem Schema \d{4}0\d{8} entsprechen).
    """
    if not bundesland or not bundesland.strip():
        raise SteuernummerFehler(
            "Bundesland fehlt – bitte in den Stammdaten hinterlegen."
        )
    land = bundesland.strip().upper()
    if land not in _LAND_TABELLE:
        raise SteuernummerFehler(f"Unbekanntes Bundesland: {bundesland!r}")

    if not steuernummer or not steuernummer.strip():
        raise SteuernummerFehler(
            "Steuernummer fehlt – bitte in den Stammdaten hinterlegen."
        )
    roh = steuernummer.strip()
    if re.match(r"^[A-Za-z]{2}", roh):
        raise SteuernummerFehler(
            "Das sieht nach einer USt-IdNr aus – ELSTER braucht die lokale "
            "Steuernummer vom Finanzamt, nicht die USt-IdNr."
        )
    ziffern = _TRENNER.sub("", roh)
    if not ziffern.isdigit():
        raise SteuernummerFehler(
            f"Steuernummer {roh!r} enthält ungültige Zeichen – erlaubt sind "
            "Ziffern sowie '/', '-', '.' und Leerzeichen."
        )

    # Bereits konvertiert (13-stellig, "0" an 5. Stelle) → durchreichen
    if len(ziffern) == 13:
        if _STNR_13.fullmatch(ziffern):
            return ziffern
        raise SteuernummerFehler(
            "13-stellige Steuernummer ohne '0' an 5. Stelle – das ist kein "
            "gültiges ELSTER-Bundesschema."
        )

    praefix, prepend = _LAND_TABELLE[land]
    erwartet = 12 - len(praefix)  # 10 Ziffern bei 2-stelligem, 11 bei 1-stelligem Präfix
    if prepend and len(ziffern) == erwartet + 1:
        ziffern = ziffern[1:]
    if len(ziffern) != erwartet:
        raise SteuernummerFehler(
            f"Steuernummer {roh!r} hat für {land} die falsche Länge – "
            f"erwartet werden {erwartet} Ziffern im Landesformat."
        )

    kombiniert = praefix + ziffern
    ergebnis = kombiniert[:4] + "0" + kombiniert[4:]
    if not _STNR_13.fullmatch(ergebnis):
        raise SteuernummerFehler(
            f"Umrechnung von {roh!r} ({land}) ergab kein gültiges "
            "ELSTER-Bundesschema."
        )
    return ergebnis


# ---------------------------------------------------------------------------
# UStVA-XML (Nutzdaten für den Upload in Mein ELSTER)
# ---------------------------------------------------------------------------

# Datentypen der Kennziffern gemäß ELSTER-XSD (usta_*.xsd, Schema-Konventionen):
# - Ganzzahl-Typ  usta_DefaultKZSType:         -?\d{1,13}
# - Cent-Typ      usta_DefaultKZSTypewithCent: -?\d{1,11}\.\d{2} (Punkt!)
_KZ_GANZZAHL = {
    "21", "35", "41", "42", "43", "44", "45", "46", "48", "49", "52", "60",
    "68", "73", "76", "77", "78", "81", "84", "86", "87", "89", "90", "91",
    "93", "94", "95",
}
_KZ_CENT = {
    "36", "47", "53", "59", "61", "62", "63", "64", "65", "66", "67", "69",
    "74", "79", "80", "83", "85", "96", "98",
}
_KZ_FLAGS = {"10", "22", "26", "29"}  # Ja/Nein-Merker, Schema-Enumeration "1"

# Kz09 ist laut XSD Pflicht, wird beim Mein-ELSTER-Upload aber ausdrücklich
# ignoriert (offizielle Hilfe, Ausschlussliste). RechnungsFee hat keine
# ERiC-Hersteller-ID → neutraler 5-stelliger Platzhalter.
_KZ09_PLATZHALTER = "00000"

_USTVA_NS = "http://finkonsens.de/elster/elsteranmeldung/ustva/v{jahr}"


def _e(text: object | None, max_len: int) -> str:
    """XML-escapen und auf XSD-maxLength kürzen."""
    return escape(str(text or "").strip())[:max_len]


def _format_kz(nr: str, wert: Decimal) -> str:
    if nr in _KZ_FLAGS:
        return "1"
    if nr in _KZ_GANZZAHL:
        return str(int(wert))
    if nr in _KZ_CENT:
        return f"{wert:.2f}" if wert >= 0 else f"-{abs(wert):.2f}"
    raise ElsterExportFehler(f"Unbekannte ELSTER-Kennziffer: Kz{nr}")


def build_ustva_xml(
    *,
    zeitraum: str,
    steuernummer13: str,
    unternehmen,
    kz_werte: dict[str, Decimal],
) -> bytes:
    """Baut die UStVA-Nutzdaten-XML für den Upload in Mein ELSTER (kein ERiC).

    zeitraum: "YYYY-MM" (Monat) oder "YYYY-QN" (Quartal).
    kz_werte: ELSTER-Kennziffer → Betrag. Bemessungsgrundlagen bereits
        gerundet (volle Euro) übergeben, Steuerbeträge centgenau.
        Kz83 (verbleibende Steuer) ist Pflicht und wird ggf. mit 0.00 gesetzt.
    """
    if not _STNR_13.fullmatch(steuernummer13 or ""):
        raise ElsterExportFehler(
            f"Steuernummer nicht im 13-stelligen ELSTER-Format: {steuernummer13!r}"
        )

    if "-Q" in zeitraum:
        jahr_s, q = zeitraum.split("-Q")
        zr = f"4{int(q)}"
    else:
        jahr_s, monat = zeitraum.split("-")
        zr = f"{int(monat):02d}"
    jahr = int(jahr_s)

    name = getattr(unternehmen, "firmenname", "") or " ".join(
        p for p in (getattr(unternehmen, "vorname", None),
                    getattr(unternehmen, "nachname", None)) if p
    )
    strasse_komplett = " ".join(
        p for p in (getattr(unternehmen, "strasse", ""),
                    getattr(unternehmen, "hausnummer", "")) if p
    ).strip()

    kz_werte = dict(kz_werte)
    kz_werte.setdefault("83", Decimal("0.00"))
    kz_teile = [f"      <Kz09>{_KZ09_PLATZHALTER}</Kz09>"]
    for nr in sorted(set(kz_werte)):
        wert = kz_werte[nr]
        if nr != "83" and wert == 0:
            continue  # 0-Kennziffern werden nicht übertragen
        kz_teile.append(f"      <Kz{nr}>{_format_kz(nr, wert)}</Kz{nr}>")

    zeilen = [
        '<?xml version="1.0" encoding="ISO-8859-15" standalone="no"?>',
        f'<Anmeldungssteuern xmlns="{_USTVA_NS.format(jahr=jahr)}" version="{jahr}">',
        f"  <Erstellungsdatum>{date.today():%Y%m%d}</Erstellungsdatum>",
        "  <DatenLieferant>",
        f"    <Name>{_e(name, 45)}</Name>",
        f"    <Strasse>{_e(strasse_komplett, 30)}</Strasse>",
        f"    <PLZ>{_e(getattr(unternehmen, 'plz', ''), 12)}</PLZ>",
        f"    <Ort>{_e(getattr(unternehmen, 'ort', ''), 30)}</Ort>",
    ]
    if getattr(unternehmen, "telefon", None):
        zeilen.append(f"    <Telefon>{_e(unternehmen.telefon, 35)}</Telefon>")
    if getattr(unternehmen, "email", None):
        zeilen.append(f"    <Email>{_e(unternehmen.email, 100)}</Email>")
    zeilen += [
        "  </DatenLieferant>",
        "  <Steuerfall>",
        "    <Unternehmer>",
        f"      <Bezeichnung>{_e(name, 45)}</Bezeichnung>",
        f"      <Name>{_e(getattr(unternehmen, 'nachname', ''), 45)}</Name>",
        f"      <Vorname>{_e(getattr(unternehmen, 'vorname', ''), 45)}</Vorname>",
        f"      <Str>{_e(getattr(unternehmen, 'strasse', ''), 30)}</Str>",
        f"      <Hausnummer>{_e(getattr(unternehmen, 'hausnummer', ''), 12)}</Hausnummer>",
        f"      <Ort>{_e(getattr(unternehmen, 'ort', ''), 30)}</Ort>",
        f"      <PLZ>{_e(getattr(unternehmen, 'plz', ''), 12)}</PLZ>",
    ]
    if getattr(unternehmen, "telefon", None):
        zeilen.append(f"      <Telefon>{_e(unternehmen.telefon, 35)}</Telefon>")
    if getattr(unternehmen, "email", None):
        zeilen.append(f"      <Email>{_e(unternehmen.email, 100)}</Email>")
    zeilen += [
        "    </Unternehmer>",
        "    <Umsatzsteuervoranmeldung>",
        f"      <Jahr>{jahr}</Jahr>",
        f"      <Zeitraum>{zr}</Zeitraum>",
        f"      <Steuernummer>{steuernummer13}</Steuernummer>",
        *kz_teile,
        "    </Umsatzsteuervoranmeldung>",
        "  </Steuerfall>",
        "</Anmeldungssteuern>",
    ]
    # ISO-8859-15-nicht darstellbare Zeichen (z. B. „—“, Emoji) als numerische
    # XML-Entitäten (&#NNN;) schreiben – valide XML, ELSTER dekodiert korrekt.
    return "\n".join(zeilen).encode("iso-8859-15", errors="xmlcharrefreplace")
