"""
=============================================================
  FILE 4: main.py  —  Entry Point & Interactive Interface
=============================================================

WHAT THIS FILE DOES:
  1. Builds the city map
  2. Starts the traffic engine with a chosen time
  3. Offers an interactive menu for:
       - Finding optimal routes
       - Viewing live traffic
       - Refreshing traffic simulation
       - Comparing multiple route options
=============================================================
"""

from city_graph    import build_sample_city
from traffic_engine import TrafficEngine
from optimizer      import RouteOptimizer


# =============================================================
#  DISPLAY HELPERS
# =============================================================

def print_banner():
    print("""
╔══════════════════════════════════════════════════════════╗
║     🚗  SMART TRAFFIC ROUTE OPTIMIZER  🚗               ║
║         AI-Based Navigation System                       ║
║                                                          ║
║   Algorithm : A* Search + Multi-Criteria Scoring         ║
║   Traffic   : Time-of-Day Gaussian Model                 ║
╚══════════════════════════════════════════════════════════╝
""")

def print_menu():
    print("""
┌─────────────────────────────────────────────┐
│  MAIN MENU                                  │
│                                             │
│  1. 🗺️  Find Best Route                    │
│  2. 🚦  View Live Traffic Report            │
│  3. 🔄  Refresh Traffic (simulate time)     │
│  4. 📍  Show City Map                       │
│  5. ❌  Exit                                │
└─────────────────────────────────────────────┘""")

def list_locations(city):
    """Print numbered list of all city locations for easy selection."""
    locations = sorted(city.nodes)
    print("\n  📍 Available Locations:")
    for i, loc in enumerate(locations, 1):
        print(f"     {i:2}. {loc}")
    return locations

def pick_location(prompt: str, locations: list) -> str:
    """Let user pick a location by number or name."""
    while True:
        raw = input(f"\n  {prompt}: ").strip()
        # Try as number
        if raw.isdigit():
            idx = int(raw) - 1
            if 0 <= idx < len(locations):
                return locations[idx]
            print("  ⚠️  Invalid number. Try again.")
        # Try as name (case-insensitive)
        else:
            matches = [l for l in locations if l.lower() == raw.lower()]
            if matches:
                return matches[0]
            print("  ⚠️  Location not found. Try again.")

def display_route_result(rank: int, route, label: str, optimizer, traffic, city):
    """Pretty-print a single route result."""
    emoji = ["🥇", "🥈", "🥉"][rank] if rank < 3 else f"#{rank+1}"
    print(f"\n  {emoji}  {label}")
    print(f"  {'─'*55}")
    print(f"  Path      : {' → '.join(route.path)}")
    print(f"  Time      : {route.total_time:.1f} min")
    print(f"  Distance  : {route.total_distance:.1f} km")
    print(f"  Avg Traffic: {traffic.describe_congestion(route.avg_congestion)} ({route.avg_congestion:.0%})")
    print(f"  Score     : {route.score:.3f}  (lower = better)")
    print(f"\n  Turn-by-Turn:")
    print(optimizer.explain_route(route, traffic, city))


# =============================================================
#  CORE FEATURES
# =============================================================

def feature_find_route(city, traffic, optimizer):
    """
    FEATURE 1: Find the best route between two locations.

    Steps:
      a) List available locations
      b) User picks start and goal
      c) Run RouteOptimizer.find_routes() → gets primary + alternatives
      d) Display all routes ranked by score
    """
    print("\n" + "="*55)
    print("  🗺️  ROUTE FINDER")
    print("="*55)

    locations = list_locations(city)

    start = pick_location("Enter START location (name or number)", locations)
    goal  = pick_location("Enter GOAL location  (name or number)", locations)

    if start == goal:
        print("\n  ⚠️  Start and goal are the same location!")
        return

    print(f"\n  🔍 Finding routes: {start}  →  {goal} ...\n")

    routes = optimizer.find_routes(start, goal, num_alternatives=2)

    if not routes:
        print("  ❌ No route found between these locations.")
        return

    labels = ["BEST ROUTE (Recommended)", "ALTERNATIVE ROUTE 1", "ALTERNATIVE ROUTE 2"]

    print("\n" + "="*55)
    print(f"  📊 ROUTE RESULTS  ({len(routes)} option(s) found)")
    print("="*55)

    for i, route in enumerate(routes):
        label = labels[i] if i < len(labels) else f"ROUTE {i+1}"
        display_route_result(i, route, label, optimizer, traffic, city)

    # Summary recommendation
    best = routes[0]
    print(f"\n  ✅ RECOMMENDATION: Take the {labels[0]}")
    print(f"     Estimated arrival in {best.total_time:.0f} minutes "
          f"covering {best.total_distance:.1f} km")


def feature_refresh_traffic(city, traffic):
    """
    FEATURE 3: Simulate traffic changing (e.g., time passing).
    Updates ~30% of roads randomly to simulate real-world changes.
    """
    print("\n  🔄 Refreshing traffic conditions...")

    # Ask if user wants to change time of day
    print(f"  Current simulation hour: {traffic.hour:02d}:00")
    change = input("  Change hour? (y/n): ").strip().lower()
    if change == 'y':
        while True:
            try:
                h = int(input("  Enter new hour (0-23): "))
                if 0 <= h <= 23:
                    traffic.hour = h
                    break
                print("  ⚠️  Enter 0–23.")
            except ValueError:
                print("  ⚠️  Enter a number.")

    traffic.refresh_traffic(city, change_fraction=0.4)
    print(f"  ✅ Traffic updated for {traffic.hour:02d}:00")


# =============================================================
#  MAIN LOOP
# =============================================================

def main():
    print_banner()

    # --- STEP 1: Build the city ---
    print("  ⏳ Loading city map...")
    city = build_sample_city()
    print(f"  ✅ City loaded: {len(city.nodes)} locations, "
          f"{sum(len(v) for v in city.edges.values())//2} roads")

    # --- STEP 2: Ask for time of day ---
    print("\n  🕐 What time of day should we simulate?")
    print("     (Affects traffic congestion levels)")
    print("     Popular choices: 8 = morning rush, 14 = midday, 18 = evening rush, 2 = night")
    while True:
        try:
            hour = int(input("  Enter hour (0-23) [default=8]: ") or "8")
            if 0 <= hour <= 23:
                break
            print("  ⚠️  Enter 0–23.")
        except ValueError:
            print("  ⚠️  Enter a valid number.")

    # --- STEP 3: Initialize traffic ---
    print(f"\n  ⏳ Initializing traffic for {hour:02d}:00...")
    traffic   = TrafficEngine(hour_of_day=hour)
    traffic.initialize_traffic(city)

    rush = "🚨 Rush Hour" if 7 <= hour <= 9 or 17 <= hour <= 19 else \
           "🌙 Night"     if hour < 6 or hour > 22 else "🚗 Normal"
    print(f"  ✅ Traffic initialized  |  Conditions: {rush}")

    # --- STEP 4: Create optimizer ---
    optimizer = RouteOptimizer(city, traffic)

    # --- STEP 5: Main menu loop ---
    while True:
        print_menu()
        choice = input("\n  Your choice (1-5): ").strip()

        if choice == "1":
            feature_find_route(city, traffic, optimizer)

        elif choice == "2":
            traffic.display_traffic_report(city)

        elif choice == "3":
            feature_refresh_traffic(city, traffic)
            # Re-create optimizer with updated traffic
            optimizer = RouteOptimizer(city, traffic)

        elif choice == "4":
            city.display_map()

        elif choice == "5":
            print("\n  👋 Thanks for using Smart Traffic Optimizer. Drive safe!\n")
            break

        else:
            print("  ⚠️  Invalid choice. Enter 1–5.")

        input("\n  Press ENTER to continue...")


# =============================================================
#  ENTRY POINT
# =============================================================

if __name__ == "__main__":
    main()
