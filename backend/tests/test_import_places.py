import json
from pathlib import Path

from app.data.import_places import stations


def station(osm_id: str, lon: float, lat: float, **tags: str) -> str:
    feature = {
        "type": "Feature",
        "id": osm_id,
        "properties": {"railway": "station", **tags},
        "geometry": {"type": "Point", "coordinates": [lon, lat]},
    }
    return "\x1e" + json.dumps(feature) + "\n"  # osmium writes GeoJSON text sequences


def test_stations_are_labelled_the_way_travellers_know_them(tmp_path: Path) -> None:
    path = tmp_path / "stations.geojsonseq"
    path.write_text(
        station("n1", 77.2, 28.5, name="Hauz Khas (Yellow Line)", station="subway")
        + station("n2", 77.3, 28.6, name="Anand Vihar", network="RapidX")
        + station("n3", 77.1, 28.5, name="Cyber City", network="Rapid Metro Gurgaon")
        + station("n4", 77.2, 28.6, name="New Delhi")
    )

    found = {p.name: p for p in stations(path)}

    assert found["Hauz Khas"].lines == ["Yellow"]
    assert found["Hauz Khas"].full_detail == "Metro station · Yellow line"
    assert found["Anand Vihar"].detail == "Namo Bharat station"
    assert found["Cyber City"].detail == "Metro station · Rapid Metro Gurgaon"
    assert found["New Delhi"].detail == "Railway station"
