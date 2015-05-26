
import numpy as np

from math import pi

from fluidsim.operators.fft.easypyfft import FFTW3DReal2Complex


class OperatorsPseudoSpectral3D(object):
    """Provides fast Fourier transform functions and 3D operators.

    """

    @staticmethod
    def _complete_params_with_default(params):
        """This static method is used to complete the *params* container.
        """

        attribs = {'type_fft': type_fft,
                   'TRANSPOSED_OK': True,
                   'coef_dealiasing': 2./3,
                   'nx': 48,
                   'ny': 48,
                   'nz': 48,
                   'Lx': 2*pi,
                   'Ly': 2*pi,
                   'Lz': 2*pi}
        params._set_child('oper', attribs=attribs)

    def __init__(self, params=None, SEQUENTIAL=None):

        self.params = params

        nx = self.nx = params.oper.nx
        ny = self.ny = params.oper.ny
        nz = self.nz = params.oper.nz

        self.shape_phys = (nz, ny, nx)

        Lx = self.Lx = params.oper.Lx
        Ly = self.Ly = params.oper.Ly
        Lz = self.Lz = params.oper.Lz

        if nx % 2 != 0 or ny % 2 != 0 or nz % 2 != 0:
            raise ValueError('nx, ny and nz have to be even.')

        self._op_fft = FFTW3DReal2Complex(nx, ny, nz)

        self.ifft3d = self._op_fft.ifft3d
        self.fft3d = self._op_fft.fft3d

        kx_adim_max = nx/2
        ky_adim_max = ny/2
        kz_adim_max = nz/2

        self.nkx = kx_adim_max + 1
        self.nky = ny
        self.nkz = nz

        self.nk0 = self.nkz
        self.nk1 = self.nky
        self.nk2 = self.nkx

        self.shape_fft = (self.nk0, self.nk1, self.nk2)

        self.deltakx = 2*pi/Lx
        self.deltaky = 2*pi/Ly
        self.deltakz = 2*pi/Lz

        self.k0 = self.deltakz * np.r_[0:kz_adim_max+1, -kz_adim_max+1:0]
        self.k1 = self.deltakz * np.r_[0:ky_adim_max+1, -ky_adim_max+1:0]
        self.k2 = self.deltakx * np.arange(self.nk2)

        K1, K0, K2 = np.meshgrid(self.k1, self.k0, self.k2, copy=False)

        self.Kz = K0
        self.Ky = K1
        self.Kx = K2

        self.K_square_nozero = K0**2 + K1**2 + K2**2
        self.K_square_nozero[0, 0, 0] = 1e-14

    def project_perpk3d(self, vx_fft, vy_fft, vz_fft):

        Kx = self.Kx
        Ky = self.Ky
        Kz = self.Kz

        tmp = (Kx * vx_fft + Ky * vy_fft + Kz * vz_fft) / self.K_square_nozero

        return (vx_fft - Kx * tmp, vy_fft - Ky * tmp, vz_fft - Kz * tmp)

    def vgradv_from_v(self, vx, vy, vz, vx_fft=None, vy_fft=None, vz_fft=None):

        ifft3d = self.ifft3d

        if vx_fft is None:
            vx_fft = self.fft3d(vx)
            vy_fft = self.fft3d(vy)
            vz_fft = self.fft3d(vz)

        Kx = self.Kx
        Ky = self.Ky
        Kz = self.Kz

        px_vx_fft = 1j * Kx * vx_fft
        py_vx_fft = 1j * Ky * vx_fft
        pz_vx_fft = 1j * Kz * vx_fft

        px_vy_fft = 1j * Kx * vy_fft
        py_vy_fft = 1j * Ky * vy_fft
        pz_vy_fft = 1j * Kz * vy_fft

        px_vz_fft = 1j * Kx * vz_fft
        py_vz_fft = 1j * Ky * vz_fft
        pz_vz_fft = 1j * Kz * vz_fft

        vgradvx = (vx * ifft3d(px_vx_fft) +
                   vy * ifft3d(py_vx_fft) +
                   vz * ifft3d(pz_vx_fft))

        vgradvy = (vx * ifft3d(px_vy_fft) +
                   vy * ifft3d(py_vy_fft) +
                   vz * ifft3d(pz_vy_fft))

        vgradvz = (vx * ifft3d(px_vz_fft) +
                   vy * ifft3d(py_vz_fft) +
                   vz * ifft3d(pz_vz_fft))

        return vgradvx, vgradvy, vgradvz


if __name__ == '__main__':
    n = 4

    from fluidsim.base.params import Parameters
    p = Parameters(tag='params')
    p._set_child(
        'oper', {'nx': n, 'ny': n, 'nz': 2*n,
                 'Lx': 2*pi, 'Ly': 2*pi, 'Lz': 2*pi})

    oper = OperatorsPseudoSpectral3D(params=p)

    field = np.ones(oper.shape_phys)

    field_fft = oper.fft3d(field)

    assert field_fft.shape == oper.shape_fft

    oper.vgradv_from_v(field, field, field)

    oper.project_perpk3d(field_fft, field_fft, field_fft)
