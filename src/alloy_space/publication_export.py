from copy import deepcopy
from pathlib import Path
from time import perf_counter

import kaleido
import plotly.graph_objects as go


# Layout size of a single 3D panel.
PANEL_WIDTH = 1200
PANEL_HEIGHT = 1000

# Final PNG: 3600 × 3000 pixels.
EXPORT_SCALE = 3

FONT_FAMILY = "Arial"
TEXT_COLOR = "#222222"

AXIS_FONT_SIZE = 17
TICK_FONT_SIZE = 17
NUMBER_FONT_SIZE = 17

# Maximum number of ticks on each axis.
AXIS_NTICKS = 5

SHOW_CANDIDATE_NUMBERS = False
SHOW_EXPERIMENTAL_NUMBERS = False

SHOW_GAPS = True
SHOW_LINKS = True

CLUSTER_MARKER_STYLE = {
    "Upper cluster": dict(
        lit_size=10,
        cand_size=22,
        cand_line_width=11,
        exp_size=15,
        link_width=10,
    ),
    "Bottom cluster": dict(
        lit_size=10,
        cand_size=22,
        cand_line_width=11,
        exp_size=18,
        link_width=10,
    ),
}

VIEW_FILES = {
    "Default": "pca_default",
    "Upper cluster": "pca_upper_cluster",
    "Bottom cluster": "pca_bottom_cluster",
}


def _write(fig, path, fmt, width, height, scale=1):
    path = Path(path)
    started = perf_counter()
    print(f"Exporting {path.name}...", flush=True)

    kaleido.write_fig_sync(
        fig,
        path=str(path),
        opts={
            "format": fmt,
            "width": width,
            "height": height,
            "scale": scale,
        },
        kopts={
            "n": 1,
            "timeout": 180,
            "page_generator": kaleido.PageGenerator(mathjax=False),
        },
    )

    print(f"Finished {path.name}: {perf_counter() - started:.1f} s", flush=True)


def save_png(fig, path, width, height):
    _write(fig, path, "png", width, height, scale=EXPORT_SCALE)


def save_svg(fig, path, width, height):
    _write(fig, path, "svg", width, height, scale=1)


def _number_font():
    return dict(family=FONT_FAMILY, size=NUMBER_FONT_SIZE, color="black")


def make_static_panel(source_fig, camera, labels, marker_style=None):
    panel = go.Figure(source_fig)

    # Remove the interface and separate information blocks.
    panel.layout.updatemenus = ()
    panel.layout.annotations = ()
    panel.layout.scene.annotations = ()

    panel.update_layout(
        title=dict(text=""),
        autosize=False,
        width=PANEL_WIDTH,
        height=PANEL_HEIGHT,
        margin=dict(l=50, r=50, t=30, b=50),
        paper_bgcolor="white",
        plot_bgcolor="white",
        showlegend=False,
        font=dict(family=FONT_FAMILY, size=TICK_FONT_SIZE, color=TEXT_COLOR),
    )

    axes = {
        f"{ax}axis": dict(
            title=dict(
                text=f"PC{i}",
                font=dict(
                    family=FONT_FAMILY,
                    size=AXIS_FONT_SIZE,
                    color=TEXT_COLOR,
                ),
            ),
            showticklabels=True,
            tickmode="auto",
            nticks=AXIS_NTICKS,
            tickvals=None,
            ticktext=None,
            tickfont=dict(
                family=FONT_FAMILY,
                size=TICK_FONT_SIZE,
                color=TEXT_COLOR,
            ),
            showbackground=False,
            showgrid=True,
            gridcolor="#D8D8D8",
            gridwidth=1,
            zeroline=False,
            showspikes=False,
        )
        for i, ax in enumerate("xyz", start=1)
    }

    panel.update_scenes(
        domain=dict(x=[0, 1], y=[0, 1]),
        camera=deepcopy(camera),
        aspectmode="cube",
        dragmode=False,
        bgcolor="white",
        **axes,
    )

    for trace in panel.data:
        name = trace.name or ""

        if name.startswith(labels["cand"]):
            trace.visible = True
            trace.mode = (
                "markers+text" if SHOW_CANDIDATE_NUMBERS else "markers"
            )
            trace.textposition = "top left"
            trace.textfont = _number_font()
            if marker_style:
                trace.marker.size = marker_style["cand_size"]
                trace.marker.line.width = marker_style["cand_line_width"]

        elif name.startswith(labels["exp"]):
            trace.visible = True
            trace.mode = (
                "markers+text" if SHOW_EXPERIMENTAL_NUMBERS else "markers"
            )
            trace.textposition = "bottom right"
            trace.textfont = _number_font()
            if marker_style:
                trace.marker.size = marker_style["exp_size"]

        elif name.startswith(labels["lit"]):
            trace.visible = True
            if marker_style:
                trace.marker.size = marker_style["lit_size"]

        elif name.startswith("Composition gaps"):
            trace.visible = SHOW_GAPS

        elif name == "Links between candidates":
            trace.visible = SHOW_LINKS
            if marker_style:
                trace.line.width = marker_style["link_width"]

    return panel


def make_legend(source_fig, labels):
    legend = go.Figure()

    # The order of legend items does not depend on the order of the layers.
    wanted = [labels["lit"], labels["cand"], labels["exp"]]
    if SHOW_GAPS:
        wanted.append("Composition gaps")
    if SHOW_LINKS:
        wanted.append("Links between candidates")

    for prefix in wanted:
        trace = next(
            (t for t in source_fig.data if (t.name or "").startswith(prefix)),
            None,
        )
        if trace is None:
            raise ValueError(f"Layer for the legend not found: {prefix}")

        # A point outside the visible area is only needed
        # to create a complete legend item.
        common = dict(
            x=[0],
            y=[0],
            name=trace.name,
            showlegend=True,
            hoverinfo="skip",
        )

        if trace.type == "isosurface":
            color = (
                trace.colorscale[0][1] if trace.colorscale else "mediumpurple"
            )
            legend.add_trace(go.Scatter(
                **common,
                mode="markers",
                marker=dict(symbol="square", size=20, color=color, opacity=0.5),
            ))

        elif trace.mode == "lines":
            legend.add_trace(go.Scatter(
                **common,
                mode="lines",
                line=trace.line.to_plotly_json(),
            ))

        else:
            marker = trace.marker.to_plotly_json()
            marker["size"] = 18
            legend.add_trace(go.Scatter(**common, mode="markers", marker=marker))

    width = 850
    height = 70 + 65 * len(legend.data)

    legend.update_layout(
        template="plotly_white",
        width=width,
        height=height,
        margin=dict(l=15, r=15, t=15, b=15),
        paper_bgcolor="white",
        plot_bgcolor="white",
        font=dict(family=FONT_FAMILY, size=28),
        showlegend=True,
        legend=dict(
            x=0,
            y=1,
            xanchor="left",
            yanchor="top",
            orientation="v",
            font=dict(size=28),
            itemsizing="constant",
            bgcolor="white",
            borderwidth=0,
        ),
        xaxis=dict(visible=False, range=[1, 2]),
        yaxis=dict(visible=False, range=[1, 2]),
    )

    return legend, width, height


def make_composition_key(source_fig):
    annotation = next(
        (a for a in source_fig.layout.annotations
         if a.name == "composition_axis_key"),
        None,
    )
    if annotation is None:
        raise ValueError(
            "Annotation composition_axis_key not found. "
            "Call the export after add_composition_key(fig)."
        )

    width = 1050
    height = 700

    key = go.Figure()
    key.update_layout(
        template="plotly_white",
        width=width,
        height=height,
        margin=dict(l=25, r=25, t=25, b=25),
        paper_bgcolor="white",
        plot_bgcolor="white",
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
    )
    key.add_annotation(
        x=0,
        y=1,
        xref="paper",
        yref="paper",
        xanchor="left",
        yanchor="top",
        align="left",
        text=annotation.text,
        showarrow=False,
        font=dict(family=FONT_FAMILY, size=26, color="#333333"),
        bgcolor="white",
        borderwidth=0,
        borderpad=0,
    )

    return key, width, height


def export_publication_figures(source_fig, views, labels, output_dir):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    missing = set(VIEW_FILES) - set(views)
    if missing:
        raise ValueError(f"Cameras are missing in VIEWS: {sorted(missing)}")

    for view_name, stem in VIEW_FILES.items():
        panel = make_static_panel(
            source_fig,
            camera=views[view_name],
            labels=labels,
            marker_style=CLUSTER_MARKER_STYLE.get(view_name),
        )
        save_png(panel, output_dir / f"{stem}.png", PANEL_WIDTH, PANEL_HEIGHT)

    legend, width, height = make_legend(source_fig, labels)
    save_png(legend, output_dir / "pca_legend.png", width, height)
    save_svg(legend, output_dir / "pca_legend.svg", width, height)

    key, width, height = make_composition_key(source_fig)
    save_png(key, output_dir / "pca_composition_trends.png", width, height)
    save_svg(key, output_dir / "pca_composition_trends.svg", width, height)

    return output_dir