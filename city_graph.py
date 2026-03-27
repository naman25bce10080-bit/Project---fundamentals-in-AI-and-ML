"""
=============================================================
  FILE 1: city_graph.py  —  The City Road Network
=============================================================

CONCEPT:
  A city is a GRAPH.
    - NODES  = Intersections / Named Locations (e.g. "City Center")
    - EDGES  = Roads connecting two nodes
    - WEIGHT = Road properties: distance (km) + speed limit (km/h)

  We use an ADJACENCY LIST to store this graph.
  Each node stores a list of its neighbors and the road details.

WHY THIS MATTERS:
  Before any AI can find the best route, it needs a map.
  This file IS that map. Real GPS systems do the same thing —
  OpenStreetMap data is just a massive version of this.
=============================================================
"""


class Road:
    """
    Represents a single road segment between two intersections.

    Attributes:
        to        : destination node name
        distance  : length of road in km
        speed_limit: maximum speed on this road (km/h)
        road_type : 'highway', 'main', or 'local'
                    (affects how much traffic slows you down)
    """

    def __init__(self, to: str, distance: float, speed_limit: int, road_type: str = "main"):
        self.to = to
        self.distance = distance          # km
        self.speed_limit = speed_limit    # km/h
        self.road_type = road_type        # highway / main / local

    def base_travel_time(self) -> float:
        """
        Base travel time in MINUTES assuming no traffic.
        Formula: time = (distance / speed) * 60
        """
        return (self.distance / self.speed_limit) * 60

    def __repr__(self):
        return f"Road(→{self.to}, {self.distance}km, {self.speed_limit}km/h, {self.road_type})"


class CityGraph:
    """
    The complete city road network stored as an adjacency list.

    self.nodes    : set of all location names
    self.edges    : dict  {  "NodeA": [ Road(...), Road(...) ],  ... }
    self.coords   : dict  {  "NodeA": (lat, lon)  }  ← for heuristic calculation
    """

    def __init__(self):
        self.nodes: set = set()
        self.edges: dict = {}      # adjacency list
        self.coords: dict = {}     # (x, y) grid coordinates for heuristic

    def add_location(self, name: str, x: float, y: float):
        """Add a named intersection/place to the map."""
        self.nodes.add(name)
        self.edges[name] = []
        self.coords[name] = (x, y)

    def add_road(self, from_node: str, to_node: str,
                 distance: float, speed_limit: int, road_type: str = "main"):
        """
        Add a BIDIRECTIONAL road between two locations.
        (Most real roads go both ways.)
        """
        self.edges[from_node].append(Road(to_node, distance, speed_limit, road_type))
        self.edges[to_node].append(Road(from_node, distance, speed_limit, road_type))

    def get_neighbors(self, node: str) -> list:
        """Return all Road objects leaving from this node."""
        return self.edges.get(node, [])

    def heuristic_distance(self, a: str, b: str) -> float:
        """
        EUCLIDEAN DISTANCE between two nodes using grid coords.
        Used by A* as the 'optimistic estimate' (heuristic).
        This never overestimates — a key requirement for A*.
        """
        ax, ay = self.coords[a]
        bx, by = self.coords[b]
        return ((ax - bx) ** 2 + (ay - by) ** 2) ** 0.5

    def display_map(self):
        """Print a readable summary of the city map."""
        print("\n" + "=" * 55)
        print("  📍 CITY MAP — Locations & Connected Roads")
        print("=" * 55)
        for node in sorted(self.nodes):
            roads = self.edges[node]
            print(f"\n  🔵 {node}")
            for road in roads:
                print(f"       └─ {road.to:<20} "
                      f"{road.distance}km  {road.speed_limit}km/h  [{road.road_type}]")
        print("=" * 55)


# =============================================================
#  BUILD THE DEMO CITY MAP
#  This function creates a realistic-looking sample city.
#  You can add/remove nodes and roads freely.
# =============================================================

def build_sample_city() -> CityGraph:
    """
    Constructs a sample city with 10 named locations.
    Returns a fully populated CityGraph ready for routing.

    City Layout (rough grid, not to scale):

        Airport ──── North Hub ──── East Mall
           |              |              |
        West Park ── City Center ── Business District
           |              |              |
        Hospital ── South Cross ── Tech Zone
                         |
                      University

    Road Types:
      - highway  : fast, but traffic hits hard (e.g., Airport link)
      - main     : standard city roads
      - local    : slow, less affected by traffic
    """
    city = CityGraph()

    # --- Add Locations with (x, y) grid coordinates ---
    city.add_location("Airport",             x=0,  y=4)
    city.add_location("North Hub",           x=2,  y=4)
    city.add_location("East Mall",           x=4,  y=4)
    city.add_location("West Park",           x=0,  y=2)
    city.add_location("City Center",         x=2,  y=2)
    city.add_location("Business District",   x=4,  y=2)
    city.add_location("Hospital",            x=0,  y=0)
    city.add_location("South Cross",         x=2,  y=0)
    city.add_location("Tech Zone",           x=4,  y=0)
    city.add_location("University",          x=2,  y=-1)

    # --- Add Roads (from, to, distance_km, speed_limit_kmph, type) ---

    # Top row
    city.add_road("Airport",           "North Hub",         5.0,  80, "highway")
    city.add_road("North Hub",         "East Mall",         4.5,  60, "main")

    # Middle row
    city.add_road("West Park",         "City Center",       3.5,  50, "main")
    city.add_road("City Center",       "Business District", 3.0,  60, "main")

    # Bottom row
    city.add_road("Hospital",          "South Cross",       4.0,  40, "local")
    city.add_road("South Cross",       "Tech Zone",         3.5,  50, "main")
    city.add_road("South Cross",       "University",        2.0,  30, "local")

    # Vertical connections (left column)
    city.add_road("Airport",           "West Park",         6.0,  70, "highway")
    city.add_road("West Park",         "Hospital",          3.0,  40, "local")

    # Vertical connections (center column)
    city.add_road("North Hub",         "City Center",       4.0,  55, "main")
    city.add_road("City Center",       "South Cross",       3.5,  50, "main")

    # Vertical connections (right column)
    city.add_road("East Mall",         "Business District", 4.5,  60, "main")
    city.add_road("Business District", "Tech Zone",         4.0,  55, "main")

    # Diagonal / shortcut roads
    city.add_road("Airport",           "City Center",       7.0,  90, "highway")
    city.add_road("City Center",       "Tech Zone",         5.5,  65, "main")
    city.add_road("North Hub",         "Business District", 5.0,  70, "highway")

    return city
