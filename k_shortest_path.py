import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import copy
import itertools

class KShortestPathApp:
    """
    Advanced Network Routing Application
    Features: 
    - K-Shortest Paths (Normal vs Link-Disjoint)
    - Interactive Node Dragging
    - External Topology Upload (.txt)
    - Dynamic Graph Editing
    """
    def __init__(self, root):
        self.root = root
        self.root.title("Advanced Network Routing Visualizer - K-Shortest Paths")
        self.root.geometry("1100x750")

        # Initial default topology (NSFNET)
        self.initialize_graph()
        
        self.k_paths = []
        self.dragging_node = None
        self.is_dragging = False
        
        self.setup_ui()
        self.plot_graph()

    def initialize_graph(self):
        """Sets up the default NSFNET 14-node topology."""
        self.G = nx.Graph()
        self.nodes_data = {
            0: "Seattle", 1: "Palo Alto", 2: "San Diego", 3: "Salt Lake City",
            4: "Boulder", 5: "Lincoln", 6: "Houston", 7: "Atlanta",
            8: "Chicago", 9: "Ann Arbor", 10: "Pittsburgh", 11: "New York",
            12: "Washington DC", 13: "Princeton"
        }
        for i, name in self.nodes_data.items():
            self.G.add_node(i, name=name)

        links = [
            (0, 1, 800), (0, 3, 850), (1, 2, 500), (1, 8, 2200),
            (2, 3, 750), (2, 6, 1400), (3, 4, 500), (4, 5, 550),
            (4, 9, 1100), (5, 6, 800), (5, 8, 600), (6, 7, 850),
            (7, 10, 700), (7, 12, 650), (8, 9, 250), (8, 11, 800),
            (9, 13, 600), (10, 12, 250), (11, 12, 250), (11, 13, 100),
            (12, 13, 150)
        ]
        self.G.add_weighted_edges_from(links)
        self.pos = nx.spring_layout(self.G, seed=42)

    def setup_ui(self):
        # Sidebar for controls
        self.sidebar = tk.Frame(self.root, width=280, bg="#f8f9fa", borderwidth=1, relief="ridge")
        self.sidebar.pack(side=tk.LEFT, fill=tk.Y)

        tk.Label(self.sidebar, text="Routing Configuration", font=("Arial", 16, "bold"), bg="#f8f9fa", fg="#333").pack(pady=(20, 10))
        
        # --- FEATURE: LINK-DISJOINT TOGGLE ---
        self.mode_label = tk.Label(self.sidebar, text="Mode: Link-Disjoint ON", font=("Arial", 10, "italic"), bg="#f8f9fa", fg="#d63384")
        self.mode_label.pack(pady=(0, 10))

        self.disjoint_var = tk.BooleanVar(value=True) 
        self.disjoint_cb = tk.Checkbutton(self.sidebar, text="Link-Disjoint Constraint", variable=self.disjoint_var, 
                                          command=self.update_mode_indicator, bg="#f8f9fa", font=("Arial", 10), activebackground="#f8f9fa")
        self.disjoint_cb.pack(pady=5)

        # Dropdowns for Source/Destination
        tk.Label(self.sidebar, text="Source Node:", bg="#f8f9fa").pack(anchor="w", padx=20)
        self.src_var = tk.StringVar()
        self.src_combo = ttk.Combobox(self.sidebar, textvariable=self.src_var, state="readonly")
        self.src_combo.pack(fill=tk.X, padx=20, pady=5)

        tk.Label(self.sidebar, text="Destination Node:", bg="#f8f9fa").pack(anchor="w", padx=20)
        self.dest_var = tk.StringVar()
        self.dest_combo = ttk.Combobox(self.sidebar, textvariable=self.dest_var, state="readonly")
        self.dest_combo.pack(fill=tk.X, padx=20, pady=5)

        self.refresh_combos()

        # K Input
        tk.Label(self.sidebar, text="Value of K:", bg="#f8f9fa").pack(anchor="w", padx=20)
        self.k_entry = tk.Entry(self.sidebar)
        self.k_entry.pack(fill=tk.X, padx=20, pady=5)
        self.k_entry.insert(0, "2")

        # Buttons
        self.btn_compute = tk.Button(self.sidebar, text="Compute Paths", command=self.compute_paths, bg="#007bff", fg="white", font=("Arial", 11, "bold"), relief="flat", cursor="hand2")
        self.btn_compute.pack(fill=tk.X, padx=20, pady=15)

        self.btn_export = tk.Button(self.sidebar, text="Export All Paths (.txt)", command=self.export_all_paths, bg="#17a2b8", fg="white", font=("Arial", 10, "bold"), relief="flat", cursor="hand2")
        self.btn_export.pack(fill=tk.X, padx=20, pady=(0, 15))

        self.btn_upload = tk.Button(self.sidebar, text="Upload Topology", command=self.upload_topology, bg="#28a745", fg="white", font=("Arial", 10), relief="flat", cursor="hand2")
        self.btn_upload.pack(fill=tk.X, padx=20, pady=5)

        self.btn_reset = tk.Button(self.sidebar, text="Reset Graph", command=self.reset_to_default, bg="#dc3545", fg="white", font=("Arial", 10), relief="flat", cursor="hand2")
        self.btn_reset.pack(fill=tk.X, padx=20, pady=5)

        tk.Button(self.sidebar, text="Clear Highlights", command=self.clear_visuals, bg="#6c757d", fg="white", relief="flat").pack(fill=tk.X, padx=20, pady=5)

        # Matplotlib Area
        self.main_area = tk.Frame(self.root, bg="white")
        self.main_area.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self.fig, self.ax = plt.subplots(figsize=(8, 6))
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.main_area)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Node Dragging Events
        self.canvas.mpl_connect("button_press_event", self.on_press)
        self.canvas.mpl_connect("button_release_event", self.on_release)
        self.canvas.mpl_connect("motion_notify_event", self.on_motion)

    def refresh_combos(self):
        """Updates the dropdown values based on the current graph nodes."""
        node_names = [self.G.nodes[n].get('name', str(n)) for n in self.G.nodes]
        self.src_combo['values'] = node_names
        self.dest_combo['values'] = node_names
        if node_names:
            if "Seattle" in node_names: self.src_combo.set("Seattle")
            else: self.src_combo.set(node_names[0])
            
            if "Lincoln" in node_names: self.dest_combo.set("Lincoln")
            else: self.dest_combo.set(node_names[-1])

    def update_mode_indicator(self):
        """Updates the UI text when toggle is changed."""
        if self.disjoint_var.get():
            self.mode_label.config(text="Mode: Link-Disjoint ON", fg="#d63384")
        else:
            self.mode_label.config(text="Mode: Link-Disjoint OFF (Normal)", fg="#0d6efd")

    def upload_topology(self):
        file_path = filedialog.askopenfilename(filetypes=[("Text Files", "*.txt")])
        if not file_path: return
        try:
            new_G = nx.Graph()
            node_map = {}
            with open(file_path, 'r') as f:
                for line in f:
                    parts = line.strip().split()
                    if len(parts) < 3: continue
                    u_name, v_name, weight = parts[0], parts[1], float(parts[2])
                    for name in [u_name, v_name]:
                        if name not in node_map:
                            obj_id = len(node_map)
                            node_map[name] = obj_id
                            new_G.add_node(obj_id, name=name)
                    new_G.add_edge(node_map[u_name], node_map[v_name], weight=weight)
            self.G = new_G
            self.pos = nx.spring_layout(self.G)
            self.k_paths = []
            self.refresh_combos()
            self.plot_graph()
            messagebox.showinfo("Success", "New Topology loaded successfully!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to parse file.\n{e}")

    def reset_to_default(self):
        self.initialize_graph()
        self.k_paths = []
        self.refresh_combos()
        self.plot_graph()

    def on_press(self, event):
        if event.inaxes != self.ax: return
        for node, (x, y) in self.pos.items():
            dist = (x - event.xdata)**2 + (y - event.ydata)**2
            if dist < 0.005:
                self.dragging_node = node
                self.is_dragging = True
                break

    def on_motion(self, event):
        if self.is_dragging and event.inaxes == self.ax:
            self.pos[self.dragging_node] = [event.xdata, event.ydata]
            self.plot_graph(self.k_paths)

    def on_release(self, event):
        self.is_dragging = False
        self.dragging_node = None

    def plot_graph(self, highlighted_paths=None):
        """Draws the graph and highlights paths. Uses curved edges if paths overlap in Normal mode."""
        self.ax.clear()
        node_labels = {n: self.G.nodes[n].get('name', n) for n in self.G.nodes}
        
        # Draw basic graph structure
        nx.draw_networkx_nodes(self.G, self.pos, ax=self.ax, node_color="#ADD8E6", node_size=700, edgecolors="#333", alpha=0.9)
        nx.draw_networkx_labels(self.G, self.pos, labels=node_labels, ax=self.ax, font_size=8, font_weight="bold")
        
        # Draw base edges in very light gray
        nx.draw_networkx_edges(self.G, self.pos, ax=self.ax, edge_color='#e0e0e0', width=1.0, alpha=0.4)

        if highlighted_paths:
            # High-contrast colors for path visualization (Red, Teal, Indigo, Orange, Pink)
            colors = ['#EF233C', '#06D6A0', '#118AB2', '#FFD166', '#FF006E']
            path_info = ""
            
            for i, (path, weight) in enumerate(highlighted_paths):
                color = colors[i % len(colors)]
                edges_in_path = list(zip(path, path[1:]))
                
                # Use curved lines if multiple paths share edges (Normal mode)
                rad = 0.0
                if not self.disjoint_var.get():
                    if i > 0:
                        rad = 0.15 * ((-1)**i * (i//2 + 1))
                
                nx.draw_networkx_edges(
                    self.G, self.pos, ax=self.ax, 
                    edgelist=edges_in_path, 
                    edge_color=color, 
                    width=3.5 if rad == 0 else 2.5, 
                    alpha=0.8,
                    connectionstyle=f"arc3,rad={rad}" if rad != 0 else "arc3,rad=0",
                    arrows=True,
                    arrowstyle='-',  # Use simple line if no direction is needed
                    arrowsize=1
                )
                
                # Format path names for legend
                names = [self.G.nodes[n].get('name', str(n)) for n in path]
                path_str = " -> ".join(names)
                
                # Color description for legend
                color_names = ['Red', 'Teal', 'Blue', 'Yellow', 'Pink']
                c_name = color_names[i % len(color_names)]
                path_info += f"P{i+1}: {weight} cost ({c_name}) | {path_str}\n"
            
            # Display stats overlay
            self.ax.text(0.02, 0.98, path_info, transform=self.ax.transAxes, verticalalignment='top', 
                         bbox=dict(boxstyle='round,pad=0.5', facecolor='white', alpha=0.85, edgecolor='#ddd'), fontsize=8)

        # Draw weights
        edge_labels = nx.get_edge_attributes(self.G, 'weight')
        nx.draw_networkx_edge_labels(self.G, self.pos, edge_labels=edge_labels, ax=self.ax, font_size=7, alpha=0.7)

        self.ax.set_title("Network Topology Explorer", fontsize=14, fontweight='bold', pad=25)
        self.ax.axis('off')
        self.canvas.draw()

    def get_node_id_by_name(self, name):
        for n in self.G.nodes:
            if self.G.nodes[n].get('name') == name: return n
        return None

    def compute_paths(self):
        src_name, dest_name = self.src_var.get(), self.dest_var.get()
        try: k = int(self.k_entry.get())
        except: messagebox.showerror("Error", "K must be an integer."); return

        src, dest = self.get_node_id_by_name(src_name), self.get_node_id_by_name(dest_name)
        if src is None or dest is None or src == dest:
            messagebox.showerror("Selection Error", "Check your source/destination."); return

        self.k_paths = []
        try:
            if self.disjoint_var.get():
                temp_G = copy.deepcopy(self.G)
                for _ in range(k):
                    try:
                        path = nx.dijkstra_path(temp_G, src, dest, weight='weight')
                        weight = nx.dijkstra_path_length(temp_G, src, dest, weight='weight')
                        self.k_paths.append((path, weight))
                        temp_G.remove_edges_from(list(zip(path, path[1:])))
                    except nx.NetworkXNoPath: break
            else:
                it = nx.shortest_simple_paths(self.G, src, dest, weight='weight')
                for path in itertools.islice(it, k):
                    weight = nx.path_weight(self.G, path, weight='weight')
                    self.k_paths.append((path, weight))
        except Exception as e: messagebox.showerror("Error", str(e))
        
        if not self.k_paths: messagebox.showinfo("Result", "No paths found.")
        self.plot_graph(self.k_paths)

    def clear_visuals(self):
        self.k_paths = []
        self.plot_graph()

    def export_all_paths(self):
        try:
            k = int(self.k_entry.get())
        except ValueError:
            messagebox.showerror("Error", "K must be an integer.")
            return

        file_path = "k_shortest_paths_output.txt"

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                nodes = list(self.G.nodes)
                for i in nodes:
                    for j in nodes:
                        if i == j:
                            continue
                            
                        src_name = self.G.nodes[i].get('name', str(i))
                        dest_name = self.G.nodes[j].get('name', str(j))
                        
                        f.write(f"===== {src_name} → {dest_name} =====\n")
                        
                        paths_found = []
                        try:
                            if self.disjoint_var.get():
                                temp_G = copy.deepcopy(self.G)
                                for _ in range(k):
                                    try:
                                        path = nx.dijkstra_path(temp_G, i, j, weight='weight')
                                        weight = nx.dijkstra_path_length(temp_G, i, j, weight='weight')
                                        paths_found.append((path, weight))
                                        temp_G.remove_edges_from(list(zip(path, path[1:])))
                                    except nx.NetworkXNoPath:
                                        break
                            else:
                                try:
                                    it = nx.shortest_simple_paths(self.G, i, j, weight='weight')
                                    for path in itertools.islice(it, k):
                                        weight = nx.path_weight(self.G, path, weight='weight')
                                        paths_found.append((path, weight))
                                except nx.NetworkXNoPath:
                                    pass
                        except Exception as e:
                            pass
                            
                        if not paths_found:
                            f.write("No path found\n")
                        else:
                            for p_idx, (path, weight) in enumerate(paths_found):
                                names = [self.G.nodes[n].get('name', str(n)) for n in path]
                                path_str = " -> ".join(names)
                                f.write(f"P{p_idx+1}: Cost = {weight} | Path = {path_str}\n")
                        f.write("\n")
            messagebox.showinfo("Success", f"All paths exported to:\n{file_path}")
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export paths:\n{str(e)}")

if __name__ == "__main__":
    import os
    try:
        root = tk.Tk()
        app = KShortestPathApp(root)
        root.protocol("WM_DELETE_WINDOW", lambda: os._exit(0))
        root.mainloop()
    except KeyboardInterrupt:
        os._exit(0)
