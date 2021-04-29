#!/usr/bin/env python
# coding: utf-8

# In[8]:


import json, requests, random, time
import pandas as pd
from lyricsgenius import Genius
from api_keys import *
from azlyrics import azlyrics
from IPython.display import clear_output


# In[13]:


genius_api = Genius(genius_api_key)
genius_api.remove_section_headers = True
genius_api.verbose = False


# In[2]:


try:
    all_music_df = pd.read_csv('CSV Files/all_music.csv').drop('Unnamed: 0', axis=1)
except:
    all_music_df = pd.DataFrame([])


# In[3]:


musixmatch_status_codes = {
    "200": "The request was successful.",
    "400": "The request had bad syntax or was inherently impossible to be satisfied.",
    "401": "Authentication failed, probably because of invalid/missing API key.",
    "402": "The usage limit has been reached, either you exceeded per day requests limits or your balance is insufficient.",
    "403": "You are not authorized to perform this operation.",
    "404": "The requested resource was not found.",
    "405": "The requested method was not found.",
    "500": "Oops. Something were wrong.",
    "503": "Our system is a bit busy at the moment and your request can’t be satisfied."
}


# ## Get List of Genres

# In[6]:


def get_genres():
    response = requests.get("https://api.musixmatch.com/ws/1.1/music.genres.get?"
                           "apikey={}".format(musixmatch_api_key))
    result = json.loads(response.content)
    print
    
    status_code = result['message']['header']['status_code']
    super_genres = []
    
    if status_code == 200:
        music_genres = result["message"]["body"]["music_genre_list"]

        for i in range(1, len(music_genres), 1):
            if (music_genres[i]["music_genre"]["music_genre_parent_id"] == 34):
                super_genres.append({
                    'genre_id': music_genres[i]["music_genre"]['music_genre_id'],
                    'genre_name': music_genres[i]['music_genre']['music_genre_name']
                })
        
    else:
        print("ERROR: ", musixmatch_status_codes[str(status_code)], "( Status Code ", status_code, ")")
        
    return super_genres


# ## Searching MusixMatch API for Top Tracks

# In[2]:


def get_top_tracks(
        page, f_music_genre_id, apikey = musixmatch_api_key,
        f_track_release_group_first_release_date_min='20110101', 
        f_track_release_group_first_release_date_max='20201231', 
        f_lyrics_language='tl', page_size=100, s_track_rating='desc'
    ):
    
        """
        Parameters:
        
            f_music_genre_id - When set, filter by this music category id.

            f_lyrics_language - Filter by the lyrics language (en,it,..).

            f_track_release_group_first_release_date_min - When set, filter the tracks with 
                release date newer than value, format is YYYYMMDD.

            f_track_release_group_first_release_date_max - When set, filter the tracks with 
                release date older than value, format is YYYYMMDD.

            s_track_rating - Sort by our popularity index for tracks (asc|desc).

            page - Define the page number for paginated results.

            page_size - Define the page size for paginated results. Range is 1 to 100.
        """
        
        data = requests.get(
            'http://api.musixmatch.com/ws/1.1/' + (
                "track.search?"
                "f_music_genre_id={}"
                "&f_track_release_group_first_release_date_min={}"
                "&f_track_release_group_first_release_date_max={}"
                "&f_lyrics_language={}"
                "&page_size={}"
                "&page={}"
                "&s_track_rating={}&format='json'"
                "&apikey={}".format(
                    f_music_genre_id, f_track_release_group_first_release_date_min,
                    f_track_release_group_first_release_date_max, f_lyrics_language,
                    page_size, page, s_track_rating, apikey
                )
            ) 
        )
        
        if data.json()['message']['header']['status_code'] == 200:
               return data.json()
            
        else:
            print("ERROR: ", musixmatch_status_codes[str(status_code)], "( Status Code ", status_code, ")")
            


# ## Collecting Lyrics

# In[4]:


def clean_song_title(title):
    while '(' in title:
        if ')' in title:
            title = title[:title.index('(')] + title[title.index(')')+1:]
        else: break

    while '[' in title:
        if ']' in title:
            title = title[:title.index('[')] + title[title.index(']')+1:]
        else: break
    
    if ' - ' in title:
        title = title[:title.index(' - ')]

    return title.strip()


# In[5]:


def clean_artist_names(name):
    if ' feat. ' in name:
        name = name[:name.index( 'feat. ')]
        
    if ' & ' in name:
        name = name[:name.index(' & ')]
        
    return name.strip()


# In[16]:


def get_lyrics(track_name, artist_name, delay):    
    bad_chars = ['\'', ',', '.', '-', '!', '?', '&']
    
    track_name = clean_song_title(track_name)
    artist_name = clean_artist_names(artist_name)
            
    print("\tcollecting lyrics from Genius: ", sep='')
            
    lyrics = genius_api.search_song(track_name, artist_name)

    if (lyrics == None):
        print('')
        print("\tcollecting lyrics from AZLyrics: ", end='')
                
        track_name = ''.join((filter(lambda i: i not in bad_chars, track_name)))
        artist_name = ''.join((filter(lambda i: i not in bad_chars, artist_name)))
        lyrics = azlyrics.lyrics(artist_name, track_name)
                
        if ('Error' in lyrics):
            print('\t\tfailed')
            lyrics = None
        else:
            print('\t\tfound')
    else:
        lyrics = lyrics.lyrics
                
    time.sleep(delay)
    return lyrics


# ## Extract Needed Data from MusixMatch JSON

# In[68]:


def get_genre_songs(genre_json, genre_collection, currindex=0):
    genre_df = pd.DataFrame(genre_json)
    length = len(genre_collection['genre_tracks'])
    nolyrics = 0
    
    for song in genre_collection['genre_tracks'][currindex:]:
        delay = random.randint(5, 10)
        currindex += 1
        
        print(genre_collection['genre_name'])
        print('\tsong ', currindex, '/', length, 'with', delay, 'second delay')
        print('\tsongs without lyrics:', nolyrics)
        print()
        
        
        details = song['track']

        genre_ids = []
        genre_names = []

        for i in details['primary_genres']['music_genre_list']:
            genre_ids.append(i['music_genre']['music_genre_id'])
            genre_names.append(i['music_genre']['music_genre_name'])

        if 'secondary_genres' in details:        
            for i in details['secondary_genres']['music_genre_list']:
                genre_ids.append(i['music_genre']['music_genre_id'])
                genre_names.append(i['music_genre']['music_genre_name'])
                
        index = genre_df[genre_df['track_id'] == details['track_id']].index
             
        if ((len(index) == 0) or (genre_json[index[0]]['lyrics'] == None)):
            lyrics = get_lyrics(details['track_name'], details['artist_name'], delay)
            
            if (lyrics == None):
                nolyrics += 1
                    
        else: lyrics = genre_json[index[0]]['lyrics']
            
                    
        if (len(index) > 0):               
            genre_json[index[0]] = {
                                'track_id': details['track_id'],
                                'track_name': details['track_name'],
                                'artist_name': details['artist_name'],
                                'genre_id': genre_ids,
                                'genre_names': genre_names,
                                'lyrics': lyrics
                            }
        else:
            genre_json.append({
                'track_id': details['track_id'],
                'track_name': details['track_name'],
                'artist_name': details['artist_name'],
                'genre_id': genre_ids,
                'genre_names': genre_names,
                'lyrics': lyrics
            })

        clear_output(wait=True)

