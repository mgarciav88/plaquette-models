from qiskit import transpile, execute
from qiskit.result import Result

from analysis.error_correction import get_counts_result
from analysis.utils import get_all_spin_up_state
from models.circuits import SinglePlaquette
from models.constants import Groups


def analyze_results(number_links: int, result_hpc: Result, time_vector: list, circuits: list, result_key=None,
                    output_correction: dict = None):
    """
    Returns an array with normalized counts for spin up states in the plaquette
    """
    count_res = []
    count_res_corrected = []
    if not result_key:
        result_key = get_all_spin_up_state(number_links)

    if result_key is None:
        return

    get_counts_result(circuits, count_res, count_res_corrected, output_correction, result_hpc, result_key,
                      time_vector)

    return count_res, count_res_corrected


def analyze_results_ignis(number_links: int, result_hpc: Result, time_vector: list, circuits: list, result_key=None,
                          meas_filter=None):
    count_res = []
    count_res_corrected = []
    if not result_key:
        result_key = get_all_spin_up_state(number_links)

    if result_key is None:
        return

    mitigated_result = meas_filter.apply(result_hpc) if meas_filter else result_hpc

    get_counts_result(circuits, count_res, count_res_corrected, mitigated_result, result_hpc, result_key,
                      time_vector, ignis=True)

    return count_res, count_res_corrected


def run_circuits(number_links: int = 4, g=1.0, time_vector=range(1), backend=None, optimization_level=None, model=None):
    if number_links != 4 and number_links != 3:
        print("Error: only triangular or square plaquettes are implemented")
        raise ValueError("Number of links can only be 3 or 4")

    if backend is None:
        raise ValueError("Backend cannot be None")

    if model is None:
        model = {
            'plaquette': SinglePlaquette,
            'gauge_group': Groups.Z2,
        }

    circuits = []

    for time_step in time_vector:
        plaquette_obj = model.get('plaquette')(number_links + 1, time_step, g, gauge_group=model.get('gauge_group'))
        circuit = plaquette_obj.generate_circuit(1)  # For Valencia, qubit 1 is the control qubit
        if optimization_level is not None:
            circuit = transpile(circuit, backend, basis_gates=['id', 'u1', 'u2', 'u3', 'cx'], optimization_level=2)

        circuits.append(circuit)

    shots = 8192  # max 8192 shots
    max_credits = 5  # max credits to spend on executions--the gui interface gives credit prices

    if optimization_level is not None:
        job_hpc = execute(circuits, backend=backend, shots=shots, max_credits=max_credits, optimization_level=0)
    else:
        job_hpc = execute(circuits, backend=backend, shots=shots, max_credits=max_credits)
    result_hpc = job_hpc.result()

    return result_hpc, circuits
