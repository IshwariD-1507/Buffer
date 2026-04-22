Smart Emergency Route Finder
A Python-based navigation system that finds optimal routes using real-world map data. It enhances traditional pathfinding by adding emergency handling, dynamic conditions, and intelligent decision-making.

Tech Stack
Python
OSMnx
NetworkX
Folium
Streamlit
Algorithms
Dijkstra's Algorithm
A* Search Algorithm
BFS (hospital search)
Bitmask Dijkstra (waypoints)
 Features
1. Normal Routing
Computes shortest path between two locations
Supports both Dijkstra and A* for comparison
2.  Emergency Mode
Finds nearby hospitals using BFS
Ranks hospitals using:
Travel distance
Simulated bed availability
Selects optimal hospital dynamically
3. Distress Handling
Simulates ambulance breakdown
Re-routes using A* from current location
Supports replacement ambulance coordination
4. Waypoint Routing
Ensures route passes through required stops (e.g., petrol pumps)
Uses bitmask-based Dijkstra for optimal traversal
5. Road Quality Reviews
Users can submit reviews (potholes, traffic, etc.)
Stores last 50 reviews per edge using heap
Applies time-decay scoring to prioritize recent data
Dynamically affects route selection
Run the Project
pip install -r requirements.txt
streamlit run app/main.py
Open: http://localhost:8501

Structure
app/main.py        # Frontend  
features/          # Core features  
graph/             # Algorithms  
map/render.py      # Visualization  
run.py             # Backend integration  
Key Concepts Demonstrated
Graph traversal and optimization
Heuristic search
Priority queues (heap)
Dynamic programming (bitmasking)
Real-time system simulation
Data-driven decision making
Future Improvements
Real-time traffic API integration
Live hospital data (beds, ER availability)
Multi-vehicle coordination
Mobile app deployment
Persistent user review system
Contributors
Team-based implementation with modular design
Each feature developed independently and integrated into a unified system
This is the link of video demonstration: https://drive.google.com/file/d/1XWkfvTNzHVbAqBdWirywgYvvVaSq0VaV/view?usp=sharing
