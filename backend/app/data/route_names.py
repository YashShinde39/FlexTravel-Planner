"""Turn the bus feed's packed route names into what is printed on the bus (ADR-0012).

The feed packs number, variant codes and direction into `route_long_name`, e.g.
`764MSTLDOWN` or `511ALNKSTLUP`, and leaves `route_short_name` empty. Visitors need the
code as printed, "764M STL", to match the bus at the stop.
"""

import re

# Direction suffix, sometimes followed by a variant number ("STLDOWN2").
_DIRECTION = re.compile(r"(UP|DOWN|DN)(\d?)$")
# Route number, optionally with a letter prefix ("GL-23").
_NUMBER = re.compile(r"^([A-Z]*-?\d+)(.*)$")
# Multi-letter codes, longest first so "LINK" wins over "LNK"-style partial matches.
_CODES = ("LINK", "LNK", "STL", "EXT", "LTD", "SPL.", "SPL", "VIA", "CL", "(NS)", "(+)", "(-)")


def display_code(long_name: str) -> str:
    """The route code as printed on the bus: `764MSTLDOWN` -> `764M STL`.

    Single letters directly after the number are variants and stay attached to it ("764M",
    "511A"); known codes become separate words. Names that don't start with a route number
    (ring routes like `TMS(+)UP`) are returned without their direction suffix only.
    """
    core = long_name.strip().upper()
    if (direction := _DIRECTION.search(core)) and direction.start() > 0:
        core = core[: direction.start()] + direction.group(2)

    match = _NUMBER.match(core)
    if not match:
        return core
    number, rest = match.groups()

    words: list[str] = []
    i = 0
    while i < len(rest):
        code = next((c for c in _CODES if rest.startswith(c, i)), None)
        if code:
            words.append(code)
            i += len(code)
        elif not words:
            number += rest[i]  # variant letter, part of the number
            i += 1
        else:
            words[-1] += rest[i]  # trailing digit or unknown letter, e.g. "STL2"
            i += 1
    return " ".join([number, *words])
