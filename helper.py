# Imports
import json
import os
from datetime import date, timedelta

import pandas as pd
import requests
import streamlit as st
from bs4 import BeautifulSoup
from pydub import AudioSegment
from pytube.__main__ import YouTube
from pytube.contrib.search import Search
from thefuzz import fuzz
from unidecode import unidecode

# Import default parameters from config.json
config = json.load(open(file="config.json"))
OFFSET = int(config["OFFSET"])
LIMIT = int(config["LIMIT"])
DEFAULT_PATH = config["DEFAULT_PATH"] + str(
    date.today()
)  # Please do not change this unless you know what you're doing!
MARKET = config[
    "MARKET"
]  # Please change the default value to yours: https://en.wikipedia.org/wiki/ISO_3166-1_alpha-2

# References
# """
# https://developer.spotify.com/documentation/web-api/
# https://developer.spotify.com/console/tracks/
# https://developer.spotify.com/console/playlists/
# """

# Get link from user
def parseInput(text):
    urlInput = text.strip().split("/")
    # urlInput = st.text_input("Spotify URL:").strip().split("/")
    # Check if input is indeed from spotify
    if "open.spotify.com" in urlInput:
        if "playlist" in urlInput:
            # Playlist link e.g https://open.spotify.com/playlist/37i9dQZF1DZ06evO4nOT7i
            playlistId = urlInput[4].split("?")[0]
            return (playlistId, "PLAYLIST")
        elif "track" in urlInput:
            # Track link    e.g https://open.spotify.com/track/1gH1h30wkQdd9zhY3j7a8T?si=f0c64d3a0a8541ae
            trackId = urlInput[4].split("?")[0]
            return (trackId, "TRACK")
        elif "album" in urlInput:
            # Album link    e.g https://open.spotify.com/album/5CNckxfLf4TCoMOoxgAU8l?si=_WkEJ46eTPaBLhuqqmpH8w
            albumId = urlInput[4].split("?")[0]
            return (albumId, "ALBUM")
    else:
        False


# Get new requests token to access spotify web api
def get_new_token():
    r = requests.request("GET", "https://open.spotify.com/")
    r_text = (
        BeautifulSoup(r.content, "html.parser")
        .find("script", {"id": "session"})
        .get_text()
    )
    return json.loads(r_text)["accessToken"]


def get_json_data_playlist(playlist_id, offset, limit, market, token):
    url = f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks?offset={offset}&limit={limit}&market={market}"
    payload = {}
    headers = {"authorization": "Bearer " + str(token), "Sec-Fetch-Dest": "empty"}
    response = requests.request("GET", url, headers=headers, data=payload)
    return json.loads(response.text)


# Get json data from spotify's web api using track id
def get_json_data_track(track_id, offset, limit, market, token):
    url = "https://api.spotify.com/v1/tracks/" + str(track_id) + f"?&market={market}"
    payload = {}
    headers = {"authorization": "Bearer " + str(token), "Sec-Fetch-Dest": "empty"}
    response = requests.request("GET", url, headers=headers, data=payload)
    return json.loads(response.text)


# Get json data from spotify's web api using album id
def get_json_data_album(album_id, offset, limit, market, token):
    url = f"https://api.spotify.com/v1/albums/{album_id}/tracks?offset={offset}&limit={limit}&market={market}"
    payload = {}
    headers = {"authorization": "Bearer " + str(token), "Sec-Fetch-Dest": "empty"}
    response = requests.request("GET", url, headers=headers, data=payload)
    return json.loads(response.text)


# Clean and get song data from the json response for playlists
def get_song_data_playlist(spotifyData):
    if spotifyData["total"] == 0:
        st.error("Empty Playlist!")
        print("Empty playlist! Aborting.")
        exit()
    else:
        songs = []
        for song in spotifyData["items"]:
            songName = song["track"]["name"]
            artistName = song["track"]["artists"][0]["name"]
            songs.append({"songName": songName, "artistName": artistName})
    return songs


# Simplify spotifyData to {'songName':songName, 'artistName':artistName}
def get_song_data_track(spotifyData):
    songName = spotifyData["name"]
    artistName = spotifyData["artists"][0]["name"]
    return [{"songName": songName, "artistName": artistName}]


# Clean and get song data from the json response for playlists
def get_song_data_album(spotifyData):
    if spotifyData["total"] == 0:
        print("Empty album! Aborting.")
        exit()
    else:
        songs = []
        for song in spotifyData["items"]:
            songName = song["name"]
            artistName = song["artists"][0]["name"]
            songs.append({"songName": songName, "artistName": artistName})
    return songs


# Filter the search videos and compare the title of the youtube videos and sort by the fuzz ratio
def filterSearchData(searchData, query):  # streamlit
    link = ""
    ratio = -1  # Start with a negative integer, fuzz.ratio()
    loc = None
    for idx, search in enumerate(searchData):
        title = unidecode(search.title)
        if link == "":
            link = search.watch_url
            ratio = fuzz.token_sort_ratio(title, query)
            loc = idx
        else:
            if fuzz.token_sort_ratio(title, query) > ratio:
                link = search.watch_url
                ratio = fuzz.token_sort_ratio(title, query)
                loc = idx
                # print(f"Fuzz Ratio: {ratio} after comparing {title} and {query}, new link: {link}")
            # else:
            #     print(f"Not using {title} when compared to {query}")
    # loc is the current idx of the final search result
    ar = None
    try:
        ar = [
            searchData[loc].title,
            searchData[loc].author,
            "{:,}".format(searchData[loc].views),
            str(timedelta(seconds=searchData[loc].length)),
            searchData[loc].watch_url,
        ]
    except:
        ar = None
    return (link, ar)


def get_youtube_link(songData):  # Streamlit version
    # To get id: videos[resultNumber]['id']
    # To get view count: videos[resultNumber]['simple_data']
    links = []
    counter = 0
    progText = "Grabbing youtube links..."
    progress_bar = st.progress(0, text=progText)
    count = len(songData)

    df = []
    for song in songData:
        # Extract song and artist name
        songName = song["songName"]
        artistName = song["artistName"]
        # Ensure that there are no unicode characters inside the query
        query = unidecode(songName + " by " + artistName)
        filtered = (None, None)
        while filtered[1] == None:
            try:
                searchData = Search(query).results
                filtered = filterSearchData(searchData, query)
            except:
                print(
                    "Error occurred while filtering the selection results, most likely from accessing YouTube object variables"
                )
        songLink = filtered[0]
        df.append(filtered[1])
        progress_bar.progress(min(int(counter + (100 / count)), 100), text=progText)
        counter += 100 / count
        links.append(songLink)
        # print(f"Found link for {songName} by {artistName}")
    df = pd.DataFrame(df, columns=["Title", "Author", "Views", "Duration", "URL"])
    return (links, df)


# Create directory for mp4 storage
def check_create_directory(DEFAULT_PATH):
    if os.path.exists(DEFAULT_PATH):
        # Default path already exists
        i = 1
        while True:
            if os.path.exists(DEFAULT_PATH + f"-{i}"):
                i += 1
            else:
                os.makedirs(DEFAULT_PATH + f"-{i}")
                return DEFAULT_PATH + f"-{i}"
    else:
        os.makedirs(DEFAULT_PATH)
        return DEFAULT_PATH


def download_from_youtube(links):  # Streamlit version
    # Get directory to download the files to
    DOWNLOAD_PATH = check_create_directory(DEFAULT_PATH)
    counter = 0
    progText = "Downloading songs from youtube..."
    progress_bar = st.progress(0, text=progText)
    count = len(links)
    # st.write(f"Files can be found at {DOWNLOAD_PATH}")
    # print(f"Links: {links}")
    # dfAr = []
    for idx, link in enumerate(links):
        downloadedSong = None
        while downloadedSong is None:
            try:
                yt = YouTube(link)
                if yt.title not in os.listdir(DOWNLOAD_PATH):
                    downloadedSong = yt.streams.get_audio_only().download(
                        output_path=DOWNLOAD_PATH
                    )
                    keywords = str.encode(
                        ", ".join(yt.keywords)
                    )  # Add video tags to metadata of file
                    os.setxattr(
                        f"{DOWNLOAD_PATH}/{yt.title}.mp4", "user.keywords", keywords
                    )
                    os.setxattr(
                        f"{DOWNLOAD_PATH}/{yt.title}.mp4", "user.url", str.encode(link)
                    )
                    # Can add extended attribute to the downloaded file to generate graphs
                else:
                    print(
                        f"Failed to download {yt.title}! Already exists in {DOWNLOAD_PATH}"
                    )
            except:
                # pass
                print(
                    f"Error occurred while downloading song {idx} {yt} from {link}, trying again..."
                )

        progress_bar.progress(min(int(counter + (100 / count)), 100), text=progText)
        counter += 100 / count
    # print(f"Download completed! All files can be located at {DOWNLOAD_PATH}")
    # dfAr = pd.DataFrame(dfAr, columns=["Title", "Author", "Views", "Duration", "URL"])
    # return (DOWNLOAD_PATH, dfAr)
    return DOWNLOAD_PATH


# Combine all songs
def combine_all_songs(path):
    songList = os.listdir(path)
    if len(songList) == 1:  # Track
        print("Nothing to combine!")
        st.write("No songs to combine!")
    else:  # Album/Playlist
        try:
            progText = "Merging songs..."
            progress_bar = st.progress(0, text=progText)
            count = len(songList)
            counter = 0
            start = None
            for song in songList:
                if start == None:
                    start = AudioSegment.from_file(path + "/" + song, "mp4")
                else:
                    temp = AudioSegment.from_file(path + "/" + song, "mp4")
                    start = start.append(temp)
                progress_bar.progress(
                    min(int(counter + (100 / count)), 100), text=progText
                )
                counter += 100 / count
            folderName = path.split("/")[-1]
            start.export(f"{path}/{folderName}-Merged.mp4", format="mp4")
            print(
                f"Playlist has been successfully merged and named {folderName}-Merged.mp4"
            )
            st.write(f"Merged file: {folderName}-Merged.mp4")
        except:
            progress_bar.progress(100, text=progText)
            st.error("Error! Try running the application as administrator.")
            print("Merge error! Try running the application as administrator.")


# Combine selected songs
def combine_selected_songs(path, songList):
    try:
        progText = "Merging songs..."
        progress_bar = st.progress(0, text=progText)
        count = len(songList)
        counter = 0
        start = None
        for song in songList:
            if start == None:
                start = AudioSegment.from_file(path + "/" + song, "mp4")
            else:
                temp = AudioSegment.from_file(path + "/" + song, "mp4")
                start = start.append(temp)
            progress_bar.progress(min(int(counter + (100 / count)), 100), text=progText)
            counter += 100 / count
        folderName = path.split("/")[-1]
        # Check there is already a merged file inside the folder
        fileList = os.listdir(path)
        mergeExists = True in ["Merged" in file for file in fileList]
        fileName = f"{path}/{folderName}-Merged.mp4"
        if mergeExists:  # deconflict and loop until name is found
            fileName = f"{path}/{folderName}-Merged.mp4"
            if os.path.exists(fileName):
                i = 1
                while True:
                    fileName = f"{path}/{folderName}-Merged{i}.mp4"
                    if os.path.exists(fileName):
                        i += 1
                    else:
                        start.export(fileName, format="mp4")
                        break
        else:
            start.export(fileName, format="mp4")
        print(
            f"Playlist has been successfully merged and named {fileName}, refresh to see new file in table."
        )
        st.write(f"Merged file: {fileName}")
    except:
        progress_bar.progress(100, text=progText)
        st.error("Error! Try running the application as administrator.")
        print("Merge error! Try running the application as administrator.")


# Main functiion that test.py will call to retrieve a dataframe of the information and inform the application of the nature of the link(PLAYLIST/TRACK/ALBUM)
def getDf(url):
    userToken = get_new_token()
    spotifyId = parseInput(url)
    if not spotifyId:
        st.error("Invalid Spotify URL")
    else:
        if "PLAYLIST" in spotifyId:
            st.success("Playlist URL Detected!")
            spotifyData = get_json_data_playlist(
                spotifyId[0], OFFSET, LIMIT, MARKET, userToken
            )
            songData = get_song_data_playlist(spotifyData)
            helper = get_youtube_link(songData)
            links = helper[0]
            df = helper[1]
            downloadPath = download_from_youtube(links)
            return (df, downloadPath)

        elif "ALBUM" in spotifyId:
            st.success("Album URL Detected!")
            spotifyData = get_json_data_album(
                spotifyId[0], OFFSET, LIMIT, MARKET, userToken
            )
            songData = get_song_data_album(spotifyData)
            helper = get_youtube_link(songData)
            links = helper[0]
            df = helper[1]
            downloadPath = download_from_youtube(links)
            return (df, downloadPath)

        elif "TRACK" in spotifyId:
            st.success("Track URL Detected!")
            spotifyData = get_json_data_track(
                spotifyId[0], OFFSET, LIMIT, MARKET, userToken
            )
            songData = get_song_data_track(spotifyData)
            helper = get_youtube_link(songData)
            links = helper[0]
            df = helper[1]
            downloadPath = download_from_youtube(links)
            return (df, downloadPath)
