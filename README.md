## About spotifyUtility
Python script/app to easily download and merge spotify playlists, albums and single tracks to local mp4 files.

## To-Do
* Organize and give code more structure
* Implement recommendations 
* Graph overviews of playlists downloaded that do not include cloned playlists.

## Getting Started

### Prerequisites
* Python >= 3.8.5
* All requirements in requirements.txt
    * Note that pytube has already been cloned locally into this repository to resolve ongoing issues with existing pytube versions that haven't been merged.

### Installation
1.Clone the repository
```
git clone https://github.com/jerheng/spotifyUtility.git
```

2.Install required packages
```
pip3 install -r requirements.txt
```

### CLI Usage
Example Usage

Playlist download and merge
```
>>> python3 main.py 
Spotify URL: https://open.spotify.com/playlist/1t1jzFVxO1hu9DP6nlGfjs?si=935052e03e0f4ca2
Playlist URL Detected!
Do you want to merge the playlist into a single file? (Y/N): Y
Grabbing Links: 100%|███████████████████████████████████████████████| 12/12 [00:10<00:00,  1.19it/s]
Downloading Songs: 100%|████████████████████████████████████████████| 12/12 [00:20<00:00,  1.74s/it]
Merging Songs: 100%|████████████████████████████████████████████████| 12/12 [00:08<00:00,  1.41it/s]
Playlist has been successfully merged and named 2023-03-15-13-Merged.mp4
Total time taken: 0:01:03.039809
```

Track download
```
>>> python3 main.py 
Spotify URL: https://open.spotify.com/track/1CmUZGtH29Kx36C1Hleqlz?si=b899524233b94b58
Track URL Detected!
Grabbing Links: 100%|█████████████████████████████████████████████████| 1/1 [00:00<00:00,  1.15it/s]
Downloading Songs: 100%|██████████████████████████████████████████████| 1/1 [00:01<00:00,  1.21s/it]
Total time taken: 0:00:02.644627
```

Album download without merge
```
>>> python3 main.py 
Spotify URL: https://open.spotify.com/album/5CNckxfLf4TCoMOoxgAU8l?si=Tl-46aawQwOkzOBIllcHXw
Album URL Detected!
Do you want to merge the playlist into a single file? (Y/N): N
Grabbing Links: 100%|███████████████████████████████████████████████| 10/10 [00:09<00:00,  1.10it/s]
Downloading Songs: 100%|████████████████████████████████████████████| 10/10 [00:10<00:00,  1.01s/it]
Total time taken: 0:00:20.532413
```

### Streamlit Web App Usage
Example Usage

```
>>> streamlit run Downloader.py
```
Downloading spotify album and auto merging all songs
![](https://github.com/jerheng/Spotify-Utility/blob/main/assets/albumUsage.gif)
 
Downloading spotify playlist and selecting what to merge
![](https://github.com/jerheng/Spotify-Utility/blob/main/assets/playlistUsage.gif)


