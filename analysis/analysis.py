from dataclasses import dataclass, field
from typing import List, Optional

from qiskit import transpile, QuantumCircuit
from qiskit.providers.ibmq import IBMQJobManager, IBMQBackend
from qiskit.result import Result

from analysis.error_mitigation import get_counts_result
from analysis.utils import get_all_spin_up_state, get_gauss_base_state
from analysis.zne_extrapolation import custom_folding
from models.circuits import SinglePlaquette
from models.constants import Groups


@dataclass
class PhysicalModel:
    plaquette: type = SinglePlaquette
    number_links: int = 3
    coupling: float = 1.0
    control_qubit: int = 1
    gauge: str = Groups.Z2


@dataclass
class ExperimentConfiguration:
    output_error_correction: bool = False
    zne_extrapolation: bool = False
    scale_factors: List[float] = field(default_factory=list)
    optimisation_level: int = 2
    num_replicas: int = 1


@dataclass
class RunConfiguration:
    time_vector: List[float]
    backend: IBMQBackend
    shots: int = 1000


def analyze_results(physical_model: PhysicalModel, experiment_configuration: ExperimentConfiguration,
                    run_configuration: RunConfiguration,
                    result_hpc: Result, result_key: Optional[str] = None, gauss_key: Optional[str] = None,
                    mitigated_counts: dict = None, ignis: bool = True, meas_filter=None):
    """
    Returns an array with normalized counts for spin up states in the plaquette
    """
    number_links = physical_model.number_links
    time_vector = run_configuration.time_vector
    shots = run_configuration.shots
    zne_extrapolation = experiment_configuration.zne_extrapolation
    scale_factors = experiment_configuration.scale_factors
    num_replicas = experiment_configuration.num_replicas

    if not result_key:
        result_key = get_all_spin_up_state(number_links)

    if not gauss_key:
        gauss_key = get_gauss_base_state(number_links)

    if result_key is None or gauss_key is None:
        return

    if ignis:
        pass
        # mitigated_counts = meas_filter.apply(result_hpc) if meas_filter else result_hpc

    results_df = get_counts_result(mitigated_counts, result_hpc, result_key, gauss_key, time_vector,
                                   zne_extrapolation, scale_factors, num_replicas, ignis=ignis, shots=shots,
                                   meas_filter=meas_filter)

    return results_df


def run_circuits(physical_model: PhysicalModel, experiment_config: ExperimentConfiguration,
                 run_config: RunConfiguration) -> \
        (IBMQJobManager, str, list):
    number_links = physical_model.number_links
    g = physical_model.coupling
    model = physical_model.plaquette
    group = physical_model.gauge
    control_qubit = physical_model.control_qubit

    time_vector = run_config.time_vector
    backend = run_config.backend
    optimization_level = experiment_config.optimisation_level
    shots = run_config.shots
    zne_extrapolation = experiment_config.zne_extrapolation
    scale_factors = experiment_config.scale_factors
    num_replicas = experiment_config.num_replicas

    if number_links != 4 and number_links != 3:
        print("Error: only triangular or square plaquettes are implemented")
        raise ValueError("Number of links can only be 3 or 4")

    if backend is None:
        raise ValueError("Backend cannot be None")

    circuits = []

    for time_step in time_vector:
        plaquette_obj = model(number_links + 1, time_step, g, gauge_group=group)
        base_circuit = plaquette_obj.generate_circuit(control_qubit)  # For Valencia, qubit 1 is the control qubit
        circuits_in_step = get_circuits_by_time_step(base_circuit, zne_extrapolation, scale_factors, backend,
                                                     optimization_level)

        circuits.extend(circuits_in_step)

    max_credits = 5  # max credits to spend on executions--the gui interface gives credit prices

    circuits = circuits * num_replicas
    job_manager = IBMQJobManager()
    if optimization_level is not None:
        job_hpc = job_manager.run(circuits, backend=backend, shots=shots, max_credits=max_credits, optimization_level=0)
    else:
        job_hpc = job_manager.run(circuits, backend=backend, shots=shots, max_credits=max_credits)

    job_set_id = job_hpc.job_set_id()

    return job_manager, job_set_id, circuits


def get_circuits_by_time_step(circuit: QuantumCircuit, zne: bool, scale_factors: list, backend: IBMQBackend,
                              optimization_level: Optional[int]) -> List[QuantumCircuit]:
    circuits_in_time_step = list()
    if not zne:
        if optimization_level is not None:
            circuit = transpile(circuit, backend, basis_gates=['id', 'u1', 'u2', 'u3', 'cx'], optimization_level=2)
        return [circuit]

    for scale in scale_factors:
        circuit = transpile(circuit, backend, basis_gates=['id', 'u1', 'u2', 'u3', 'cx'],
                            optimization_level=2)

        folded_circuit = custom_folding(circuit, scale, seed=150)
        circuits_in_time_step.append(folded_circuit)

    return circuits_in_time_step
