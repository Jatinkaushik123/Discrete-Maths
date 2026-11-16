"""
student.py - Core data models and conflict graph representation.

Discrete Mathematics Concepts:
- Entity Set: S = {s_1, s_2, ..., s_N}
- Conflict Graph: Undirected graph G_C = (V, E) where V = S,
  and {u, v} in E denotes mutual incompatibility.
- Feasible Team: An Independent (Stable) Set T subseteq S of cardinality k.
"""

from dataclasses import dataclass
from enum import Enum
from typing import List, Set, Dict


class Skill(str, Enum):
    TECH = "Tech"
    SPONSORSHIP = "Sponsorship"
    DESIGN = "Design"
    LOGISTICS = "Logistics"
    MARKETING = "Marketing"

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class Student:
    id: int
    name: str
    year: int  # 1, 2, 3, or 4
    skill: Skill
    rating: int  # 1 to 5

    @property
    def is_senior(self) -> bool:
        """Senior defined as 3rd or 4th year."""
        return self.year in (3, 4)

    @property
    def is_junior(self) -> bool:
        """Junior defined as 1st or 2nd year."""
        return self.year in (1, 2)

    def __repr__(self) -> str:
        return (
            f"Student(id={self.id}, name='{self.name}', Y{self.year}, "
            f"skill={self.skill.value}, rating={self.rating})"
        )


class ConflictGraph:
    """
    Represents mutual student incompatibilities as an adjacency matrix and
    adjacency set representation for O(1) conflict lookups.
    """

    def __init__(self, size: int):
        self.size = size
        # Adjacency matrix for quick O(1) indexed lookup
        self.matrix: List[List[bool]] = [[False] * size for _ in range(size)]
        # Map of student_id -> set of incompatible student_ids
        self.adj_set: Dict[int, Set[int]] = {i: set() for i in range(size)}
        self.edge_count = 0

    def add_conflict(self, id1: int, id2: int) -> None:
        """Add an undirected edge indicating mutual incompatibility between id1 and id2."""
        if id1 == id2:
            return
        if not self.matrix[id1][id2]:
            self.matrix[id1][id2] = True
            self.matrix[id2][id1] = True
            self.adj_set[id1].add(id2)
            self.adj_set[id2].add(id1)
            self.edge_count += 1

    def are_incompatible(self, id1: int, id2: int) -> bool:
        """Check if id1 and id2 conflict in O(1) time."""
        return self.matrix[id1][id2]

    def has_conflict_with_team(self, candidate_id: int, team_ids: List[int]) -> bool:
        """
        Check if candidate_id conflicts with ANY member already present in the team.
        Operates in O(|team|) time, which is <= k (e.g. <= 5).
        """
        for member_id in team_ids:
            if self.matrix[candidate_id][member_id]:
                return True
        return False
