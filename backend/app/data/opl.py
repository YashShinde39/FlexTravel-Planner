"""A reader for OPL, osmium's one-line-per-object text format for OpenStreetMap data.

`osmium cat -f opl` turns a .osm.pbf extract into lines such as:

    n42 v3 dV c0 t2024-01-01T00:00:00Z i0 u Tname=Rajiv%20%Chowk x77.2195 y28.6328
    w7 v1 dV c0 t2024-01-01T00:00:00Z i0 u Trailway=subway Nn42,n43
    r9 v5 dV c0 t2024-01-01T00:00:00Z i0 u Ttype=route,route=subway Mn42@stop,w7@

Only what the Metro feed needs is kept: node positions, way node lists, relation members,
and everyone's tags. Spaces, commas and other special characters in tags and roles are
escaped as `%<hex code point>%` (`%20%` is a space, `%2192%` is "→").
"""

import re
from dataclasses import dataclass, field
from pathlib import Path

_ESCAPE = re.compile(r"%([0-9a-fA-F]+)%")


def unescape(text: str) -> str:
    return _ESCAPE.sub(lambda match: chr(int(match.group(1), 16)), text)


def _tags(field_value: str) -> dict[str, str]:
    tags = {}
    for pair in field_value.split(","):
        if "=" in pair:
            key, value = pair.split("=", 1)
            tags[unescape(key)] = unescape(value)
    return tags


@dataclass
class Member:
    type: str  # "n", "w" or "r"
    ref: int
    role: str


@dataclass
class OsmData:
    node_coords: dict[int, tuple[float, float]] = field(default_factory=dict)  # (lon, lat)
    node_tags: dict[int, dict[str, str]] = field(default_factory=dict)
    way_nodes: dict[int, list[int]] = field(default_factory=dict)
    relation_tags: dict[int, dict[str, str]] = field(default_factory=dict)
    relation_members: dict[int, list[Member]] = field(default_factory=dict)


def parse(lines) -> OsmData:
    data = OsmData()
    for line in lines:
        line = line.rstrip("\n")
        if not line:
            continue
        head, *fields = line.split(" ")
        kind, object_id = head[0], int(head[1:])
        values = {f[0]: f[1:] for f in fields if f}
        if kind == "n":
            if values.get("x"):  # nodes deleted from the extract have no position
                data.node_coords[object_id] = (float(values["x"]), float(values["y"]))
            if values.get("T"):
                data.node_tags[object_id] = _tags(values["T"])
        elif kind == "w":
            refs = values.get("N", "")
            data.way_nodes[object_id] = [int(ref[1:]) for ref in refs.split(",") if ref]
        elif kind == "r":
            data.relation_tags[object_id] = _tags(values.get("T", ""))
            members = []
            for member in values.get("M", "").split(","):
                if not member:
                    continue
                ref, _, role = member.partition("@")
                members.append(Member(type=ref[0], ref=int(ref[1:]), role=unescape(role)))
            data.relation_members[object_id] = members
    return data


def read(path: Path) -> OsmData:
    with path.open(encoding="utf-8") as lines:
        return parse(lines)
