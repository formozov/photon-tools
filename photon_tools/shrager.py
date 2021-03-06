# -*- coding: utf-8 -*-

from __future__ import division
import numpy as np
from numpy import sqrt, min, max, sum
from numpy.linalg import inv

"""
Deprecated.

This was originally written for the MEM FCS analysis but was found to
be quite unstable. Now we're just using a naive truncated Newton
method instead.
"""

def shrager(Q, g, C, x0, d, mu=1e-4):
    """
    Use Shrager's algorithm to minimize an objective of the form,

    :math:`\frac{1}{2} \langle x \vert Q \vert x \rangle - \langle g \vert x \rangle`

    under the linear inequality constraints :math:`\langle C \vert x \rangle \le d`.

    Note that the algorithm assumes that the matrix :math:`Q` is
    easily invertible, often being of the form,

    :math:`(\nabla f)^T (\nabla f) + \epsilon \mathrm{diag}\left[(\nabla f)^T (\nabla f)\right]`

    Follows

    :type Q: array of shape ``(n,n)``
    :param Q: Quadratic contribution
    :type g: array of shape ``(n,)``
    :param g: Linear contribution
    :type C: array of shape ``(n,n)``
    :param C: Inequality constraint matrix
    :type x0: array of shape ``(n,)``
    :type d: array of shape ``(n,)``
    :param d: Inequality constraint offsets
    :type mu: ``float``, optional
    :returns: In addition to the terminal iterate the routine returns
    a dictionary containing some state which can be used to verify the
    solution,

      * ``on_constraints``: A boolean array indicating which
        constraints the solution lies on (the ``True`` elements) and
        which of those it should fall within (the ``False`` elements)
    """

    l = Q.shape[0]
    assert Q.shape[1] == l
    assert g.shape == (l,)
    assert C.shape == (l,l)
    assert x0.shape == (l,)

    # Step 1
    Qinv = inv(Q)
    x = x0 + np.dot(Qinv, g)

    # Do we already have a solution?
    p = np.dot(C, x) - d
    if np.all(p <= 0):
        return (x, {})

    # Step 2
    R = np.dot(C, np.dot(Qinv, C.T))
    R += mu * np.diag(R)
    b = np.zeros(l, dtype=bool)
    lambd = np.zeros(l, dtype='f8')

    h = np.empty(l)

    while True:
        # Step 5
        dz_dlambd = p - np.dot(R, lambd)
        candidates = np.logical_and(b == False, dz_dlambd > 0)
        if not np.any(candidates):
            break # on to Step 6
        else:
            print('dz_dlambda', dz_dlambd)
            j = argmax_of(dz_dlambd, candidates)
            b[j] = True
            print(np.abs(h-lambd).max())
            print('set', j, b)
            h[:] = lambd

            while True:
                # Step 3
                Rs = R[b,:][:,b]
                lambd[b] = np.dot(inv(Rs), p[b])
                lambd[np.logical_not(b)] = 0

                # Step 4
                candidates = lambd < 0
                print('lambda', lambd)
                if np.any(candidates):
                    rho = h[candidates] / (h[candidates] - lambd[candidates])
                    print('rho', rho)
                    jj = np.argmin(rho)
                    j = np.argwhere(candidates)[jj]
                    b[j] = False
                    print('clear', j, b)
                    h[:] = (1 - rho[jj]) * h + rho[jj] * lambd
                else:
                    break # on to Step 5

    # Step 6
    Rs = R[b,:][:,b]
    lambd[b] = np.dot(inv(Rs), p[b] + mu * np.diag(Rs * lambd[b]))
    lambd[np.logical_not(b)] = 0
    info = {'on_constraints': b, 'lambda': lambd}
    x = x0 + np.dot(Qinv, g - np.dot(C[b,:].T, lambd[b]))
    return (x, info)

def argmax_of(arr, pred):
    """
    Return the index of the maximum element of ``arr`` limited to those elements where
    the corresponding element of ``pred`` is ``True``.

    :type arr: array of shape ``(n,)``
    :type pred: boolean array of shape ``(n,)``
    """
    idx = np.argmax(arr[pred])
    return np.argwhere(pred)[idx]

def test_case():
    x = shrager(Q = np.array([[1,0], [0,1]]),
                g = np.array([0,0]),
                C = np.array([[2.52, 1.57], [1.98,0]]),
                d = np.array([-41, -35]),
                mu = 0.02,
                x0 = np.array([0,0])
    )
    print('expected', [-17.6768, 0])
    print('computed', x)

if __name__ == '__main__':
    test_case()
