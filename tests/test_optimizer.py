"""
tests/test_optimizer.py - Comprehensive unit tests for discrete math team formation.

Verifies:
1. Combinatorial correctness and optimality guarantee
2. Seniority and junior quota enforcement
3. Skill diversity constraint verification
4. Conflict graph independence (no two selected students share an edge)
5. Variance penalty balancing behavior
6. Infeasible constraint handling
"""

import math
import pytest
from student import Student, Skill, ConflictGraph
from dataset import get_default_dataset
from optimizer import TeamFormationOptimizer


def test_combinatorial_counts():
    students, conflict_graph = get_default_dataset()
    n = len(students)
    k = 5
    expected_combinations = math.comb(n, k)
    assert expected_combinations == 65780


def test_bnb_matches_brute_force_optimality():
    """Branch & bound must find the exact same global optimum as exhaustive search."""
    students, conflict_graph = get_default_dataset()
    optimizer = TeamFormationOptimizer(
        students=students,
        conflict_graph=conflict_graph,
        team_size=5,
        min_seniors=2,
        min_juniors=1,
        min_distinct_skills=3,
        variance_penalty_weight=1.5,
    )
    best_bnb, stats_bnb = optimizer.solve_branch_and_bound()
    best_naive, stats_naive = optimizer.solve_naive_brute_force()

    assert best_bnb is not None
    assert best_naive is not None
    assert abs(best_bnb.objective_value - best_naive.objective_value) < 1e-6
    assert best_bnb.total_score == best_naive.total_score


def test_constraints_satisfied_on_default_dataset():
    students, conflict_graph = get_default_dataset()
    optimizer = TeamFormationOptimizer(
        students=students,
        conflict_graph=conflict_graph,
        team_size=5,
        min_seniors=2,
        min_juniors=1,
        min_distinct_skills=3,
        variance_penalty_weight=1.5,
    )
    best_team, stats = optimizer.solve_branch_and_bound()
    assert best_team is not None

    team = best_team.team
    assert len(team) == 5

    # 1. Senior constraint (at least 2)
    seniors = [s for s in team if s.is_senior]
    assert len(seniors) >= 2

    # 2. Junior constraint (at least 1)
    juniors = [s for s in team if s.is_junior]
    assert len(juniors) >= 1

    # 3. Distinct skills (at least 3)
    skills = {s.skill for s in team}
    assert len(skills) >= 3

    # 4. Conflict-free (Independent Set)
    for i in range(len(team)):
        for j in range(i + 1, len(team)):
            assert not conflict_graph.are_incompatible(team[i].id, team[j].id)


def test_variance_penalty_promotes_balance():
    """
    Given candidates where Team A has ratings [5, 5, 5, 5, 1] (sum 21, mean 4.2, var 2.56)
    and Team B has ratings [4, 4, 4, 4, 5] (sum 21, mean 4.2, var 0.16),
    with lambda=2.0:
      Obj(A) = 21 - 2*2.56 = 15.88
      Obj(B) = 21 - 2*0.16 = 20.68
    Team B should be selected due to superior balance.
    """
    students = [
        Student(0, "A1", 4, Skill.TECH, 5),
        Student(1, "A2", 3, Skill.DESIGN, 5),
        Student(2, "A3", 4, Skill.SPONSORSHIP, 5),
        Student(3, "A4", 3, Skill.LOGISTICS, 5),
        Student(4, "A5", 1, Skill.MARKETING, 1),  # Highly unbalanced novice
        Student(5, "B1", 4, Skill.TECH, 4),
        Student(6, "B2", 3, Skill.DESIGN, 4),
        Student(7, "B3", 4, Skill.SPONSORSHIP, 4),
        Student(8, "B4", 3, Skill.LOGISTICS, 4),
        Student(9, "B5", 1, Skill.MARKETING, 5),  # Well-balanced
    ]

    cg = ConflictGraph(10)
    # Force separation: cross-conflicts between team A and team B members
    for a in range(5):
        for b in range(5, 10):
            cg.add_conflict(a, b)

    optimizer = TeamFormationOptimizer(
        students=students,
        conflict_graph=cg,
        team_size=5,
        min_seniors=2,
        min_juniors=1,
        min_distinct_skills=3,
        variance_penalty_weight=2.0,
    )

    best_team, _ = optimizer.solve_branch_and_bound()
    assert best_team is not None

    selected_ids = {s.id for s in best_team.team}
    # Should choose the balanced group B [5, 6, 7, 8, 9]
    assert selected_ids == {5, 6, 7, 8, 9}
    assert best_team.variance < 0.2


def test_infeasible_constraints_graceful_exit():
    """If constraints cannot be satisfied, optimizer returns None without error."""
    students = [
        Student(0, "S1", 1, Skill.TECH, 4),
        Student(1, "S2", 1, Skill.TECH, 4),
        Student(2, "S3", 1, Skill.TECH, 4),
    ]
    cg = ConflictGraph(3)
    # Impossible: requires 2 seniors when all 3 are 1st year juniors
    optimizer = TeamFormationOptimizer(
        students=students,
        conflict_graph=cg,
        team_size=3,
        min_seniors=2,
        min_juniors=1,
        min_distinct_skills=1,
    )
    best_team, stats = optimizer.solve_branch_and_bound()
    assert best_team is None
    assert stats.feasible_solutions_found == 0
