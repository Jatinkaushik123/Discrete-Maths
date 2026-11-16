"""
main.py - Entry point for the College Fest Team Formation Optimization project.

Usage:
    python main.py
    python main.py --team-size 5 --lambda-weight 1.5 --compare-naive
"""

import sys
import argparse
from dataset import get_default_dataset
from optimizer import TeamFormationOptimizer
from visualizer import (
    print_banner,
    print_student_pool,
    print_search_comparison,
    print_pruning_breakdown,
    print_optimal_team,
    print_discrete_math_insights,
)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Optimizing Team Formation in College Fests using Discrete Mathematics & Combinatorial Search",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "-k", "--team-size", type=int, default=5, help="Team size (cardinality k)"
    )
    parser.add_argument(
        "--min-seniors", type=int, default=2, help="Minimum senior members (Year 3/4)"
    )
    parser.add_argument(
        "--min-juniors", type=int, default=1, help="Minimum junior members (Year 1/2)"
    )
    parser.add_argument(
        "--min-skills", type=int, default=3, help="Minimum distinct primary skills"
    )
    parser.add_argument(
        "-l",
        "--lambda-weight",
        type=float,
        default=1.5,
        help="Variance penalty weight lambda: f(T) = TotalScore - lambda * Variance",
    )
    parser.add_argument(
        "--skip-naive",
        action="store_true",
        help="Skip the naive brute-force baseline comparison (useful for large N)",
    )
    parser.add_argument(
        "--hide-pool", action="store_true", help="Do not print the initial student pool table"
    )
    return parser.parse_args()


def main():
    args = parse_args()
    print_banner()

    # Load synthetic dataset and conflict graph
    students, conflict_graph = get_default_dataset()

    if not args.hide_pool:
        print_student_pool(students, conflict_graph)

    print(
        f"Initializing Optimizer with Constraints:\n"
        f"  • Team Size (k): {args.team_size}\n"
        f"  • Senior Quota (Year 3/4): >= {args.min_seniors}\n"
        f"  • Junior Quota (Year 1/2): >= {args.min_juniors}\n"
        f"  • Distinct Skills: >= {args.min_skills}\n"
        f"  • Variance Penalty (λ): {args.lambda_weight}\n"
    )

    optimizer = TeamFormationOptimizer(
        students=students,
        conflict_graph=conflict_graph,
        team_size=args.team_size,
        min_seniors=args.min_seniors,
        min_juniors=args.min_juniors,
        min_distinct_skills=args.min_skills,
        variance_penalty_weight=args.lambda_weight,
    )

    # 1. Run Constrained Branch-and-Bound with Early Pruning
    print("Running Constrained Branch-and-Bound search with early pruning...")
    best_team_bnb, stats_bnb = optimizer.solve_branch_and_bound()

    # 2. Run Naive Brute Force Baseline (if requested)
    if not args.skip_naive:
        print("Running Naive Brute Force baseline (evaluating all C(N, k) combinations)...")
        best_team_naive, stats_naive = optimizer.solve_naive_brute_force()
        print_search_comparison(stats_naive, stats_bnb)
        # Sanity check: Ensure both algorithms agree on optimal objective value
        if best_team_naive and best_team_bnb:
            assert abs(best_team_naive.objective_value - best_team_bnb.objective_value) < 1e-6, (
                "Mathematical inconsistency: Branch & Bound optimum does not match Brute Force optimum!"
            )

    # 3. Print Taxonomy of Pruned Decision Branches
    print_pruning_breakdown(stats_bnb)

    # 4. Display Selected Optimal Team Profile & Verification
    print_optimal_team(best_team_bnb, args.lambda_weight)

    # 5. Theoretical Pedagogical Breakdown
    print_discrete_math_insights()


if __name__ == "__main__":
    main()
