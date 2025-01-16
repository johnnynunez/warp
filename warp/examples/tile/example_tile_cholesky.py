# Copyright (c) 2025 NVIDIA CORPORATION.  All rights reserved.
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

###########################################################################
# Example Tile Cholesky
#
# Shows how to write a simple kernel computing a Cholesky factorize and
# triangular solve using Warp Cholesky Tile APIs.
#
###########################################################################

import numpy as np

import warp as wp

wp.init()
wp.set_module_options({"enable_backward": False})

BLOCK_DIM = 128
TILE = 32

# Both should work
np_type, wp_type = np.float64, wp.float64
# np_type, wp_type = np.float32, wp.float32


@wp.kernel
def cholesky(
    A: wp.array2d(dtype=wp_type),
    L: wp.array2d(dtype=wp_type),
    X: wp.array2d(dtype=wp_type),
    Y: wp.array2d(dtype=wp_type),
):
    i, j, _ = wp.tid()

    a = wp.tile_load(A, i, j, m=TILE, n=TILE)
    l = wp.tile_cholesky(a)
    wp.tile_store(L, i, j, l)

    x = wp.tile_load(X, i, j, m=TILE, n=1)
    y = wp.tile_cholesky_solve(l, x)
    wp.tile_store(Y, i, j, y)


if __name__ == "__main__":
    wp.set_device("cuda:0")

    A_h = np.ones((TILE, TILE), dtype=np_type) + 5 * np.diag(np.ones(TILE), 0)
    L_h = np.zeros_like(A_h)

    A_wp = wp.array2d(A_h, dtype=wp_type)
    L_wp = wp.array2d(L_h, dtype=wp_type)

    X_h = np.arange(TILE, dtype=np_type).reshape((TILE, 1))
    Y_h = np.zeros_like(X_h)

    X_wp = wp.array2d(X_h, dtype=wp_type)
    Y_wp = wp.array2d(Y_h, dtype=wp_type)

    wp.launch_tiled(cholesky, dim=[1, 1], inputs=[A_wp, L_wp, X_wp, Y_wp], block_dim=BLOCK_DIM)

    L_np = np.linalg.cholesky(A_h)
    Y_np = np.linalg.solve(A_h, X_h)

    print("A:\n", A_h)
    print("L (Warp):\n", L_wp)
    print("L (Numpy):\n", L_np)

    print("x:\n", X_h)
    print("A\\n (Warp):\n", Y_wp.numpy())
    print("A\\x (Numpy):\n", Y_np)

    assert np.allclose(Y_wp.numpy(), Y_np) and np.allclose(L_wp.numpy(), L_np)

    print("Example Tile Cholesky passed")