# Imports
import pandas as pd
import streamlit as st
from helper import combine_all_songs, getDf
from st_aggrid import AgGrid
from st_aggrid.grid_options_builder import GridOptionsBuilder


# Create Grid
def createGrid(df):
    # Setup grid
    df = pd.DataFrame(df)

    # Set up the table with agGrid
    gb = GridOptionsBuilder.from_dataframe(df)

    # gb.configure_selection(selection_mode='multiple', use_checkbox=True)
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
    gb.configure_column(
        "Title", editable=False, groupable=False
    )  # headerCheckboxSelection=True
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


# Setup appearance of application and receive input
st.set_page_config(layout="wide")
st.title("Spotify Utility")
url = st.text_input("Enter your Spotify URL")
col1, col2, col3 = st.columns([1, 1, 8])

# Initialize session variables for latest downloaded
if "latestDownloaded" not in st.session_state:
    st.session_state["latestDownloaded"] = None

submitButton = col1.button("Download")
with col1:
    mergeCheckbox = col2.checkbox(
        label="Auto-Merge", value=False
    )  # Change value here to False if you dont want to auto merge

# If button is clicked, download and merge if mergeCheckbox is selected
grid = None  # Initial value to check if there is an existing grid on the page
if submitButton:
    retObj = getDf(url)
    df = retObj[0]
    st.session_state["latestDownloaded"] = df
    downloadPath = retObj[1]
    st.session_state["downloadPath"] = downloadPath

    if mergeCheckbox:
        # st.write("Merging songs") #Run the merging script
        # Call combine_all_songs function
        combine_all_songs(downloadPath)
    st.write(f"Files can be found at {downloadPath}")
    grid = createGrid(df)

if (
    "latestDownloaded" in st.session_state
    and st.session_state["latestDownloaded"] is not None
    and not grid
):
    st.write("Latest downloaded")
    createGrid(st.session_state["latestDownloaded"])
