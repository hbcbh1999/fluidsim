import os
import matplotlib.pyplot as plt
from matplotlib import animation
from fluiddyn.util import mpi
from fluiddyn.io import FLUIDSIM_PATH, FLUIDDYN_PATH_SCRATCH,stdout_redirected
from fluidsim.util.util import pathdir_from_namedir, load_state_phys_file

class MoviesBase(object):
    
    def _set_path(self):
        """
        Sets path attribute specifying the location of saved files.
        Tries different directories int the following order:
        FLUIDSIM_PATH, FLUIDDYN_PATH_SCRATCH, output.path_run
        
        .. TODO:Need to check if pathdir_from_namedir call is reqd.
        """
        self.path = os.path.join(FLUIDSIM_PATH, self.sim.name_run)
        
        if not os.path.exists(self.path):
            self.path = os.path.join(
                FLUIDDYN_PATH_SCRATCH, self.sim.name_run)
            if not os.path.exists(self.path):
                self.path = self.output.path_run
                if not os.path.exists(self.path):
                    self.path = None
        
        self.path = pathdir_from_namedir(self.path)

    def _set_font(self, family='serif', size=12):
        """
        Use to set font attribute. May be either an alias (generic name is CSS parlance), such as 
        serif, sans-serif, cursive, fantasy, or monospace, a real font name or a list of real font names.
        """

        self.font = {'family': family,
                'color': 'black',
                'weight': 'normal',
                'size': size,
                }
        

    def _ani_get_field(self, time):
        """
        Loads a saved file corresponding to an approx. time, and
        returns contour data
        """
        #sim_temp = load_state_phys_file(self.path, t_approx=time)
        #self.sim.init_fields.get_state_from_simul(sim_temp)
        self.sim = load_state_phys_file(self.path, t_approx=time)

        return self._select_field()
    
    def _select_field(self, field=None, key_field=None):
        """
        Once a saved file is loaded, this selects the field and mpi-gathers.
        
        Returns
        -------
        field : nd array
        key_field : string
        """
        raise NotImplementedError('_select_field function declaration missing')
    
        
    def animate(self, numfig=None, nb_contours=10, frame_dt=300, file_dt=0.1, xmax=None, ymax=None, save_file=None):
        """
        Load the key field from multiple save files and display as
        an animated plot.

        Parameters
        ----------
        numfig : Figure number on the window  eg: Figure 1
        frame_dt : Interval between animated frames in milliseconds
        file_dt : Approx. interval between saved files to load
        
        .. TODO: Use FuncAnimation with blit=True option.
        """

        if mpi.nb_proc > 1:
            raise ValueError('Do NOT use this script with MPI !\n'
                           'The MPI version of get_state_from_simul()\n'
                             'is not implemented.')
 
        self._ani_init(numfig, nb_contours, file_dt, xmax, ymax)
        self._animation = animation.FuncAnimation(self._ani_fig, self._ani_update, self._ani_t,
                                                   interval=frame_dt, blit=False)

        if save_file is not None:
            self._ani_save(save_file, frame_dt) 
    
    def _ani_init(self):
        pass
    
    def _ani_update(self):
        pass
      
    def _ani_save(self, filename=r'movie.avi', frame_dt=300):
        try:
            Writer = animation.writers['ffmpeg']
        except KeyError:
            Writer = animation.writers['mencoder']
        
        print 'Saving movie to ',filename,'...'
        writer = Writer(
            fps=1000. / frame_dt, metadata=dict(artist='Me'), bitrate=1800)
        self._animation.save(filename, writer=writer)  # _animation_ is a FuncAnimation object


class MoviesBase1D(MoviesBase):

    def _ani_init(self, numfig, nb_contours, file_dt, xmax, ymax):
        """
        Initializes animated fig. and list of times of save files to load
        """
        self._ani_fig, self._ani_ax = plt.subplots()
        self._ani_line, = self._ani_ax.plot([], [])
        self._ani_t = []
        self._set_font()
        self._set_path()

        ax = self._ani_ax
        ax.set_xlabel('x', fontdict=self.font)
        ax.set_ylabel('u', fontdict=self.font)
        ax.set_xlim(0, xmax)
        ax.set_ylim(-ymax, ymax)

        t = 0
        tmax = int(self.sim.time_stepping.t)
        while t <= tmax:
            self._ani_t.append(t)
            t += file_dt

    def _ani_update(self, time):
        """
        Loads contour data and updates figure
        """

        x = self.oper.x_seq
        with stdout_redirected():
            y, key_field = self._ani_get_field(time)

        self._ani_line.set_data(x, y)
        title = (key_field +
                 ', t = {0:.3f}, '.format(self.sim.time_stepping.t) +
                 self.output.name_solver +
                 ', nh = {0:d}'.format(self.params.oper.nx))
        self._ani_ax.set_title(title)
        
        return self._ani_line


class MoviesBase2D(MoviesBase):

    def _ani_init(self, numfig, nb_contours, file_dt, xmax=None, ymax=None):
        """
        Initializes animated fig. and list of times of save files to load
        """
        self._ani_nbc = nb_contours
        self._ani_t = []
        self._set_font()
        self._set_path()


        x_left_axe = 0.08
        z_bottom_axe = 0.07
        width_axe = 0.87
        height_axe = 0.87
        size_axe = [x_left_axe, z_bottom_axe,
                    width_axe, height_axe]

        if mpi.rank == 0:
            self._ani_fig, self._ani_ax = self.output.figure_axe(numfig=numfig,
                                                                   size_axe=size_axe)

        t = 0
        tmax = int(self.sim.time_stepping.t)
        while t <= tmax:
            self._ani_t.append(t)
            t += file_dt

    def _ani_update(self, time):
        """
        Loads contour data and updates figure
        
        .. TODO: Set contour limits, without which animations can be misleading
        """

        x = self.oper.x_seq
        y = self.oper.y_seq
        with stdout_redirected():
            field, key_field = self._ani_get_field(time)

        contours = self._ani_ax.contourf(x, y, field, self._ani_nbc, cmap=plt.cm.jet)

        
        # self._ani_fig.colorbar(contours)
        self._ani_fig.contours = contours
        title = (key_field +
                 ', t = {0:.3f}, '.format(self.sim.time_stepping.t) +
                 self.output.name_solver +
                 ', nh = {0:d}'.format(self.params.oper.nx))
        
        try:
            vmax = self._quiver_plot(self._ani_ax)
            title += r', max(|v|) = {0:.3f}'.format(vmax)
        except:
            pass
        
        self._ani_ax.set_title(title)
        return contours
