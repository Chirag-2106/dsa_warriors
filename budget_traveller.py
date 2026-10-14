
import heapq
import csv
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

N, M = map(int, input("Enter N and M: ").split())
K, C = map(int, input("Enter K and C: ").split())

if N < 1 or M < 0 or K < 0 or C < 0:
    raise ValueError("Invalid input")

flights = []
graph = [[] for _ in range(N + 1)]

for i in range(M):
    u, v, p = map(int, input().split())

    if not (1 <= u <= N and 1 <= v <= N) or p < 0:
        raise ValueError("Invalid flight")

    flights.append((u, v, p))
    graph[u].append((v, p, i))

max_flights = K + 1
INF = float("inf")

dist = [
    [[INF] * (C + 1) for _ in range(N + 1)]
    for _ in range(max_flights + 1)
]

parent = {}
dist[0][1][0] = 0
pq = [(0, 0, 1, 0)]

while pq:
    cost, steps, city, used = heapq.heappop(pq)

    if cost != dist[steps][city][used]:
        continue

    if steps == max_flights:
        continue

    for nxt, price, fid in graph[city]:
        new_steps = steps + 1

        # Normal flight
        normal_cost = cost + price

        if normal_cost < dist[new_steps][nxt][used]:
            dist[new_steps][nxt][used] = normal_cost
            parent[(new_steps, nxt, used)] = (
                (steps, city, used), fid, False
            )
            heapq.heappush(
                pq, (normal_cost, new_steps, nxt, used)
            )

        # Flight using a coupon
        if used < C:
            coupon_cost = cost + price // 2

            if coupon_cost < dist[new_steps][nxt][used + 1]:
                dist[new_steps][nxt][used + 1] = coupon_cost
                parent[(new_steps, nxt, used + 1)] = (
                    (steps, city, used), fid, True
                )
                heapq.heappush(
                    pq,
                    (coupon_cost, new_steps, nxt, used + 1)
                )

best = min(
    (dist[s][N][c], s, c)
    for s in range(max_flights + 1)
    for c in range(C + 1)
)

if best[0] == INF:
    print(-1)

else:
    answer, steps, used = best
    state = (steps, N, used)
    chosen = []

    while state != (0, 1, 0):
        previous, fid, coupon = parent[state]
        chosen.append((fid, coupon))
        state = previous

    chosen.reverse()

    path = [1]
    selected_ids = set()
    coupon_ids = set()
    running_cost = 0
    journey = []

    for fid, coupon in chosen:
        u, v, price = flights[fid]

        selected_ids.add(fid)
        path.append(v)

        paid = price // 2 if coupon else price

        if coupon:
            coupon_ids.add(fid)
            print(f"Coupon on {u}->{v}: {price} -> {paid}")

        running_cost += paid

        journey.append({
            "fid": fid,
            "u": u,
            "v": v,
            "price": price,
            "paid": paid,
            "coupon": coupon,
            "running": running_cost
        })

        print(f"Flight {u}->{v}, running cost: {running_cost}")

    print("Minimum cost:", answer)
    print("Path:", " -> ".join(map(str, path)))
    print("Intermediate stops:", max(0, len(path) - 2))
    print("Coupons used:", len(coupon_ids))

    # Export flight information to CSV
    with open("result.csv", "w", newline="") as file:
        writer = csv.writer(file)

        writer.writerow([
            "FlightID", "From", "To", "Price",
            "Selected", "CouponUsed"
        ])

        for i, (u, v, p) in enumerate(flights):
            writer.writerow([
                i + 1,
                u,
                v,
                p,
                "x" if i in selected_ids else "",
                "x" if i in coupon_ids else ""
            ])

    print("CSV saved as result.csv")

    # Create the directed flight graph
    G = nx.MultiDiGraph()
    G.add_nodes_from(range(1, N + 1))

    for i, (u, v, p) in enumerate(flights):
        G.add_edge(u, v, key=i, weight=p)

    pos = nx.spring_layout(G, seed=42)

    # Colour the cities
    node_colors = []

    for city in G.nodes():
        if city == 1:
            node_colors.append("green")
        elif city == N:
            node_colors.append("red")
        elif city in path:
            node_colors.append("orange")
        else:
            node_colors.append("lightblue")

    edges = list(G.edges(keys=True))

    edge_colors = [
        "gold" if i in coupon_ids
        else "dodgerblue" if i in selected_ids
        else "gray"
        for u, v, i in edges
    ]

    fig, ax = plt.subplots(figsize=(11, 7))

    nx.draw_networkx_nodes(
        G, pos,
        node_color=node_colors,
        node_size=900,
        ax=ax
    )

    nx.draw_networkx_labels(
        G, pos,
        font_weight="bold",
        ax=ax
    )

    nx.draw_networkx_edges(
        G, pos,
        edgelist=edges,
        edge_color=edge_colors,
        arrows=True,
        arrowsize=20,
        connectionstyle="arc3,rad=0.08",
        ax=ax
    )

    # Display the original price on every flight
    labels = {
        (u, v, i): str(p)
        for i, (u, v, p) in enumerate(flights)
    }

    nx.draw_networkx_edge_labels(
        G, pos,
        edge_labels=labels,
        font_size=9,
        ax=ax
    )

    # Create highlighted lines for the chosen route
    route_lines = []

    for leg in journey:
        x1, y1 = pos[leg["u"]]
        x2, y2 = pos[leg["v"]]

        line, = ax.plot(
            [x1, x2],
            [y1, y2],
            color="gold" if leg["coupon"] else "deepskyblue",
            linewidth=4,
            alpha=0,
            zorder=4
        )

        route_lines.append(line)

    # Traveller marker starts at city 1
    start_x, start_y = pos[1]

    traveller, = ax.plot(
        [start_x],
        [start_y],
        marker="o",
        markersize=16,
        markerfacecolor="white",
        markeredgecolor="black",
        markeredgewidth=2,
        linestyle="None",
        zorder=10
    )

    # Live animation status
    status_text = ax.text(
        0.02, 0.98,
        "Ready to travel",
        transform=ax.transAxes,
        va="top",
        fontsize=11,
        fontweight="bold",
        bbox=dict(
            boxstyle="round,pad=0.4",
            facecolor="white",
            alpha=0.9
        )
    )

    def update(frame):
        if not journey:
            status_text.set_text("Journey completed!")
            return [traveller, status_text]

        # Starting frame
        if frame == 0:
            x, y = pos[path[0]]
            traveller.set_data([x], [y])
            status_text.set_text(
                f"Starting at city {path[0]} | Cost: ₹0"
            )
            return [traveller, status_text, *route_lines]

        # Determine the current flight and animation progress
        leg_index = min(
            (frame - 1) // 20,
            len(journey) - 1
        )

        step_frame = (frame - 1) % 20
        leg = journey[leg_index]

        x1, y1 = pos[leg["u"]]
        x2, y2 = pos[leg["v"]]

        fraction = step_frame / 19

        x = x1 + (x2 - x1) * fraction
        y = y1 + (y2 - y1) * fraction

        traveller.set_data([x], [y])

        # Highlight the route already travelled
        for i, line in enumerate(route_lines):
            line.set_alpha(0.95 if i <= leg_index else 0)
            line.set_linewidth(5 if i == leg_index else 3)

        # Update cost and coupon information
        if leg["coupon"]:
            status_text.set_text(
                f"Coupon: {leg['u']} → {leg['v']} | "
                f"₹{leg['price']} → ₹{leg['paid']} | "
                f"Running cost: ₹{leg['running']}"
            )
        else:
            status_text.set_text(
                f"Flying: {leg['u']} → {leg['v']} | "
                f"Running cost: ₹{leg['running']}"
            )

        # Final frame: place traveller at destination
        if frame >= len(journey) * 20:
            x, y = pos[path[-1]]
            traveller.set_data([x], [y])

            status_text.set_text(
                f"Journey complete! Cost: ₹{answer} | "
                f"Stops: {max(0, len(path) - 2)} | "
                f"Coupons: {len(coupon_ids)}"
            )

        return [traveller, status_text, *route_lines]

    ax.set_title(
        f"Budget Traveller | Minimum Cost: ₹{answer}",
        fontsize=14,
        fontweight="bold"
    )

    ax.text(
        0.02, 0.02,
        "Green = Start | Red = Destination | "
        "Blue = Selected flight | Gold = Coupon flight",
        transform=ax.transAxes,
        fontsize=9
    )

    ax.axis("off")
    fig.tight_layout()

    if journey:
        animation = FuncAnimation(
            fig,
            update,
            frames=len(journey) * 20 + 1,
            interval=60,
            blit=False,
            repeat=False
        )

        # Keep the animation object alive
        plt.show()

    else:
        status_text.set_text(
            "Already at destination; no flights needed."
        )
        plt.show()
