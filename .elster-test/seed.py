"""Throwaway-Seed für den ELSTER-Export-Test (Issue #360 Review).
Läuft gegen http://localhost:8002 mit isoliertem HOME=/tmp/rf-elster-test.
Nutzt ausschließlich die echten HTTP-Endpunkte (wie das Frontend)."""
import json
import urllib.request

BASE = "http://localhost:8002/api"


def req(method, path, data=None):
    r = urllib.request.Request(
        BASE + path, method=method,
        data=json.dumps(data).encode() if data is not None else None,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(r) as resp:
        body = resp.read()
        return json.loads(body) if body else {}


# --- Stammdaten: Unternehmen (macht /setup zufrieden, Teil 1) ---
_methode_unt = "PUT" if req("GET", "/unternehmen") else "POST"
unt = req(_methode_unt, "/unternehmen", {
    "firmenname": "Test & Söhne Gärtnerei GmbH",
    "strasse": "Musterweg",
    "hausnummer": "12a",
    "plz": "40213",
    "ort": "Düsseldorf",
    "telefon": "0211 1234567",
    "email": "test@example.org",
    "bundesland": "NW",
    "steuernummer": "133/8150/8159",
    "ist_kleinunternehmer": False,
    "voranmeldungsrhythmus": "quartal",
    "versteuerungsart": "ist",
    "kontenrahmen": "SKR03",
})
print("unternehmen:", unt["id"], unt["firmenname"])

# --- Konto (Setup-Gate Teil 2) ---
konto = (req("GET", "/konten?nur_aktive=false") or [None])[0]
if not konto:
    konto = req("POST", "/konten", {
    "name": "Geschäftskonto",
    "anbieter": "Testbank",
    "kontoart": "bank",
    "iban": "DE89370400440532013000",
    "kontotyp": "geschaeftlich",
    "ist_standard": True,
})
print("konto:", konto["id"])

# --- Kategorien nachschlagen ---
kategorien = {k["name"]: k for k in req("GET", "/kategorien")}
kat_erloes19 = kategorien["Betriebseinnahmen"]
kat_erloes7 = kategorien["Betriebseinnahmen (7%)"]
kat_ig = kategorien["Innergemeinschaftliche Lieferungen"]
kat_buero = kategorien["Büromaterial"]
kat_bau = kategorien["Bauleistungen / §13b Abs. 2"]

# --- Kunden ---
kunde_inland = req("POST", "/kunden", {
    "firmenname": "Inland Kunde GmbH",
    "strasse": "Hauptstr.", "hausnummer": "1",
    "plz": "10115", "ort": "Berlin", "land": "DE",
})
kunde_fr = req("POST", "/kunden", {
    "firmenname": "Client Test SARL",
    "strasse": "Rue de Test", "hausnummer": "5",
    "plz": "75001", "ort": "Paris", "land": "FR",
    "ust_idnr": "FR40303265045",
})
print("kunden:", kunde_inland["id"], kunde_fr["id"])


def rechnung(kunde_id, datum, netto, ust_satz, beschreibung, kategorie_id,
             zahlungsdatum, **extra):
    r = req("POST", "/rechnungen", {
        "typ": "ausgang",
        "kunde_id": kunde_id,
        "datum": datum,
        "ist_entwurf": False,
        "positionen": [{
            "beschreibung": beschreibung,
            "menge": "1",
            "netto": netto,
            "ust_satz": ust_satz,
            "kategorie_id": kategorie_id,
        }],
        **extra,
    })
    z = req("POST", f"/rechnungen/{r['id']}/zahlung-bar", {
        "datum": zahlungsdatum,
        "zahlungsart": "Bank",
    })
    print(f"rechnung {r['id']} ({beschreibung}): {r['rechnungsnummer']} -> zahlung {z}")
    return r


# a) Inland 19 %
rechnung(kunde_inland["id"], "2026-07-15", "1234.56", "19",
         "Beratungsleistung Juli", kat_erloes19["id"], "2026-07-28")
# b) Inland 7 %
rechnung(kunde_inland["id"], "2026-08-10", "300.00", "7",
         "Pflanzenlieferung", kat_erloes7["id"], "2026-08-20")
# c) Innergemeinschaftliche Lieferung FR, 0 %
rechnung(kunde_fr["id"], "2026-09-05", "2000.00", "0",
         "Innergemeinschaftliche Lieferung", kat_ig["id"], "2026-09-18",
         ist_eu_lieferung=True)

# d) Journal-Ausgabe Bürobedarf mit Vorsteuerabzug
j1 = req("POST", "/journal", {
    "datum": "2026-08-03",
    "beschreibung": "Büromaterial Testkauf",
    "kategorie_id": kat_buero["id"],
    "zahlungsart": "Bank",
    "art": "Ausgabe",
    "brutto_betrag": "119.00",
    "ust_satz": "19",
    "vorsteuerabzug": True,
})
print("journal Büromaterial:", j1["id"], j1.get("vorsteuer_betrag"))

# e) Journal-Ausgabe §13b Abs. 2 Bauleistung (brutto-Feld = Netto-Bemessung)
j2 = req("POST", "/journal", {
    "datum": "2026-09-12",
    "beschreibung": "Bauleistung Subunternehmer §13b",
    "kategorie_id": kat_bau["id"],
    "zahlungsart": "Bank",
    "art": "Ausgabe",
    "brutto_betrag": "500.00",
    "ust_satz": "19",
    "vorsteuerabzug": True,
    "ust_sonderfall": "13b_abs2",
})
print("journal 13b:", j2["id"], j2.get("ust_sonderfall"), j2.get("vorsteuer_betrag"))

print("setup-status:", req("GET", "/setup/status"))
