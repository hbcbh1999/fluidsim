"""Operators finite differences (:mod:`fluidsim.operators.op_finitediff`)
===============================================================================

.. currentmodule:: fluidsim.operators.op_finitediff

Provides:

.. autoclass:: OperatorFiniteDiff1DPeriodic
   :members:
   :private-members:

.. autoclass:: OperatorFiniteDiff2DPeriodic
   :members:
   :private-members:

"""
import numpy as np
import scipy.sparse as sparse


class OperatorFiniteDiff1DPeriodic(object):

    @staticmethod
    def _complete_params_with_default(params):
        """This static method is used to complete the *params* container.
        """
        attribs = {'nx': 48, 'Lx': 8.}
        params.set_child('oper', attribs=attribs)

    def __init__(self, params=None):

        if not params.ONLY_COARSE_OPER:
            nx = int(params.oper.nx)
        else:
            nx = 4

        Lx = float(params.oper.Lx)

        print(nx, Lx)
        
        self.nx = nx
        self.size = nx
        self.shape = [nx]
        self.shapeX_loc = self.shape
        self.Lx = Lx
        self.deltax = Lx/nx
        dx = self.deltax

        self.xs = np.linspace(0, Lx, nx)

        self.sparse_px = sparse.diags(
            diagonals=[-np.ones(nx-1), np.ones(nx-1), -1, 1],
            offsets=[-1, 1, nx-1, -(nx-1)])
        self.sparse_px = self.sparse_px/(2*dx)

        self.sparse_pxx = sparse.diags(
            diagonals=[np.ones(nx-1), -2*np.ones(nx), np.ones(nx-1), 1, 1],
            offsets=[-1, 0, 1, nx-1, -(nx-1)])

        self.sparse_pxx = self.sparse_pxx/dx**2

    def px(self, a):
        return self.sparse_px.dot(a.flat)

    def pxx(self, a):
        return self.sparse_pxx.dot(a.flat)

    def identity(self):
        return sparse.identity(self.size)

    def produce_str_describing_oper(self):
        """Produce a string describing the operator."""
        if (self.Lx/np.pi).is_integer():
            str_Lx = repr(int(self.Lx/np.pi)) + 'pi'
        else:
            str_Lx = '{:.3f}'.format(self.Lx).rstrip('0')

        return ('L='+str_Lx+'_{}').format(self.nx)

    def produce_long_str_describing_oper(self):
        """Produce a string describing the operator."""
        if (self.Lx/np.pi).is_integer():
            str_Lx = repr(int(self.Lx/np.pi)) + 'pi'
        else:
            str_Lx = '{:.3f}'.format(self.Lx).rstrip('0')
        return (
            'Finite difference operator 1D,\n'
            'nx = {0:6d}\n'.format(self.nx) +
            'Lx = ' + str_Lx + '\n')


class OperatorFiniteDiff2DPeriodic(OperatorFiniteDiff1DPeriodic):

    @staticmethod
    def _complete_params_with_default(params):
        """This static method is used to complete the *params* container.
        """

        attribs = {'nx': 48,
                   'ny': 48,
                   'Lx': 8,
                   'Ly': 8}
        params.set_child('oper', attribs=attribs)

    def __init__(self, params=None):

        Lx = float(params.oper.Lx)
        Ly = float(params.oper.Ly)

        if not params.ONLY_COARSE_OPER:
            nx = int(params.oper.nx)
            ny = int(params.oper.ny)
        else:
            nx = 4
            ny = 4

        self.nx = nx
        self.ny = ny
        self.shape = [ny, nx]
        size = nx*ny
        self.size = size
        self.Lx = Lx
        self.Ly = Ly
        self.deltax = Lx/nx
        self.deltay = Ly/ny
        dx = self.deltax
        dy = self.deltay

        self.xs = np.linspace(0, Lx, nx)
        self.ys = np.linspace(0, Ly, ny)

        def func_i1_mat(i0_mat, iv):
            i1 = i0_mat % nx
            i0 = i0_mat // nx
            if iv == 0:
                i1_mat = i0*nx + (i1+1) % nx
            elif iv == 1:
                i1_mat = i0*nx + (i1-1) % nx
            else:
                raise ValueError('Shouldn''t be here...')
            return i1_mat

        values = np.array([1, -1])/(2*dx)
        self.sparse_px = self._create_sparse(values, func_i1_mat)

        def func_i1_mat(i0_mat, iv):
            i1 = i0_mat % nx
            i0 = i0_mat // nx
            if iv == 0:
                i1_mat = i0_mat
            elif iv == 1:
                i1_mat = i0*nx + (i1+1) % nx
            elif iv == 2:
                i1_mat = i0*nx + (i1-1) % nx
            else:
                raise ValueError('Shouldn''t be here...')
            return i1_mat

        values = np.array([-2, 1, 1])/dx**2
        self.sparse_pxx = self._create_sparse(values, func_i1_mat)

        def func_i1_mat(i0_mat, iv):
            i1 = i0_mat % nx
            i0 = i0_mat // nx
            if iv == 0:
                i1_mat = ((i0+1)*nx) % size + i1
            elif iv == 1:
                i1_mat = ((i0-1)*nx) % size + i1
            else:
                raise ValueError('Shouldn''t be here...')
            return i1_mat

        values = np.array([1, -1])/(2*dy)
        self.sparse_py = self._create_sparse(values, func_i1_mat)

        def func_i1_mat(i0_mat, iv):
            i1 = i0_mat % nx
            i0 = i0_mat // nx
            if iv == 0:
                i1_mat = i0_mat
            elif iv == 1:
                i1_mat = ((i0+1)*nx) % size + i1
            elif iv == 2:
                i1_mat = ((i0-1)*nx) % size + i1
            else:
                raise ValueError('Shouldn''t be here...')
            return i1_mat

        values = np.array([-2, 1, 1])/dx**2
        self.sparse_pyy = self._create_sparse(values, func_i1_mat)

    def _create_sparse(self, values, func_i1_mat):
        size = self.size
        nb_values = len(values)
        data = np.empty(size*nb_values)
        i0s = np.empty(size*nb_values)
        i1s = np.empty(size*nb_values)

        for i0_mat in xrange(size):
            for iv, v in enumerate(values):
                data[nb_values*i0_mat+iv] = v
                i0s[nb_values*i0_mat+iv] = i0_mat
                i1s[nb_values*i0_mat+iv] = func_i1_mat(i0_mat, iv)
        return sparse.coo_matrix(
            (data, (i0s, i1s)), shape=(size, size))

    def py(self, a):
        return self.sparse_py.dot(a.flat)

    def pyy(self, a):
        return self.sparse_pyy.dot(a.flat)

    def produce_str_describing_oper(self):
        """Produce a string describing the operator."""
        if (self.Lx/np.pi).is_integer():
            str_Lx = repr(int(self.Lx/np.pi)) + 'pi'
        else:
            str_Lx = '{:.3f}'.format(self.Lx).rstrip('0')
        if (self.Ly/np.pi).is_integer():
            str_Ly = repr(int(self.Ly/np.pi)) + 'pi'
        else:
            str_Ly = '{:.3f}'.format(self.Ly).rstrip('0')
        return ('L='+str_Lx+'x'+str_Ly+'_{}x{}').format(
            self.nx, self.ny)

    def produce_long_str_describing_oper(self):
        """Produce a string describing the operator."""
        if (self.Lx/np.pi).is_integer():
            str_Lx = repr(int(self.Lx/np.pi)) + 'pi'
        else:
            str_Lx = '{:.3f}'.format(self.Lx).rstrip('0')
        if (self.Ly/np.pi).is_integer():
            str_Ly = repr(int(self.Ly/np.pi)) + 'pi'
        else:
            str_Ly = '{:.3f}'.format(self.Ly).rstrip('0')
        return (
            'Finite difference operator 2D,\n'
            'nx = {0:6d} ; ny = {1:6d}\n'.format(self.nx, self.ny) +
            'Lx = ' + str_Lx + ' ; Ly = ' + str_Ly + '\n')


if __name__ == '__main__':
    nx = 3
    ny = 3
    oper = OperatorFiniteDiff2DPeriodic([ny, nx], [nx/2., ny/2.])
    a = np.arange(nx*ny).reshape([ny, nx])
