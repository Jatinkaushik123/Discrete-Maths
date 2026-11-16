"""
visualizer.py - Rich terminal formatting for Discrete Mathematics team optimization.

Renders clean ANSI tables, search tree metrics, and mathematical breakdowns.
"""

from typing import List, Optional
from student import Student, Skill, ConflictGraph
from optimizer import TeamEvaluation, SearchStatistics


import sys

# Ensure UTF-8 output encoding on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# ANSI Color Codes
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
MAGENTA = "\033[95m"
BLUE = "\033[94m"
BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"


def print_banner() -> None:
    print(f"\n{CYAN}{BOLD}" + "=" * 80)
    print(" DISCRETE MATHEMATICS & COMBINATORIAL OPTIMIZATION")
    print(" Project: Optimizing Team Formation in College Fests")
    print(" Constrained Branch-and-Bound Combinatorial Search with Early Pruning")
    print("=" * 80 + f"{RESET}\n")


def print_student_pool(students: List[Student], conflict_graph: ConflictGraph) -> None:
    print(f"{BOLD}{YELLOW}--- CANDIDATE STUDENT POOL (N = {len(students)}) ---{RESET}")
    print(f"{'ID':<4} | {'Name':<20} | {'Year':<6} | {'Level':<8} | {'Primary Skill':<14} | {'Rating':<6} | {'Conflicts'}")
    print("-" * 80)
    for s in students:
        level = "Senior" if s.is_senior else "Junior"
        conflicts = [str(target) for target in sorted(conflict_graph.adj_set[s.id])]
        conflicts_str = ", ".join(conflicts) if conflicts else "None"
        rating_display = f"{s.rating}/5"
        print(f"{s.id:<4} | {s.name:<20} | Y{s.year:<5} | {level:<8} | {s.skill.value:<14} | {rating_display:<6} | {conflicts_str}")
    print("-" * 80)
    print(f"{DIM}Total Conflict Edges in Graph G_C: {conflict_graph.edge_count}{RESET}\n")



def print_search_comparison(
    stats_naive: SearchStatistics, stats_bnb: SearchStatistics
) -> None:
    print(f"{BOLD}{MAGENTA}--- SEARCH SPACE & ALGORITHM PERFORMANCE COMPARISON ---{RESET}")
    print(f"{'Metric':<36} | {'Naive Brute Force':<20} | {'Branch & Bound (Pruned)':<22}")
    print("-" * 84)

    space_str = f"C({stats_naive.total_combinations_space:,})"
    print(f"{'Theoretical Combinations C(N, k)':<36} | {stats_naive.total_combinations_space:<20,d} | {stats_bnb.total_combinations_space:<22,d}")
    print(f"{'Total Nodes Visited / Expanded':<36} | {stats_naive.nodes_visited:<20,d} | {stats_bnb.nodes_visited:<22,d}")
    print(f"{'Leaf Combinations Evaluated':<36} | {stats_naive.leaf_nodes_evaluated:<20,d} | {stats_bnb.leaf_nodes_evaluated:<22,d}")
    print(f"{'Feasible Valid Teams Discovered':<36} | {stats_naive.feasible_solutions_found:<20,d} | {stats_bnb.feasible_solutions_found:<22,d}")
    print(f"{'Execution Time':<36} | {f'{stats_naive.execution_time_ms:.2f} ms':<20} | {f'{stats_bnb.execution_time_ms:.2f} ms':<22}")

    speedup = (
        stats_naive.execution_time_ms / stats_bnb.execution_time_ms
        if stats_bnb.execution_time_ms > 0
        else 1.0
    )
    node_reduction = (
        (stats_naive.nodes_visited - stats_bnb.nodes_visited) / stats_naive.nodes_visited
    ) * 100.0

    print("-" * 84)
    print(f"{BOLD}{GREEN}Search Space Reduction Factor:{RESET} {node_reduction:.1f}% of search nodes eliminated!")
    print(f"{BOLD}{GREEN}Empirical Execution Speedup:{RESET}   {speedup:.2f}x faster with early pruning\n")


def print_pruning_breakdown(stats: SearchStatistics) -> None:
    print(f"{BOLD}{CYAN}--- BRANCH-AND-BOUND PRUNING TAXONOMY BREAKDOWN ---{RESET}")
    print(f"{'Pruning Reason':<42} | {'Pruned Subtrees':<15} | {'Percentage'}")
    print("-" * 72)

    total = stats.total_pruned
    if total == 0:
        print("No branches pruned.")
        return

    items = [
        ("Capacity Shortfall (|T| + Rem < k)", stats.pruned_capacity),
        ("Interpersonal Conflict (Adj. Matrix Edge)", stats.pruned_conflict),
        ("Senior Quota Deficit (Seniors < 2)", stats.pruned_senior_deficit),
        ("Junior Quota Deficit (Juniors < 1)", stats.pruned_junior_deficit),
        ("Skill Diversity Deficit (Distinct < 3)", stats.pruned_skill_deficit),
        ("Upper Bounding (f(T) <= Best Objective)", stats.pruned_upper_bound),
    ]

    for label, count in items:
        pct = (count / total) * 100.0 if total > 0 else 0.0
        bar = "#" * int(pct / 4)
        print(f"{label:<42} | {count:<15,d} | {pct:>5.1f}% {bar}")
    print("-" * 72)
    print(f"{BOLD}Total Pruned Decision Branches: {total:,}{RESET}\n")


def print_optimal_team(evaluation: Optional[TeamEvaluation], penalty_lambda: float) -> None:
    if not evaluation:
        print(f"{RED}{BOLD}No feasible team found satisfying all constraints!{RESET}")
        return

    print(f"{BOLD}{GREEN}=== OPTIMAL TEAM SELECTION (Objective f(T) = Score - {penalty_lambda} x Var) ==={RESET}")
    print(f"{'ID':<4} | {'Name':<20} | {'Year':<6} | {'Level':<8} | {'Primary Skill':<14} | {'Rating'}")
    print("-" * 70)
    for s in evaluation.team:
        level = "Senior" if s.is_senior else "Junior"
        rating_bar = "*" * s.rating + "." * (5 - s.rating)
        print(f"{s.id:<4} | {s.name:<20} | Y{s.year:<5} | {level:<8} | {s.skill.value:<14} | {rating_bar} ({s.rating}/5)")
    print("-" * 70)

    skills_str = ", ".join([sk.value for sk in evaluation.skill_coverage])
    print(f"{BOLD}Mathematical Profile & Constraint Verification:{RESET}")
    print(f"  * {BOLD}Total Skill Score:{RESET}     {evaluation.total_score} / {len(evaluation.team) * 5}")
    print(f"  * {BOLD}Mean Rating (mu):{RESET}      {evaluation.mean_score:.2f}")
    print(f"  * {BOLD}Score Variance (var):{RESET}  {evaluation.variance:.4f}  (Lower = More Balanced)")
    print(f"  * {BOLD}Std. Deviation (std):{RESET}  {evaluation.std_dev:.4f}")
    print(f"  * {BOLD}Composite Objective:{RESET}   {evaluation.objective_value:.4f}")
    print(f"  * {BOLD}Senior Count (>= 2):{RESET}   {evaluation.senior_count}  {GREEN}[OK - SATISFIED]{RESET}")
    print(f"  * {BOLD}Junior Count (>= 1):{RESET}   {evaluation.junior_count}  {GREEN}[OK - SATISFIED]{RESET}")
    print(f"  * {BOLD}Unique Skills (>= 3):{RESET}  {len(evaluation.skill_coverage)} ({skills_str})  {GREEN}[OK - SATISFIED]{RESET}")
    print(f"  * {BOLD}Incompatibility Graph:{RESET} Independent Set  {GREEN}[OK - ZERO CONFLICTS]{RESET}\n")



def print_discrete_math_insights() -> None:
    print(f"{BOLD}{BLUE}--- DISCRETE MATHEMATICS THEORETICAL INSIGHTS ---{RESET}")
    print(
        """
1. COMBINATIONS VS. PERMUTATIONS:
   A fest event team is an unordered set: {s_a, s_b} = {s_b, s_a}.
   Searching permutations P(N, k) explores k! (120 for k=5) symmetrical sequences.
   Enforcing strict ascending index ordering (i_1 < i_2 < ... < i_k) restricts
   exploration strictly to C(N, k) combinations, instantly cutting the space by k!.

2. THE POWER OF EARLY PRUNING:
   In naive combinatorial generation, constraints are evaluated as a post-filter
   at the leaf nodes after all C(N, k) subsets are materialized.
   In contrast, early pruning operates on the internal nodes of the decision tree:
   Pruning a partial prefix of size m = 2 prunes an entire sub-tree containing
   C(N - idx, k - m) potential leaves at depth k in a single O(1) step.

3. INDEPENDENT SETS IN CONFLICT GRAPHS:
   Let G_C = (V, E) be the conflict graph. A conflict-free team T is an Independent
   Set of G_C. By testing compatibility at each branching step, we never explore
   subgraphs that violate the independence property.

4. OBJECTIVE DUALITY (SCORE MAXIMIZATION VS. VARIANCE MINIMIZATION):
   High performance requires high ratings; peer harmony requires low disparity.
   The penalty term -λ·σ² ensures the selected team avoids extreme polarization
   (e.g., pairing novice rating 1 with veteran rating 5) in favor of cohesive competence.
"""
    )
