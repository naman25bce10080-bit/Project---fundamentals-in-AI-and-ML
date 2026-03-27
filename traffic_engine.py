"""
=============================================================
  FILE 2: traffic_engine.py  —  Live Traffic Simulation
=============================================================

CONCEPT:
  Real traffic varies by:
    1. TIME OF DAY  — rush hours are congested
    2. ROAD TYPE    — highways jam worse than local roads
    3. RANDOMNESS   — accidents, events cause sudden spikes

  We model each road as having a CONGESTION LEVEL from 0.0 to 1.0:
    0.0 = completely free (no cars)
    0.5 = moderate traffic
    1.0 = gridlock (road is blocked)

  This congestion is then used by the optimizer to calculate
  ACTUAL travel time (which is always ≥ base travel time).

THE "ML" ANGLE:
  We use a simple LINEAR MODEL to predict congestion:

    congestion = base_factor(road_type)
               + time_factor(hour_of_day)
               + random_noise()

  This is exactly what real traffic prediction models do —
  just with far more features and trained on real GPS data.
  The structure is the same.
=============================================================
"""

import random
import math


# =============================================================
#  CONGESTION MULTIPLIER TABLE
#  How much does congestion slow you down on each road type?
#  Think of it as: at congestion=1.0, speed is multiplied by...
# =============================================================

CONGESTION_IMPACT = {
    "highway": 0.65,   
    "main":    0.85,  
    "local":   0.35,   # local roads — not much traffic anyway
}


class TrafficEngine:
    """
    Manages traffic congestion for every road in the city.

    Key idea:
      - We store congestion as a dict keyed by (from, to) tuples
      - Congestion updates every time you call refresh_traffic()
      - The optimizer reads congestion to compute real travel times
    """

    def __init__(self, hour_of_day: int = None):
        """
        hour_of_day: 0-23. If None, uses current system time.
                     Controls whether it's rush hour or not.
        """
        if hour_of_day is None:
            import datetime
            hour_of_day = datetime.datetime.now().hour

        self.hour = hour_of_day
        self.congestion: dict = {}   # (from_node, to_node) → float [0.0, 1.0]

    def _time_factor(self) -> float:
        """
        Returns a 0.0–1.0 factor based on hour of day.

        Uses a GAUSSIAN CURVE centered on rush hours:
          - Morning rush: 8 AM  (peak = 0.75)
          - Evening rush: 6 PM  (peak = 0.90)
          - Night        (1–5 AM): near 0 (quiet roads)

        This mimics the bell-curve shape of real traffic patterns.
        """
        # Morning rush centered at 8 AM
        morning = 0.75 * math.exp(-0.5 * ((self.hour - 8) / 1.5) ** 2)
        # Evening rush centered at 18 (6 PM)
        evening = 0.90 * math.exp(-0.5 * ((self.hour - 18) / 1.5) ** 2)
        # Return the higher of the two peaks
        return max(morning, evening)

    def _base_congestion(self, road_type: str) -> float:
        """
        Even outside rush hours, some congestion exists.
        Highways carry more cars by default.
        """
        base = {
            "highway": 0.25,
            "main":    0.15,
            "local":   0.05,
        }
        return base.get(road_type, 0.10)

    def compute_congestion(self, road_type: str) -> float:
        """
        THE CORE TRAFFIC MODEL:

          congestion = base + (time_factor × type_weight) + noise

        Clipped to [0.0, 1.0] range.
        """
        base   = self._base_congestion(road_type)
        time_f = self._time_factor()

        # Road-type weight: highways amplify rush hour more
        type_weight = {"highway": 1.0, "main": 0.75, "local": 0.40}
        rush_contribution = time_f * type_weight.get(road_type, 0.5)

        # Small random noise simulates unpredictable events
        noise = random.uniform(-0.05, 0.10)

        congestion = base + rush_contribution + noise
        return max(0.0, min(1.0, congestion))   # clamp to [0, 1]

    def initialize_traffic(self, city_graph):
        """
        Populate congestion values for every road in the city.
        Called once at startup.
        """
        self.congestion = {}
        for node in city_graph.nodes:
            for road in city_graph.get_neighbors(node):
                key = (node, road.to)
                if key not in self.congestion:
                    c = self.compute_congestion(road.road_type)
                    # Store both directions (same congestion level, bidirectional road)
                    self.congestion[key]            = c
                    self.congestion[(road.to, node)] = c

    def refresh_traffic(self, city_graph, change_fraction: float = 0.3):
        """
        Simulate traffic CHANGING OVER TIME.
        Only updates a fraction of roads each refresh (realistic —
        not all roads change simultaneously).

        change_fraction: how many roads to update (0.3 = 30%)
        """
        all_roads = list(self.congestion.keys())
        n_to_change = max(1, int(len(all_roads) * change_fraction))
        roads_to_update = random.sample(all_roads, n_to_change)

        for key in roads_to_update:
            from_node, to_node = key
            # Find road type
            road_type = "main"
            for road in city_graph.get_neighbors(from_node):
                if road.to == to_node:
                    road_type = road.road_type
                    break
            new_c = self.compute_congestion(road_type)
            self.congestion[key]                = new_c
            self.congestion[(to_node, from_node)] = new_c

    def get_congestion(self, from_node: str, to_node: str) -> float:
        """Look up current congestion on a specific road segment."""
        return self.congestion.get((from_node, to_node), 0.1)

    def effective_travel_time(self, road, from_node: str) -> float:
        """
        ACTUAL travel time accounting for congestion.

        Formula:
          actual_time = base_time × slowdown_multiplier

        Where slowdown_multiplier uses the road's impact factor:
          - At congestion=0.0: multiplier = 1.0  (no slowdown)
          - At congestion=1.0: multiplier = 1 / (1 - impact)

        Example: highway at full congestion (impact=0.85):
          multiplier = 1 / (1 - 0.85×1.0) = 1 / 0.15 ≈ 6.7×  (near gridlock)
        """
        congestion = self.get_congestion(from_node, road.to)
        impact     = CONGESTION_IMPACT.get(road.road_type, 0.5)
        slowdown   = 1 - (impact * congestion)
        slowdown   = max(0.05, slowdown)   # never fully zero (road never truly 0 speed)

        actual_time = road.base_travel_time() / slowdown
        return actual_time

    def describe_congestion(self, level: float) -> str:
        """Human-readable description of a congestion level."""
        if level < 0.20: return "🟢 Free Flow"
        if level < 0.45: return "🟡 Light Traffic"
        if level < 0.65: return "🟠 Moderate"
        if level < 0.80: return "🔴 Heavy Traffic"
        return                   "🚨 Gridlock"

    def display_traffic_report(self, city_graph):
        """Print current congestion on all roads."""
        print("\n" + "=" * 60)
        print(f"  🚦 LIVE TRAFFIC REPORT  (Hour: {self.hour:02d}:00)")
        print("=" * 60)
        seen = set()
        for node in sorted(city_graph.nodes):
            for road in city_graph.get_neighbors(node):
                key = tuple(sorted([node, road.to]))
                if key in seen:
                    continue
                seen.add(key)
                c = self.get_congestion(node, road.to)
                desc = self.describe_congestion(c)
                print(f"  {node:<22} ↔  {road.to:<22}  {desc}  ({c:.0%})")
        print("=" * 60)
