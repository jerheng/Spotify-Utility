# Imports
import json
import os
import time
from datetime import date, timedelta

import requests
from bs4 import BeautifulSoup
from pydub import AudioSegment
from thefuzz import fuzz
from tqdm import tqdm
from unidecode import unidecode

from pytube.__main__ import YouTube
from pytube.contrib.search import Search

# Default Params
OFFSET = 0
LIMIT = (
    50
)  # Note that the limit for albums is 50, hence the default is 50 but do edit for your playlists as you require
# Example usage of OFFSET and LIMIT: https://api.spotify.com/v1/artists/1vCWHaC5f2uS3yhpwWbIA6/albums?album_type=SINGLE&offset=20&limit=10
# In this example, in a list of 50 (total) singles by the specified artist : From the twentieth (offset) single, retrieve the next 10 (limit) singles.
MARKET = (
    "SG"  # 2 Character country code: https://en.wikipedia.org/wiki/ISO_3166-1_alpha-2
)
# Default download path for the mp4 files.
DEFAULT_PATH = f"./downloads/{date.today()}"
SEARCH_LIMIT = 10

# References
# """
# https://developer.spotify.com/documentation/web-api/
# https://developer.spotify.com/console/tracks/
# https://developer.spotify.com/console/playlists/
# """


# Get link from user
def parseInput():
    urlInput = input("Spotify URL: ").strip().split("/")
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


# Check if user wants to merge playlist
def checkMerge():
    while True:
        check = (
            str(input("Do you want to merge the playlist into a single file? (Y/N): "))
            .strip()
            .upper()
        )
        if check == "Y":
            return True
        elif check == "N":
            return False
        else:
            print("Invalid input! Please only enter Y or N")


# Get new requests token to access spotify web api
def get_new_token():
    r = requests.request("GET", "https://open.spotify.com/")
    r_text = (
        BeautifulSoup(r.content, "html.parser")
        .find("script", {"id": "session"})
        .get_text()
    )
    return json.loads(r_text)["accessToken"]


# Get json data from spotify's web api using playlist id
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
def filterSearchData(searchData, query):
    link = ""
    ratio = -1  # Start with a negative integer, fuzz.ratio()
    for search in searchData:
        title = unidecode(search.title)
        if link == "":
            link = search.watch_url
            ratio = fuzz.token_sort_ratio(title, query)
        else:
            if fuzz.token_sort_ratio(title, query) > ratio:
                link = search.watch_url
                ratio = fuzz.token_sort_ratio(title, query)
                # print(f"Fuzz Ratio: {ratio} after comparing {title} and {query}, new link: {link}")
            # else:
            #     print(f"Not using {title} when compared to {query}")
    return link


# Use the song data to get a youtube link for the song
def get_youtube_link(songData):
    # To get id: videos[resultNumber]['id']
    # To get view count: videos[resultNumber]['simple_data']
    links = []
    for song in tqdm(songData, desc="Grabbing Links", ncols=100, smoothing=1):
        # Extract song and artist name
        songName = song["songName"]
        artistName = song["artistName"]
        # Ensure that there are no unicode characters inside the query
        query = unidecode(songName + " by " + artistName)
        searchData = None
        while searchData is None:
            try:
                searchData = Search(query).results
                songLink = filterSearchData(searchData, query)
            except:
                pass
                # print(
                #     "Error occurred while filtering the selection results, most likely from accessing YouTube object variables"
                # )
        links.append(songLink)
        # print(f"Found link for {songName} by {artistName}")
    return links


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


# Use links to then download files
# def download_from_youtube(links):
#     # Get directory to download the files to
#     DOWNLOAD_PATH = check_create_directory(DEFAULT_PATH)
#     for idx, link in enumerate(
#         tqdm(links, desc="Downloading Songs", ncols=100, smoothing=1)
#     ):
#         yt = YouTube(link)
#         try:
#             if yt.title not in os.listdir(DOWNLOAD_PATH):
#                 # print(f"Downloading {yt.title} from URL: {link}")
#                 # video = yt.streams.filter(only_audio=True).first()
#                 # out_file = video.download(output_path=DOWNLOAD_PATH)
#                 yt.streams.get_audio_only().download(output_path=DOWNLOAD_PATH)
#             else:
#                 print(
#                     f"Failed to download {yt.title}! Already exists in {DOWNLOAD_PATH}"
#                 )
#         except:
#             if idx == len(links) - 1:
#                 print(f"Error occured while downloading song {idx} {yt} from {link}")
#             else:
#                 print(
#                     f"Error occured while downloading song {idx} {yt} from {link}, continuing download process"
#                 )
#     # print(f"Download completed! All files can be located at {DOWNLOAD_PATH}")
#     return DOWNLOAD_PATH

# Use links to then download files
def download_from_youtube(links):
    # Get directory to download the files to
    DOWNLOAD_PATH = check_create_directory(DEFAULT_PATH)
    for idx, link in enumerate(
        tqdm(links, desc="Downloading Songs", ncols=100, smoothing=1)
    ):
        downloadedSong = None
        while downloadedSong is None:
            try:
                yt = YouTube(link)
                if yt.title not in os.listdir(DOWNLOAD_PATH):
                    # print(f"Downloading {yt.title} from URL: {link}")
                    # video = yt.streams.filter(only_audio=True).first()
                    # out_file = video.download(output_path=DOWNLOAD_PATH)
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
                else:
                    print(
                        f"Failed to download {yt.title}! Already exists in {DOWNLOAD_PATH}"
                    )
            except:
                pass
                # print(
                #     f"Error occurred while downloading song {idx} {yt} from {link}, trying again..."
                # )
    # print(f"Download completed! All files can be located at {DOWNLOAD_PATH}")
    return DOWNLOAD_PATH


# Combine all songs
def combine_all_songs(path):
    songList = os.listdir(path)
    if len(songList) == 1:
        print("Nothing to combine!")
        exit()
    try:
        start = None
        for song in tqdm(songList, desc="Merging Songs", ncols=100, smoothing=1):
            if start is None:
                start = AudioSegment.from_file(path + "/" + song, "mp4")
            else:
                temp = AudioSegment.from_file(path + "/" + song, "mp4")
                start = start.append(temp)
        folderName = path.split("/")[-1]
        start.export(f"{path}/{folderName}-Merged.mp4", format="mp4")
        print(
            f"Playlist has been successfully merged and named {folderName}-Merged.mp4"
        )
    except:
        print("Error! Try running the application as administrator.")


# Main function
def main():
    spotifyId = parseInput()
    if not spotifyId:
        print(
            "Invalid URL! Not a valid Spotify Playlist URL. Example: https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M"
        )
        exit()
    else:
        start = time.time()
        # Check if track or playlist
        userToken = get_new_token()
        if spotifyId[1] == "PLAYLIST":
            print("Playlist URL Detected!")
            mergeBool = checkMerge()
            spotifyData = get_json_data_playlist(
                spotifyId[0], OFFSET, LIMIT, MARKET, userToken
            )
            songData = get_song_data_playlist(spotifyData)
            links = get_youtube_link(songData)
            downloadPath = download_from_youtube(links)
            if mergeBool:
                combine_all_songs(downloadPath)
        elif spotifyId[1] == "TRACK":  # Track
            print("Track URL Detected!")
            spotifyData = get_json_data_track(
                spotifyId[0], OFFSET, LIMIT, MARKET, userToken
            )
            songData = get_song_data_track(spotifyData)
            links = get_youtube_link(songData)
            download_from_youtube(links)

        elif spotifyId[1] == "ALBUM":
            print("Album URL Detected!")
            mergeBool = checkMerge()
            spotifyData = get_json_data_album(
                spotifyId[0], OFFSET, LIMIT, MARKET, userToken
            )
            songData = get_song_data_album(spotifyData)
            links = get_youtube_link(songData)
            downloadPath = download_from_youtube(links)
            if mergeBool:
                combine_all_songs(downloadPath)
        end = time.time()
        print(f"Total time taken: {timedelta(seconds=end-start)}")
    exit()


main()
