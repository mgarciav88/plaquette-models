import itertools

import numpy as np
from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister

from models.constants import Groups


class Plaquette:
    def __init__(self, n_qubits: int, t: float = 1.0, g: float = 1.0):
        self.n_qubits = n_qubits
        self.t = t
        self.g = g
        self.q_register = QuantumRegister(n_qubits, 'q')
        self.circuit = QuantumCircuit(self.q_register)

    def apply_h_gate(self, q_list: list):
        for q_ind in q_list:
            self.circuit.h(self.q_register[q_ind])

    def apply_x_gate(self, q_list: list):
        for q_ind in q_list:
            self.circuit.x(self.q_register[q_ind])

    def forward_entangle(self, qs_real: list, q_control: int):
        # entangle the qubits and induce the interaction
        for q_ind in qs_real:
            self.circuit.cz(self.q_register[q_control], self.q_register[q_ind])
            self.circuit.s(self.q_register[q_ind])
            self.circuit.s(self.q_register[q_control])

    def backward_entangle(self, qs_real: list, q_control: int):
        for q_ind in qs_real[::-1]:
            self.circuit.sdg(self.q_register[q_control])
            self.circuit.sdg(self.q_register[q_ind])
            self.circuit.cz(self.q_register[q_control], self.q_register[q_ind])

    def rotate_qubits(self, index_only_h: int, qs_real: list):
        qs_copy = qs_real.copy()
        qs_copy.remove(index_only_h)
        for q_ind in qs_copy:
            self.circuit.h(self.q_register[q_ind])
            self.circuit.s(self.q_register[q_ind])

        self.circuit.h(self.q_register[index_only_h])

    def backward_rotate_qubits(self, index_only_h: int, qs_real: list):
        qs_copy = qs_real.copy()
        qs_copy.remove(index_only_h)
        self.circuit.h(self.q_register[index_only_h])

        for q_ind in qs_copy:
            self.circuit.sdg(self.q_register[q_ind])
            self.circuit.h(self.q_register[q_ind])

    def x_rotate(self, q_list: list):
        for q_ind in q_list:
            self.circuit.h(self.q_register[q_ind])

    def x_back_rotate(self, q_list: list):
        self.x_rotate(q_list)

    def y_back_rotate(self, q_list: list):
        for q_ind in q_list:
            self.circuit.sdg(self.q_register[q_ind])
            self.circuit.h(self.q_register[q_ind])

    def y_rotate(self, q_list: list):
        for q_ind in q_list:
            self.circuit.h(self.q_register[q_ind])
            self.circuit.s(self.q_register[q_ind])

    def time_evolution(self, q_control: int, time_factor: float = 1.0):
        self.circuit.h(self.q_register[q_control])
        self.circuit.u1(2 * time_factor * self.t * self.g, self.q_register[q_control])
        self.circuit.h(self.q_register[q_control])


class SinglePlaquette(Plaquette):
    def __init__(self, n_qubits: int, t: float = 1.0, g: float = 1.0, gauge_group: str = Groups.Z2):
        super().__init__(n_qubits, t, g)
        self.gauge_group = gauge_group

    def generate_circuit(self, q_control: int):
        qs_real = list(range(self.n_qubits))
        qs_real.remove(q_control)
        if self.gauge_group == Groups.Z2:
            return self.z2_models(q_control, qs_real)
        elif self.gauge_group == Groups.U1:
            return self.u1_models(q_control, qs_real)

    def z2_models(self, q_control: int, qs_real: list):
        if self.n_qubits - 1 == 4:
            self.generate_square_z2(q_control, qs_real)
        elif self.n_qubits - 1 == 3:
            self.generate_triangle_z2(q_control, qs_real)

        c_register = ClassicalRegister(self.n_qubits, 'c')
        meas = QuantumCircuit(self.q_register, c_register)
        meas.barrier(self.q_register)
        meas.measure(self.q_register, c_register)

        return self.circuit + meas

    def u1_models(self, q_control: int, qs_real: list):
        if self.n_qubits - 1 == 3:
            self.generate_triangle_u1(q_control, qs_real)
            print('Triangle')
        elif self.n_qubits - 1 == 4:
            self.generate_square_u1(q_control, qs_real)
            print('Square')

        c_register = ClassicalRegister(self.n_qubits, 'c')

        meas = QuantumCircuit(self.q_register, c_register)
        meas.barrier(self.q_register)
        meas.measure(self.q_register, c_register)

        return self.circuit + meas

    def generate_triangle_u1(self, q_control: int, qs_real: list):
        self.circuit.u2(np.pi / 2, np.pi / 2, self.q_register[q_control])  # np.pi in the latest notebook
        self.apply_x_gate(qs_real)
        self.apply_h_gate(qs_real)

        self.forward_entangle(qs_real, q_control)
        self.time_evolution(q_control)
        self.backward_entangle(qs_real, q_control)

        self.apply_h_gate(qs_real)

        for q_ind in qs_real[::-1]:
            self.x_back_rotate([q_ind])
            qs_real_copy = qs_real.copy()
            qs_real_copy.remove(q_ind)
            self.y_back_rotate(qs_real_copy)
            # self.backward_rotate_qubits(q_ind, qs_real)

            self.forward_entangle(qs_real, q_control)
            self.time_evolution(q_control, time_factor=-1)
            self.backward_entangle(qs_real, q_control)

            self.y_rotate(qs_real_copy)
            self.x_rotate([q_ind])

            # self.rotate_qubits(q_ind, qs_real)

        self.circuit.u2(-np.pi / 2, -np.pi / 2, self.q_register[q_control])

    def generate_square_u1(self, q_control: int, qs_real: list):
        self.circuit.h(self.q_register[q_control])

        self.apply_h_gate(qs_real)

        self.forward_entangle(qs_real, q_control)
        self.time_evolution(q_control)
        self.backward_entangle(qs_real, q_control)

        self.apply_h_gate(qs_real)

        self.y_back_rotate(qs_real)

        self.forward_entangle(qs_real, q_control)
        self.time_evolution(q_control)
        self.backward_entangle(qs_real, q_control)

        self.y_rotate(qs_real)

        for x_q_pair in itertools.combinations(qs_real, 2):
            y_q_pair = [q_ind for q_ind in qs_real if q_ind not in x_q_pair]
            self.x_back_rotate(x_q_pair)
            self.y_back_rotate(y_q_pair)

            if (x_q_pair[0] in qs_real[0:1] and x_q_pair[1] in qs_real[0:1]) or (
                    x_q_pair[0] in qs_real[2:3] and x_q_pair[1] in qs_real[2:3]):
                time_factor = -1
            else:
                time_factor = 1

            self.forward_entangle(qs_real, q_control)
            self.time_evolution(q_control, time_factor=time_factor)
            self.backward_entangle(qs_real, q_control)

            self.y_rotate(y_q_pair)
            self.x_rotate(x_q_pair)

        self.circuit.h(self.q_register[q_control])

    def generate_square_z2(self, q_control: int, qs_real: list):
        self.circuit.h(self.q_register[q_control])
        self.apply_h_gate(qs_real)
        self.forward_entangle(qs_real, q_control)
        self.time_evolution(q_control)
        self.backward_entangle(qs_real, q_control)
        self.apply_h_gate(qs_real)
        self.circuit.h(self.q_register[q_control])

    def generate_triangle_z2(self, q_control: int, qs_real: list):
        self.circuit.u2(np.pi / 2, np.pi / 2, self.q_register[q_control])
        self.apply_h_gate(qs_real)
        self.forward_entangle(qs_real, q_control)
        self.time_evolution(q_control)
        self.backward_entangle(qs_real, q_control)
        self.apply_h_gate(qs_real)
        self.circuit.u2(-np.pi / 2, -np.pi / 2, self.q_register[q_control])
