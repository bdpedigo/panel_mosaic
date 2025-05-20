from pathlib import Path
from typing import Any, Union

import cairosvg
import matplotlib.pyplot as plt
import skunk


def _label_axes(
    axs,
    label_mapping: dict[str, str] = None,
    fontsize: int = 30,
    label_pos: tuple[float, float] = (0.0, 1.0),
    horizontalalignment: str = "left",
    verticalalignment: str = "top",
) -> None:
    for label, ax in axs.items():
        ax.autoscale(False)
        if label_mapping is not None:
            if label in label_mapping:
                label = label_mapping[label]
        ax.text(
            *label_pos,
            label + "",
            horizontalalignment=horizontalalignment,
            verticalalignment=verticalalignment,
            transform=ax.transAxes,
            fontsize=fontsize,
            clip_on=False,
        )
        ax.set(xticks=[], yticks=[])


def _ax_off(ax, panel_borders: bool = False) -> None:
    ax.set(xticks=[], yticks=[])
    if not panel_borders:
        ax.spines[["left", "right", "top", "bottom"]].set_visible(False)


class PanelMosaic:
    def __init__(
        self,
        mosaic: Any,
        figsize=(10, 8),
        layout="tight",
        gridspec_kw=None,
        panel_borders=False,
    ):
        self.mosaic = mosaic
        self.figsize = figsize
        self.layout = layout
        self.panel_borders = panel_borders

        if gridspec_kw is None:
            self.gridspec_kw = dict(hspace=0.0, wspace=0.0)

        self.fig, self.axs = self._set_up_axes()
        self._format_axes()

        self.panel_mapping = None

        # self._svg = skunk.pltsvg(self.fig)

    @property
    def svg(self):
        for label in self.svg_panel_mapping.keys():
            skunk.connect(self.axs[label], label)
        svg = skunk.insert(self.svg_panel_mapping)
        return svg

    def _set_up_axes(self):
        # ioff/ion is to avoid displaying the matplotlib figure in notebooks, which
        # will just look like a bunch of blue boxes
        plt.ioff()
        fig, axs = plt.subplot_mosaic(
            mosaic=self.mosaic,
            figsize=self.figsize,
            layout=self.layout,
            gridspec_kw=self.gridspec_kw,
        )
        plt.ion()
        return fig, axs

    def label_axes(
        self,
        label_mapping: dict[str, str] = None,
        fontsize: int = 30,
        label_pos: tuple[float, float] = (0.0, 1.0),
        horizontalalignment: str = "left",
        verticalalignment: str = "top",
    ) -> None:
        """
        Label the axes of the figure with the panel labels.

        Parameters
        ----------
        fontsize :
            The fontsize of the panel labels.
        label_pos :
            The position of the panel labels. This is a tuple of two floats, where the
            first float is the x position and the second float is the y position.
            Coordinates are interpreted in axis space, where (0, 0) is the bottom left
            and (1, 1) is the top right.
        horizontalalignment :
            The horizontal alignment of the panel labels.
        verticalalignment :
            The vertical alignment of the panel labels.
        """
        _label_axes(
            self.axs,
            label_mapping=label_mapping,
            fontsize=fontsize,
            label_pos=label_pos,
            horizontalalignment=horizontalalignment,
            verticalalignment=verticalalignment,
        )

    def _format_axes(self, panel_borders: bool = False) -> None:
        """
        Format the axes of the figure.

        Parameters
        ----------
        panel_borders :
            Whether to display borders around the panels.
        """
        for _, ax in self.axs.items():
            _ax_off(ax, panel_borders)

    def map(self, panel_mapping: dict) -> None:
        """
        Map panel images from specified file paths.

        Parameters
        ----------
        panel_mapping :
            A dictionary mapping panel labels to file paths of panel images.
        """
        fixed_panel_mapping = {}
        for label, path in panel_mapping.items():
            if isinstance(path, Path):
                fixed_panel_mapping[label] = str(path)
            else:
                fixed_panel_mapping[label] = path
        panel_mapping = fixed_panel_mapping

        self.panel_mapping = panel_mapping

        png_panel_mapping = {}
        for label, path in panel_mapping.items():
            if path.endswith(".png"):
                png_panel_mapping[label] = path
        self.png_panel_mapping = png_panel_mapping

        for label, path in png_panel_mapping.items():
            with open(path, "rb") as f:
                img = plt.imread(f)
                new_ax = self.axs[label].inset_axes([0.01, 0.01, 0.98, 0.98], zorder=-1)
                new_ax.imshow(img, interpolation="none", aspect=None)
                _ax_off(new_ax)

        svg_panel_mapping = {}
        for label, path in panel_mapping.items():
            if path.endswith(".svg"):
                svg_panel_mapping[label] = path
        self.svg_panel_mapping = svg_panel_mapping

        # for label in svg_panel_mapping.keys():
        #     skunk.connect(self.axs[label], label)
        # self.axs[label].set_axis_on()

        # self.svg = skunk.insert(svg_panel_mapping)

        # for ax in self.axs.values():
        #     ax.set_axis_on()

    def __repr__(self) -> str:
        rep = ""
        rep += PanelMosaic.__name__ + "(\n"
        rep += f"    fig={self.fig.__repr__()},\n"
        rep += f"    axs={self.axs.__repr__()},\n"
        rep += f"    panel_mapping={self.panel_mapping.__repr__()},\n"
        rep += ")"
        return rep

    def _repr_pretty_(self, p, cycle):
        # simply show the plot
        """A convenience function to dispaly SVG string in Jupyter Notebook"""
        import base64

        import IPython.display as display

        data = base64.b64encode(self.svg.encode("utf8"))
        display.display(
            display.HTML("<img src=data:image/svg+xml;base64," + data.decode() + ">")
        )

    def show(self) -> None:
        """
        Display the figure.

        This function is useful for displaying the figure in a Jupyter notebook.
        """
        skunk.display(self.svg)

    def _get_dummy_axes(self):
        return self.fig.copy(), self.axs.copy()

    def get_axis_sizes(self):
        sizes = {}
        for label, ax in self.axs.items():
            bbox = ax.get_window_extent().transformed(
                self.fig.dpi_scale_trans.inverted()
            )
            width, height = bbox.width, bbox.height
            sizes[label] = (width, height)
        return sizes

    def show_dummies(self, fontsize: int = 20, precision: str = ".2f") -> None:
        """
        Display the figure with dummy text showing the width and height of each panel.

        Parameters
        ----------
        fontsize :
            The fontsize of the dummy text.
        precision :
            The precision of the position displays.
        """
        dummy_fig, dummy_axs = self._set_up_axes()
        sizes = self.get_axis_sizes()
        # dummy_fig, dummy_axs = self._get_dummy_axes()
        _label_axes(dummy_axs)
        for label, ax in dummy_axs.items():
            # bbox = ax.get_window_extent().transformed(
            #     dummy_fig.dpi_scale_trans.inverted()
            # )
            # width, height = bbox.width, bbox.height
            width, height = sizes[label]
            ax.text(
                0.5,
                0.5,
                f"({width:{precision}}, {height:{precision}})",
                ha="center",
                va="center",
                fontsize=fontsize,
                transform=ax.transAxes,
                clip_on=False,
                zorder=100,
            )
            # turn off axis transparency
            ax.patch.set_alpha(0)
        skunk.display(skunk.pltsvg(dummy_fig))

    def write(
        self, out_path: Union[str, Path], formats: tuple = ("svg", "pdf")
    ) -> None:
        """
        Write the figure to specified file(s).

        Parameters
        ----------
        out_path :
            The path to write the figure to. The file extension will be appended
            automatically.
        formats :
            The file formats to write the figure to. This is a tuple of strings
            currently supported are "svg" and "pdf".
        """
        if isinstance(out_path, Path):
            out_path = str(out_path)
        if "svg" in formats:
            self.write_svg(out_path)
        if "pdf" in formats:
            self.write_pdf(out_path)

    def write_svg(self, out_path: Union[str, Path]) -> None:
        """
        Write the figure to an SVG file.

        Parameters
        ----------
        out_path :
            The path to write the figure to. The file extension will be appended
            automatically.
        """
        with open(out_path + ".svg", "w") as f:
            f.write(self.svg)

    def write_pdf(self, out_path: Union[str, Path]) -> None:
        """
        Write the figure to a PDF file.

        Requires the `cairosvg` package to be installed.

        Parameters
        ----------
        out_path :
            The path to write the figure to. The file extension will be appended
            automatically.
        """
        cairosvg.svg2pdf(bytestring=self.svg, write_to=str(out_path) + ".pdf")


def panel_mosaic(
    mosaic: Union[str, list[list]],
    panel_mapping: dict[str, str],
    figsize: tuple = (10, 8),
    fontsize: int = 30,
    panel_borders: bool = False,
    layout: str = "tight",
    label_pos: tuple = (0, 1),
) -> str:
    pm = PanelMosaic(
        mosaic=mosaic,
        figsize=figsize,
        layout=layout,
    )
    pm.label_axes(fontsize=fontsize, label_pos=label_pos)
    pm.format_axes(panel_borders=panel_borders)
    pm.map(panel_mapping)
    return pm
