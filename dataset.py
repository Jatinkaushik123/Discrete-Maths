"""
dataset.py - Generates realistic synthetic student pool and conflict matrix.

Discrete Mathematics Context:
- Universe size N = 26 students
- Diverse representation across Year in {1, 2, 3, 4}
- Skill coverage across {Tech, Sponsorship, Design, Logistics, Marketing}
- Ratings from 1 (Novice) to 5 (Expert)
- Explicit conflict graph edges representing incompatible student pairs.
"""

from typing import List, Tuple
from student import Student, Skill, ConflictGraph


def get_default_dataset() -> Tuple[List[Student], ConflictGraph]:
    """
    Returns a curated dataset of 26 students with realistic academic attributes
    and a conflict graph with known incompatible pairs.
    """
    students: List[Student] = [
        Student(id=0,  name="Jatin Kaushik",    year=4, skill=Skill.TECH,        rating=5),
        Student(id=1,  name="Viraj Singh",       year=3, skill=Skill.DESIGN,      rating=5),
        Student(id=2,  name="Rohan Verma",      year=4, skill=Skill.LOGISTICS,   rating=4),
        Student(id=3,  name="Ananya Iyer",      year=2, skill=Skill.SPONSORSHIP, rating=4),
        Student(id=4,  name="Kabir Mehta",      year=1, skill=Skill.TECH,        rating=4),
        Student(id=5,  name="Ishita Roy",       year=3, skill=Skill.MARKETING,   rating=5),
        Student(id=6,  name="Vikram Singh",     year=4, skill=Skill.SPONSORSHIP, rating=3),
        Student(id=7,  name="Sneha Kulkarni",   year=2, skill=Skill.DESIGN,      rating=3),
        Student(id=8,  name="Aditya Nair",      year=1, skill=Skill.LOGISTICS,   rating=3),
        Student(id=9,  name="Pooja Rao",        year=3, skill=Skill.TECH,        rating=4),
        Student(id=10, name="Karan Malhotra",   year=2, skill=Skill.MARKETING,   rating=4),
        Student(id=11, name="Tanvi Deshmukh",   year=4, skill=Skill.DESIGN,      rating=4),
        Student(id=12, name="Siddharth Gupta",  year=1, skill=Skill.SPONSORSHIP, rating=2),
        Student(id=13, name="Meera Nambiar",    year=3, skill=Skill.LOGISTICS,   rating=5),
        Student(id=14, name="Varun Joshi",      year=2, skill=Skill.TECH,        rating=3),
        Student(id=15, name="Rhea Sen",         year=4, skill=Skill.MARKETING,   rating=3),
        Student(id=16, name="Devansh Kapoor",   year=1, skill=Skill.DESIGN,      rating=4),
        Student(id=17, name="Natasha Bhat",     year=3, skill=Skill.SPONSORSHIP, rating=5),
        Student(id=18, name="Arjun Chawla",     year=2, skill=Skill.LOGISTICS,   rating=2),
        Student(id=19, name="Kriti Saxena",     year=4, skill=Skill.TECH,        rating=4),
        Student(id=20, name="Manish Pandey",    year=1, skill=Skill.MARKETING,   rating=3),
        Student(id=21, name="Priyanka Bose",    year=3, skill=Skill.DESIGN,      rating=3),
        Student(id=22, name="Harsh Aggarwal",   year=4, skill=Skill.SPONSORSHIP, rating=4),
        Student(id=23, name="Simran Kaur",      year=2, skill=Skill.TECH,        rating=5),
        Student(id=24, name="Nikhil Reddy",     year=1, skill=Skill.LOGISTICS,   rating=4),
        Student(id=25, name="Zoya Khan",        year=3, skill=Skill.MARKETING,   rating=4),
    ]

    conflict_graph = ConflictGraph(len(students))

    # Incompatible pairs (disputes, concurrent committee commitments, personal conflicts):
    conflict_pairs = [
        (0, 6),    # Aarav (Tech 5) and Vikram (Sponsorship 3) - lead dispute
        (1, 11),   # Diya (Design 5) and Tanvi (Design 4) - past creative disagreement
        (2, 8),    # Rohan (Logistics 4) and Aditya (Logistics 3)
        (3, 17),   # Ananya (Sponsorship 4) and Natasha (Sponsorship 5)
        (4, 14),   # Kabir (Tech 4) and Varun (Tech 3)
        (5, 10),   # Ishita (Marketing 5) and Karan (Marketing 4)
        (9, 19),   # Pooja (Tech 4) and Kriti (Tech 4)
        (12, 22),  # Siddharth (Sponsorship 2) and Harsh (Sponsorship 4)
        (13, 18),  # Meera (Logistics 5) and Arjun (Logistics 2)
        (16, 21),  # Devansh (Design 4) and Priyanka (Design 3)
        (0, 1),    # Aarav and Diya - scheduling collision
        (5, 15),   # Ishita and Rhea
    ]

    for u, v in conflict_pairs:
        conflict_graph.add_conflict(u, v)

    return students, conflict_graph
