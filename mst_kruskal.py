import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import tkinter as tk
from tkinter import ttk, messagebox
import heapq

class MSTApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Minimum Spanning Tree (Prim & Kruskal) - Visualizer")
        self.root.geometry("1100x700")

        # Initialize Graph (NSFNET 14 nodes)
        self.G = nx.Graph()
        self.nodes = {
            0: "Seattle", 1: "Palo Alto", 2: "San Diego", 3: "Salt Lake City",
            4: "Boulder", 5: "Lincoln", 6: "Houston", 7: "Atlanta",
            8: "Chicago", 9: "Ann Arbor", 10: "Pittsburgh", 11: "New York",
            12: "Washington DC", 13: "Princeton"
        }
        for i, name in self.nodes.items():
            self.G.add_node(i, name=name)

        # Realistic NSFNET Links
        self.edges = [
            (0, 1, 800), (0, 3, 850), (1, 2, 500), (1, 8, 2200),
            (2, 3, 750), (2, 6, 1400), (3, 4, 500), (4, 5, 550),
            (4, 9, 1100), (5, 6, 800), (5, 8, 600), (6, 7, 850),
            (7, 10, 700), (7, 12, 650), (8, 9, 250), (8, 11, 800),
            (9, 13, 600), (10, 12, 250), (11, 12, 250), (11, 13, 100),
            (12, 13, 150)
        ]
        self.G.add_weighted_edges_from(self.edges)

        self.mst_edges = []
        self.total_weight = 0
        self.dragging_node = None
        self.is_dragging = False

        # Initial layout
        self.pos = nx.spring_layout(self.G, seed=42)
        self.visible_nodes = set(self.G.nodes)

        self.setup_ui()
        self.plot_graph()

    def setup_ui(self):
        # Sidebar
        self.sidebar = tk.Frame(self.root, width=250, bg="#f0f0f0", padx=10, pady=10)
        self.sidebar.pack(side=tk.LEFT, fill=tk.Y)

        tk.Label(self.sidebar, text="MST (Kruskal's Algorithm)", font=("Arial", 14, "bold"), bg="#f0f0f0").pack(pady=10)
        tk.Label(self.sidebar, text="(Drag nodes to move them)", font=("Arial", 8, "italic"), bg="#f0f0f0", fg="gray").pack()

        # Total Weight Label
        self.weight_label = tk.Label(self.sidebar, text="Total MST Weight: 0", font=("Arial", 10, "bold"), bg="#f0f0f0", fg="#4CAF50")
        self.weight_label.pack(pady=10)

        # Buttons
        tk.Button(self.sidebar, text="Compute MST (Kruskal's)", command=self.compute_kruskal, bg="#4CAF50", fg="white", font=("Arial", 10, "bold")).pack(fill=tk.X, pady=5)
        tk.Button(self.sidebar, text="Compute MST (Prim's)", command=self.compute_mst, bg="#8E44AD", fg="white", font=("Arial", 10, "bold")).pack(fill=tk.X, pady=5)
        tk.Button(self.sidebar, text="Load Topology (topology_sample.txt)", command=self.load_topology_from_file, bg="#FF9800", fg="white").pack(fill=tk.X, pady=5)
        tk.Button(self.sidebar, text="Clear Highlights", command=self.clear_visuals, bg="#2196F3", fg="white").pack(fill=tk.X, pady=5)
        tk.Button(self.sidebar, text="Reset Layout", command=self.reset_layout, bg="#9E9E9E", fg="white").pack(fill=tk.X, pady=5)

        # Graph Editing
        tk.Label(self.sidebar, text="--- Edit Graph ---", bg="#f0f0f0", font=("Arial", 10, "italic")).pack(pady=10)
        
        # Add Node
        tk.Label(self.sidebar, text="Node Name:", bg="#f0f0f0").pack(anchor="w")
        self.new_node_entry = tk.Entry(self.sidebar)
        self.new_node_entry.pack(fill=tk.X, pady=2)
        tk.Button(self.sidebar, text="Add Node", command=self.add_node).pack(fill=tk.X, pady=2)
        tk.Button(self.sidebar, text="Remove Node", command=self.remove_node).pack(fill=tk.X, pady=2)

        # Add Edge
        tk.Label(self.sidebar, text="Edge (Node1, Node2, Weight):", bg="#f0f0f0").pack(anchor="w")
        self.edge_entry = tk.Entry(self.sidebar)
        self.edge_entry.insert(0, "Seattle, Chicago, 1500")
        self.edge_entry.pack(fill=tk.X, pady=2)
        tk.Button(self.sidebar, text="Add/Update Edge", command=self.add_edge).pack(fill=tk.X, pady=2)
        tk.Button(self.sidebar, text="Remove Edge", command=self.remove_edge).pack(fill=tk.X, pady=2)

        # Main Plot Area
        self.main_area = tk.Frame(self.root, bg="white")
        self.main_area.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self.fig, self.ax = plt.subplots(figsize=(8, 6))
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.main_area)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # Bind Mouse Events for dragging
        self.canvas.mpl_connect("button_press_event", self.on_press)
        self.canvas.mpl_connect("button_release_event", self.on_release)
        self.canvas.mpl_connect("motion_notify_event", self.on_motion)

    def on_press(self, event):
        if event.inaxes != self.ax: return
        # Check if we clicked on a node
        for node in self.visible_nodes:
            x, y = self.pos[node]
            dist = (x - event.xdata)**2 + (y - event.ydata)**2
            if dist < 0.005: # Threshold for selection
                self.dragging_node = node
                self.is_dragging = True
                break

    def on_motion(self, event):
        if self.is_dragging and event.inaxes == self.ax:
            self.pos[self.dragging_node] = [event.xdata, event.ydata]
            self.plot_graph()

    def on_release(self, event):
        self.is_dragging = False
        self.dragging_node = None

    def reset_layout(self):
        self.pos = nx.spring_layout(self.G, seed=42)
        self.visible_nodes = set(self.G.nodes)
        self.plot_graph()

    def plot_graph(self):
        """Renders the graph and highlights the Minimum Spanning Tree edges."""
        self.ax.clear()
        
        # Only draw nodes that are marked as visible
        nodes_to_draw = list(self.visible_nodes)
        if not nodes_to_draw: return

        # Draw Nodes
        nx.draw_networkx_nodes(self.G, self.pos, nodelist=nodes_to_draw, ax=self.ax, node_color="#ADD8E6", node_size=700)
        nx.draw_networkx_labels(self.G, self.pos, labels={n: self.G.nodes[n].get('name', n) for n in nodes_to_draw}, ax=self.ax, font_size=8)
        
        # Filter Edges that are between visible nodes
        edge_list = []
        for u, v in self.G.edges():
            if u in self.visible_nodes and v in self.visible_nodes:
                edge_list.append((u, v))

        edge_colors = []
        widths = []
        
        mst_set = set()
        for u, v in self.mst_edges:
            mst_set.add(tuple(sorted((u, v))))

        for u, v in edge_list:
            if tuple(sorted((u, v))) in mst_set:
                edge_colors.append("#228B22") # Forest Green for MST
                widths.append(3)
            else:
                edge_colors.append("#CCCCCC") # Light Gray for non-MST edges
                widths.append(1)

        nx.draw_networkx_edges(self.G, self.pos, edgelist=edge_list, ax=self.ax, edge_color=edge_colors, width=widths, alpha=0.7)
        edge_labels = {(u, v): d['weight'] for u, v, d in self.G.edges(data=True) if (u, v) in edge_list or (v, u) in edge_list}
        nx.draw_networkx_edge_labels(self.G, self.pos, edge_labels=edge_labels, ax=self.ax, font_size=7)

        self.ax.set_title("Minimum Spanning Tree (MST)")
        self.ax.axis('off')
        self.canvas.draw()

    def get_node_id_by_name(self, name):
        """Helper to find node ID from city name."""
        for n in self.G.nodes:
            if self.G.nodes[n].get('name') == name:
                return n
        return None

    def load_topology_from_file(self):
        """Loads network topology from topology_sample.txt."""
        import os
        filename = "topology_sample.txt"
        if not os.path.exists(filename):
            messagebox.showerror("Error", f"File '{filename}' not found.")
            return

        try:
            with open(filename, 'r') as f:
                lines = f.readlines()

            # Clear existing graph
            self.G.clear()
            self.nodes = {}
            node_map = {}
            current_id = 0

            for line in lines:
                parts = line.strip().split()
                if len(parts) != 3:
                    continue
                u_name, v_name, weight = parts[0], parts[1], float(parts[2])

                for name in [u_name, v_name]:
                    if name not in node_map:
                        node_map[name] = current_id
                        self.G.add_node(current_id, name=name)
                        self.nodes[current_id] = name
                        current_id += 1
                
                self.G.add_edge(node_map[u_name], node_map[v_name], weight=weight)

            self.clear_visuals()
            self.reset_layout()
            messagebox.showinfo("Success", f"Loaded topology from {filename}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load topology: {e}")

    def compute_mst(self):
        """
        Implementation of Prim's Algorithm for Minimum Spanning Tree.
        Complexity: O(E log V) using a binary heap.
        """
        if not self.G.nodes: return
        
        # Start with an arbitrary node
        start_node = list(self.G.nodes)[0]
        visited = {start_node}
        edges_heap = [] # Stores (weight, from_node, to_node)
        
        # Add all edges connected to the start node into the priority queue
        for v in self.G.neighbors(start_node):
            weight = self.G[start_node][v]['weight']
            heapq.heappush(edges_heap, (weight, start_node, v))
            
        self.mst_edges = []
        self.total_weight = 0
        
        # Continue until all reachable nodes are visited
        while edges_heap and len(visited) < len(self.G.nodes):
            # Extract the cheapest edge connecting visited set to unvisited set
            weight, u, v = heapq.heappop(edges_heap)
            
            if v not in visited:
                # Add edge to MST
                visited.add(v)
                self.mst_edges.append((u, v))
                self.total_weight += weight
                
                # Add new adjacent edges to the heap
                for next_v in self.G.neighbors(v):
                    if next_v not in visited:
                        next_weight = self.G[v][next_v]['weight']
                        heapq.heappush(edges_heap, (next_weight, v, next_v))
        
        self.weight_label.config(text=f"Total MST Weight: {self.total_weight:.2f}")
        
        # Only keep nodes that are part of the MST edges (or the start node if only 1 node)
        mst_nodes = set()
        for u, v in self.mst_edges:
            mst_nodes.add(u)
            mst_nodes.add(v)
        
        if not mst_nodes and list(self.G.nodes):
            mst_nodes.add(list(self.G.nodes)[0])

        self.visible_nodes = mst_nodes # Hide unconnected nodes
        self.plot_graph()
        
        if len(visited) < len(self.G.nodes):
            messagebox.showwarning("Warning", "The graph is currently disconnected. Showing MST for the primary component.")

    def compute_kruskal(self):
        """
        Implementation of Kruskal's Algorithm for Minimum Spanning Tree.
        Complexity: O(E log E) or O(E log V).
        """
        if not self.G.nodes: return

        # Union-Find (Disjoint Set Union) Structure
        parent = {n: n for n in self.G.nodes}
        def find(i):
            if parent[i] == i: return i
            parent[i] = find(parent[i])
            return parent[i]

        def union(i, j):
            root_i = find(i)
            root_j = find(j)
            if root_i != root_j:
                parent[root_i] = root_j
                return True
            return False

        # Get all edges and sort by weight
        edges = []
        for u, v, d in self.G.edges(data=True):
            edges.append((d['weight'], u, v))
        edges.sort()

        self.mst_edges = []
        self.total_weight = 0
        mst_nodes = set()

        for weight, u, v in edges:
            if union(u, v):
                self.mst_edges.append((u, v))
                self.total_weight += weight
                mst_nodes.add(u)
                mst_nodes.add(v)

        self.weight_label.config(text=f"Total MST Weight (Kruskal): {self.total_weight:.2f}")
        
        # In a connected graph, all nodes will be in mst_nodes. 
        # For disconnected graphs, it shows the forest.
        if not mst_nodes and list(self.G.nodes):
            mst_nodes.add(list(self.G.nodes)[0])
            
        self.visible_nodes = mst_nodes
        self.plot_graph()

        if len(self.mst_edges) < len(self.G.nodes) - 1:
            messagebox.showwarning("Warning", "The graph is disconnected. Showing a Minimum Spanning Forest.")

    def clear_visuals(self):
        """Resets the visualization to show the base graph."""
        self.mst_edges = []
        self.total_weight = 0
        self.weight_label.config(text="Total MST Weight: 0")
        self.visible_nodes = set(self.G.nodes) # Restore all nodes
        self.plot_graph()

    def add_node(self):
        """Adds a new node to the graph."""
        name = self.new_node_entry.get().strip()
        if not name: return
        new_id = max(self.G.nodes) + 1 if self.G.nodes else 0
        self.G.add_node(new_id, name=name)
        self.nodes[new_id] = name
        self.visible_nodes.add(new_id) # Ensure new node is visible
        
        # Assign a random/default position if not existing
        if new_id not in self.pos:
            import numpy as np
            import random
            self.pos[new_id] = np.array([random.uniform(-1, 1), random.uniform(-1, 1)])
            
        self.plot_graph()

    def remove_node(self):
        """Removes a node from the graph."""
        name = self.new_node_entry.get().strip()
        if not name: return
        node_id = self.get_node_id_by_name(name)
        if node_id is not None:
            self.G.remove_node(node_id)
            if node_id in self.nodes: del self.nodes[node_id]
            if node_id in self.pos: del self.pos[node_id]
            if node_id in self.visible_nodes: self.visible_nodes.remove(node_id)
            self.plot_graph()
        else:
            messagebox.showerror("Error", f"Node '{name}' not found.")

    def add_edge(self):
        """Adds or updates an edge weight."""
        text = self.edge_entry.get()
        try:
            n1_name, n2_name, w = [x.strip() for x in text.split(',')]
            u = self.get_node_id_by_name(n1_name)
            v = self.get_node_id_by_name(n2_name)
            if u is None or v is None: raise Exception("Nodes not found")
            self.G.add_edge(u, v, weight=float(w))
            self.plot_graph()
        except Exception as e:
            messagebox.showerror("Error", f"Expected Format: Node1, Node2, Weight.\nError: {e}")

    def remove_edge(self):
        """Removes an edge from the graph."""
        text = self.edge_entry.get()
        try:
            parts = [x.strip() for x in text.split(',')]
            n1_name, n2_name = parts[0], parts[1]
            u = self.get_node_id_by_name(n1_name)
            v = self.get_node_id_by_name(n2_name)
            if self.G.has_edge(u, v):
                self.G.remove_edge(u, v)
                self.plot_graph()
        except:
            messagebox.showerror("Error", "Expected Format: Node1, Node2")

if __name__ == "__main__":
    import os
    try:
        root = tk.Tk()
        app = MSTApp(root)
        root.protocol("WM_DELETE_WINDOW", lambda: os._exit(0))
        root.mainloop()
    except KeyboardInterrupt:
        os._exit(0)
