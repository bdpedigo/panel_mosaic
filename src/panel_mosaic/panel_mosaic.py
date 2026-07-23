import time
from pathlib import Path
from typing import Any, Optional, Union

import cairosvg
import matplotlib.pyplot as plt
import skunk
from matplotlib import patches as mpatches
from matplotlib import patheffects
from mpl_toolkits.axes_grid1 import Size
from mpl_toolkits.axes_grid1.axes_divider import make_axes_locatable


def _ax_off(ax, panel_borders: bool = False) -> None:
    ax.set(xticks=[], yticks=[])
    if not panel_borders:
        ax.spines[["left", "right", "top", "bottom"]].set_visible(False)
    else:
        ax.spines[["left", "right", "top", "bottom"]].set_visible(True)
        ax.spines[["left", "right", "top", "bottom"]].set_linewidth(2)
        ax.spines[["left", "right", "top", "bottom"]].set_color("black")


class PanelMosaic:
    def __init__(
        self,
        mosaic: Any,
        panel_mapping: Optional[dict[str, Union[str, Path]]] = None,
        figsize=(10, 8),
        layout="constrained",
        gridspec_kw=None,
        panel_borders=False,
        label_fontsize=30,
        label_pos=(0, 0.99),
        label_mapping: Optional[dict[str, str]] = None,
        label_dodge="left",
        label_dodge_factor: float = 0.01,
        label_linewidth: Optional[float] = 3,
    ):
        self.mosaic = mosaic
        self.figsize = figsize
        self.layout = layout
        self.panel_borders = panel_borders
        self.label_fontsize = label_fontsize
        self.label_pos = label_pos
        if isinstance(label_dodge, bool) and label_dodge:
            label_dodge = "left"
        self.label_dodge = label_dodge
        self.label_dodge_factor = label_dodge_factor
        self.label_mapping = label_mapping
        self.panel_mapping = panel_mapping
        self.label_linewidth = label_linewidth
        self.dividers = {}

        if gridspec_kw is None:
            self.gridspec_kw = dict(hspace=0.0, wspace=0.0)
        else:
            self.gridspec_kw = gridspec_kw

        self._svg = None
        self.fig, self.axs = self._set_up_axes()

        self._label_axes()
        self._format_axes()
        self._map()

    @property
    def svg(self):
        if self._svg is None:
            for label in self.svg_panel_mapping.keys():
                skunk.connect(self.axs[label], label)
            svg = skunk.insert(self.svg_panel_mapping)
            self._svg = svg
        return self._svg

    # @property
    # def svg_dummy(self):
    #     for label in self.svg_panel_mapping.keys():
    #         skunk.connect(self.axs[label], label)
    #         svg = skunk.insert(self.svg_panel_mapping)
    #         self._svg = svg

    def _set_up_axes(self):
        # ioff/ion is to avoid displaying the matplotlib figure in notebooks, which
        # will just look like a bunch of blue boxes
        plt.ioff()
        fig, axs = plt.subplot_mosaic(
            mosaic=self.mosaic,
            figsize=self.figsize,
            layout=self.layout,
            gridspec_kw=self.gridspec_kw,
            dpi=300,
        )
        for ax in axs.values():
            ax.set_anchor("E")
        plt.ion()
        return fig, axs

    def get_divider(self, label: str):
        if label in self.dividers:
            return self.dividers[label]
        else:
            ax = self.axs[label]
            ax.autoscale(False)  # TODO necessary?
            divider = make_axes_locatable(ax)
            self.dividers[label] = divider
            return divider

    def _label_axes(
        self,
        axs: Optional[dict[str, Any]] = None,
        horizontalalignment: str = "left",
        verticalalignment: str = "top",
    ) -> None:
        """
        Label the axes of the figure with the panel labels.

        Parameters
        ----------
        horizontalalignment :
            The horizontal alignment of the panel labels.
        verticalalignment :
            The vertical alignment of the panel labels.
        """
        if axs is None:
            axs = self.axs
        fontsize = self.label_fontsize
        label_pos = self.label_pos
        dodge = self.label_dodge
        self.dividers = {}
        if label_pos is not None:
            for label, ax in axs.items():
                mapped_label = ""
                if self.label_mapping is not None:
                    if label in self.label_mapping:
                        mapped_label = self.label_mapping[label]

                ax.autoscale(False)

                if dodge:
                    divider = self.get_divider(label)
                    label_ax = divider.append_axes(
                        self.label_dodge,
                        size=Size.Fixed(fontsize * self.label_dodge_factor),
                        pad=0,
                    )
                    label_ax.set(xticks=[], yticks=[])
                    label_ax.set_frame_on(False)
                    label_ax.set_xlim(ax.get_xlim())
                    label_ax.set_ylim(ax.get_ylim())
                    ax.set(
                        xticks=[], yticks=[]
                    )  # for some reason this is needed for the parent axes
                else:
                    label_ax = ax

                text = label_ax.text(
                    *label_pos,
                    mapped_label + "",
                    horizontalalignment=horizontalalignment,
                    verticalalignment=verticalalignment,
                    transform=label_ax.transAxes,
                    fontsize=fontsize,
                    clip_on=False,
                )
                if self.label_linewidth is not None:
                    text.set_path_effects(
                        [
                            patheffects.withStroke(
                                linewidth=self.label_linewidth, foreground="white"
                            )
                        ]
                    )
                label_ax.set(xticks=[], yticks=[])
                # label_ax.set_facecolor((0.2, 0.2, 0.2, 0.2))

    def draw_arrow(self, source, side="right", size=0.1, scale=50, dummy=False) -> None:
        """
        Connect two axes together.

        Parameters
        ----------
        source :
            The label of the source axis.
        """

        divider = self.get_divider(source)
        arrow_ax = divider.append_axes(
            side,
            # size=Size.Fixed(size),
            size="{}%".format(size * 100),
            pad=0,
        )
        arrow_ax.set(xticks=[], yticks=[])
        arrow_ax.set_frame_on(False)

        # arrow_ax.annotate(
        #     "",
        #     xy=(1, 0.5),
        #     xytext=(0.1, 0.5),
        #     xycoords="axes fraction",
        #     textcoords="axes fraction",
        #     arrowprops=dict(arrowstyle="->", lw=2.5, color="black"),
        # )

        if not dummy:
            x_tail, y_tail = 0.1, 0.5
            x_head, y_head = 0.9, 0.5
            arrow = mpatches.FancyArrowPatch(
                (x_tail, y_tail), (x_head, y_head), mutation_scale=scale, color="black"
            )
            arrow_ax.add_patch(arrow)

            arrow_ax.set_xlim((0, 1))
            arrow_ax.set_ylim((0, 1))
            arrow_ax.set(xticks=[], yticks=[])
        return arrow_ax

    def _format_axes(
        self, axs: Optional[dict[str, Any]] = None, panel_borders: Optional[bool] = None
    ) -> None:
        """
        Format the axes of the figure.
        """
        if axs is None:
            axs = self.axs
        if panel_borders is None:
            panel_borders = self.panel_borders
        for _, ax in axs.items():
            _ax_off(ax, panel_borders)

    def _map(self) -> None:
        """
        Map panel images from specified file paths.
        """
        panel_mapping = self.panel_mapping

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
                # TODO add an inset axis for svg images too
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
        self.fig.canvas.draw()
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
        # dummy_fig, dummy_axs = self._set_up_axes()
        dummy_fig, dummy_axs = self.fig, self.axs
        sizes = self.get_axis_sizes()
        # dummy_fig, dummy_axs = self._get_dummy_axes()
        # self._format_axes(dummy_axs, panel_borders=True)
        # self._label_axes(dummy_axs)

        texts = []
        for label, ax in dummy_axs.items():
            # bbox = ax.get_window_extent().transformed(
            #     dummy_fig.dpi_scale_trans.inverted()
            # )
            # width, height = bbox.width, bbox.height
            width, height = sizes[label]
            text = ax.text(
                0.5,
                0.5,
                f"({width:{precision}}, {height:{precision}})",
                ha="center",
                va="center",
                fontsize=fontsize,
                transform=ax.transAxes,
                clip_on=False,
                zorder=100,
                backgroundcolor="white",
            )
            texts.append(text)
            # turn off axis transparency
            # ax.patch.set_alpha(0)
        skunk.display(skunk.pltsvg(dummy_fig))
        for text in texts:
            text.remove()

    def write(
        self,
        out_path: Union[str, Path],
        formats: tuple = ("svg", "pdf", "png"),
        dpi=300,
        verbose: bool = False,
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
            if verbose:
                print(f"Writing SVG to {out_path}.svg")
                timer_start = time.time()
            self.write_svg(out_path)
            if verbose:
                print(f"SVG written in {time.time() - timer_start:.2f} seconds")
        if "png" in formats:
            if verbose:
                print(f"Writing PNG to {out_path}.png")
                timer_start = time.time()
            self.write_png(out_path, dpi=dpi)
            if verbose:
                print(f"PNG written in {time.time() - timer_start:.2f} seconds")
        if "pdf" in formats:
            if verbose:
                print(f"Writing PDF to {out_path}.pdf")
                timer_start = time.time()
            self.write_pdf(out_path)
            if verbose:
                print(f"PDF written in {time.time() - timer_start:.2f} seconds")

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

    def write_png(self, out_path: Union[str, Path], dpi=300) -> None:
        """
        Write the figure to a PNG file.

        Parameters
        ----------
        out_path :
            The path to write the figure to. The file extension will be appended
            automatically.
        """
        cairosvg.svg2png(bytestring=self.svg, write_to=str(out_path) + ".png", dpi=dpi)
        # self.fig.savefig(str(out_path) + ".png", bbox_inches="tight", dpi=300)

    def close(self) -> None:
        """
        Close the figure.
        """
        plt.close(self.fig)

    def lock_axes(self) -> None:
        """
        Fix the axes of the figure to stop auto-resizing when adding content.
        """
        self.fig.canvas.draw()
        self.fig.set_layout_engine("none")


def panel_mosaic(
    mosaic: Union[str, list[list]],
    panel_mapping: dict[str, str],
    figsize: tuple = (10, 8),
    label_fontsize: int = 30,
    panel_borders: bool = False,
    layout: str = "tight",
    label_pos: tuple = (0, 1),
    label_dodge: bool = True,
) -> "PanelMosaic":
    # TODO deprecate this function
    pm = PanelMosaic(
        mosaic=mosaic,
        panel_mapping=panel_mapping,
        figsize=figsize,
        layout=layout,
        panel_borders=panel_borders,
        label_fontsize=label_fontsize,
        label_pos=label_pos,
        label_dodge=label_dodge,
    )
    return pm
