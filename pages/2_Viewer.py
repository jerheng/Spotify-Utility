# Download viewer
# Imports
import math
import os
from datetime import datetime

import pandas as pd
import streamlit as st
from helper import combine_selected_songs
from natsort import natsorted
from st_aggrid import AgGrid
from st_aggrid.grid_options_builder import GridOptionsBuilder

# Helper functions

# Display bytes nicely
def convert_size(size_bytes):
    if size_bytes == 0:
        return "0B"
    size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return "%s %s" % (s, size_name[i])


# Create dataframe from the folder selected.
def genDataframe(folder):
    folderPath = "./downloads/" + folder
    fileNames = os.listdir(folderPath)
    for idx, song in enumerate(fileNames):
        modifiedDate = datetime.fromtimestamp(
            os.path.getmtime(folderPath + f"/{song}")
        ).strftime("%Y-%m-%d %H:%M:%S")
        size = convert_size(os.path.getsize(folderPath + f"/{song}"))
        fileNames[idx] = [fileNames[idx], modifiedDate, size]
    fileNames = natsorted(fileNames)
    return pd.DataFrame(fileNames, columns=["Title", "Modified Date", "Size"])


# Create grid
def createGrid(df):
    # Setup grid
    df = pd.DataFrame(df)

    # Set up the table with agGrid
    gb = GridOptionsBuilder.from_dataframe(df)

    if st.session_state["selectedRows"]:
        gb.configure_selection(
            selection_mode="multiple",
            use_checkbox=True,
            pre_selected_rows=[st.session_state["selectedRows"]],
        )
    else:
        gb.configure_selection(selection_mode="multiple", use_checkbox=True)

    gb.configure_default_column(
        groupable=True,
        value=True,
        enableRowGroup=True,
        aggFunc="sum",
        editable=False,
        resizable=True,
        sortable=True,
        filter=True,
    )

    gb.configure_column("Title", headerCheckboxSelection=True)

    grid_options = gb.build()

    # Create the table using agGrid
    grid = AgGrid(
        df,
        gridOptions=grid_options,
        data_return_mode="as_input",
        use_sidebar=True,
        fit_columns_on_grid_load=True,
        reload_data=False,
    )
    return grid


# Page layout and structure
st.set_page_config(layout="wide")
st.title("Downloads viewer")


# Initialize folderList variable
folderList = (
    None
)  # If folderList var is None, then there are no folders or no downloads folder so the select box will not be rendered

# Initialize session selectedRows var
st.session_state["selectedRows"] = None

# Check if downloads folder is empty or if there is even a downloads folder
if "downloads" not in os.listdir():
    st.error("No Downloads!")
elif "downloads" in os.listdir():
    if len(os.listdir("./downloads")) == 0:
        st.error("Downloads folder is empty!")
    else:
        folderList = natsorted(
            os.listdir("./downloads")
        )  # Sorts the folders correctly in descending order.

# Check if folderList is None or not
folderSelection = None  # Default to None
if folderList is not None:
    folderSelection = st.selectbox(
        label="Folder", options=folderList, index=len(folderList) - 1, key="selectBox"
    )  # Folder selection

# Display the selected folder in a table with the columns Title | Modified Date | File Size
if folderSelection:
    grid = createGrid(genDataframe(folderSelection))
    st.session_state["selectedRows"] = grid.selected_rows
# st.write(st.session_state)

# Create a button for users to select what they want to merge here.
col1, col2, col3, col4 = st.columns([1, 1, 1, 8])

mergeButton = col1.button("Merge")
if mergeButton:
    selected = st.session_state["selectedRows"]
    if not selected:
        st.error("Nothing selected!")
    elif len(selected) == 1:
        st.error("Unable to merge! Only one song selected!")
    else:
        selectedSongs = [item["Title"] for item in st.session_state["selectedRows"]]
        # print(selectedSongs)
        combine_selected_songs(f"./downloads/{folderSelection}", selectedSongs)
        # Add a button next to Merge Selected to refresh table

refreshButton = col2.button("Refresh")

viewSongsBox = col3.checkbox("Preview Songs", value=False)


def viewSongPlayer(folderSelection):
    # Generate audio object for all songs in current selected folder
    songList = natsorted(os.listdir(f"./downloads/{folderSelection}"))
    for song in songList:
        # Check if file is .mp4
        if song.split(".")[-1] == "mp4":
            st.write(song)
            st.audio(
                open(f"./downloads/{folderSelection}/{song}", "rb").read(),
                format="audio/ogg",
            )


if viewSongsBox:  # if box is selected
    viewSongPlayer(folderSelection)
