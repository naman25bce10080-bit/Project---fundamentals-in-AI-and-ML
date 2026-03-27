# 🚗 Smart Traffic Route Optimizer

An AI-based navigation system that simulates a city, models real-world traffic conditions, and finds the **best driving routes** using advanced algorithms.

---

## 📌 Overview

This project implements a **smart route planning system** similar to real-world navigation tools (like Google Maps), with:

* 🗺️ A city modeled as a **graph**
* 🚦 Dynamic **traffic simulation**
* 🧠 **A* (A-star) pathfinding algorithm**
* 📊 Multi-criteria route scoring (time, distance, congestion)

It not only finds the shortest path — it finds the **best practical route under real traffic conditions**.

---

## ⚙️ How It Works

### 1. City as a Graph

Defined in `city_graph.py` 

* Nodes → locations (e.g., Airport, City Center)
* Edges → roads
* Each road has:

  * Distance
  * Speed limit
  * Road type (highway/main/local)

---

### 2. Traffic Simulation

Handled by `traffic_engine.py` 

Traffic is dynamically generated based on:

* Time of day (rush hour vs night)
* Road type
* Random variations (accidents, delays)

Each road gets a **congestion score (0.0 → 1.0)** that affects travel time.

---

### 3. Route Optimization (A* Algorithm)

Implemented in `optimizer.py` 

Uses:

* **A*** search → finds optimal path efficiently
* Heuristic → Euclidean distance
* Cost → real travel time (adjusted for traffic)

Also:

* Generates **alternative routes**
* Scores routes using:

  ```
  Score = time + distance + congestion
  ```

---

### 4. Interactive Interface

Main program: `main.py` 

Provides:

* Route search
* Traffic reports
* Simulation refresh
* Map display

---

### 5. Test Script

Quick validation: `test_run.py` 

Ensures:

* All modules work correctly
* Routing and traffic are functional

---

## 🛠️ Installation & Setup

### ✅ Requirements

* Python 3.8 or higher
* No external libraries required (pure Python)

---

### 📥 Step 1: Clone or Download

```bash
git clone <your-repo-url>
cd smart-traffic-optimizer
```

OR just place all `.py` files in one folder.

---

### ▶️ Step 2: Run Test (Recommended)

```bash
python test_run.py
```

Expected output:

```
✅ ALL TESTS PASSED — Run 'python main.py' to start!
```

---

### 🚀 Step 3: Start the Application

```bash
python main.py
```

---

## 🎮 How to Use

### 1. Start Program

You’ll see a menu like:

```
1. Find Best Route
2. View Live Traffic Report
3. Refresh Traffic
4. Show City Map
5. Exit
```

---

### 2. Find a Route

* Choose option `1`
* Select:

  * Start location
  * Destination

You’ll get:

* 🥇 Best route
* 🥈 Alternative routes
* Travel time
* Distance
* Traffic conditions
* Turn-by-turn instructions

---

### 3. View Traffic

Option `2` shows:

* Congestion level for every road
* Visual indicators (Free → Gridlock)

---

### 4. Refresh Traffic

Option `3`:

* Simulates real-time traffic changes
* Optionally change time of day

---

### 5. Show Map

Option `4`:

* Displays all locations and connections

---

## 🧠 Key Concepts Used

### ✔ Graph Theory

* Adjacency list representation
* Nodes & weighted edges

### ✔ A* Algorithm

* Efficient shortest-path search
* Uses:

  * `g(n)` → actual cost
  * `h(n)` → estimated cost

### ✔ Simulation Modeling

* Gaussian-based traffic patterns
* Random noise for realism

### ✔ Multi-Criteria Decision Making

* Balances:

  * Time
  * Distance
  * Congestion

---

## 📁 Project Structure

```
├── city_graph.py        # City map and graph structure
├── traffic_engine.py    # Traffic simulation
├── optimizer.py        # A* routing + scoring
├── main.py             # Interactive program
├── test_run.py         # Test script
└── README.md           # Documentation
```

---

## 🧪 Example Scenario

* Start: Airport
* Destination: University
* Time: 8 AM (rush hour)

System will:

1. Simulate heavy traffic
2. Run A*
3. Compare multiple routes
4. Recommend the fastest practical path

---

## 🔧 Customization

You can easily modify:

### Add new locations

```python
city.add_location("New Place", x=5, y=5)
```

### Add roads

```python
city.add_road("A", "B", distance=3.0, speed_limit=60)
```

### Adjust scoring weights

In `optimizer.py`:

```python
W_TIME = 0.50
W_DISTANCE = 0.20
W_CONGESTION = 0.30
```

---

## 🚀 Future Improvements

* Real map integration (OpenStreetMap)
* Live GPS data
* Machine learning traffic prediction
* GUI (Tkinter / Web app)
* Vehicle-specific routing (bike, truck)

---

## 👨‍💻 Author

Developed as a learning project demonstrating:

* AI search algorithms
* Simulation systems
* Real-world problem modeling

---

## 📜 License

This project is open for educational use and modification.

---

## ✅ Summary

This system demonstrates how modern navigation works by combining:

* Graph theory
* AI pathfinding
* Traffic simulation

👉 Result: **Smart, realistic route recommendations**

---

**Run it, explore it, and try modifying the city — that’s where the real learning happens.**
