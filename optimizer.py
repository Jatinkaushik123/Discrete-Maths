"""
optimizer.py - Constrained combinatorial search and branch-and-bound optimization.

Discrete Mathematics Core:
- Combinations: Selecting unordered k-subsets from N candidates.
- Search Space Size: C(N, k) = N! / (k!(N-k)!).
- State Space Tree: Nodes represent partial teams; branches represent candidate additions.
- Constraints: Multi-predicate filter (seniority, junior quota, skill diversity, graph independence).
- Objective: Maximize total rating while minimizing rating variance.
"""

import time
import math
import itertools
from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Dict, Set
from student import Student, Skill, ConflictGraph


@dataclass
class TeamEvaluation:
    team: List[Student]
    total_score: int
    mean_score: float
    variance: float
    std_dev: float
    objective_value: float
    skill_coverage: Set[Skill]
    senior_count: int
    junior_count: int

    def __repr__(self) -> str:
        names = [s.name for s in self.team]
        return (
            f"TeamEvaluation(score={self.total_score}, var={self.variance:.3f}, "
            f"obj={self.objective_value:.3f}, members={names})"
        )


@dataclass
class SearchStatistics:
    algorithm_name: str
    total_combinations_space: int = 0
    nodes_visited: int = 0
    leaf_nodes_evaluated: int = 0
    feasible_solutions_found: int = 0
    pruned_capacity: int = 0
    pruned_conflict: int = 0
    pruned_senior_deficit: int = 0
    pruned_junior_deficit: int = 0
    pruned_skill_deficit: int = 0
    pruned_upper_bound: int = 0
    execution_time_ms: float = 0.0

    @property
    def total_pruned(self) -> int:
        return (
            self.pruned_capacity
            + self.pruned_conflict
            + self.pruned_senior_deficit
            + self.pruned_junior_deficit
            + self.pruned_skill_deficit
            + self.pruned_upper_bound
        )


class TeamFormationOptimizer:
    """
    Branch-and-Bound Combinatorial Optimizer for constrained event team formation.
    """

    def __init__(
        self,
        students: List[Student],
        conflict_graph: ConflictGraph,
        team_size: int = 5,
        min_seniors: int = 2,
        min_juniors: int = 1,
        min_distinct_skills: int = 3,
        variance_penalty_weight: float = 1.0,
    ):
        self.students = sorted(students, key=lambda s: s.rating, reverse=True)
        # Re-assign IDs based on sorted order for convenient prefix/suffix indexing
        self.n = len(self.students)
        self.k = team_size
        self.min_seniors = min_seniors
        self.min_juniors = min_juniors
        self.min_distinct_skills = min_distinct_skills
        self.variance_lambda = variance_penalty_weight

        # Re-map conflict graph to sorted student indices
        self.conflict_graph = ConflictGraph(self.n)
        for i in range(self.n):
            for j in range(i + 1, self.n):
                orig_id_i = self.students[i].id
                orig_id_j = self.students[j].id
                if conflict_graph.are_incompatible(orig_id_i, orig_id_j):
                    self.conflict_graph.add_conflict(i, j)

        # Precompute suffix lookups for O(1) pruning decisions
        self._precompute_lookups()

    def _precompute_lookups(self) -> None:
        """
        Precomputes cumulative suffix counts for seniors and juniors.
        suffix_seniors[i] = total seniors available from index i to N-1.
        suffix_juniors[i] = total juniors available from index i to N-1.
        """
        self.suffix_seniors = [0] * (self.n + 1)
        self.suffix_juniors = [0] * (self.n + 1)
        for i in range(self.n - 1, -1, -1):
            self.suffix_seniors[i] = self.suffix_seniors[i + 1] + (
                1 if self.students[i].is_senior else 0
            )
            self.suffix_juniors[i] = self.suffix_juniors[i + 1] + (
                1 if self.students[i].is_junior else 0
            )

        # Precompute maximum possible sum of any m students from remaining candidates
        # Since students are sorted in descending order of rating:
        self.ratings = [s.rating for s in self.students]

    def evaluate_team(self, team: List[Student]) -> TeamEvaluation:
        """Computes statistical metrics and objective score for a complete team."""
        total_score = sum(s.rating for s in team)
        mean_score = total_score / self.k
        variance = sum((s.rating - mean_score) ** 2 for s in team) / self.k
        std_dev = math.sqrt(variance)
        objective_value = total_score - (self.variance_lambda * variance)
        skill_coverage = {s.skill for s in team}
        senior_count = sum(1 for s in team if s.is_senior)
        junior_count = sum(1 for s in team if s.is_junior)

        return TeamEvaluation(
            team=team,
            total_score=total_score,
            mean_score=mean_score,
            variance=variance,
            std_dev=std_dev,
            objective_value=objective_value,
            skill_coverage=skill_coverage,
            senior_count=senior_count,
            junior_count=junior_count,
        )

    def is_valid_team(self, team_indices: List[int]) -> bool:
        """Ground-truth predicate for constraint satisfaction verification."""
        if len(team_indices) != self.k:
            return False

        team = [self.students[i] for i in team_indices]

        # 1. Seniority constraint
        seniors = sum(1 for s in team if s.is_senior)
        if seniors < self.min_seniors:
            return False

        # 2. Junior constraint
        juniors = sum(1 for s in team if s.is_junior)
        if juniors < self.min_juniors:
            return False

        # 3. Skill diversity constraint
        skills = {s.skill for s in team}
        if len(skills) < self.min_distinct_skills:
            return False

        # 4. Conflict-free (Independent Set)
        for i in range(len(team_indices)):
            for j in range(i + 1, len(team_indices)):
                if self.conflict_graph.are_incompatible(team_indices[i], team_indices[j]):
                    return False

        return True

    def solve_branch_and_bound(self) -> Tuple[Optional[TeamEvaluation], SearchStatistics]:
        """
        Executes Constrained Backtracking / Branch-and-Bound combinatorial search with
        rigorous early pruning.
        """
        stats = SearchStatistics(algorithm_name="Constrained Branch & Bound with Early Pruning")
        stats.total_combinations_space = math.comb(self.n, self.k)

        best_team: Optional[TeamEvaluation] = None
        best_objective: float = -float("inf")

        start_time = time.perf_counter()

        def backtrack(
            start_idx: int,
            current_team_indices: List[int],
            current_sum: int,
            current_seniors: int,
            current_juniors: int,
            current_skills: Set[Skill],
        ) -> None:
            nonlocal best_team, best_objective

            stats.nodes_visited += 1
            m = len(current_team_indices)
            remaining_needed = self.k - m

            # Base Case: Team of size k reached
            if remaining_needed == 0:
                stats.leaf_nodes_evaluated += 1
                stats.feasible_solutions_found += 1
                team = [self.students[idx] for idx in current_team_indices]
                eval_result = self.evaluate_team(team)
                if eval_result.objective_value > best_objective:
                    best_objective = eval_result.objective_value
                    best_team = eval_result
                return

            # Branch Exploration over remaining candidates
            for idx in range(start_idx, self.n):
                # PRUNING RULE 1: Capacity shortfall
                # If available students from idx to n-1 cannot fill remaining_needed slots
                available_students = self.n - idx
                if available_students < remaining_needed:
                    stats.pruned_capacity += 1
                    break  # All subsequent indices will also fail capacity

                # PRUNING RULE 2: Senior quota viability
                # Can remaining pool provide enough seniors?
                if current_seniors + self.suffix_seniors[idx] < self.min_seniors:
                    stats.pruned_senior_deficit += 1
                    break  # Suffix counts are monotonically non-increasing

                # PRUNING RULE 3: Junior quota viability
                # Can remaining pool provide enough juniors?
                if current_juniors + self.suffix_juniors[idx] < self.min_juniors:
                    stats.pruned_junior_deficit += 1
                    break  # Suffix counts are monotonically non-increasing

                candidate = self.students[idx]

                # PRUNING RULE 4: Skill diversity upper bound
                # Even if every remaining candidate adds a distinct skill, can we reach threshold?
                unique_skills_with_candidate = (
                    len(current_skills) + (0 if candidate.skill in current_skills else 1)
                )
                if unique_skills_with_candidate + (remaining_needed - 1) < self.min_distinct_skills:
                    stats.pruned_skill_deficit += 1
                    continue

                # PRUNING RULE 5: Interpersonal conflict (Graph Independence check)
                if self.conflict_graph.has_conflict_with_team(idx, current_team_indices):
                    stats.pruned_conflict += 1
                    continue

                # PRUNING RULE 6: Upper Bounding (Branch-and-Bound Admissibility)
                # Max additional score possible is picking the top remaining_needed ratings available
                # Since ratings are sorted descending, best possible sum from idx is sum(ratings[idx : idx + remaining_needed])
                # Since variance >= 0, upper bound on objective = current_sum + candidate.rating + max_future_ratings - 0
                max_future_ratings_sum = sum(self.ratings[idx + 1 : idx + remaining_needed])
                upper_bound_score = current_sum + candidate.rating + max_future_ratings_sum
                if upper_bound_score <= best_objective:
                    stats.pruned_upper_bound += 1
                    continue

                # Recursive Descent into child node
                current_team_indices.append(idx)
                backtrack(
                    start_idx=idx + 1,
                    current_team_indices=current_team_indices,
                    current_sum=current_sum + candidate.rating,
                    current_seniors=current_seniors + (1 if candidate.is_senior else 0),
                    current_juniors=current_juniors + (1 if candidate.is_junior else 0),
                    current_skills=current_skills | {candidate.skill},
                )
                # Backtrack state
                current_team_indices.pop()

        # Launch root search
        backtrack(
            start_idx=0,
            current_team_indices=[],
            current_sum=0,
            current_seniors=0,
            current_juniors=0,
            current_skills=set(),
        )

        stats.execution_time_ms = (time.perf_counter() - start_time) * 1000.0
        return best_team, stats

    def solve_naive_brute_force(self) -> Tuple[Optional[TeamEvaluation], SearchStatistics]:
        """
        Executes Naive Brute Force: generates all C(N, k) combinations without any
        lookahead or pruning, checking all constraints only at the leaf nodes.
        Serves as academic benchmark baseline.
        """
        stats = SearchStatistics(algorithm_name="Naive Brute Force (Generate All C(N, k))")
        stats.total_combinations_space = math.comb(self.n, self.k)

        best_team: Optional[TeamEvaluation] = None
        best_objective: float = -float("inf")

        start_time = time.perf_counter()

        for combo in itertools.combinations(range(self.n), self.k):
            stats.nodes_visited += 1
            stats.leaf_nodes_evaluated += 1

            if not self.is_valid_team(list(combo)):
                continue

            stats.feasible_solutions_found += 1
            team = [self.students[idx] for idx in combo]
            eval_result = self.evaluate_team(team)

            if eval_result.objective_value > best_objective:
                best_objective = eval_result.objective_value
                best_team = eval_result

        stats.execution_time_ms = (time.perf_counter() - start_time) * 1000.0
        return best_team, stats
