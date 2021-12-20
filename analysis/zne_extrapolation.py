from mitiq.zne.scaling import fold_gates_at_random


def custom_folding(circuit, scale_factor, seed=150):
    folded = fold_gates_at_random(circuit,
                                  scale_factor,
                                  fidelities={'single': 1.0},
                                  seed=seed)
    return folded
