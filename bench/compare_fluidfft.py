#!/usr/bin/env python
"""
python simul_profile.py
mpirun -np 8 python simul_profile.py

with gprof2dot and graphviz (command dot):

gprof2dot -f pstats profile.pstats | dot -Tpng -o profile.png

"""

from fluidsim.solvers.ns2d.solver import Simul as Simul
from fluidsim.solvers.ns2d.solver_fluidfft import Simul as SimulFluidfft

params = Simul.create_default_params()

params.short_name_type_run = 'profile'

nh = 512
params.oper.nx = nh
params.oper.ny = nh
Lh = 6.
params.oper.Lx = Lh
params.oper.Ly = Lh

params.oper.coef_dealiasing = 2./3

params.FORCING = True
params.forcing.type = 'tcrandom'
params.forcing.nkmax_forcing = 5
params.forcing.nkmin_forcing = 4
params.forcing.forcing_rate = 1.


delta_x = Lh/nh
params.nu_8 = 2.*10e-1*params.forcing.forcing_rate**(1./3)*delta_x**8

try:
    params.f = 1.
    params.c2 = 200.
except (KeyError, AttributeError):
    pass

params.time_stepping.deltat0 = 1.e-4
params.time_stepping.USE_CFL = False

params.time_stepping.it_end = 10
params.time_stepping.USE_T_END = False

params.oper.type_fft = 'FFTWCY'

params.output.periods_print.print_stdout = 0

params.output.HAS_TO_SAVE = True
params.output.periods_save.phys_fields = 0.1
params.output.periods_save.spatial_means = 0.1
params.output.periods_save.spectra = 0.1
# params.output.periods_save.spect_energy_budg = 0.
# params.output.periods_save.increments = 0.


sim = Simul(params)



import pstats
import cProfile

cProfile.runctx('sim.time_stepping.start()',
                globals(), locals(), 'profile.pstats')


# params.oper.type_fft = 'fft2d.mpi_with_fftw1d'
# params.oper.type_fft = 'mpi_with_fftwmpi2d'
# params.oper.type_fft = 'with_cufft'

params2 = SimulFluidfft.create_default_params()
params.oper.type_fft = params2.oper.type_fft

params.short_name_type_run = 'profile2'

sim_fluidfft = SimulFluidfft(params)

cProfile.runctx('sim_fluidfft.time_stepping.start()',
                globals(), locals(), 'profile_fluidfft.pstats')

if sim.oper.rank == 0:
    s = pstats.Stats('profile.pstats')
    s.strip_dirs().sort_stats('time').print_stats(10)

    s = pstats.Stats('profile_fluidfft.pstats')
    s.strip_dirs().sort_stats('time').print_stats(10)

    print(
        'with gprof2dot and graphviz (command dot):\n'
        'gprof2dot -f pstats profile.pstats | dot -Tpng -o profile.png\n'
        'gprof2dot -f pstats profile_fluidfft.pstats | dot -Tpng -o profile_fluidfft.png')
