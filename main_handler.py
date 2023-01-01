"""
Here we will spawn threads for trackers and piece connectoncs etc

There will be a minimum of three threads:
1. Announcements -> can be multiplied
2. pieces gathering -> can be multiplied
3. app

There will be spawned more threads as possible (for example: more threads for pieces and announcements if we have tons of torrents)
"""


# if we download a lot of torrents thrtr will be a lot of these
def decide_pieces_threads():
    pass

# if we seed a lot of torents we will have a lot of these but if we download X amount of torrents than we will give more threads to pieces gathering
def decide_announcements_threads():
    pass

import asyncore