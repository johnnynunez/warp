import numpy as np
import warp as wp

import torch

#wp.config.mode = "debug"

wp.init()
wp.set_module_options({"enable_backward": True})
wp.set_device("cuda:0")


wp.build.clear_kernel_cache()

TILE_M = 8
TILE_N = 4

@wp.kernel
def tile_copy(A: wp.array2d(dtype=float),
              B: wp.array2d(dtype=float)):
    
    # tile index
    i, j = wp.tid() 
    
    a = wp.tile_load(A, i, j, m=TILE_M, n=TILE_N)
    wp.tile_store(B, i, j, a)


def test_tile_copy():

    rng = np.random.default_rng(42)

    M = TILE_M*7
    N = TILE_N*5

    A = rng.random((M, N), dtype=np.float32)
    B = rng.random((M, N), dtype=np.float32)

    A_wp = wp.array(A, requires_grad=True)
    B_wp = wp.array(B, requires_grad=True)

    with wp.Tape() as tape:
        wp.launch(tile_copy, dim=[int(M/TILE_M), int(N/TILE_N)], inputs=[A_wp, B_wp], tile_size=8)

    # verify forward pass
    assert(np.allclose(A, B_wp.numpy(), rtol=1.e-4))
    print("Copy forward passed")

    # verify backward pass
    B_wp.grad = wp.ones_like(B_wp)
    tape.backward()

    assert(np.allclose(A_wp.grad.numpy(), B_wp.grad.numpy()))
    print("Copy backward passed")

@wp.func
def unary_func(x: float):
    return wp.sin(x)

@wp.kernel
def tile_unary_map(input: wp.array2d(dtype=float),
                   output: wp.array2d(dtype=float)):
    
    # tile index
    i, j = wp.tid() 
    
    a = wp.tile_load(input, i, j, m=TILE_M, n=TILE_N)
    
    sa = wp.tile_map(unary_func, a)
    
    wp.tile_store(output, i, j, sa)


def test_tile_unary_map():

    rng = np.random.default_rng(42)

    M = TILE_M*7
    N = TILE_N*5

    A = rng.random((M, N), dtype=np.float32)
    B = np.sin(A)

    A_grad = np.cos(A)

    A_wp = wp.array(A, requires_grad=True)
    B_wp = wp.zeros_like(A_wp, requires_grad=True)

    with wp.Tape() as tape:
        wp.launch(tile_unary_map, dim=[int(M/TILE_M), int(N/TILE_N)], inputs=[A_wp, B_wp], tile_size=8)

    # verify forward pass
    assert(np.allclose(B, B_wp.numpy(), rtol=1.e-4))
    print("Unary map forward passed")

    # verify backward pass
    B_wp.grad = wp.ones_like(B_wp)
    tape.backward()

    assert(np.allclose(A_wp.grad.numpy(), A_grad))
    print("Unary map backward passed")


@wp.func
def binary_func(x: float, y: float):
    return wp.sin(x) + y

@wp.kernel
def tile_binary_map(input_a: wp.array2d(dtype=float),
                   input_b: wp.array2d(dtype=float),
                   output: wp.array2d(dtype=float)):
    
    # tile index
    i, j = wp.tid() 
    
    a = wp.tile_load(input_a, i, j, m=TILE_M, n=TILE_N)
    b = wp.tile_load(input_b, i, j, m=TILE_M, n=TILE_N)
    
    sa = wp.tile_map(binary_func, a, b)
    
    wp.tile_store(output, i, j, sa)


def test_tile_binary_map():

    rng = np.random.default_rng(42)

    M = TILE_M*7
    N = TILE_N*5

    A = rng.random((M, N), dtype=np.float32)
    B = rng.random((M, N), dtype=np.float32)
    C = np.sin(A) + B

    A_grad = np.cos(A)
    B_grad = np.ones_like(B)

    A_wp = wp.array(A, requires_grad=True)
    B_wp = wp.array(B, requires_grad=True)
    C_wp = wp.zeros_like(A_wp, requires_grad=True)

    with wp.Tape() as tape:
        wp.launch(tile_binary_map, dim=[int(M/TILE_M), int(N/TILE_N)], inputs=[A_wp, B_wp, C_wp], tile_size=8)

    # verify forward pass
    assert(np.allclose(C, C_wp.numpy(), rtol=1.e-4))
    print("Binary map forward passed")

    # verify backward pass
    C_wp.grad = wp.ones_like(C_wp)
    tape.backward()

    assert(np.allclose(A_wp.grad.numpy(), A_grad))
    assert(np.allclose(B_wp.grad.numpy(), B_grad))
    
    print("Binary map backward passed")

test_tile_copy()
test_tile_unary_map()
test_tile_binary_map()


# @wp.kernel
# def gemm(A: wp.array2d(dtype=float),
#          B: wp.array2d(dtype=float),
#          C: wp.array2d(dtype=float)):

#     # output index
#     i, j = wp.tid()

#     sum = float(0.0)

#     for k in range(0, A.shape[1]):
#         sum += A[i, k]*B[k, j]

#     C[i, j] = sum



# TILE_M = wp.constant(64)
# TILE_N = wp.constant(64)
# TILE_K = wp.constant(8)

# @wp.kernel
# def gemm_tiled(A: wp.array2d(dtype=float),
#                B: wp.array2d(dtype=float),
#                C: wp.array2d(dtype=float)):

#     # output tile index
#     i, j = wp.tid()

#     sum = wp.tile_zeros(m=TILE_M, n=TILE_N, dtype=wp.float32)

#     M = A.shape[0]
#     N = B.shape[1]
#     K = A.shape[1]

#     count = int(K / TILE_K) # todo: must be the same as TILE_K

#     for k in range(count):

#         a = wp.tile_load(A, i, k, m=TILE_M, n=TILE_K)
#         b = wp.tile_load(B, k, j, m=TILE_K, n=TILE_N)

#         # sum += a*b
#         wp.tile_matmul(a, b, sum)

#     wp.tile_store(C, i, j, sum)


# s = 0.0

# for i, j in tile.shape:

#     s += tile[i-1, i-1]
#     s += tile[i, i-1]
#     s += tile[i,]



# M = TILE_M*7
# K = TILE_K*4
# N = TILE_N*6

# rng = np.random.default_rng(42)
# A = rng.random((M, K), dtype=np.float32)
# B = rng.random((K, N), dtype=np.float32)
# C = np.zeros((M, N), dtype=np.float32)

# A_wp = wp.array(A)
# B_wp = wp.array(B)
# C_wp = wp.array(C)

# iters = 10

# with wp.ScopedTimer("NumPy"):

#     for i in range(iters):
#         C = A@B

# wp.force_load(device="cuda:0")

# with wp.ScopedTimer("Warp", cuda_filter=wp.TIMING_KERNEL):

#     for i in range(iters):
#         wp.launch(gemm, dim=(M, N), inputs=[A_wp, B_wp, C_wp])


#     print(np.allclose(C, C_wp.numpy(), rtol=1.e-4))

#     for i in range(iters):
#         wp.launch(gemm_tiled, dim=(int(M/TILE_M), int(N/TILE_N)), inputs=[A_wp, B_wp, C_wp], tile_size=128)
#         wp.synchronize()


#     print(np.allclose(C, C_wp.numpy(), rtol=1.e-4))


# A_tc = torch.from_numpy(A).to("cuda:0")
# B_tc = torch.from_numpy(B).to("cuda:0")
# C_tc = torch.from_numpy(C).to("cuda:0")

# for i in range(10):
#     torch.matmul(A_tc, B_tc, out=C_tc)

# with wp.ScopedTimer("Torch"):

#     for i in range(iters):
#         torch.matmul(A_tc, B_tc, out=C_tc)

#     torch.cuda.synchronize()

    


