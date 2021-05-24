import itertools
import json

import numpy as np
from qiskit import QuantumRegister, QuantumCircuit, ClassicalRegister, execute
from qiskit.ignis.mitigation import complete_meas_cal, CompleteMeasFitter

from analysis.constants import MATRIX, STATES


def get_counts_result(circuits, count_res, count_res_corrected, output_correction, result_hpc, result_key,
                      time_vector, ignis=False):
    for time_ind, time_step in enumerate(time_vector):
        data = result_hpc.get_counts(circuits[time_ind])
        one_count = data.get(result_key, 0) / 8192
        if ignis:
            corrected_one_count = apply_ignis_error_correction(output_correction, circuits[time_ind], result_key)
        else:
            corrected_one_count = apply_error_correction(data, output_correction, result_key)

        count_res.append(one_count)
        count_res_corrected.append(corrected_one_count)


def apply_error_correction(experiment_data, error_correction, result_key):
    if error_correction is None:
        return experiment_data.get(result_key, 0)

    possible_states = error_correction.get(STATES)
    row_to_choose = possible_states.index(result_key)
    correction_vector = error_correction.get(MATRIX)[row_to_choose]
    experiment_vector = [experiment_data.get(state, 0) / 8192 for state in possible_states]

    res = 0

    for exp_res, cor_val in zip(experiment_vector, correction_vector):
        res += exp_res * cor_val

    return res


def apply_ignis_error_correction(mitigated_result, circuit, result_key):
    mitigated_counts = mitigated_result.get_counts(circuit)
    return mitigated_counts.get(result_key, 0) / 8192


class CustomErrorCorrection:
    def __init__(self, n_qubits=4, shots=1000):
        self.n_qubits = n_qubits
        self.shots = shots

    def build_set_of_states(self):
        possible_states = list()
        for state in itertools.product([0, 1], repeat=self.n_qubits):
            state_to_str = list(map(str, state))
            possible_states.append(''.join(state_to_str))

        return possible_states

    def get_probabilities_vector(self, counts):
        #     counts = result.get_counts()
        possible_states = self.build_set_of_states()
        probability_vector = list()
        for state in possible_states:
            probability_vector.append(counts.get(state, 0) / self.shots)

        return probability_vector

    def build_circuit(self, initial_state):
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

    def build_probability_matrix(self, backend):
        possible_states = self.build_set_of_states()
        probability_matrix = list()
        circuits = list()
        for initial_state in possible_states:
            qc = self.build_circuit(initial_state)
            circuits.append(qc)

        job_hpc = execute(circuits, backend=backend, shots=self.shots, max_credits=5)
        result_hpc = job_hpc.result()

        for ind, _ in enumerate(possible_states):
            probability_matrix.append(self.get_probabilities_vector(result_hpc.get_counts(circuits[ind])))

        return {MATRIX: np.linalg.inv(probability_matrix), STATES: possible_states}

    @staticmethod
    def save_correction_results(error_correction, filename):
        with open(filename, 'w') as file:
            json.dump(error_correction, file)

    @staticmethod
    def load_correction_results(filename):
        with open(filename, 'r') as file:
            error_correction = json.load(file)
        return error_correction


class IgnisErrorCorrection:
    def __init__(self, n_qubits=4, shots=1000):
        self.n_qubits = n_qubits
        self.shots = shots
        self.meas_fitter = None

    def get_meas_fitter(self, backend):
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
