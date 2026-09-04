import inspect
from itertools import permutations

import pytest


MODULE_CANDIDATES = (
    "travel_routing",
    "routing",
    "route_planner",
    "travel_planner.routing",
    "src.travel_routing",
)

FUNCTION_CANDIDATES = (
    "find_optimal_route",
    "calculate_optimal_route",
    "compute_optimal_route",
    "plan_route",
)


@pytest.fixture(scope="module")
def route_fn():
    imported_modules = []

    for module_name in MODULE_CANDIDATES:
        module = pytest.importorskip(module_name)
        imported_modules.append(module_name)

        for function_name in FUNCTION_CANDIDATES:
            function = getattr(module, function_name, None)
            if callable(function):
                return function

    pytest.fail(
        "Could not locate a callable routing function. "
        f"Checked modules {imported_modules} for function names {FUNCTION_CANDIDATES}."
    )


def _invoke_route(route_fn, graph, start, end, budget, max_travel_time):
    signature = inspect.signature(route_fn)
    accepted = signature.parameters

    args_by_name = {
        "graph": graph,
        "network": graph,
        "routes": graph,
        "start": start,
        "source": start,
        "origin": start,
        "end": end,
        "target": end,
        "destination": end,
        "budget": budget,
        "max_budget": budget,
        "travel_budget": budget,
        "max_travel_time": max_travel_time,
        "max_time": max_travel_time,
        "time_limit": max_travel_time,
    }

    kwargs = {}
    for name in accepted:
        if name in args_by_name:
            kwargs[name] = args_by_name[name]

    if kwargs:
        return route_fn(**kwargs)

    return route_fn(graph, start, end, budget, max_travel_time)


def _parse_route_result(result):
    if isinstance(result, dict):
        path = result.get("path", result.get("route"))
        cost = result.get("cost", result.get("total_cost"))
        travel_time = result.get("time", result.get("total_time"))
    elif isinstance(result, tuple) and len(result) >= 3:
        path, cost, travel_time = result[0], result[1], result[2]
    else:
        raise AssertionError(
            "Unsupported route return format. Expected dict with path/cost/time "
            "or tuple(path, cost, time)."
        )

    if path is None or cost is None or travel_time is None:
        raise AssertionError(
            "Route result must include path, cost, and travel time values."
        )

    return path, cost, travel_time


def _all_simple_paths(graph, start, end):
    if start == end:
        return [[start]]

    nodes = list(graph.keys())
    if start not in nodes or end not in nodes:
        return []

    middle_nodes = [node for node in nodes if node not in (start, end)]
    paths = []

    for length in range(len(middle_nodes) + 1):
        for middle in permutations(middle_nodes, length):
            candidate = [start, *middle, end]
            if _path_metrics(graph, candidate) is not None:
                paths.append(candidate)

    return paths


def _path_metrics(graph, path):
    total_cost = 0
    total_time = 0

    for current, nxt in zip(path, path[1:]):
        edge = graph.get(current, {}).get(nxt)
        if edge is None:
            return None

        total_cost += edge["cost"]
        total_time += edge["time"]

    return total_cost, total_time


def _best_feasible_path(graph, start, end, budget, max_travel_time):
    candidates = []

    for path in _all_simple_paths(graph, start, end):
        metrics = _path_metrics(graph, path)
        if metrics is None:
            continue

        total_cost, total_time = metrics
        if total_cost <= budget and total_time <= max_travel_time:
            candidates.append((path, total_cost, total_time))

    if not candidates:
        return None

    return min(candidates, key=lambda item: (item[1], item[2], len(item[0])))


def _sample_graph():
    return {
        "A": {
            "B": {"cost": 40, "time": 30},
            "C": {"cost": 20, "time": 25},
            "D": {"cost": 150, "time": 10},
        },
        "B": {
            "D": {"cost": 30, "time": 15},
            "E": {"cost": 25, "time": 40},
        },
        "C": {
            "B": {"cost": 15, "time": 10},
            "D": {"cost": 60, "time": 35},
        },
        "D": {"E": {"cost": 10, "time": 10}},
        "E": {},
    }


def test_standard_route_matches_expected_minimum(route_fn):
    graph = _sample_graph()
    budget = 80
    max_travel_time = 90

    expected = _best_feasible_path(graph, "A", "D", budget, max_travel_time)
    assert expected is not None

    result = _invoke_route(route_fn, graph, "A", "D", budget, max_travel_time)
    path, cost, travel_time = _parse_route_result(result)

    assert path == expected[0]
    assert cost == expected[1]
    assert travel_time == expected[2]


def test_route_stays_within_budget_and_time_constraints(route_fn):
    graph = _sample_graph()
    budget = 70
    max_travel_time = 60

    result = _invoke_route(route_fn, graph, "A", "D", budget, max_travel_time)
    path, cost, travel_time = _parse_route_result(result)

    metrics = _path_metrics(graph, path)
    assert metrics is not None

    computed_cost, computed_time = metrics
    assert computed_cost == cost
    assert computed_time == travel_time
    assert cost <= budget
    assert travel_time <= max_travel_time


def test_negative_budget_raises_value_error(route_fn):
    graph = _sample_graph()

    with pytest.raises(ValueError):
        _invoke_route(route_fn, graph, "A", "D", -1, 60)


def test_zero_travel_time_with_non_identical_nodes_raises(route_fn):
    graph = _sample_graph()

    with pytest.raises(ValueError):
        _invoke_route(route_fn, graph, "A", "D", 100, 0)


def test_start_equals_end_with_zero_time_returns_zero_cost_route(route_fn):
    graph = _sample_graph()

    result = _invoke_route(route_fn, graph, "C", "C", 0, 0)
    path, cost, travel_time = _parse_route_result(result)

    assert path == ["C"]
    assert cost == 0
    assert travel_time == 0


def test_disconnected_nodes_raise_error(route_fn):
    graph = _sample_graph()
    graph["X"] = {}

    with pytest.raises(ValueError):
        _invoke_route(route_fn, graph, "A", "X", 500, 500)


def test_raises_when_no_path_satisfies_constraints(route_fn):
    graph = _sample_graph()

    with pytest.raises(ValueError):
        _invoke_route(route_fn, graph, "A", "E", budget=5, max_travel_time=5)


def test_mathematical_accuracy_across_multiple_constraints(route_fn):
    graph = _sample_graph()
    scenarios = [
        ("A", "D", 80, 90),
        ("A", "D", 70, 60),
        ("A", "E", 60, 90),
        ("C", "E", 50, 70),
    ]

    for start, end, budget, max_travel_time in scenarios:
        expected = _best_feasible_path(graph, start, end, budget, max_travel_time)
        assert expected is not None

        result = _invoke_route(route_fn, graph, start, end, budget, max_travel_time)
        path, cost, travel_time = _parse_route_result(result)

        assert path == expected[0]
        assert cost == expected[1]
        assert travel_time == expected[2]
