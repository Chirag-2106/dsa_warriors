import csv
import itertools
import math
import random
import time
import matplotlib.animation as animation
import matplotlib.pyplot as plt
import networkx as nx

def generate_random_graph(n, edge_prob=0.3, seed=42):
    random.seed(seed)
    G = nx.Graph()
    G.add_nodes_from(range(1, n + 1))
    for u in range(1, n + 1):
        for v in range(u + 1, n + 1):
            if random.random() < edge_prob:
                G.add_edge(u, v)
    return G

def capacitated_welsh_powell(G, R):
    start_time = time.perf_counter()
    sorted_nodes = sorted(G.nodes(), key=lambda node: G.degree(node), reverse=True)
    
    assignment = {}
    slots = {}

    for u in sorted_nodes:
        slot_id = 1
        while True:
            current_occupants = slots.get(slot_id, [])
            if len(current_occupants) < R:
                conflict = any(G.has_edge(u, occupant) for occupant in current_occupants)
                if not conflict:
                    assignment[u] = slot_id
                    slots.setdefault(slot_id, []).append(u)
                    break
            slot_id += 1

    elapsed = (time.perf_counter() - start_time) * 1000
    return assignment, slots, len(slots), elapsed

def exact_capacitated_coloring(G, R, time_limit=10.0):
    start_time = time.perf_counter()
    nodes = list(G.nodes())
    n = len(nodes)
    
    greedy_assign, greedy_slots, ub, _ = capacitated_welsh_powell(G, R)
    best_assignment = greedy_assign.copy()
    min_slots_needed = [ub]

    nodes.sort(key=lambda x: G.degree(x), reverse=True)
    node_idx_map = {node: i for i, node in enumerate(nodes)}
    
    adj = {u: set(G.neighbors(u)) for u in nodes}
    
    current_assignment = {}
    slot_occupants = {}

    def backtrack(idx, max_slot_used):
        if time.perf_counter() - start_time > time_limit:
            return

        if idx == n:
            if max_slot_used < min_slots_needed[0]:
                min_slots_needed[0] = max_slot_used
                best_assignment.clear()
                best_assignment.update(current_assignment)
            return

        u = nodes[idx]

        if max_slot_used >= min_slots_needed[0]:
            return

        for s in range(1, max_slot_used + 2):
            if s >= min_slots_needed[0]:
                break
            
            if len(slot_occupants.get(s, [])) >= R:
                continue
            
            if any(occupant in adj[u] for occupant in slot_occupants.get(s, [])):
                continue

            current_assignment[u] = s
            slot_occupants.setdefault(s, []).append(u)
            new_max = max(max_slot_used, s)

            backtrack(idx + 1, new_max)

            slot_occupants[s].remove(u)
            del current_assignment[u]

    backtrack(0, 0)
    elapsed = (time.perf_counter() - start_time) * 1000

    optimal_slots = {}
    for node, s in best_assignment.items():
        optimal_slots.setdefault(s, []).append(node)

    return best_assignment, optimal_slots, min_slots_needed[0], elapsed

def export_timetable_csv(slots_dict, R, filename="timetable_problem4.csv"):
    header = ["Slot"] + [f"Hall_{i+1}" for i in range(R)]
    with open(filename, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        for s in sorted(slots_dict.keys()):
            row = [f"Slot {s}"] + slots_dict[s] + ["Empty"] * (R - len(slots_dict[s]))
            writer.writerow(row)
    print(f"-> Saved Timetable CSV to: {filename}")

def visualize_results(G, assignment, slots_dict, R):
    fig, axes = plt.subplots(1, 2, figsize=(15, 6))

    ax_graph = axes[0]
    pos = nx.spring_layout(G, seed=42)
    node_colors = [assignment[node] for node in G.nodes()]
    
    nx.draw_networkx_nodes(G, pos, ax=ax_graph, node_color=node_colors, cmap=plt.cm.tab20, node_size=500)
    nx.draw_networkx_edges(G, pos, ax=ax_graph, alpha=0.4)
    nx.draw_networkx_labels(G, pos, ax=ax_graph, font_color="black", font_weight="bold")
    ax_graph.set_title("Conflict Graph (Coloured by Time Slot)", fontsize=12, fontweight="bold")
    ax_graph.axis("off")

    ax_table = axes[1]
    ax_table.axis("off")
    
    table_data = []
    cell_colours = []
    col_labels = [f"Hall {i+1}" for i in range(R)]
    row_labels = [f"Slot {s}" for s in sorted(slots_dict.keys())]

    for s in sorted(slots_dict.keys()):
        row = [f"Course {u}" for u in slots_dict[s]] + ["-"] * (R - len(slots_dict[s]))
        row_colors = [plt.cm.tab20((s - 1) % 20) for _ in slots_dict[s]] + ["#f0f0f0"] * (R - len(slots_dict[s]))
        table_data.append(row)
        cell_colours.append(row_colors)

    table = ax_table.table(
        cellText=table_data,
        cellColours=cell_colours,
        rowLabels=row_labels,
        colLabels=col_labels,
        loc="center",
        cellLoc="center"
    )
    table.scale(1, 1.8)
    table.set_fontsize(10)
    ax_table.set_title(f"Final Timetable Grid (Max {R} Halls/Slot)", fontsize=12, fontweight="bold")

    plt.tight_layout()
    plt.show()

def plot_benchmark_comparison(R=3):
    n_sizes = [6, 10, 14, 18, 22]
    greedy_times, exact_times = [], []
    greedy_slots, exact_slots = [], []

    for n in n_sizes:
        test_g = generate_random_graph(n, edge_prob=0.35, seed=n)
        
        _, _, g_slot_count, g_time = capacitated_welsh_powell(test_g, R)
        greedy_slots.append(g_slot_count)
        greedy_times.append(g_time)

        _, _, e_slot_count, e_time = exact_capacitated_coloring(test_g, R, time_limit=5.0)
        exact_slots.append(e_slot_count)
        exact_times.append(e_time)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5))

    ax1.plot(n_sizes, greedy_slots, marker='o', label='Greedy (Welsh-Powell)')
    ax1.plot(n_sizes, exact_slots, marker='s', linestyle='--', label='Exact (Branch-and-Bound)')
    ax1.set_title("Slots Used vs. Course Count (N)")
    ax1.set_xlabel("Number of Courses (N)")
    ax1.set_ylabel("Total Slots")
    ax1.legend()
    ax1.grid(True)

    ax2.plot(n_sizes, greedy_times, marker='o', color='orange', label='Greedy Time (ms)')
    ax2.plot(n_sizes, exact_times, marker='s', color='red', linestyle='--', label='Exact Time (ms)')
    ax2.set_title("Running Time vs. Course Count (N)")
    ax2.set_xlabel("Number of Courses (N)")
    ax2.set_ylabel("Time (ms)")
    ax2.legend()
    ax2.grid(True)

    plt.tight_layout()
    plt.show()

def animate_course_assignment(G, assignment, R):
    fig, ax = plt.subplots(figsize=(8, 7))
    pos = nx.spring_layout(G, seed=42)
    cmap = plt.cm.tab20

    sorted_nodes = sorted(G.nodes(), key=lambda node: G.degree(node), reverse=True)
    history = []
    current_state = {}

    for u in sorted_nodes:
        current_state = current_state.copy()
        current_state[u] = assignment[u]
        history.append((u, assignment[u], current_state))

    def update(frame_idx):
        ax.clear()
        node_added, slot_given, active_colors = history[frame_idx]

        node_color_list = [
            cmap((active_colors[node] - 1) % 20) if node in active_colors else "#d3d3d3"
            for node in G.nodes()
        ]

        nx.draw_networkx_nodes(
            G, pos, ax=ax,
            node_color=node_color_list,
            node_size=600,
            edgecolors="black"
        )
        nx.draw_networkx_edges(G, pos, ax=ax, alpha=0.35, edge_color="gray")
        nx.draw_networkx_labels(G, pos, ax=ax, font_color="black", font_weight="bold")

        ax.set_title(
            f"Step {frame_idx + 1}/{len(history)}: Assigning Course {node_added} -> Slot {slot_given}",
            fontsize=12,
            fontweight="bold"
        )
        ax.axis("off")

    ani = animation.FuncAnimation(
        fig, update, frames=len(history), interval=600, repeat=False
    )
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    N = 12
    R = 3
    DENSITY = 0.35

    print(f"--- Problem 4: Exam Scheduling (N={N}, R={R}) ---")
    G = generate_random_graph(n=N, edge_prob=DENSITY, seed=42)

    g_assign, g_slots, g_k, g_ms = capacitated_welsh_powell(G, R)
    print(f"\n[Greedy Welsh-Powell]")
    print(f"Total Slots: {g_k} | Status: Heuristic/Approximate | Execution Time: {g_ms:.3f} ms")

    e_assign, e_slots, e_k, e_ms = exact_capacitated_coloring(G, R, time_limit=10.0)
    print(f"\n[Exact Branch-and-Bound]")
    print(f"Total Slots: {e_k} | Status: Proven Optimal | Execution Time: {e_ms:.3f} ms")

    print("\n[Optimal Timetable Assignment]")
    for s in sorted(e_slots.keys()):
        print(f"  Slot {s}: Courses {e_slots[s]}")

    export_timetable_csv(e_slots, R, "exam_timetable.csv")

    visualize_results(G, e_assign, e_slots, R)

    plot_benchmark_comparison(R=R)

    animate_course_assignment(G, e_assign, R)