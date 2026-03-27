"""
=============================================================
  FILE 3: optimizer.py  —  A* Search + Route Scoring
=============================================================

CONCEPT — THE A* ALGORITHM:
  A* is the gold standard for shortest-path problems.
  It is used in Google Maps, game AI, and robotics.

  It works like a smart BFS. Instead of blindly exploring
  all neighbors, it PRIORITIZES nodes using:

      f(n) = g(n) + h(n)

  Where:
    g(n) = actual cost to reach node n from start
    h(n) = HEURISTIC — estimated cost from n to goal
           (we use Euclidean distance ÷ max_speed)

  KEY INSIGHT:
    If h(n) never OVERESTIMATES the real cost,
    A* is GUARANTEED to find the optimal path.

=============================================================
  MULTI-CRITERIA SCORING (the ML layer):
  After finding multiple candidate routes, we SCORE them
  using a weighted combination of factors:

    Score = w1×time + w2×distance + w3×congestion_risk
            - w4×reliability_bonus

  This is exactly how real navigation systems rank routes
  (fastest vs. shortest vs. most reliable).
=============================================================
"""

import heapq


# =============================================================
#  RESULT OBJECTS
# =============================================================

class RouteResult:
    """
    Stores the complete result of a route search.

    path         : ordered list of location names
    total_time   : estimated travel time in minutes
    total_distance: total km
    avg_congestion: average congestion across all roads
    score        : composite quality score (lower = better)
    """

    def __init__(self, path, total_time, total_distance, avg_congestion):
        self.path            = path
        self.total_time      = total_time        # minutes
        self.total_distance  = total_distance    # km
        self.avg_congestion  = avg_congestion    # 0.0 – 1.0
        self.score           = 0.0               # set by scorer

    def __repr__(self):
        return (f"Route({' → '.join(self.path)}, "
                f"{self.total_time:.1f}min, "
                f"{self.total_distance:.1f}km, "
                f"congestion={self.avg_congestion:.0%})")


# =============================================================
#  A* SEARCH ENGINE
# =============================================================

class AStarSearch:
    """
    Implements the A* search algorithm over a CityGraph,
    using TrafficEngine to compute real (traffic-adjusted) costs.
    """

    def __init__(self, city_graph, traffic_engine):
        self.graph   = city_graph
        self.traffic = traffic_engine

    def search(self, start: str, goal: str) -> RouteResult | None:
        """
        Run A* from `start` to `goal`.

        Returns a RouteResult or None if no path exists.

        Internal data structures:
          open_set  : min-heap of (f_score, node)
          came_from : dict tracking how we reached each node
          g_score   : best known cost (time in minutes) to each node
          f_score   : g_score + heuristic estimate to goal
        """

        # --- Validate inputs ---
        if start not in self.graph.nodes:
            raise ValueError(f"Unknown start location: '{start}'")
        if goal not in self.graph.nodes:
            raise ValueError(f"Unknown goal location: '{goal}'")
        if start == goal:
            return RouteResult([start], 0.0, 0.0, 0.0)

        # --- Initialize ---
        open_set  = []                  # priority queue: (f, node)
        came_from = {}                  # node → previous node
        g_score   = {node: float('inf') for node in self.graph.nodes}
        f_score   = {node: float('inf') for node in self.graph.nodes}

        g_score[start] = 0.0
        f_score[start] = self._heuristic(start, goal)

        heapq.heappush(open_set, (f_score[start], start))

        closed_set = set()              # nodes we've fully processed

        # --- Main A* Loop ---
        while open_set:

            # Pop the node with lowest f_score
            current_f, current = heapq.heappop(open_set)

            # GOAL REACHED — reconstruct path
            if current == goal:
                return self._reconstruct(came_from, current, goal)

            # Skip if already processed
            if current in closed_set:
                continue
            closed_set.add(current)

            # --- Explore all neighbors ---
            for road in self.graph.get_neighbors(current):
                neighbor = road.to

                if neighbor in closed_set:
                    continue

                # Cost of this step = actual travel time with traffic
                step_cost = self.traffic.effective_travel_time(road, current)

                tentative_g = g_score[current] + step_cost

                if tentative_g < g_score[neighbor]:
                    # Found a better path to neighbor — record it
                    came_from[neighbor] = (current, road)
                    g_score[neighbor]   = tentative_g
                    f_score[neighbor]   = tentative_g + self._heuristic(neighbor, goal)
                    heapq.heappush(open_set, (f_score[neighbor], neighbor))

        # No path found
        return None

    def _heuristic(self, node: str, goal: str) -> float:
        """
        Admissible heuristic: Euclidean distance / max_speed_assumed.
        Converts grid distance to a time estimate in minutes.
        Using 90 km/h as max speed means we never overestimate.
        """
        grid_dist = self.graph.heuristic_distance(node, goal)
        assumed_max_speed = 90  # km/h — optimistic
        # grid unit ≈ 2 km per unit (calibrated to our city layout)
        approx_km = grid_dist * 2
        return (approx_km / assumed_max_speed) * 60   # minutes

    def _reconstruct(self, came_from: dict, current: str, goal: str) -> RouteResult:
        """
        Walk backwards through came_from to rebuild the full path.
        Also collects travel time, distance, and congestion stats.
        """
        path            = [current]
        total_time      = 0.0
        total_distance  = 0.0
        congestion_vals = []

        node = current
        while node in came_from:
            prev_node, road = came_from[node]
            path.append(prev_node)

            # Accumulate stats
            total_time     += self.traffic.effective_travel_time(road, prev_node)
            total_distance += road.distance
            congestion_vals.append(self.traffic.get_congestion(prev_node, node))

            node = prev_node

        path.reverse()  # flip from goal→start to start→goal

        avg_congestion = sum(congestion_vals) / len(congestion_vals) if congestion_vals else 0.0

        return RouteResult(path, total_time, total_distance, avg_congestion)


# =============================================================
#  ALTERNATIVE ROUTE FINDER
#  Finds multiple routes by temporarily blocking roads
#  from the primary route 
# =============================================================

class RouteOptimizer:
    """
    Orchestrates route finding + multi-criteria scoring.

    Steps:
      1. Find primary (optimal) route with A*
      2. Find 1-2 alternatives by blocking edges on primary path
      3. Score all routes with weighted criteria
      4. Return sorted list: best → worst
    """

    # Scoring weights (must sum to 1.0)
    W_TIME        = 0.50    # 50% weight on travel time
    W_DISTANCE    = 0.20    # 20% weight on distance
    W_CONGESTION  = 0.30    # 30% weight on congestion risk

    def __init__(self, city_graph, traffic_engine):
        self.graph   = city_graph
        self.traffic = traffic_engine
        self.astar   = AStarSearch(city_graph, traffic_engine)

    def find_routes(self, start: str, goal: str, num_alternatives: int = 2) -> list:
        """
        Returns up to (1 + num_alternatives) ranked RouteResults.

        Strategy for alternatives:
          - Find primary route
          - For each road in primary route, temporarily inflate its
            cost by 10× and re-run A* → gives a genuinely different path
          - Deduplicate and score
        """
        all_routes = []

        # === PRIMARY ROUTE ===
        primary = self.astar.search(start, goal)
        if primary is None:
            return []
        all_routes.append(primary)

        # === ALTERNATIVE ROUTES ===
        # Try blocking each edge in the primary path one at a time
        primary_edges = list(zip(primary.path, primary.path[1:]))
        attempts      = 0

        for (u, v) in primary_edges:
            if attempts >= num_alternatives:
                break

            # Temporarily boost congestion on this edge to make it unattractive
            original_uv = self.traffic.congestion.get((u, v), 0.1)
            original_vu = self.traffic.congestion.get((v, u), 0.1)
            self.traffic.congestion[(u, v)] = 0.999   # near gridlock
            self.traffic.congestion[(v, u)] = 0.999

            alt = self.astar.search(start, goal)

            # Restore original congestion
            self.traffic.congestion[(u, v)] = original_uv
            self.traffic.congestion[(v, u)] = original_vu

            if alt and alt.path != primary.path and not self._is_duplicate(alt, all_routes):
                all_routes.append(alt)
                attempts += 1

        # === SCORE ALL ROUTES ===
        self._score_routes(all_routes)

        # Sort by score (lower is better)
        all_routes.sort(key=lambda r: r.score)
        return all_routes

    def _is_duplicate(self, route: RouteResult, existing: list) -> bool:
        """Check if a route is already in the list (same path)."""
        return any(route.path == r.path for r in existing)

    def _score_routes(self, routes: list):
        """
        Multi-criteria scoring using min-max normalization.

        For each metric, normalize to [0, 1] across all routes,
        then compute weighted sum.

        Lower score = better route.
        """
        if len(routes) == 1:
            routes[0].score = 0.0
            return

        # Extract values
        times        = [r.total_time      for r in routes]
        distances    = [r.total_distance  for r in routes]
        congestions  = [r.avg_congestion  for r in routes]

        # Min-max normalize each dimension
        def normalize(values):
            mn, mx = min(values), max(values)
            if mx == mn:
                return [0.0] * len(values)
            return [(v - mn) / (mx - mn) for v in values]

        n_times  = normalize(times)
        n_dists  = normalize(distances)
        n_congs  = normalize(congestions)

        for i, route in enumerate(routes):
            route.score = (
                self.W_TIME       * n_times[i]  +
                self.W_DISTANCE   * n_dists[i]  +
                self.W_CONGESTION * n_congs[i]
            )

    def explain_route(self, route: RouteResult, traffic_engine, city_graph) -> str:
        """
        Generate a turn-by-turn explanation of the route
        with per-segment congestion info.
        """
        lines = []
        for i in range(len(route.path) - 1):
            u, v       = route.path[i], route.path[i + 1]
            congestion = traffic_engine.get_congestion(u, v)
            status     = traffic_engine.describe_congestion(congestion)

            # Find road details
            for road in city_graph.get_neighbors(u):
                if road.to == v:
                    t = traffic_engine.effective_travel_time(road, u)
                    lines.append(
                        f"  Step {i+1}: {u:<22} → {v:<22}  "
                        f"{road.distance}km  {t:.1f}min  {status}"
                    )
                    break

        return "\n".join(lines)
