r"""Tests für den ELSTER-UStVA-XML-Export (Mein-ELSTER-Upload, Issue #360).

Format-Vertrag verifiziert gegen:
- offizielle ELSTER-Hilfe (themaGlobal=ustva_upload): Nutzdaten-only,
  Root <Anmeldungssteuern>, ISO-8859-15, version-Attribut = Jahresversion
- ELSTER-XSD (geierlein-Mirror usta_201301.xsd): Pflichtfelder Jahr, Zeitraum,
  Steuernummer, Kz09, Kz83; Typen \d{4}0\d{8} / Ganzzahl / ".dd"; Zeitraum
  01-12 bzw. 41-44
- Forum-Praxisbeispiel (thread 425731): funktionierender Upload-Aufbau
"""
import asyncio
import re
from datetime import date
from decimal import Decimal
from xml.etree import ElementTree as ET

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from api.ustva import ustva_xml
from database.connection import Base
from database.models import Unternehmen
from utils.elster import ElsterExportFehler, build_ustva_xml

NS = "http://finkonsens.de/elster/elsteranmeldung/ustva/v2026"


def _unternehmen(**kw) -> Unternehmen:
    base = dict(
        firmenname="Muster GmbH", vorname="Max", nachname="Mustermann",
        strasse="Musterweg", hausnummer="12", plz="12345", ort="Musterstadt",
        email="steuer@muster.de", telefon="030/123456",
        steuernummer="151/815/08154", bundesland="BY",
    )
    base.update(kw)
    return Unternehmen(**base)


def _parse(xml: bytes) -> ET.Element:
    return ET.fromstring(xml.decode("iso-8859-15"))


async def _lese_body(resp) -> bytes:
    return b"".join([c async for c in resp.body_iterator])


def test_deklaration_und_root():
    xml = build_ustva_xml(
        zeitraum="2026-03", steuernummer13="9151081508154",
        unternehmen=_unternehmen(), kz_werte={"81": Decimal("150000"), "83": Decimal("28500.00")},
    )
    assert xml.startswith(b'<?xml version="1.0" encoding="ISO-8859-15" standalone="no"?>')
    root = _parse(xml)
    assert root.tag == f"{{{NS}}}Anmeldungssteuern"
    assert root.get("version") == "2026"
    assert f'xmlns="{NS}"' in xml.decode("iso-8859-15")


def test_namespace_und_version_folgen_dem_jahr_des_zeitraums():
    xml = build_ustva_xml(
        zeitraum="2024-Q2", steuernummer13="9151081508154",
        unternehmen=_unternehmen(), kz_werte={"83": Decimal("0.00")},
    )
    root = _parse(xml)
    assert root.get("version") == "2024"
    assert 'xmlns="http://finkonsens.de/elster/elsteranmeldung/ustva/v2024"' in xml.decode("iso-8859-15")


def test_elementstruktur_und_reihenfolge():
    xml = build_ustva_xml(
        zeitraum="2026-03", steuernummer13="9151081508154",
        unternehmen=_unternehmen(), kz_werte={"83": Decimal("0.00")},
    )
    root = _parse(xml)
    kinder = [c.tag.split("}")[-1] for c in root]
    assert kinder == ["Erstellungsdatum", "DatenLieferant", "Steuerfall"]
    assert re.fullmatch(r"\d{8}", root.findtext("{*}Erstellungsdatum"))
    steuerfall = root.find("{*}Steuerfall")
    ustva = steuerfall.find("{*}Umsatzsteuervoranmeldung")
    assert ustva.findtext("{*}Jahr") == "2026"
    assert ustva.findtext("{*}Zeitraum") == "03"
    assert ustva.findtext("{*}Steuernummer") == "9151081508154"


@pytest.mark.parametrize("zeitraum,ziel", [
    ("2026-01", "01"), ("2026-12", "12"),
    ("2026-Q1", "41"), ("2026-Q2", "42"), ("2026-Q3", "43"), ("2026-Q4", "44"),
])
def test_zeitraum_mapping(zeitraum, ziel):
    xml = build_ustva_xml(
        zeitraum=zeitraum, steuernummer13="9151081508154",
        unternehmen=_unternehmen(), kz_werte={"83": Decimal("0.00")},
    )
    ustva = _parse(xml).find("{*}Steuerfall/{*}Umsatzsteuervoranmeldung")
    assert ustva.findtext("{*}Zeitraum") == ziel
    assert ustva.findtext("{*}Jahr") == "2026"


def test_kz_formate_ganzzahl_vs_cent():
    xml = build_ustva_xml(
        zeitraum="2026-03", steuernummer13="9151081508154",
        unternehmen=_unternehmen(),
        kz_werte={
            "81": Decimal("150000"),      # Bemessungsgrundlage → Ganzzahl
            "86": Decimal("25000"),
            "66": Decimal("15000.55"),    # Vorsteuer → 2 Dezimalen, Punkt
            "83": Decimal("-1200.50"),    # Zahllast negativ erlaubt
        },
    )
    ustva = _parse(xml).find("{*}Steuerfall/{*}Umsatzsteuervoranmeldung")
    assert ustva.findtext("{*}Kz81") == "150000"
    assert ustva.findtext("{*}Kz86") == "25000"
    assert ustva.findtext("{*}Kz66") == "15000.55"
    assert ustva.findtext("{*}Kz83") == "-1200.50"


def test_kz83_ist_pflicht_auch_bei_null():
    ustva = _parse(build_ustva_xml(
        zeitraum="2026-03", steuernummer13="9151081508154",
        unternehmen=_unternehmen(), kz_werte={},
    )).find("{*}Steuerfall/{*}Umsatzsteuervoranmeldung")
    assert ustva.findtext("{*}Kz83") == "0.00"


def test_nulle_kz_werden_nicht_emitiert():
    ustva = _parse(build_ustva_xml(
        zeitraum="2026-03", steuernummer13="9151081508154",
        unternehmen=_unternehmen(),
        kz_werte={"81": Decimal("0"), "86": Decimal("0.00"), "83": Decimal("0.00")},
    )).find("{*}Steuerfall/{*}Umsatzsteuervoranmeldung")
    kzs = [e.tag.split("}")[-1] for e in ustva if e.tag.split("}")[-1].startswith("Kz")]
    assert kzs == ["Kz09", "Kz83"]


def test_kz09_als_schema_pflichtfeld_vorhanden():
    ustva = _parse(build_ustva_xml(
        zeitraum="2026-03", steuernummer13="9151081508154",
        unternehmen=_unternehmen(), kz_werte={},
    )).find("{*}Steuerfall/{*}Umsatzsteuervoranmeldung")
    assert re.fullmatch(r"\d{5}", ustva.findtext("{*}Kz09"))


def test_umlaute_und_escapes_in_iso_8859_15():
    xml = build_ustva_xml(
        zeitraum="2026-03", steuernummer13="9151081508154",
        unternehmen=_unternehmen(firmenname="Müller & Söhne — €uro"),
        kz_werte={"83": Decimal("0.00")},
    )
    text = xml.decode("iso-8859-15")
    assert "Müller" in text and "&amp;" in text
    # Parse über die Bytes prüft Encoding-Konsistenz
    _parse(xml)


def test_unternehmer_block_im_steuerfall():
    root = _parse(build_ustva_xml(
        zeitraum="2026-03", steuernummer13="9151081508154",
        unternehmen=_unternehmen(), kz_werte={},
    ))
    unt = root.find("{*}Steuerfall/{*}Unternehmer")
    assert unt is not None
    assert unt.findtext("{*}Bezeichnung") == "Muster GmbH"
    assert unt.findtext("{*}Name") == "Mustermann"
    assert unt.findtext("{*}Str") == "Musterweg"
    assert unt.findtext("{*}Hausnummer") == "12"


def test_steuerummer_validierung_am_eingang():
    with pytest.raises(ElsterExportFehler):
        build_ustva_xml(
            zeitraum="2026-03", steuernummer13="15181508154",  # nur 11-stellig
            unternehmen=_unternehmen(), kz_werte={},
        )


# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------

@pytest.fixture
def db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    session.add(_unternehmen())
    session.commit()
    yield session
    session.close()


def test_endpoint_liefert_xml_mit_attachment_header(db):
    resp = ustva_xml(zeitraum="2026-Q1", db=db)
    assert resp.media_type == "application/xml"
    assert "attachment" in resp.headers["Content-Disposition"]
    assert "UStVA_2026-Q1_ELSTER.xml" in resp.headers["Content-Disposition"]
    body = asyncio.run(_lese_body(resp))
    assert body.startswith(b"<?xml")
    ustva = _parse(body).find("{*}Steuerfall/{*}Umsatzsteuervoranmeldung")
    assert ustva.findtext("{*}Steuernummer") == "9151081508154"
    assert ustva.findtext("{*}Zeitraum") == "41"


def test_endpoint_422_ohne_steuernummer(db):
    db.query(Unternehmen).first().steuernummer = None
    db.commit()
    with pytest.raises(Exception) as exc:
        ustva_xml(zeitraum="2026-Q1", db=db)
    assert "422" in str(exc.value)


def test_endpoint_422_ohne_bundesland(db):
    db.query(Unternehmen).first().bundesland = None
    db.commit()
    with pytest.raises(Exception) as exc:
        ustva_xml(zeitraum="2026-Q1", db=db)
    assert "422" in str(exc.value)


def test_endpoint_422_kleinunternehmer(db):
    db.query(Unternehmen).first().ist_kleinunternehmer = True
    db.commit()
    with pytest.raises(Exception) as exc:
        ustva_xml(zeitraum="2026-Q1", db=db)
    assert "422" in str(exc.value)


def test_endpoint_422_ungueltiger_zeitraum(db):
    with pytest.raises(Exception) as exc:
        ustva_xml(zeitraum="kein-zeitraum", db=db)
    assert "422" in str(exc.value)


def test_endpoint_404_ohne_unternehmen(db):
    db.query(Unternehmen).delete()
    db.commit()
    with pytest.raises(Exception) as exc:
        ustva_xml(zeitraum="2026-Q1", db=db)
    assert "404" in str(exc.value)
