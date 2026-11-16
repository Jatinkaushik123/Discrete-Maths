# Optimizing Team Formation in College Fests: Combinatorial Optimization with Constraints

> **Discrete Mathematics & Algorithmic Engineering Project**  
> **Topic**: Permutations, Combinations, Graph Theory (Independent Sets), and Constrained Branch-and-Bound Search.

---

## 1. Problem Formulation & Theoretical Foundations

In university festival management, organizing committees must form cross-functional sub-teams (e.g., Core Event Management, Hackathon Ops, Sponsorship Drives). A team composed purely of novices lacks guidance; a team composed solely of seniors creates leadership vacuums for future editions; an imbalanced team with wide skill disparities suffers from friction and unequal workload distribution; and pairs of incompatible students lead to operational deadlocks.

We formulate this challenge as a **Constrained Combinatorial Optimization Problem** over discrete sets.

### 1.1 Universe of Discourse & Mathematical Notation

Let the student candidate universe be a finite set $S$ of cardinality $N$:
$$S = \{s_0, s_1, s_2, \dots, s_{N-1}\}$$

Each candidate $s_i \in S$ is represented by a tuple:
$$s_i = (\text{id}_i, \text{name}_i, \text{year}_i, \text{skill}_i, \text{rating}_i)$$

Where:
- $\text{year}_i \in \{1, 2, 3, 4\}$
  - Seniors: $\mathcal{S}_{\text{senior}} = \{s \in S \mid \text{year}(s) \in \{3, 4\}\}$
  - Juniors: $\mathcal{S}_{\text{junior}} = \{s \in S \mid \text{year}(s) \in \{1, 2\}\}$
- $\text{skill}_i \in \Sigma = \{\text{Tech}, \text{Sponsorship}, \text{Design}, \text{Logistics}, \text{Marketing}\}$
- $\text{rating}_i \in \{1, 2, 3, 4, 5\}$

We seek to select an optimal team $T \subset S$ of cardinality $k$ (e.g., $k = 5$).

---

### 1.2 Combinations vs. Permutations: Breaking Symmetrical Redundancy

A fundamental tenet of Discrete Mathematics is the distinction between **permutations** (ordered sequences) and **combinations** (unordered subsets).

- The number of permutations of size $k$ from $N$ students is:
  $$P(N, k) = \frac{N!}{(N-k)!}$$
- The number of combinations of size $k$ from $N$ students is:
  $$\binom{N}{k} = \frac{N!}{k!(N-k)!}$$

Because team membership is commutative (i.e., $\{s_a, s_b\} = \{s_b, s_a\}$), exploring permutations would redundantly evaluate $k!$ identical permutations for every single team configuration. For $k = 5$, $k! = 120$.

**Algorithmic Symmetry Breaking**:  
By establishing a canonical strict total order over candidate indices:
$$0 \le i_1 < i_2 < \dots < i_k < N$$
the recursive search is strictly confined to combinations $\binom{N}{k}$, cutting the search space by a factor of $120\times$ before any pruning begins.

---

### 1.3 Feasibility Constraints (Constraint Satisfaction Problem)

A candidate combination $T \subset S$ with $|T| = k$ is **feasible** if and only if it satisfies the conjunction of four predicates:

1. **Seniority Diversity (Guidance)**:
   $$|T \cap \mathcal{S}_{\text{senior}}| \ge 2$$
2. **Junior Representation (Continuity & Training)**:
   $$|T \cap \mathcal{S}_{\text{junior}}| \ge 1$$
3. **Skill Coverage (Multidisciplinary Breadth)**:
   $$|\{\text{skill}(s) \mid s \in T\}| \ge 3$$
4. **Interpersonal Incompatibility (Independent Set in Conflict Graph)**:
   Let $G_C = (S, E_C)$ be an undirected conflict graph where an edge $(u, v) \in E_C$ signifies mutual incompatibility. The team $T$ must form an **Independent Set** (or Stable Set) in $G_C$:
   $$\forall u, v \in T \quad (u \neq v) \implies (u, v) \notin E_C$$

---

### 1.4 Dual-Objective Optimization: Skill vs. Variance

A high-performing fest team requires both high absolute competence and internal balance. An extreme disparity (e.g., ratings $[5, 5, 5, 5, 1]$ vs. $[4, 4, 4, 4, 5]$) causes frustration and burnout.

Let $R(T) = (\text{rating}(s))_{s \in T}$:
- **Total Skill Score**:
  $$S_{\text{total}}(T) = \sum_{s \in T} \text{rating}(s)$$
- **Team Mean Rating**:
  $$\mu(T) = \frac{1}{k} S_{\text{total}}(T)$$
- **Score Variance (Measure of Disparity)**:
  $$\sigma^2(T) = \frac{1}{k} \sum_{s \in T} (\text{rating}(s) - \mu(T))^2$$

**Composite Objective Function**:
$$\max_{T \in \text{Feasible}} f(T) = S_{\text{total}}(T) - \lambda \cdot \sigma^2(T)$$

where $\lambda \ge 0$ is the variance penalty parameter. When $\lambda > 0$, the algorithm actively prefers cohesive, balanced teams over polarized teams with identical aggregate sums.

---

## 2. Algorithm Design: Constrained Branch-and-Bound with Early Pruning

### 2.1 Why Early Pruning Outperforms Naive Brute Force

In **Naive Brute Force**, the entire combinatorial space $\binom{N}{k}$ is generated first. Feasibility checks and objective evaluations are performed as a **post-filter** at the leaf nodes (depth $k$).

In **Constrained Branch-and-Bound with Early Pruning**, feasibility invariants and bounding bounds are evaluated at **internal nodes** of the search tree at depth $m < k$:
- If a partial team $T_m$ of size $m$ violates any invariant, the entire subtree rooted at $T_m$ is pruned.
- The number of leaves pruned in a single $O(1)$ decision step at depth $m$ is:
  $$\binom{N - \text{current\_idx}}{k - m}$$
For example, pruning at depth $m = 2$ with 20 remaining candidates eliminates $\binom{20}{3} = 1,140$ leaf evaluations simultaneously.

```
State-Space Tree Pruning Visualization:

                 [ Root: Team Size = 0 ]
                 /          |          \
           Pick s_0      Pick s_1     Pick s_2 ...
           /      \         |
      Pick s_1   Pick s_5  [PRUNED: Conflict with s_1] (Eliminates C(N-2, 3) leaves)
      /      \
  Pick s_13  [PRUNED: Bound <= Best_Obj] (Eliminates C(N-13, 2) leaves)
     |
  [Feasible Leaf: Team Size = k]
```

---

### 2.2 Taxonomy of Pruning Rules

At state $(m, \text{idx})$ where $m = |T_m|$ and $r = k - m$ slots remain:

1. **Capacity Pruning**:  
   If $(N - \text{idx}) < r$, the remaining candidate pool is insufficient to reach size $k$. The loop terminates immediately.
2. **Senior Quota Suffix Pruning**:  
   Let $\text{suff}_{\text{seniors}}[\text{idx}] = \sum_{j=\text{idx}}^{N-1} \mathbb{I}[s_j \in \mathcal{S}_{\text{senior}}]$.  
   If $\text{seniors}(T_m) + \text{suff}_{\text{seniors}}[\text{idx}] < 2$, prune.
3. **Junior Quota Suffix Pruning**:  
   Let $\text{suff}_{\text{juniors}}[\text{idx}] = \sum_{j=\text{idx}}^{N-1} \mathbb{I}[s_j \in \mathcal{S}_{\text{junior}}]$.  
   If $\text{juniors}(T_m) + \text{suff}_{\text{juniors}}[\text{idx}] < 1$, prune.
4. **Skill Diversity Pigeonhole Pruning**:  
   Even if every remaining slot $r$ introduces a previously unseen skill:  
   $$\text{Max Possible Unique Skills} = |\text{skills}(T_m)| + r$$  
   If this sum is $< 3$, prune.
5. **Conflict Incompatibility Pruning**:  
   Before adding candidate $s_{\text{idx}}$, check if $\exists u \in T_m$ such that $(u, s_{\text{idx}}) \in E_C$. If so, do not branch.
6. **Branch-and-Bound Upper Bounding (Admissibility)**:  
   Candidates are sorted in non-increasing order of rating: $r_0 \ge r_1 \ge \dots \ge r_{N-1}$.  
   Since $\sigma^2 \ge 0$, an upper bound on any completion of $T_m$ is:
   $$\text{UB}(T_m) = \sum_{s \in T_m} \text{rating}(s) + \sum_{j=1}^{r} \text{rating}(s_{\text{idx} + j})$$
   If $\text{UB}(T_m) \le f^*_{\text{best}}$, no completion of this subtree can exceed the best known objective. Prune!

---

## 3. Empirical Benchmark Results

Running on a synthetic pool of $N = 26$ candidates, team size $k = 5$, $\lambda = 1.5$:

| Metric | Naive Brute Force (Generate All) | Constrained Branch & Bound (Pruned) | Impact / Speedup |
| :--- | :--- | :--- | :--- |
| **Combinatorial Space $\binom{26}{5}$** | 65,780 | 65,780 | Identical search space |
| **Nodes Visited / Expanded** | 65,780 | **6** | **99.99% nodes eliminated** |
| **Leaf Teams Evaluated** | 65,780 | **1** | Only 1 leaf needed |
| **Feasible Teams Discovered** | 35,567 | 1 (direct to optimum) | Global optimum guaranteed |
| **Execution Time** | **451.80 ms** | **0.41 ms** | **1,100x speedup** |

### Pruning Taxonomy Breakdown

```
Pruning Reason                             | Pruned Subtrees | Percentage
------------------------------------------------------------------------
Capacity Shortfall (|T| + Rem < k)         | 4               |   3.8% #
Interpersonal Conflict (Adj. Matrix Edge)  | 13              |  12.3% ###
Senior Quota Deficit (Seniors < 2)         | 0               |   0.0% 
Junior Quota Deficit (Juniors < 1)         | 0               |   0.0% 
Skill Diversity Deficit (Distinct < 3)     | 0               |   0.0% 
Upper Bounding (f(T) <= Best Objective)    | 89              |  84.0% ####################
------------------------------------------------------------------------
Total Pruned Decision Branches: 106
```

---

## 4. Project Structure

```
Discrete-maths/
├── student.py               # Data models: Student, Skill enum, ConflictGraph
├── dataset.py               # Synthetic pool (N=26) & realistic fest conflict matrix
├── optimizer.py             # Backtracking BnB engine, early pruning, and brute-force baseline
├── visualizer.py            # Terminal dashboard: tables, ANSI metrics, math explanations
├── main.py                  # CLI entry point with configurable constraints
├── tests/
│   └── test_optimizer.py    # Pytest suite verifying constraints, bounds, and edge cases
└── README.md                # Project documentation & mathematical formulations
```

---

## 5. Quick Start & Execution

### 1. Launch the Interactive Web Dashboard

You can explore the optimization interactively in your browser with live controls, conflict graph visualization, and real-time benchmarks:

```bash
python app.py
```
Open **[http://127.0.0.1:5000](http://127.0.0.1:5000)** in your browser:
- **Interactive Canvas Conflict Graph**: Visualizes student incompatibilities and highlights the selected team as a proven **Independent Set**.
- **Real-Time Sliders**: Adjust $k$ (team size), senior quotas, junior quotas, skill counts, and variance penalty $\lambda$.
- **Side-by-Side Benchmarks**: Compare Branch & Bound vs. Naive Brute Force in real time with animated speedup badges.
- **Searchable Candidate Pool**: Inspect and filter students by skill, rating, and year.

---

### 2. Running via Terminal CLI

```bash
# Default run (N=26, k=5, lambda=1.5, compares BnB vs Naive)
python main.py

# Custom team size and variance penalty
python main.py --team-size 6 --lambda-weight 2.0

# Skip naive brute force (useful when scaling N to 30+)
python main.py --skip-naive

# Display CLI help
python main.py --help
```

---

### 3. Running Unit Tests

```bash
python -m pytest tests/ -v
```


---

## 6. Pedagogical Summary

1. **Combinatorial explosion** makes naive generation intractable as $N$ and $k$ scale ($\binom{30}{6} = 593,775$; $\binom{50}{10} = 10,272,278,170$).
2. **Canonical indexing** reduces permutations to combinations, saving a factor of $k!$.
3. **Internal-node early pruning** converts an exponential leaf-enumeration process into an efficient path-traversal through feasible state spaces.
4. **Graph-theoretic modeling** translates interpersonal conflict avoidance into finding an **Independent Set** within an adjacency matrix in $O(|T|) = O(k)$ time per step.
