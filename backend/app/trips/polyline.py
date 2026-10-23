"""Decode Google's encoded polyline format, which OpenTripPlanner uses for leg shapes."""


def decode(encoded: str, precision: int = 5) -> list[tuple[float, float]]:
    """Return [lon, lat] pairs (GeoJSON order) from an encoded polyline.

    The format stores each coordinate as the difference from the previous one, scaled by
    10^precision, zig-zag encoded (sign in the lowest bit) and split into 5-bit chunks.
    https://developers.google.com/maps/documentation/utilities/polylinealgorithm
    """
    coordinates: list[tuple[float, float]] = []
    index = lat = lon = 0
    factor = 10**precision

    def next_value() -> int:
        nonlocal index
        result = shift = 0
        while True:
            chunk = ord(encoded[index]) - 63
            index += 1
            result |= (chunk & 0x1F) << shift
            shift += 5
            if chunk < 0x20:  # no continuation bit: last chunk of this value
                break
        return ~(result >> 1) if result & 1 else result >> 1

    while index < len(encoded):
        lat += next_value()
        lon += next_value()
        coordinates.append((lon / factor, lat / factor))
    return coordinates
