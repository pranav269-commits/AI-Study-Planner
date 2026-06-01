# modules/algorithms.py
# CO2 search algorithms used by the Algorithm Visualizer.

from collections import deque
import heapq

def bfs(graph, start, goal):
    queue = deque([[start]])
    visited, seen = [], set()
    while queue:
        path = queue.popleft()
        node = path[-1]
        if node in seen:
            continue
        visited.append(node)
        seen.add(node)
        if node == goal:
            cost = sum(graph[path[i]][path[i + 1]] for i in range(len(path) - 1))
            return visited, path, cost
        for nb in graph.get(node, {}):
            if nb not in seen:
                queue.append(path + [nb])
    return visited, [], float("inf")

def dfs(graph, start, goal):
    stack = [[start]]
    visited, seen = [], set()
    while stack:
        path = stack.pop()
        node = path[-1]
        if node in seen:
            continue
        visited.append(node)
        seen.add(node)
        if node == goal:
            cost = sum(graph[path[i]][path[i + 1]] for i in range(len(path) - 1))
            return visited, path, cost
        for nb in reversed(list(graph.get(node, {}).keys())):
            if nb not in seen:
                stack.append(path + [nb])
    return visited, [], float("inf")

def ucs(graph, start, goal):
    pq = [(0, [start])]
    visited, seen = [], set()
    while pq:
        cost, path = heapq.heappop(pq)
        node = path[-1]
        if node in seen:
            continue
        visited.append(node)
        seen.add(node)
        if node == goal:
            return visited, path, cost
        for nb, w in graph.get(node, {}).items():
            if nb not in seen:
                heapq.heappush(pq, (cost + w, path + [nb]))
    return visited, [], float("inf")

def greedy(graph, start, goal, h):
    pq = [(h.get(start, 0), [start])]
    visited, seen = [], set()
    while pq:
        _, path = heapq.heappop(pq)
        node = path[-1]
        if node in seen:
            continue
        visited.append(node)
        seen.add(node)
        if node == goal:
            cost = sum(graph[path[i]][path[i + 1]] for i in range(len(path) - 1))
            return visited, path, cost
        for nb in graph.get(node, {}):
            if nb not in seen:
                heapq.heappush(pq, (h.get(nb, 0), path + [nb]))
    return visited, [], float("inf")

def astar(graph, start, goal, h):
    pq = [(h.get(start, 0), 0, [start])]
    visited, seen = [], set()
    while pq:
        f, g, path = heapq.heappop(pq)
        node = path[-1]
        if node in seen:
            continue
        visited.append(node)
        seen.add(node)
        if node == goal:
            return visited, path, g
        for nb, w in graph.get(node, {}).items():
            if nb not in seen:
                ng = g + w
                heapq.heappush(pq, (ng + h.get(nb, 0), ng, path + [nb]))
    return visited, [], float("inf")

