from pathlib import Path
import json
import numpy as np
import time
import folium
from matplotlib.colors import LinearSegmentedColormap, ListedColormap
import matplotlib.pyplot as plt
import streamlit as st
import leafmap.foliumap as leafmap
import leafmap.colormaps as cm

import matplotlib as mpl
import numpy
from rio_tiler.colormap import cmap
from streamlit_folium import st_folium

def display_map(map_secrets):
    m = leafmap.Map(
        locate_control=True,
        latlon_control=True,
        minimap_control=True,
        center=map_secrets["coords"],
        zoom=map_secrets["zoom"],
    )

    colors_dict = get_colormap()

    m.add_cog_layer(
        "https://magisterkacog.blob.core.windows.net/cogs/4_4_cdom_20230409_cog_next.tif",
        name=str(st.session_state.layer),
        nodata=0,
        colormap=f"{json.dumps(colors_dict)}",
        # colormap_name = "ndvi".lower(),
        bidx=1,
        rescale="0,255",
    )
    print(map_secrets)
    folium_map = st_folium(
        m,
        width=None,
        height=700,
        center=map_secrets["coords"],
        zoom=map_secrets["zoom"],
    )
    print(folium_map)
    return folium_map

@st.cache_data
def get_colormap():
    cmap = mpl.cm.YlOrRd
    max_for_each_class = [5, 20, 50, 100, 1000]
    for_pixels = np.interp(max_for_each_class, (0, 1000), (1, 255), right=0, left=0)

    scalar_mappable = mpl.cm.ScalarMappable(cmap=cmap).to_rgba(
        np.arange(0, 1.0001, 1 / (len(max_for_each_class) - 1)), alpha=True, bytes=False
    )

    colors_dict = {}
    pixel_values = list(range(1, 20))
    for pixel in pixel_values:
        for i in range(0, len(max_for_each_class)):
            if pixel <= for_pixels[i]:
                colors_dict[pixel] = mpl.colors.rgb2hex(
                    scalar_mappable[i], keep_alpha=False
                )
                break
    return colors_dict

st.title("Normalized Multi-Band Drought Index")

if not "map_secrets" in st.session_state:
    st.session_state["map_secrets"] = {"coords": [49.8663, 20.1654], "zoom": 9}
    st.session_state["map_secrets_new"] = st.session_state.map_secrets

layers = ["2022-02-01", "2022-03-01", "2022-04-01"]

if not "layer" in st.session_state:
    st.session_state["layer"] = layers[len(layers) - 1]

widget = st.empty()

if st.button("Next layer"):
    st.session_state["map_secrets"] = st.session_state.map_secrets_new
    if st.session_state.layer == layers[len(layers) - 1]:
        st.session_state["layer"] = layers[0]
    else:
        st.session_state["layer"] = layers[layers.index(st.session_state.layer) + 1]

st.session_state["layer"] = widget.select_slider(
    label="Choose displayed date", options=layers, value=st.session_state.layer
)

row1_col1, row1_col2 = st.columns([7, 1])

palette_name = "YlOrRd"
vmin_value = 0
vmax_value = 1000

with row1_col1:
    map = display_map(st.session_state.map_secrets)
    if "center" in map:
        st.session_state["map_secrets_new"] = {
            "coords": [map["center"]["lat"], map["center"]["lng"]],
            "zoom": map["zoom"],
        }

with row1_col2:
    colors = ['#ffffcc', '#fed976', '#fd8c3c', '#e2191c',]
    # get_colormap()
    
    fig, ax = plt.subplots(figsize=(1, 4))
    norm = mpl.colors.Normalize(vmin=0, vmax=1000)
    col_map = ListedColormap(name="NDVI", colors=list(colors), N=4)
    cb = mpl.colorbar.ColorbarBase(
        ax, norm=norm, cmap=col_map
    )
    ax.set_yticks([0,250,500, 750, 1000], labels=[0, 20, 50, 100, 1000])
    
    # if show_name:
    #     pos = list(ax.get_position().bounds)
    #     x_text = pos[0] - 0.01
    #     y_text = pos[1] + pos[3] / 2.0
    #     fig.text(x_text, y_text, cmap, va="center", ha="right", fontsize=font_size)

    st.write(
        fig
        # cm.create_colormap(
        #     palette_name,
        #     # label=selected_col.replace("_", " ").title(),
        #     width=1,
        #     height=3,
        #     orientation="vertical",
        #     vmin=vmin_value,
        #     vmax=vmax_value,
        #     font_size=10,
        # )
    )
