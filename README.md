# Plaquette models

This repo contains code and jupyter notebooks that can be used to reconstruct the results presented in
[ Real-time dynamics of Plaquette Models using NISQ Hardware](https://arxiv.org/abs/2109.15065).

The repo is organized in such a way that the python modules are all part of the src module, while notebooks includes 
the jupyter notebooks with examples on how to use the different modules. Be aware that this is written so that 
experiments reported in the paper can be reproduced, but it is not a package with all the required validation, error 
handling, etc., so going much beyond the examples presented in the notebooks might require modifying the python code in 
src.

## Pre-requisites

* IBM Quantum account (free version provides access to various hardware that can be used to reproduce these experiments).

Follow the instructions in [IBM account](https://www.ibm.com/account) to create an account or login to it.

* Obtain your personal token to access the IBMQ systems.

## Installation

It is recommended to use a python environment to run this code. Any of the traditional virtual 
environment management tools such as `virtualenv`, `pipenv`, etc. would work, but here we assume `virtualenv` is used.

After activating a virtual environment, install all necessary third party packages using:

```bash
pip install -r requirement.txt
```

The notebooks assume credentials are stored in the system, so before running any of them, make sure the following 
command is run within a python session:

```python
from qiskit import IBMQ

IBMQ.save_acount(token)
```

This needs the token obtained from IBM and linked to your account. 

Once the token is stored, the notebooks use the command:

```python
from qiskit import IBMQ

IBMQ.load_account()
```
To obtain access to the quantum systems.

## Running the notebooks

Two notebooks are included in the notebooks directory:

1. circuits: includes examples showing how to generate and visualize the basic circuits used in the paper.
2. experiments: includes examples on how to run the experiments and generate some of the plots presented in the paper. 
Be aware that plotting functionality is very limited to specific results, so you would probably need to create your own 
plotting functionality to obtain specific results.
