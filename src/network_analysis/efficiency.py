
import networkx as nx


def global_weighted_efficiency(G):
    n = len(G)
    denom = n * (n - 1)
    if denom != 0:
        lengths = nx.all_pairs_dijkstra_path_length(G, weight='weight')
        node_counts = dict(nx.all_pairs_shortest_path_length(G))
        g_eff = 0
        for source, targets in lengths:
            for target, weighted_distance in targets.items():
                if weighted_distance > 0 and source != target:
                    g_eff += 1 / weighted_distance
        g_eff /= denom
        # g_eff = sum(1 / d for s, tgts in lengths
        #                   for t, d in tgts.items() if d > 0) / denom
    else:
        g_eff = 0
    # TODO This can be made more efficient by computing all pairs shortest
    # path lengths in parallel.
    return g_eff