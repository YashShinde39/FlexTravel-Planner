"""What we know about each Metro and Namo Bharat line, for generating their timetable.

There is no official, downloadable timetable for the Delhi Metro (ADR-0011), so the feed
is generated (ADR-0016): stations and track from OpenStreetMap, and from this file how
often trains run, when the first and last ones leave, how fast they go and how long
changing lines takes. Values have sources where one exists; the rest are estimates to
tune, marked as such. Re-check the sources when updating, and change AS_OF.
"""

from dataclasses import dataclass

AS_OF = "2026-10-24"


@dataclass(frozen=True)
class Headways:
    """Minutes between trains: weekday peaks (08-11, 17-21), the rest of the day, after
    21:00, and all day on Sundays."""

    peak: float
    day: float
    late: float
    sunday: float


@dataclass(frozen=True)
class Hours:
    """When the first and last trains leave the terminals ("HH:MM", Delhi time)."""

    first: str
    last: str
    sunday_first: str


@dataclass(frozen=True)
class Line:
    id: str
    name: str  # as shown to travellers, e.g. "Yellow Line"
    agency: str  # key into AGENCIES; fares differ per agency
    route_type: int  # GTFS: 1 = metro, 2 = rail (colours come from OpenStreetMap)
    # OpenStreetMap route relations, one per direction. Each lists the stops in order and
    # the track between them.
    relations: tuple[int, ...]
    headways: Headways
    hours: Hours
    # Which line's calibrated speed to use (see SPEED_CHECKS); a line in SPEED_CHECKS uses
    # its own.
    speed_from: str
    source: str


@dataclass(frozen=True)
class Agency:
    id: str
    name: str
    url: str


AGENCIES = {
    "dmrc": Agency("dmrc", "Delhi Metro", "https://www.delhimetrorail.com"),
    # Run by the Delhi Metro since 2019, but priced separately.
    "rmg": Agency("rmg", "Rapid Metro Gurgaon", "https://www.delhimetrorail.com"),
    "ncrtc": Agency("ncrtc", "Namo Bharat", "https://ncrtc.in"),
}

# Delhi Metro hours: trains from about 05:30 on weekdays and 06:00 on Sundays (the regular
# Sunday timetable starts at 06:00, Business Today, 2026-10-16), until about 23:00.
_DMRC_HOURS = Hours(first="05:30", last="23:00", sunday_first="06:00")

# Frequencies. DMRC publishes no per-line table: its busiest corridors run every 2 min
# 18 s at peak (DMRC, 2026). Other values are estimates by line size and ridership.
_DMRC_SOURCE = "Estimate; busiest corridors every 2-3 min at peak (DMRC, 2026)"

LINES = (
    Line(
        id="red",
        name="Red Line",
        agency="dmrc",
        route_type=1,
        relations=(447214, 8037718),
        headways=Headways(peak=4, day=6, late=8, sunday=6),
        hours=_DMRC_HOURS,
        speed_from="red",
        source=_DMRC_SOURCE,
    ),
    Line(
        id="yellow",
        name="Yellow Line",
        agency="dmrc",
        route_type=1,
        relations=(447210, 8037712),
        headways=Headways(peak=2.5, day=4, late=7, sunday=5),
        hours=_DMRC_HOURS,
        speed_from="red",
        source=_DMRC_SOURCE,
    ),
    Line(
        id="blue",
        name="Blue Line",
        agency="dmrc",
        route_type=1,
        relations=(447209, 8037669),
        headways=Headways(peak=3, day=5, late=8, sunday=6),
        hours=_DMRC_HOURS,
        speed_from="red",
        source=_DMRC_SOURCE,
    ),
    # Every other Blue Line train goes to Vaishali instead of Noida.
    Line(
        id="blue-vaishali",
        name="Blue Line",
        agency="dmrc",
        route_type=1,
        relations=(2535795, 8037670),
        headways=Headways(peak=6, day=10, late=12, sunday=10),
        hours=_DMRC_HOURS,
        speed_from="red",
        source=_DMRC_SOURCE,
    ),
    Line(
        id="green",
        name="Green Line",
        agency="dmrc",
        route_type=1,
        relations=(8037666, 8037687),
        headways=Headways(peak=5, day=8, late=10, sunday=8),
        hours=_DMRC_HOURS,
        speed_from="red",
        source=_DMRC_SOURCE,
    ),
    Line(
        id="green-kirti-nagar",
        name="Green Line",
        agency="dmrc",
        route_type=1,
        relations=(2535796, 8037675),
        headways=Headways(peak=8, day=10, late=12, sunday=10),
        hours=_DMRC_HOURS,
        speed_from="red",
        source=_DMRC_SOURCE,
    ),
    Line(
        id="violet",
        name="Violet Line",
        agency="dmrc",
        route_type=1,
        relations=(2535797, 8037705),
        headways=Headways(peak=4, day=6, late=8, sunday=6),
        hours=_DMRC_HOURS,
        speed_from="red",
        source=_DMRC_SOURCE,
    ),
    Line(
        id="pink",
        name="Pink Line",
        agency="dmrc",
        route_type=1,
        relations=(8241298, 8242437),
        headways=Headways(peak=5, day=7, late=10, sunday=7),
        hours=_DMRC_HOURS,
        speed_from="red",
        source=_DMRC_SOURCE,
    ),
    Line(
        id="magenta",
        name="Magenta Line",
        agency="dmrc",
        route_type=1,
        relations=(8385429, 8385430),
        headways=Headways(peak=4, day=6, late=9, sunday=6),
        hours=_DMRC_HOURS,
        speed_from="red",
        source=_DMRC_SOURCE,
    ),
    # The new Majlis Park - Deepali Chowk section, not yet joined to the rest of the line.
    Line(
        id="magenta-majlis-park",
        name="Magenta Line",
        agency="dmrc",
        route_type=1,
        relations=(20300114, 20300115),
        headways=Headways(peak=8, day=10, late=12, sunday=10),
        hours=_DMRC_HOURS,
        speed_from="red",
        source=_DMRC_SOURCE,
    ),
    # Peak every 7.5 min, otherwise 12 (Business Standard, DMRC announcement, c. 2022).
    Line(
        id="grey",
        name="Grey Line",
        agency="dmrc",
        route_type=1,
        relations=(3537978, 8051592),
        headways=Headways(peak=7.5, day=12, late=12, sunday=12),
        hours=_DMRC_HOURS,
        speed_from="red",
        source="Business Standard (DMRC), c. 2022",
    ),
    # Every 5-7 min, 06:00 to 22:00 (Godrej Properties guide, January 2025).
    Line(
        id="rapid-metro",
        name="Rapid Metro",
        agency="rmg",
        route_type=1,
        relations=(4481323, 7890002),
        headways=Headways(peak=5, day=7, late=10, sunday=7),
        hours=Hours(first="06:00", last="22:00", sunday_first="06:00"),
        speed_from="red",
        source="Godrej Properties guide, January 2025",
    ),
    # Every 10 min, Sarai Kale Khan - Modipuram in about 55 min (Railway Journal, 2026).
    # 06:00 to 22:00, from 08:00 on Sundays (NCRTC, as reported).
    Line(
        id="namo-bharat",
        name="Namo Bharat",
        agency="ncrtc",
        route_type=2,
        relations=(17337287, 17337288),
        headways=Headways(peak=10, day=10, late=15, sunday=15),
        hours=Hours(first="06:00", last="22:00", sunday_first="08:00"),
        speed_from="namo-bharat",
        source="Railway Journal, 2026; NCRTC",
    ),
)

# Published end-to-end journey times, in minutes. Lines listed here get a running speed
# that reproduces their time; other lines borrow one (Line.speed_from).
SPEED_CHECKS = {
    "red": (63, "Rithala - Shaheed Sthal, MetroGo, 2026"),
    "namo-bharat": (55, "Sarai Kale Khan - Modipuram, Railway Journal, 2026"),
}
# Published times we don't calibrate on but report against, to see how far off we are.
# Yellow's 69 min would need 56 km/h between stops, far above the Red Line's.
TIME_REPORTS = {
    "yellow": (69, "Samaypur Badli - Millennium City Centre, NoBroker, 2026"),
}

# Time lost at each stop: the doors open and close, plus braking and accelerating.
STOP_OVERHEAD_S = 40

# Minutes to change lines, from getting off one train to being able to board the next.
# Estimates to tune: most changes are a few minutes inside one station; these are the
# known long walks (separate buildings joined by skywalks, or very deep platforms).
DEFAULT_CHANGE_MIN = 4
CHANGE_MIN = {
    "Kashmere Gate": 7,
    "Hauz Khas": 8,
    "Rajouri Garden": 7,
    "Welcome": 7,
    "Punjabi Bagh West": 7,
    "Sikanderpur": 7,
    "Inderlok": 6,
    "Janakpuri West": 6,
    "Lajpat Nagar": 6,
    "Netaji Subhash Place": 6,
    "Azadpur": 6,
    "Karkarduma": 6,
    "Anand Vihar": 8,  # Blue, Pink and Namo Bharat in three buildings
    "New Ashok Nagar": 7,
    "Sarai Kale Khan": 8,
    # Same platform: the Blue Line's branches, and the Green Line's.
    "Yamuna Bank": 2,
    "Ashok Park Main": 2,
}

# Stations that are one interchange but have different names on different lines.
SAME_STATION = {"Sarai Kale Khan - Nizamuddin": "Sarai Kale Khan"}
