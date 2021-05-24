import numpy as np
from qiskit import QuantumRegister, QuantumCircuit, ClassicalRegister


def square_z2(t: float = 1.0, g: float = 1.0, q_control: int = 1):
    # defines the circuit for the square plaquette
    # for Valencia: q[1] is the ancillary qubit
    n_qubits = 5
    q = QuantumRegister(n_qubits, 'q')
    circ = QuantumCircuit(q)
    qlist = list(range(n_qubits))
    qlist.remove(q_control)
    # ancillary as eigenstate in the x-basis
    circ.h(q[q_control])
    # for 4-spin interaction start with the x-basis
    for q_ind in qlist:
        circ.h(q[q_ind])

    # entangle the qubits and induce the interaction
    for q_ind in qlist:
        circ.cz(q[q_control], q[q_ind])
        circ.s(q[q_ind])
        circ.s(q[q_control])

    #
    circ.h(q[q_control])
    circ.u1(2 * t * g, q[q_control])
    circ.h(q[q_control])
    #

    for q_ind in qlist[::-1]:
        circ.sdg(q[q_control])
        circ.sdg(q[q_ind])
        circ.cz(q[q_control], q[q_ind])

    #
    c = ClassicalRegister(n_qubits, 'c')
    #
    # rotate measurements so that they are in the x-basis

    for q_ind in qlist:
        circ.h(q[q_ind])

    # rotate the ancillary before making the measurements
    circ.h(q[1])

    meas = QuantumCircuit(q, c)
    meas.barrier(q)
    meas.measure(q, c)
    qc = circ + meas

    return qc


def triangle_z2(t=1.0, g=1.0):
    # defines the circuit for the triangular plaquette
    n_qubits = 4
    q = QuantumRegister(n_qubits, 'q')
    circ = QuantumCircuit(q)
    # q1 is the ancillary
    q_control = 1
    circ.u2(np.pi / 2, np.pi / 2, q[q_control])

    qlist = [0, 2, 3]

    for q_ind in qlist:
        circ.h(q[q_ind])

    # entangle the qubits and induce the interaction

    for q_ind in qlist:
        circ.cz(q[q_control], q[q_ind])
        circ.s(q[q_ind])
        circ.s(q[q_control])

    ##
    circ.h(q[q_control])
    circ.u1(2 * t * g, q[q_control])
    circ.h(q[q_control])
    ##

    for q_ind in qlist[::-1]:
        circ.sdg(q[q_control])
        circ.sdg(q[q_ind])
        circ.cz(q[q_control], q[q_ind])

    #
    c = ClassicalRegister(n_qubits, 'c')

    for q_ind in qlist:
        circ.h(q[q_ind])

    circ.u2(-np.pi / 2, -np.pi / 2, q[q_control])

    meas = QuantumCircuit(q, c)
    meas.barrier(q)
    meas.measure(q, c)
    qc = circ + meas

    return qc
