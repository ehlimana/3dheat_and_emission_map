
from trame.app import get_server
from trame.ui.vuetify3 import SinglePageLayout
from trame.widgets import vuetify3 as vuetify
from pyvista.trame.ui import plotter_ui


import numpy as np
import logging
import os

os.environ["PYVISTA_OFF_SCREEN"] = "true"

import pyvista as pv

pv.OFF_SCREEN = True
# ==================================================
# DATA
# ==================================================

terrain = pv.read("data/terrain.vtp")

grid = pv.read(
    "data/grid_mesh.vtp"
)

grid.cell_data["active"] = grid["heat"]

print(grid.array_names)
texture = pv.read_texture(
    "data/osm_cropped.jpg"
)



print("Terrain:", terrain.n_points, terrain.n_cells)
print("Grid:", grid.n_points, grid.n_cells)

# ==================================================
# CONFIG
# ==================================================

LAYER_CONFIG = {
    "Heat Demand": {
        "column": "heat",
        "unit": "MWh/year",
        "cmap": "Spectral"
    },

    "CO₂": {
        "column": "co",
        "unit": "ktons/year",
        "cmap": "Spectral"
    },
    "NOx": {
        "column": "nox",
        "unit": "ktons/year",
        "cmap": "Spectral"
    },
    "SO₂": {
        "column": "sox",
        "unit": "ktons/year",
        "cmap": "Spectral"
    },
    "PM2.5": {
        "column": "pm25",
        "unit": "ktons/year",
        "cmap": "Spectral"
    }
}

ACTIVE_LAYER = "Heat Demand"

# ==================================================
# PLOTTER
# ==================================================

plotter = pv.Plotter(
    off_screen=True,
    window_size=(1200, 800)
)

plotter.set_background("white")
light = pv.Light(
    position=(50000, 50000, 30000),
    focal_point=(0, 0, 0),
    intensity=1.3
)

plotter.add_light(light)
# ==================================================
# TERRAIN
# ==================================================

plotter.add_mesh(
    terrain,
    texture=texture,
    smooth_shading=True,
    ambient=0.35,
    diffuse=0.85,
    specular=0.15
)

plotter.add_mesh(
    terrain,
    scalars="hillshade",
    cmap="gray",
    opacity=0.15,
    lighting=False,
    show_scalar_bar=False
)


# ==================================================
# GRID
# ==================================================

cfg = LAYER_CONFIG[ACTIVE_LAYER]

vals = grid[cfg["column"]]
vals_clean = vals[~np.isnan(vals)]

vmin = float(np.percentile(vals_clean, 5))
vmax = float(np.percentile(vals_clean, 95))

grid_actor = plotter.add_mesh(
    grid,
    scalars="active",
    cmap=cfg["cmap"],
    opacity=0.65,
    smooth_shading=True,
    show_edges=False,
    clim=[vmin, vmax],
    show_scalar_bar=False
)
print("Actors:", len(plotter.renderer.actors))




# ==================================================
# CAMERA
# ==================================================

plotter.view_isometric()
plotter.reset_camera()
plotter.camera.zoom(2.0)
plotter.camera.view_angle = 35
plotter.add_axes()    
plotter.add_camera_orientation_widget()
#try:
 #   plotter.enable_eye_dome_lighting()
#except Exception as e:
 #   logging.warning(e)

#try:
 #   plotter.enable_terrain_style()
#except Exception:
#    pass



# ==================================================
# CONTROLS
# ==================================================
server = get_server()
state = server.state
state.indicator = ACTIVE_LAYER
state.show_grid = True

state.colorbar_html = ""
def update_colorbar(layer, unit, vmin, vmax):

    state.colorbar_html = f"""
    <div style="
        font-family: Arial, sans-serif;
        padding: 10px;
    ">

        <div style="
            font-size:16px;
            font-weight:bold;
            margin-bottom:4px;
        ">
            {layer}
        </div>

        <div style="
            font-size:12px;
            color:#555;
            margin-bottom:15px;
        ">
            {unit}
        </div>

        <div style="
            display:flex;
            align-items:stretch;
        ">

            <div style="
                height:220px;
                width:28px;
                border-radius:4px;
                border:1px solid #ccc;
                background:linear-gradient(
                    to top,
                    #5e4fa2,
                    #3288bd,
                    #66c2a5,
                    #abdda4,
                    #e6f598,
                    #ffffbf,
                    #fee08b,
                    #fdae61,
                    #f46d43,
                    #d53e4f,
                    #9e0142
                );
            ">
            </div>

            <div style="
                height:220px;
                display:flex;
                flex-direction:column;
                justify-content:space-between;
                margin-left:10px;
                font-size:12px;
            ">
                <span>{vmax:,.2f}</span>
                <span>{(vmax*0.75 + vmin*0.25):,.2f}</span>
                <span>{(vmax+vmin)/2:,.2f}</span>
                <span>{(vmax*0.25 + vmin*0.75):,.2f}</span>
                <span>{vmin:,.2f}</span>
            </div>

        </div>

        <div style="
            margin-top:10px;
            font-size:11px;
            color:#666;
        ">
            Percentile range (P5-P95)
        </div>

    </div>
    """


update_colorbar(
    ACTIVE_LAYER,
    cfg["unit"],
    vmin,
    vmax
)

state.indicator = "Heat Demand"

# ==================================================
# UPDATE LAYER
# ==================================================
def update_indicator(indicator):

    cfg = LAYER_CONFIG[indicator]

    vals = grid[cfg["column"]]

    grid.cell_data["active"] = vals
    grid.set_active_scalars("active")

    vmin = float(np.nanpercentile(vals, 5))
    vmax = float(np.nanpercentile(vals, 95))

    grid_actor.mapper.scalar_range = (
        vmin,
        vmax
    )
    grid_actor.mapper.Modified()
    grid.Modified()
    update_colorbar(indicator,cfg["unit"],vmin,vmax)

    plotter.render()
    view.update()

@state.change("indicator")
def indicator_changed(indicator, **kwargs):
    update_indicator(indicator)    


# ==================================================
# RESET CAMERA
# ==================================================

def reset_camera():

    plotter.view_isometric()
    plotter.reset_camera()

    plotter.camera.zoom(2.0)
    plotter.camera.view_angle = 35
    plotter.render()
    view.update()



# ==================================================
# LAYOUT
# ==================================================

with SinglePageLayout(server) as layout:

    layout.title.set_text(
        "3D mapa toplotnih potreba i emisija KS"
    )
    state.layers = list(LAYER_CONFIG.keys())

    with layout.content:

        with vuetify.VContainer(
            fluid=True,
            classes="pa-0 fill-height"
        ):

            with vuetify.VRow(
                classes="fill-height ma-0"
            ):

                with vuetify.VCol(
                    cols="9"
                ):
                    view = plotter_ui(plotter)

                with vuetify.VCol(
                    cols="3"
                ):
                    vuetify.VSelect(
                        v_model=("indicator", "Heat Demand"),
                        items=("layers",),
                    )

                    vuetify.VContainer(
                        v_html=("colorbar_html",)
                    )



if __name__ == "__main__":
    server.start(port=int(os.environ.get("PORT", 8080)))
