import panel as pn

import os
os.environ["PYVISTA_OFF_SCREEN"] = "true"
os.environ["DISPLAY"] = ""
import pyvista as pv
import numpy as np
import logging

pn.extension("vtk")

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


colorbar = pn.pane.HTML(
    "",
    width=260,
    height=320,
    sizing_mode="fixed"
)

def update_colorbar(layer, unit, vmin, vmax):

    colorbar.object = f"""
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

#try:
 #   plotter.enable_eye_dome_lighting()
#except Exception as e:
 #   logging.warning(e)

#try:
 #   plotter.enable_terrain_style()
#except Exception:
#    pass

plotter.add_axes()    
plotter.add_camera_orientation_widget()
# ==================================================
# INFO PANELS
# ==================================================



# ==================================================
# VTK PANE
# ==================================================

vtk_pane = pn.pane.VTK(
    plotter.ren_win,
    sizing_mode="stretch_both"
)

# ==================================================
# CONTROLS
# ==================================================

indicator_select = pn.widgets.Select(
    name="Pokazatelj",
    options=list(LAYER_CONFIG.keys()),
    value=ACTIVE_LAYER
)

grid_toggle = pn.widgets.Checkbox(
    name="Prikaži Grid",
    value=True
)
grid_actor.SetVisibility(
    bool(grid_toggle.value)
)

reset_btn = pn.widgets.Button(
    name="Reset Camera",
    button_type="primary"
)



# ==================================================
# UPDATE LAYER
# ==================================================
def update_indicator(event):

    try:

        layer = event.new
        cfg = LAYER_CONFIG[layer]

        vals = grid[cfg["column"]]
        vals_clean = vals[~np.isnan(vals)]

        if len(vals_clean) == 0:
            return

        vmin = float(np.nanpercentile(vals_clean, 5))
        vmax = float(np.nanpercentile(vals_clean, 95))

        grid.cell_data["active"] = vals

        mapper = grid_actor.mapper

        mapper.scalar_range = (vmin, vmax)

        try:
            mapper.lookup_table.apply_cmap(
                cfg["cmap"]
            )
        except Exception:
            pass

        mapper.Modified()
        grid.Modified()

        update_colorbar(
            layer,
            cfg["unit"],
            vmin,
            vmax
        )

        plotter.render()
        vtk_pane.param.trigger("object")

    except Exception as e:
        logging.exception(e)


indicator_select.param.watch(
    update_indicator,
    "value"
)

# ==================================================
# GRID VISIBILITY
# ==================================================

def toggle_grid(event):

    try:

        grid_actor.SetVisibility(
            bool(event.new)
        )

        plotter.render()
        vtk_pane.param.trigger("object")
    except Exception as e:
        logging.exception(e)

grid_toggle.param.watch(
    toggle_grid,
    "value"
)

# ==================================================
# RESET CAMERA
# ==================================================

def reset_camera(event):

    plotter.view_isometric()
    plotter.reset_camera()
    plotter.camera.zoom(2.0)    
    plotter.camera.view_angle = 35
    plotter.render()
    vtk_pane.param.trigger("object")


reset_btn.on_click(
    reset_camera
)

# ==================================================
# LAYOUT
# ==================================================

controls = pn.Column(
    "## Analiza",
    indicator_select,
    grid_toggle,
    reset_btn,
    pn.Spacer(height=20),
    pn.Spacer(height=10),
    colorbar,
    width=300
)

dashboard = pn.Row(
    controls,
    vtk_pane,
    sizing_mode="stretch_both"
)

template = pn.template.FastListTemplate(
    title="3D mapa toplotnih potreba i emisija u KS",
    main=[dashboard]
)

template.servable()
