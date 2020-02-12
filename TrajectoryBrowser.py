import numpy as np
from matplotlib.text import Text
import pandas as pd
from cartopy.feature import NaturalEarthFeature
from cartopy.crs import Geodetic, EuroPP
from matplotlib.gridspec import GridSpec
import matplotlib.pyplot as plt
from matplotlib.widgets import TextBox, RadioButtons
import matplotlib.style as mplstyle

mplstyle.use('fast')


# matplotlib.rc('text', usetex=False)
# matplotlib.use('GTK3Cairo')
# ['GTK3Agg', 'GTK3Cairo', 'MacOSX', 'nbAgg', 'Qt4Agg', 'Qt4Cairo', 'Qt5Agg', 'Qt5Cairo', 'TkAgg', 'TkCairo',
# 'WebAgg', 'WX', 'WXAgg', 'WXCairo', 'agg', 'cairo', 'pdf', 'pgf', 'ps', 'svg', 'template']


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
        self.ax.set_xlim(0, 0.4)
        self.ax.set_axis_off()
        self.ax2.set_aspect('auto')
        self.ax3.set_aspect('auto')
        axbox = plt.axes([0.6, 0.02, 0.3, 0.05])
        initial_text = "40666B"
        self.text_box = TextBox(axbox, 'ICAO', initial=initial_text)

        # rax = plt.axes([0.05, 0.7, 0.15, 0.15], )
        # radio = RadioButtons(rax, (X.index.get_level_values(0).unique()))

        self.X = X
        self.dataind = 0
        self.extra_feature = extra_feature
        self.test_list = self.X.index.get_level_values(0).unique()  # [0:80]
        len_required = 0.05 * (self.test_list.shape[0] + 1)  # 0.2
        self.ys = np.linspace(0.07, len_required, num=self.test_list.shape[0], endpoint=False)
        self.xs = np.ones(self.test_list.shape[0]) * 0.05
        self.list_all_text = []
        for i in range(0, self.test_list.shape[0]):
            if self.ys[i] < 1:
                element = self.ax.text(self.xs[i], self.ys[i], self.test_list[i], ha='center', va='center', picker=True,
                                       clip_on=True)  # todo: in case not clear bbox= dict(facecolor='red', alpha=0.5)
                fid_icao = self.X.loc[self.test_list[i], :].loc[:, 'fid'].unique()
                x_fid = np.linspace(0.1, (fid_icao.shape[0] + 1) * 0.05, num=fid_icao.shape[0], endpoint=False)
                self.list_all_text.append(element)
                for j in range(0, fid_icao.shape[0]):  # todo: update when new fid is implemented + legend
                    element2 = self.ax.text(x_fid[j], self.ys[i], fid_icao[j], ha='left', va='center',
                                            picker=True, clip_on=True)
                    self.list_all_text.append(element2)
            else:
                element3 = self.ax.text(self.xs[i], self.ys[i], self.test_list[i], ha='center', va='center',
                                        picker=True,
                                        clip_on=True,
                                        visible=False)  # todo: in case not clear bbox= dict(facecolor='red', alpha=0.5)
                self.list_all_text.append(element3)
                fid_icao = self.X.loc[self.test_list[i], :].loc[:, 'fid'].unique()
                x_fid = np.linspace(0.1, (fid_icao.shape[0] + 1) * 0.05, num=fid_icao.shape[0], endpoint=False)
                for j in range(0, fid_icao.shape[0]):  # todo: update when new fid is implemented + legend
                    element4 = self.ax.text(x_fid[j], self.ys[i], fid_icao[j], ha='left', va='center',
                                            picker=True, clip_on=True, visible=False)
                    self.list_all_text.append(element4)

        self.lastind = 0

        self.icao = 0
        self.fid = 0

        self.text = self.ax.text(-0.2, 0.95, 'selected: none',
                                 transform=self.ax.transAxes, va='top')
        self.selected, = self.ax.plot([self.xs[0]], [self.ys[0]], '_', ms=50, alpha=1,
                                      color='yellow', visible=False)

        self.fig.canvas.mpl_connect('pick_event', self.onpick)
        self.text_box.on_submit(self.submit)
        self.ax.callbacks.connect('ylim_changed', self.on_ylims_change)
        plt.show()

    def submit(self, text):

        self.icao = text
        self.lastind = np.where(self.test_list == self.icao)[0]
        self.update()

        return text

    def on_ylims_change(self, axes):
        for i in self.list_all_text:
            limits_y = self.ax.get_ylim()
            if limits_y[0] - 0.2 < i._y < limits_y[1] + 0.2:
                i.set_visible(True)
            else:
                i.set_visible(False)

    def onpick(self, event):

        if isinstance(event.artist, Text):
            text = event.artist

            if np.where(self.test_list == text.get_text())[0].shape[0] > 0:
                self.icao = text.get_text()
                self.lastind = np.where(self.test_list == self.icao)[0]
                self.update()
            else:
                self.fid = text  # todo:maybe update all with this method
                self.dataind = self.X.loc[self.X.loc[:, 'fid'] == self.fid.get_text()]
                self.icao = self.dataind.index.unique().values[0][0]
                self.update_fid()

    def update(self):

        dataind = self.X.loc[self.icao]
        dataind = dataind.reset_index()

        self.ax2.cla()
        land = NaturalEarthFeature(
            category='cultural',
            name='admin_0_countries',
            scale='10m',
            facecolor='none',
            edgecolor='#524c50', alpha=0.2)

        self.ax2.add_feature(land, zorder=2)

        # todo: actual of Schipol are 3.4, 5.41 (3.2 e 5.8)
        self.ax2.set_extent((3.2, 5.8, 51, 54))

        self.ax2.plot(dataind.loc[:, 'lon'], dataind.loc[:, 'lat'], zorder=4, transform=Geodetic())
        # todo:add different color depending on trajectory
        self.selected.set_visible(True)
        self.selected.set_data(self.xs[self.lastind], self.ys[self.lastind])

        self.text.set_text('selected: ' + self.icao)
        self.ax3.cla()  # todo: add correct units depending on featuer
        self.ax3.set_aspect('auto')
        self.ax3.plot(dataind.loc[:, 'ts'], dataind.loc[:, self.extra_feature])
        self.fig.canvas.draw()

    def update_fid(self):

        self.dataind = self.dataind.reset_index()

        self.ax2.cla()
        land = NaturalEarthFeature(
            category='cultural',
            name='admin_0_countries',
            scale='10m',
            facecolor='none',
            edgecolor='#524c50', alpha=0.2)

        self.ax2.add_feature(land, zorder=2)

        # todo: actual of Schipol are 3.4, 5.41 (3.2 e 5.8)
        self.ax2.set_extent((3.2, 5.8, 51, 54))

        self.ax2.plot(self.dataind.loc[:, 'lon'], self.dataind.loc[:, 'lat'], zorder=4, transform=Geodetic())
        # todo:add different color depending on trajectory
        self.selected.set_visible(True)
        self.selected.set_data(self.fid._x, self.fid._y)

        self.text.set_text('selected: ' + self.fid.get_text())
        self.ax3.cla()  # todo: add correct units depending on featuer
        self.ax3.set_aspect('auto')
        self.ax3.plot(self.dataind.loc[:, 'ts'], self.dataind.loc[:, self.extra_feature])
        self.fig.canvas.draw()


