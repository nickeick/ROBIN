# ROBIN
Hi! Welcome to the ROBIN project. A discord bot and virtual assisstant.

The code is made up of a server and clients that connect over a local network as well as an SQLite3 database.

In order to get the program running you will need a few things in addition to the files here:
- You will need FFMPEG which you can download at https://www.ffmpeg.org/

- You will need a number of python external libraries including:
  - DiscordAPI
  - Tkinter
  - Speech_Recognition
  - youtube-dl
  - sqlite3

- You will need environmental variables including...
  - TOKEN= for the discord API connection
  - AUDIO_PATH= for a location to store your audio files (default is in the same directory)
  - DATABASE_PATH= for a location to store your data (default is in the same directory)
  - FFMPEG_PATH= the location of your ffmpeg executable


