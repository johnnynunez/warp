import os

verify_fp = False       # verify inputs and outputs are finite after each launch
verify_cuda = False     # if true will check CUDA errors after each kernel launch / memory operation

enable_backward = False # disable code gen of backwards pass

mode = "release"