"""
app.py - Flask Web Application for Discrete Mathematics Fest Team Optimizer.

Provides an interactive GUI for exploring:
1. Combinatorial Search Space and Branch & Bound early pruning.
2. Conflict Graph visualization and Independent Set verification.
3. Real-time constraint adjustment and live speedup benchmarks.
"""

from flask import Flask, jsonify, request, send_from_directory
from typing import Dict, Any, List
from dataset import get_default_dataset
from optimizer import TeamFormationOptimizer
import os

app = Flask(__name__, static_folder="static", template_folder="templates")

# Initialize default dataset in memory
students, conflict_graph = get_default_dataset()


@app.route("/")
def index():
    return send_from_directory("static", "index.html")


@app.route("/api/dataset", methods=["GET"])
def get_dataset():
    """Returns candidate students and conflict graph edges."""
    students_data = [
        {
            "id": s.id,
            "name": s.name,
            "year": s.year,
            "level": "Senior" if s.is_senior else "Junior",
            "skill": s.skill.value,
            "rating": s.rating,
            "conflicts": sorted(list(conflict_graph.adj_set[s.id])),
        }
        for s in students
    ]

    edges = []
    seen = set()
    for u in range(len(students)):
        for v in conflict_graph.adj_set[u]:
            edge = tuple(sorted((u, v)))
            if edge not in seen:
                seen.add(edge)
                edges.append({"source": edge[0], "target": edge[1]})

    return jsonify({
        "total_students": len(students),
        "students": students_data,
        "edges": edges,
        "conflict_edge_count": conflict_graph.edge_count,
    })


@app.route("/api/optimize", methods=["POST"])
def optimize():
    """Runs Branch & Bound search and optional Naive Brute Force baseline."""
    data = request.get_json() or {}
    team_size = int(data.get("team_size", 5))
    min_seniors = int(data.get("min_seniors", 2))
    min_juniors = int(data.get("min_juniors", 1))
    min_skills = int(data.get("min_skills", 3))
    lambda_weight = float(data.get("lambda_weight", 1.5))
    run_naive = bool(data.get("run_naive", True))

    optimizer = TeamFormationOptimizer(
        students=students,
        conflict_graph=conflict_graph,
        team_size=team_size,
        min_seniors=min_seniors,
        min_juniors=min_juniors,
        min_distinct_skills=min_skills,
        variance_penalty_weight=lambda_weight,
    )

    # Branch and Bound with early pruning
    best_bnb, stats_bnb = optimizer.solve_branch_and_bound()

    response: Dict[str, Any] = {
        "success": best_bnb is not None,
        "bnb_stats": {
            "name": stats_bnb.algorithm_name,
            "combinations_space": stats_bnb.total_combinations_space,
            "nodes_visited": stats_bnb.nodes_visited,
            "leaves_evaluated": stats_bnb.leaf_nodes_evaluated,
            "feasible_found": stats_bnb.feasible_solutions_found,
            "time_ms": round(stats_bnb.execution_time_ms, 2),
            "total_pruned": stats_bnb.total_pruned,
            "pruning_breakdown": {
                "capacity": stats_bnb.pruned_capacity,
                "conflict": stats_bnb.pruned_conflict,
                "senior_deficit": stats_bnb.pruned_senior_deficit,
                "junior_deficit": stats_bnb.pruned_junior_deficit,
                "skill_deficit": stats_bnb.pruned_skill_deficit,
                "upper_bound": stats_bnb.pruned_upper_bound,
            },
        },
    }

    if best_bnb:
        response["team"] = {
            "members": [
                {
                    "id": s.id,
                    "name": s.name,
                    "year": s.year,
                    "level": "Senior" if s.is_senior else "Junior",
                    "skill": s.skill.value,
                    "rating": s.rating,
                }
                for s in best_bnb.team
            ],
            "member_ids": [s.id for s in best_bnb.team],
            "total_score": best_bnb.total_score,
            "mean_score": round(best_bnb.mean_score, 2),
            "variance": round(best_bnb.variance, 4),
            "std_dev": round(best_bnb.std_dev, 4),
            "objective_value": round(best_bnb.objective_value, 4),
            "senior_count": best_bnb.senior_count,
            "junior_count": best_bnb.junior_count,
            "unique_skills": [sk.value for sk in best_bnb.skill_coverage],
        }

    # Run Naive baseline if requested
    if run_naive and stats_bnb.total_combinations_space <= 200000:
        best_naive, stats_naive = optimizer.solve_naive_brute_force()
        speedup = (
            stats_naive.execution_time_ms / stats_bnb.execution_time_ms
            if stats_bnb.execution_time_ms > 0
            else 1.0
        )
        node_reduction = (
            (stats_naive.nodes_visited - stats_bnb.nodes_visited)
            / stats_naive.nodes_visited
        ) * 100.0

        response["naive_stats"] = {
            "name": stats_naive.algorithm_name,
            "combinations_space": stats_naive.total_combinations_space,
            "nodes_visited": stats_naive.nodes_visited,
            "leaves_evaluated": stats_naive.leaf_nodes_evaluated,
            "feasible_found": stats_naive.feasible_solutions_found,
            "time_ms": round(stats_naive.execution_time_ms, 2),
            "speedup_factor": round(speedup, 1),
            "node_reduction_pct": round(node_reduction, 2),
        }

    return jsonify(response)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
