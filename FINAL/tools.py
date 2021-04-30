#!/usr/bin/env python
# coding: utf-8

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


def clean_artist_names(name):
    if ' feat. ' in name:
        name = name[:name.index( 'feat. ')]
        
    if ' & ' in name:
        name = name[:name.index(' & ')]
        
    return name.strip()