import os
from pytest import fixture, mark
import numpy as np
import xarray as xr
import matplotlib

from xyzpy.plot.color import convert_colors
from xyzpy.plot.plotter_matplotlib import lineplot
from xyzpy.plot.plotter_bokeh import ilineplot


DISPLAY_PRESENT = 'DISPLAY' in os.environ
no_display_msg = "No display found."
needs_display = mark.skipif(not DISPLAY_PRESENT, reason=no_display_msg)

matplotlib.use('Template')


@fixture
def dataset_3d():
    x = [1, 2, 3, 4, 5, 6, 8]
    z = [10, 20, 40, 80]
    d = np.random.rand(7, 4)
    ds = xr.Dataset()
    ds["x"] = x
    ds["z"] = z
    ds["y"] = (("x", "z"), d)
    return ds


@fixture
def dataset_heatmap():
    x = np.linspace(10, 20, 11)
    y = np.linspace(20, 40, 21)
    xx, yy = np.meshgrid(x, y)
    c = np.cos(((xx**2 + yy**2)**0.5) / 2)
    s = np.cos(((xx**2 + yy**2)**0.5) / 2)
    ds = xr.Dataset(
        coords={'x': x,
                'y': y},
        data_vars={'c': (('y', 'x'), c),
                   's': (('y', 'x'), s)})
    return ds.where(ds.y < 35)


@fixture
def dataset_scatter():
    x = np.random.randn(100, 100)
    y = np.random.randn(100, 100)
    z = np.random.randn(100)

    a = np.linspace(0, 3, 100)
    b = np.linspace(0, 3, 100)

    ds = xr.Dataset(
        coords={'a': a,
                'b': b},
        data_vars={'x': (('a', 'b'), x),
                   'y': (('a', 'b'), y),
                   'z': ('b', z)})
    return ds.where(ds.z > 0.5)


# --------------------------------------------------------------------------- #
# TEST COLORS                                                                 #
# --------------------------------------------------------------------------- #

class TestConvertColors:
    def test_simple(self):
        cols = [(1, 0, 0, 1), (0, 0.5, 0, 0.5)]
        new_cols = list(convert_colors(cols, outformat='BOKEH'))
        assert new_cols == [(255, 0, 0, 1), (0, 127, 0, 0.5)]


# --------------------------------------------------------------------------- #
# TEST PLOTTERS                                                               #
# --------------------------------------------------------------------------- #

@mark.parametrize("plot_fn", [lineplot, ilineplot])
class TestCommonInterface:
    @mark.parametrize("colors", [True, False, None])
    @mark.parametrize("markers", [True, False, None])
    def test_works_2d(self,
                      plot_fn,
                      dataset_3d,
                      colors,
                      markers):
        plot_fn(dataset_3d, "x", "y", "z", return_fig=True,
                colors=colors,
                markers=markers)

    @mark.parametrize("colormap", ['xyz', 'neon', 'viridis'])
    @mark.parametrize("colormap_log", [True, False])
    @mark.parametrize("colormap_reverse", [True, False])
    @mark.parametrize("string_z_coo", [True, False])
    def test_color_options(self,
                           plot_fn,
                           dataset_3d,
                           string_z_coo,
                           colormap,
                           colormap_log,
                           colormap_reverse):
        if string_z_coo:
            dataset_3d = dataset_3d.copy(deep=True)
            dataset_3d['z'] = ['a', 'b', 'c', 'd']
        plot_fn(dataset_3d, "x", "y", "z", return_fig=True,
                colors=True,
                colormap=colormap,
                colormap_log=colormap_log,
                colormap_reverse=colormap_reverse)

    @mark.parametrize("markers", [True, False, None])
    def test_works_1d(self,
                      plot_fn,
                      dataset_3d,
                      markers):
        plot_fn(dataset_3d.loc[{"z": 40}], "x", "y", return_fig=True,
                markers=markers)

    @mark.parametrize("padding", [None, 0.1])
    @mark.parametrize("xlims", [None, (0., 10.)])
    @mark.parametrize("ylims", [None, (-1., 1.)])
    def test_plot_range(self,
                        dataset_3d,
                        plot_fn,
                        padding,
                        xlims,
                        ylims):
        plot_fn(dataset_3d, "x", "y", "z", return_fig=True,
                padding=padding,
                xlims=xlims,
                ylims=ylims)

    @mark.parametrize("xlog", [None, True, False])
    @mark.parametrize("ylog", [None, True, False])
    @mark.parametrize("xticks", [None, (2, 3,)])
    @mark.parametrize("yticks", [None, (0.2, 0.3,)])
    @mark.parametrize("vlines", [None, (2, 3,)])
    @mark.parametrize("hlines", [None, (0.2, 0.3,)])
    def test_ticks_and_lines(self,
                             dataset_3d,
                             plot_fn,
                             xlog,
                             ylog,
                             xticks,
                             yticks,
                             vlines,
                             hlines):
        plot_fn(dataset_3d, "x", "y", "z", return_fig=True,
                xticks=xticks,
                yticks=yticks,
                vlines=vlines,
                hlines=hlines)

    def test_multi_var(self, plot_fn):
        # TODO: works
        # TODO: colors
        # TODO: labels
        # TODO: ytitle
        # TODO: padding, and lims
        pass


class TestHeatmap:
    def test_simple(self, dataset_heatmap):
        dataset_heatmap.xyz.heatmap('x', 'y', 'c', return_fig=True)


class TestScatter:

    def test_normal(self, dataset_scatter):
        dataset_scatter.xyz.scatter('x', 'y')
