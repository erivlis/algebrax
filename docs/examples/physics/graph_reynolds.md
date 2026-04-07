# Graph Reynolds Number

A metric derived from Fluid Dynamics (Rayleigh-Plesset) to predict "Turbulence" (Congestion) in a network.
$Re_G = \frac{\text{Momentum}}{\text{Viscosity}} = \frac{\text{Total Flow}}{\text{Algebraic Connectivity}}$

!!! note "Dependency"
This example requires `networkx` and `numpy`.

<!-- name: test_graph_reynolds -->

```python linenums="1"
import networkx as nx
import numpy as np


def calculate_graph_reynolds(G: nx.Graph, flow_dict: dict) -> float:
    """
    Calculates the 'Rivlis-Plesset Number' (Rp) for a network.
    """
    # 1. Momentum (Total Flow)
    total_flow = sum(flow_dict.values())
    if total_flow == 0: return 0.0

    # 2. Viscosity (Algebraic Connectivity / Fiedler Value)
    # High connectivity = Low drag (fluid moves easily).
    try:
        # weight='capacity' if edges have capacity
        viscosity = nx.algebraic_connectivity(G)
    except:
        viscosity = 0.001  # Disconnected graph

    # 3. Reynolds Calculation
    return total_flow / (viscosity + 1e-9)


def analyze_stability(rp: float) -> str:
    if rp < 1000:
        return "Laminar Flow (Stable)"
    elif 1000 <= rp < 2000:
        return "Transitional (Wobbling)"
    else:
        return "Turbulent (Cavitation Imminent!)"


# Simulation
G = nx.grid_2d_graph(5, 5)
flow_laminar = {e: 0.1 for e in G.edges()}
flow_turbulent = {e: 5000.0 for e in G.edges()}

rp_lam = calculate_graph_reynolds(G, flow_laminar)
rp_turb = calculate_graph_reynolds(G, flow_turbulent)

print(f"Scenario A: {analyze_stability(rp_lam)}")
print(f"Scenario B: {analyze_stability(rp_turb)}")
```
