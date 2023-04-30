import json

import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl

import streamlit as st
import leafmap.foliumap as leafmap
from streamlit_folium import st_folium


def display_map(map_secrets):
    m = leafmap.Map(
        minimap_control=True,
    )

    colors_dict = get_colormap()

    m.add_cog_layer(
        "https://magisterkacog.blob.core.windows.net/cogs/4_4_cdom_20230409_cog.tif",
        name=str(st.session_state.layer),
        nodata=0,
        colormap=f"{json.dumps(colors_dict)}",
        bidx=1,
        rescale="0,255",
    )

    folium_map = st_folium(
        m,
        width=None,
        height=700,
        center=map_secrets["coords"],
        zoom=map_secrets["zoom"],
    )

    return folium_map


@st.cache_data
def get_colormap():
    cmap = mpl.cm.YlOrRd

    scalar_mappable = mpl.cm.ScalarMappable(cmap=cmap).to_rgba(
        np.arange(1, 6, 1), alpha=True, bytes=False
    )

    colors_dict = {}
    pixel_values = list(range(1, 6))
    for idx, pixel in enumerate(pixel_values):
        colors_dict[pixel] = mpl.colors.rgb2hex(scalar_mappable[idx], keep_alpha=False)
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

with row1_col1:
    map = display_map(st.session_state.map_secrets)
    if "center" in map:
        st.session_state["map_secrets_new"] = {
            "coords": [map["center"]["lat"], map["center"]["lng"]],
            "zoom": map["zoom"],
        }

with row1_col2:
    colors = list(get_colormap().values())
    fig, ax = plt.subplots(figsize=(1, 4))
    norm = mpl.colors.Normalize(vmin=0, vmax=1000)
    col_map = mpl.colors.ListedColormap(name="NDVI", colors=list(colors), N=5)
    cb = mpl.colorbar.ColorbarBase(ax, norm=norm, cmap=col_map)
    ax.set_yticks([0, 200, 400, 600, 800, 1000], labels=[0, 5, 20, 50, 100, 1000])

    st.write(fig)
