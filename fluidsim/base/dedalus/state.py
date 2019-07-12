"""State of the variables (:mod:`fluidsim.base.dedalus.state`)
===============================================================

Provides:

.. autoclass:: StateDedalus
   :members:
   :private-members:

"""


from ..state import StateBase


class StatePhysDedalus:
    def __init__(self, dedalus_solver, keys):
        self.dedalus_solver = dedalus_solver
        self.keys = keys

    def get_var(self, key):
        return self.dedalus_solver.state[key]["g"]

    def set_var(self, key, value):
        self.dedalus_solver.state[key]["g"][:] = value

    def initialize(self, value):
        for key in self.keys:
            self.get_var(key).fill(value)

    @property
    def nbytes(self):
        return 1

    @property
    def info(self):
        return "Dedalus state"


class StateDedalus(StateBase):
    @staticmethod
    def _complete_info_solver(info_solver):
        """Complete the ParamContainer info_solver.

        This is a static method!
        """
        info_solver.classes.State._set_attribs(
            {
                "keys_state_phys": ["b", "vx", "vz"],
                "keys_computable": [],
                "keys_phys_needed": ["b", "vx", "vz"],
            }
        )

    def compute(self, key):
        """Compute scalar fields such a component of the velocity or vorticity."""
        return self.get_var(key)

    def __init__(self, sim, oper=None):
        super().__init__(sim, oper)
        sim.init_dedalus()
        self.state_phys = StatePhysDedalus(self.sim.dedalus_solver, self.keys_state_phys)
