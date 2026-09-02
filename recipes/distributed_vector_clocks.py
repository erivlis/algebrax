# %%
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "algebrax",
# ]
# [tool.uv.sources]
# algebrax = { path = ".." }
# ///

# %% [markdown]
# # Distributed Causal Ordering, Lamport Clocks & Vector Clock Join-Semilattices
#
# ## Abstract & Physical Motivation
# In distributed systems without a shared physical clock or centralized coordinator (e.g. peer-to-peer networks,
# Dynamo-style databases, distributed consensus, and collaborative editors), establishing the chronological sequence
# of events is non-trivial due to variable network latency, clock drift, and relativistic frame independence.
#
# In 1978, Leslie Lamport introduced the **Happened-Before Relation** ($\to$), formalizing logical causality:
# 1. If events $a$ and $b$ occur within the same process and $a$ occurs before $b$, then $a \to b$.
# 2. If $a$ is the sending of a message by one process and $b$ is its receipt by another, then $a \to b$.
# 3. If $a \to b$ and $b \to c$, then $a \to c$ (Transitivity).
#
# Two events are **concurrent** ($a \parallel b$) if neither causally precedes the other:
#
# $$a \parallel b \iff (a \not\to b) \land (b \not\to a)$$
#
# While Lamport's scalar logical clock provides a weak monotonic morphism ($a \to b \implies L(a) < L(b)$),
# it cannot detect concurrency because $L(a) < L(b)$ does *not* imply $a \to b$.
#
# To achieve an exact causal isomorphism, Colin Fidge and Friedemann Mattern developed **Vector Clocks**.
# Vector Clocks map distributed causality onto a **Bounded Join-Semilattice** $(\mathbb{N}^k, \le, \vee)$
# and an **Arctic / Max-Plus Semiring** $(\mathbb{N} \cup \{-\infty\}, \max, +)$ over event DAGs.
#
# ---
#
# ## Theoretical Foundations & Algebraic Rigor
#
# ### 1. The Vector Clock Join-Semilattice $(\mathbb{N}^k, \le, \vee)$
# Let $\mathcal{P} = \{P_1, P_2, \dots, P_k\}$ be a set of $k$ distributed processes.
# A Vector Clock is a coordinate tuple $V = (v_1, v_2, \dots, v_k) \in \mathbb{N}^k$, where $V[i]$ represents
# the latest logical time coordinate of process $P_i$ known to the local observer.
#
# * **Partial Order ($\le$):**
#   $$V_a \le V_b \iff \forall i \in \{1, \dots, k\}, \; V_a[i] \le V_b[i]$$
#
# * **Strict Causal Precedence ($V_a < V_b \iff a \to b$):**
#   $$V_a < V_b \iff (V_a \le V_b) \land (V_a \neq V_b)$$
#
# * **Concurrent Events ($a \parallel b$):**
#   $$a \parallel b \iff \neg(V_a \le V_b) \land \neg(V_b \le V_a)$$
#
# * **Semilattice Join / Merge ($\vee$):**
#   When process $P_j$ receives a message with timestamp $V_{\text{msg}}$, it computes the component-wise supremum:
#   $$(V_{\text{local}} \vee V_{\text{msg}})[i] = \max(V_{\text{local}}[i], V_{\text{msg}}[i])$$
#   In AlgebraX, this operation is performed directly using `ax.lattice.combine(v1, v2, max, default=0)`.
#
# ### 2. The Arctic / Max-Plus Semiring $(\mathbb{R}_{\ge 0} \cup \{-\infty\}, \max, +)$
# In causal dependency DAGs, the earliest propagation timestamp along multi-hop network paths is governed by
# the **Arctic (Max-Plus) Semiring**:
#
# * **Additive Operation ($\oplus$):** $\max(a, b)$ with identity $\mathbf{0}_{\text{Arctic}} = -\infty$.
# * **Multiplicative Operation ($\otimes$):** $a + b$ with identity $\mathbf{1}_{\text{Arctic}} = 0$.
# * **DAG Contraction:** Matrix power $E^k$ over the Arctic semiring evaluates the longest causal latency path
#   spanning $k$ hops across the distributed network.

# %%
from typing import Any

import algebrax as ax


# %%
def tick_vector_clock(clock: dict[str, int], process_id: str) -> dict[str, int]:
    """Increments the local logical clock component for the specified process."""
    res = dict(clock)
    res[process_id] = res.get(process_id, 0) + 1
    return res


def merge_vector_clocks(c1: dict[str, int], c2: dict[str, int]) -> dict[str, int]:
    """Computes the Join-Semilattice supremum (V1 join V2) taking component-wise maximums."""
    return ax.lattice.combine(c1, c2, max, default=0)


def compare_vector_clocks(c1: dict[str, int], c2: dict[str, int]) -> str:
    """Evaluates the partial order relation between two vector clocks:

    Returns 'precedes' (c1 < c2), 'succeeds' (c1 > c2), 'equal' (c1 == c2), or 'concurrent' (c1 || c2).
    """
    all_keys = set(c1.keys()) | set(c2.keys())
    le12 = all(c1.get(k, 0) <= c2.get(k, 0) for k in all_keys)
    le21 = all(c2.get(k, 0) <= c1.get(k, 0) for k in all_keys)

    if le12 and le21:
        return "equal"
    if le12:
        return "precedes"
    if le21:
        return "succeeds"
    return "concurrent"


# %% [markdown]
# ## Step 1: Distributed Message Passing Simulation
#
# We simulate a 3-process cluster (`P0`, `P1`, `P2`) executing local actions and cross-process message sends:
#
# * **Event `e0_1`**: `P0` executes a local step ($L=1, V=(1,0,0)$).
# * **Event `e0_2`**: `P0` sends message $M_1$ to `P1` ($L=2, V=(2,0,0)$).
# * **Event `e1_1`**: `P1` executes a local step ($L=1, V=(0,1,0)$).
# * **Event `e1_2`**: `P1` receives $M_1$ from `P0` ($L=\max(1, 2)+1=3, V=(2,1,0)\vee(0,1,0) + (0,1,0) = (2,2,0)$).
# * **Event `e2_1`**: `P2` executes an isolated local step ($L=1, V=(0,0,1)$).
# * **Event `e1_3`**: `P1` sends message $M_2$ to `P2` ($L=4, V=(2,3,0)$).
# * **Event `e2_2`**: `P2` receives $M_2$ from `P1` ($L=\max(1, 4)+1=5, V=(2,3,2)$).

# %%
def simulate_distributed_cluster() -> dict[str, dict[str, Any]]:
    """Simulates an asynchronous distributed execution across 3 processes,

    tracking Lamport scalar clocks and Vector clocks for every event.
    """
    processes = ["P0", "P1", "P2"]

    # Initial state
    scalar_clocks = dict.fromkeys(processes, 0)
    vector_clocks = {p: dict.fromkeys(processes, 0) for p in processes}

    event_log: dict[str, dict[str, Any]] = {}
    inflight_messages: dict[str, dict[str, Any]] = {}

    def local_event(event_id: str, proc: str, description: str) -> None:
        scalar_clocks[proc] += 1
        vector_clocks[proc] = tick_vector_clock(vector_clocks[proc], proc)
        event_log[event_id] = {
            "event_id": event_id,
            "process": proc,
            "type": "LOCAL",
            "desc": description,
            "scalar_clock": scalar_clocks[proc],
            "vector_clock": dict(vector_clocks[proc]),
        }

    def send_event(event_id: str, msg_id: str, src: str, dest: str, description: str) -> None:
        scalar_clocks[src] += 1
        vector_clocks[src] = tick_vector_clock(vector_clocks[src], src)
        inflight_messages[msg_id] = {
            "scalar": scalar_clocks[src],
            "vector": dict(vector_clocks[src]),
        }
        event_log[event_id] = {
            "event_id": event_id,
            "process": src,
            "type": "SEND",
            "desc": f"{description} (Send {msg_id} -> {dest})",
            "scalar_clock": scalar_clocks[src],
            "vector_clock": dict(vector_clocks[src]),
            "msg_id": msg_id,
        }

    def receive_event(event_id: str, msg_id: str, dest: str, description: str) -> None:
        msg = inflight_messages[msg_id]
        scalar_clocks[dest] = max(scalar_clocks[dest], msg["scalar"]) + 1
        merged_v = merge_vector_clocks(vector_clocks[dest], msg["vector"])
        vector_clocks[dest] = tick_vector_clock(merged_v, dest)
        event_log[event_id] = {
            "event_id": event_id,
            "process": dest,
            "type": "RECEIVE",
            "desc": f"{description} (Recv {msg_id})",
            "scalar_clock": scalar_clocks[dest],
            "vector_clock": dict(vector_clocks[dest]),
            "msg_id": msg_id,
        }

    # Trace execution
    local_event("e0_1", "P0", "P0 initializes transaction batch")
    send_event("e0_2", "M1", "P0", "P1", "P0 sends replicated state M1 to P1")
    local_event("e1_1", "P1", "P1 processes local write")
    receive_event("e1_2", "M1", "P1", "P1 applies replicated state M1 from P0")
    local_event("e2_1", "P2", "P2 handles independent user query")
    send_event("e1_3", "M2", "P1", "P2", "P1 forwards checkpoint M2 to P2")
    receive_event("e2_2", "M2", "P2", "P2 synchronizes checkpoint M2 from P1")

    return event_log


# %% [markdown]
# ## Step 2: Causal Precedence & Concurrency Classification Matrix
#
# We compute the pairwise causality relationship across all events in the distributed trace.
# Notice how `e1_1` ($L=1, V=(0,1,0)$) and `e0_1` ($L=1, V=(1,0,0)$) are identified as **concurrent** ($a \parallel b$),
# while scalar clocks alone could not distinguish causal succession from concurrent execution.

# %%
def compute_causality_matrix(
    event_log: dict[str, dict[str, Any]],
) -> dict[str, dict[str, str]]:
    """Evaluates the full pairwise causality matrix across all recorded events."""
    event_ids = list(event_log.keys())
    matrix: dict[str, dict[str, str]] = {e1: {} for e1 in event_ids}

    for e1 in event_ids:
        v1 = event_log[e1]["vector_clock"]
        for e2 in event_ids:
            v2 = event_log[e2]["vector_clock"]
            matrix[e1][e2] = compare_vector_clocks(v1, v2)

    return matrix


# %% [markdown]
# ## Step 3: Causal Event Graph Contraction via Boolean & Arctic Semirings
#
# The direct process transitions and message transmission channels form a Directed Acyclic Graph (DAG).
#
# We evaluate:
# 1. **Causal Reachability Matrix:** Contracting the adjacency matrix $E$ via `ax.matrix.power` over `BooleanSemiring`.
# 2. **Earliest Arrival Time:** Contracting transmission weights over `ArcticSemiring` $(\max, +)$.

# %%
def compute_causal_dag_analysis(
    event_log: dict[str, dict[str, Any]],
) -> tuple[dict[str, dict[str, bool]], dict[str, dict[str, float]]]:
    """Analyzes the causal dependency DAG using Boolean reachability and Arctic critical path semirings."""
    event_ids = list(event_log.keys())

    # Build direct causal adjacency matrix E
    # Edge exists if same process consecutive event or message send -> receive
    direct_adj_bool: dict[str, dict[str, bool]] = {e: {} for e in event_ids}
    direct_adj_arctic: dict[str, dict[str, float]] = {e: {} for e in event_ids}

    # 1. Intra-process sequential edges (weight = 1 ms local latency)
    proc_events: dict[str, list[str]] = {}
    for e_id, data in event_log.items():
        proc_events.setdefault(data["process"], []).append(e_id)

    for _, e_list in proc_events.items():
        for idx in range(len(e_list) - 1):
            u, v = e_list[idx], e_list[idx + 1]
            direct_adj_bool[u][v] = True
            direct_adj_arctic[u][v] = 1.0

    # 2. Inter-process message edges (weight = 5 ms network latency)
    sends = {data["msg_id"]: e_id for e_id, data in event_log.items() if data["type"] == "SEND"}
    for e_id, data in event_log.items():
        if data["type"] == "RECEIVE":
            msg_id = data.get("msg_id")
            if msg_id and msg_id in sends:
                src_event = sends[msg_id]
                direct_adj_bool[src_event][e_id] = True
                direct_adj_arctic[src_event][e_id] = 5.0

    # Multi-hop transitive closure via Boolean Semiring: E* = E ⊕ E^2 ⊕ E^3 ...
    bool_semiring = ax.semiring.BooleanSemiring()
    reachability: dict[str, dict[str, bool]] = {e: dict(direct_adj_bool[e]) for e in event_ids}

    curr_power = direct_adj_bool
    for _ in range(len(event_ids)):
        curr_power = ax.matrix.dot(curr_power, direct_adj_bool, semiring=bool_semiring)
        for r, row in curr_power.items():
            for c, val in row.items():
                if val:
                    reachability.setdefault(r, {})[c] = True

    # Multi-hop critical path latency via Arctic (Max-Plus) Semiring
    arctic_semiring = ax.semiring.ArcticSemiring()
    max_latency_dag: dict[str, dict[str, float]] = {e: dict(direct_adj_arctic[e]) for e in event_ids}

    curr_arctic = direct_adj_arctic
    for _ in range(len(event_ids)):
        curr_arctic = ax.matrix.dot(curr_arctic, direct_adj_arctic, semiring=arctic_semiring)
        for r, row in curr_arctic.items():
            for c, val in row.items():
                prev = max_latency_dag.get(r, {}).get(c, -float('inf'))
                max_latency_dag.setdefault(r, {})[c] = max(prev, val)

    return reachability, max_latency_dag


# %% [markdown]
# ## Step 4: State-Based CRDT & Version Vector Synchronization
#
# In Conflict-Free Replicated Data Types (CRDTs), independent replicas converge without centralized consensus
# by calculating the least upper bound (LUB) join of state vectors.
#
# We demonstrate deterministic synchronization between two diverging replica nodes `Replica_Alpha` and `Replica_Beta`.

# %%
def synchronize_crdt_replicas(
    state_alpha: dict[str, int],
    state_beta: dict[str, int],
) -> tuple[dict[str, int], str]:
    """Merges two divergent CRDT replica state vectors via Join-Semilattice supremum."""
    comp = compare_vector_clocks(state_alpha, state_beta)
    merged_state = merge_vector_clocks(state_alpha, state_beta)
    return merged_state, comp


# %%
def run_demo() -> None:
    """Executes distributed causal ordering simulation and analytical verifications."""
    print("=== Step 1: Distributed Message Passing Trace ===")
    trace = simulate_distributed_cluster()
    for e_id, info in trace.items():
        v_str = ", ".join(f"{p}:{info['vector_clock'].get(p, 0)}" for p in ['P0', 'P1', 'P2'])
        desc = info['desc']
        proc = info['process']
        etype = info['type']
        s_clk = info['scalar_clock']
        print(f"  Event [{e_id:4s}] ({proc}) {etype:7s} | L={s_clk} | V=({v_str}) | {desc}")

    print("\n=== Step 2: Causality & Concurrency Classification Matrix ===")
    causal_mat = compute_causality_matrix(trace)
    print("  Comparing e0_1 vs e1_1:", causal_mat["e0_1"]["e1_1"], "(Expected: concurrent)")
    assert causal_mat["e0_1"]["e1_1"] == "concurrent"
    assert causal_mat["e1_1"]["e0_1"] == "concurrent"

    print("  Comparing e0_1 vs e1_2:", causal_mat["e0_1"]["e1_2"], "(Expected: precedes)")
    assert causal_mat["e0_1"]["e1_2"] == "precedes"
    assert causal_mat["e1_2"]["e0_1"] == "succeeds"

    print("  Comparing e0_1 vs e2_2:", causal_mat["e0_1"]["e2_2"], "(Expected: precedes via 2-hop causality)")
    assert causal_mat["e0_1"]["e2_2"] == "precedes"

    print("\n=== Step 3: Causal Graph Contraction & Arctic Critical Latency ===")
    reach, latencies = compute_causal_dag_analysis(trace)
    print(f"  Causal Reachability from e0_1 to e2_2: {reach.get('e0_1', {}).get('e2_2', False)}")
    assert reach.get("e0_1", {}).get("e2_2", False) is True

    # Path e0_1 -> e0_2 (1ms) -> e1_2 (5ms) -> e1_3 (1ms) -> e2_2 (5ms) = 12ms
    lat_e01_e22 = latencies.get("e0_1", {}).get("e2_2", 0.0)
    print(f"  Critical Path Latency from e0_1 to e2_2: {lat_e01_e22:.1f} ms")
    assert lat_e01_e22 >= 12.0

    print("\n=== Step 4: CRDT Replicas Join-Semilattice Synchronization ===")
    rep_a = {"node_1": 4, "node_2": 2, "node_3": 0}
    rep_b = {"node_1": 1, "node_2": 5, "node_3": 3}
    merged, relation = synchronize_crdt_replicas(rep_a, rep_b)
    print(f"  Replica A: {rep_a}")
    print(f"  Replica B: {rep_b}")
    print(f"  Relation : {relation} (Concurrent Divergence)")
    print(f"  Merged   : {merged}")
    assert relation == "concurrent"
    assert merged == {"node_1": 4, "node_2": 5, "node_3": 3}


def main() -> None:
    """Entry point for CLI and script execution."""
    run_demo()
    print("==========================================================================")
    print("Recipe: Distributed Vector Clocks & Causal Semilattices Finished Successfully!")
    print("==========================================================================")


if __name__ == "__main__":
    main()
