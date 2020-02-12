import numpy as np
from matplotlib.text import Text
import pandas as pd
from cartopy.feature import NaturalEarthFeature
from cartopy.crs import Geodetic, EuroPP
from matplotlib.gridspec import GridSpec
import matplotlib.pyplot as plt

class TrajectoryBrowser(object):
    """
    Click on a ICAO code on the top left, (or unique Flight identifier) to select and highlight it
    On the right its ground track will be shown
    On the Bottom-left the Extra-feature chosen (alt, gs,...)
    """

    def __init__(self, X, extra_feature):

        self.fig = plt.figure()
        gs = GridSpec(2, 2, figure=self.fig)
        self.ax = self.fig.add_subplot(gs[0, 0])
        self.ax3 = self.fig.add_subplot(gs[1, 0])
        self.ax2 = self.fig.add_subplot(gs[:, 1], projection=EuroPP(), zorder=1)
        self.ax.set_ylim(0, 1)
        self.ax.set_xlim(0,0.4)
        self.ax.set_axis_off()
        self.ax2.set_aspect('auto')
        self.ax3.set_aspect('auto')

        self.X = X
        self.extra_feature = extra_feature
        self.test_list = self.X.index.get_level_values(0).unique()
        len_required = 0.05 * (self.test_list.shape[0] + 1)  # 0.2
        self.ys = np.linspace(0.07, len_required, num=len(self.test_list), endpoint=False)
        self.xs = np.ones(len(self.test_list)) * 0.05
        for i in range(0, len(self.test_list)):
            self.ax.text(self.xs[i], self.ys[i], self.test_list[i], ha= 'center', va= 'center',usetex=None, picker=True, clip_on=True) #todo: in case not clear bbox= dict(facecolor='red', alpha=0.5)

        #todo: if rows with single flights is present print also on screen

        self.lastind = 0

        self.icao = 0

        self.text = self.ax.text(-0.2, 0.95, 'selected: none',
                            transform=self.ax.transAxes, va='top')
        self.selected, = self.ax.plot([self.xs[0]], [self.ys[0]], '_', ms=50, alpha=1,
                                 color='yellow', visible=False)



    def fig(self):
        return self.fig

    def onpress(self, event):
        if self.lastind is None:
            return
        if event.key not in ('n', 'p'):
            return
        if event.key == 'n':
            inc = 1
        else:
            inc = -1

        self.lastind += inc
        self.lastind = np.clip(self.lastind, 0, len(self.xs) - 1)
        self.update()

    def onpick(self, event):

        if isinstance(event.artist, Text):
            text = event.artist

        self.icao = text.get_text()
        self.lastind = np.where(self.test_list==self.icao)[0]
        self.update()

    def update(self):
        if self.lastind is None:
            return

        dataind = self.X.loc[self.icao]
        dataind = dataind.reset_index()  # todo modificare

        self.ax2.cla()
        land = NaturalEarthFeature(
            category='cultural',
            name='admin_0_countries',
            scale='10m',
            facecolor='none',
            edgecolor='#524c50', alpha=0.2)

        self.ax2.add_feature(land, zorder=2)

        #todo: actual of Schipol are 3.4, 5.41 (3.2 e 5.8)
        self.ax2.set_extent((3.2, 5.8, 51, 54))

        self.ax2.plot(dataind.loc[:,'lon'], dataind.loc[:,'lat'], zorder=4, transform=Geodetic())

        self.selected.set_visible(True)
        self.selected.set_data(self.xs[self.lastind], self.ys[self.lastind])

        self.text.set_text('selected: ' + self.icao)
        self.ax3.cla()
        self.ax3.set_aspect('auto')
        self.ax3.plot(dataind.loc[:,'ts'], dataind.loc[:,self.extra_feature])
        self.fig.canvas.draw()


