"""
=============================================================
  test_run.py  —  Automated test to verify everything works
=============================================================
Run this first to make sure all files are correct:
    python test_run.py
=============================================================
"""

print("=" * 55)
print("  SMART TRAFFIC OPTIMIZER — Test Run")
print("=" * 55)

# --- Test 1: Import all modules ---
print("\n[1/5] Importing modules...")
from city_graph     import build_sample_city
from traffic_engine  import TrafficEngine
from optimizer       import RouteOptimizer
print("  ✅ All imports OK")

# --- Test 2: Build city ---
print("\n[2/5] Building city graph...")
city = build_sample_city()
assert len(city.nodes) == 10, "Should have 10 locations"
print(f"  ✅ City: {len(city.nodes)} nodes, "
      f"{sum(len(v) for v in city.edges.values())//2} roads")

# --- Test 3: Traffic engine ---
print("\n[3/5] Testing traffic engine (hour=8, morning rush)...")
traffic = TrafficEngine(hour_of_day=8)
traffic.initialize_traffic(city)
c = traffic.get_congestion("Airport", "North Hub")
print(f"  ✅ Airport→North Hub congestion: {c:.0%}  {traffic.describe_congestion(c)}")

# --- Test 4: A* single route ---
print("\n[4/5] Testing A* routing: Airport → University...")
optimizer = RouteOptimizer(city, traffic)
routes = optimizer.find_routes("Airport", "University", num_alternatives=2)
assert len(routes) >= 1, "Should find at least 1 route"
best = routes[0]
print(f"  ✅ Best route: {' → '.join(best.path)}")
print(f"     Time: {best.total_time:.1f} min  |  Distance: {best.total_distance:.1f} km")

# --- Test 5: Multiple routes ---
print("\n[5/5] Checking alternative routes...")
for i, r in enumerate(routes):
    tag = ["BEST", "ALT1", "ALT2"][i] if i < 3 else f"ALT{i}"
    print(f"  [{tag}] {' → '.join(r.path)}  ({r.total_time:.1f}min, score={r.score:.3f})")

print("\n" + "=" * 55)
print("  ✅ ALL TESTS PASSED — Run 'python main.py' to start!")
print("=" * 55)
