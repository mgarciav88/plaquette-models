import itertools
import json

import numpy as np
import pandas as pd
from qiskit import QuantumRegister, QuantumCircuit, ClassicalRegister, execute
from qiskit.ignis.mitigation import complete_meas_cal, CompleteMeasFitter
from qiskit.providers.ibmq import IBMQBackend

from src.analysis.constants import MATRIX, STATES
from src.observables.gauss import gauss_law, sector_2, gauss_law_squared


def get_counts_result(output_correction, result_hpc, result_key: str, gauss_key: str, time_vector: list,
                      zne_extrapolation: bool, scale_factors: list, num_replicas: int, ignis: bool = False,
                      shots: int = 1000, meas_filter=None) -> (list, list):
    results = list()
    experiments_params = get_exp_params(time_vector, zne_extrapolation, scale_factors, num_replicas)
    time_steps = len(time_vector)
    num_scales = len(scale_factors) if zne_extrapolation else 1

    for exp_ind in range(time_steps * num_scales * num_replicas):
        non_corrected_counts = result_hpc.get_counts(exp_ind)
        one_count = non_corrected_counts.get(result_key, 0) / shots
        experiment_result = dict()
        replica_ind = experiments_params[exp_ind][-1]

        experiment_result.update({
            'replica': replica_ind,
        })

        if zne_extrapolation:
            time_ind = experiments_params[exp_ind][0]
            scale_ind = experiments_params[exp_ind][1]
            experiment_result.update({
                'scale_factor': scale_ind,
            })
        else:
            time_ind = experiments_params[exp_ind][0]

        experiment_result.update({
            'time': time_ind
        })

        if ignis:
            corrected_counts = meas_filter.apply(non_corrected_counts)
            corrected_one_count = apply_ignis_error_correction(corrected_counts, exp_ind, result_key, shots)
            gauss_law_obs, gauss_law_obs_corrected = gauss_law(non_corrected_counts, corrected_counts, shots)
            gauss_2_obs, gauss_2_obs_corrected = sector_2(gauss_key, non_corrected_counts, corrected_counts,
                                                          shots)
            gauss_law_sq_obs, gauss_law_sq_obs_corrected = gauss_law_squared(non_corrected_counts, corrected_counts,
                                                                             shots)
            experiment_result.update({
                'gauss_law': gauss_law_obs,
                'gauss_law_corrected': gauss_law_obs_corrected,
                'sector_2': gauss_2_obs,
                'sector_2_corrected': gauss_2_obs_corrected,
                'gauss_law_squared': gauss_law_sq_obs,
                'gauss_law_squared_corrected': gauss_law_sq_obs_corrected,
            })
        else:
            corrected_one_count = apply_error_correction(non_corrected_counts, output_correction, result_key, shots)

        experiment_result.update({
            'original': one_count,
            'output_corrected': corrected_one_count,
        })

        results.append(experiment_result)

    results_df = pd.DataFrame(results)

    return results_df


def apply_error_correction(experiment_data, error_correction: dict, result_key: str, shots: int = 1000):
    if error_correction is None:
        return experiment_data.get(result_key, 0)

    possible_states = error_correction.get(STATES)
    row_to_choose = possible_states.index(result_key)
    correction_vector = error_correction.get(MATRIX)[row_to_choose]
    experiment_vector = [experiment_data.get(state, 0) / shots for state in possible_states]

    res = 0

    for exp_res, cor_val in zip(experiment_vector, correction_vector):
        res += exp_res * cor_val

    return res


def apply_ignis_error_correction(mitigated_counts, circ_ind: int, result_key: str, shots: int):
    return mitigated_counts.get(result_key, 0) / shots


class CustomErrorMitigation:
    def __init__(self, n_qubits: int = 4, shots: int = 1000):
        self.n_qubits = n_qubits
        self.shots = shots

    def _build_set_of_states(self):
        possible_states = list()
        for state in itertools.product([0, 1], repeat=self.n_qubits):
            state_to_str = list(map(str, state))
            possible_states.append(''.join(state_to_str))

        return possible_states

    def _get_probabilities_vector(self, counts: dict):
        possible_states = self._build_set_of_states()
        probability_vector = list()
        for state in possible_states:
            probability_vector.append(counts.get(state, 0) / self.shots)

        return probability_vector

    def _build_circuit(self, initial_state: str):
        if self.n_qubits != len(initial_state):
            raise Exception('Error in parameters, number of qubits does not agree with initial_state')
        q = QuantumRegister(self.n_qubits, 'q')
        circ = QuantumCircuit(q)
        for q_ind, q_state in enumerate(initial_state[::-1]):  # Flipping the state to map to qubit order
            if q_state == '1':
                circ.x(q[q_ind])

        c = ClassicalRegister(self.n_qubits, 'c')
        meas = QuantumCircuit(q, c)
        meas.measure(q, c)
        qc = circ + meas

        return qc

    def build_probability_matrix(self, backend: IBMQBackend):
        possible_states = self._build_set_of_states()
        probability_matrix = list()
        circuits = list()
        for initial_state in possible_states:
            qc = self._build_circuit(initial_state)
            circuits.append(qc)

        job_hpc = execute(circuits, backend=backend, shots=self.shots, max_credits=5)
        result_hpc = job_hpc.result()

        for ind, _ in enumerate(possible_states):
            probability_matrix.append(self._get_probabilities_vector(result_hpc.get_counts(circuits[ind])))

        return {MATRIX: np.linalg.inv(probability_matrix), STATES: possible_states}

    @staticmethod
    def save_correction_results(error_correction: dict, filename: str):
        with open(filename, 'w') as file:
            json.dump(error_correction, file)

    @staticmethod
    def load_correction_results(filename: str):
        with open(filename, 'r') as file:
            error_correction = json.load(file)
        return error_correction


class IgnisErrorMitigation:
    def __init__(self, n_qubits: int = 4, shots: int = 1000):
        self.n_qubits = n_qubits
        self.shots = shots
        self.meas_fitter = None

    def get_meas_fitter(self, backend: IBMQBackend):
        q_bits = list(range(self.n_qubits))
        cal_circuits, state_labels = complete_meas_cal(qubit_list=q_bits, circlabel='mitigationError')

        cal_job = execute(cal_circuits,
                          backend=backend,
                          shots=self.shots,
                          optimization_level=0)

        cal_results = cal_job.result()
        meas_fitter = CompleteMeasFitter(cal_results, state_labels)
        sep_labs = list(map(lambda lab: " ".join(lab), meas_fitter.filter.state_labels))
        filter_obj = meas_fitter.filter
        filter_obj._state_labels = list(sep_labs)
        self.meas_fitter = meas_fitter
        return meas_fitter.filter

    def plot_calibration(self):
        self.meas_fitter.plot_calibration()


def get_exp_params(time_vector: list, zne_extrapolation: bool, scale_factors: list, num_replicas: int):
    replicas = list(range(num_replicas))
    if not zne_extrapolation:
        return np.array(np.meshgrid(time_vector, replicas)).T.reshape(-1, 2)

    return np.array(np.meshgrid(time_vector, scale_factors, replicas)).T.reshape(-1, 3)
