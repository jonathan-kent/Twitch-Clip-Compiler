import config
import os
import os.path
from os import path
import datetime
import socket
from time import sleep
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from moviepy.editor import *
from moviepy.video.tools.cuts import find_video_period
from Google import Create_Service
from googleapiclient.http import MediaFileUpload


GAME_NAME = "Valorant"
URL = "https://www.twitch.tv/directory/game/VALORANT/clips?range=7d"
LINKS = []


class clip_downloader:

    def __init__(self):
        if not path.isdir(config.download_path):
            print("not a path")
        chrome_options = webdriver.ChromeOptions()
        prefs = {"download.default_directory" : config.download_path}
        chrome_options.add_experimental_option("prefs",prefs)
        self.driver = webdriver.Chrome(config.driver_path,chrome_options=chrome_options)
        self.driver.get(URL)
        sleep(3)

    def get_links(self):
        link_class_name = "tw-full-width.tw-interactive.tw-link.tw-link--hover-underline-none.tw-link--inherit"
        duration_class_name = "tw-align-items-center.tw-border-radius-small.tw-c-background-overlay.tw-c-text-overlay.tw-flex.tw-font-size-6.tw-justify-content-center.tw-media-card-stat"
        clip_info_class_name = "tw-interactive.tw-link.tw-link--hover-underline-none.tw-link--inherit"

        links = []
        durations = []
        titles = []
        streamers = []
        mins = 0
        secs = 0
        while mins < 10:
            mins = 0
            secs = 0
            clips = self.driver.find_elements_by_class_name(link_class_name)
            clip_durations = self.driver.find_elements_by_class_name(duration_class_name)
            clip_info = self.driver.find_elements_by_class_name(clip_info_class_name)
            for idx, val in enumerate(clip_info):
                if idx % 3 == 0:
                    titles.append(val.text)
                elif idx % 3 == 1:
                    streamers.append(val.text)
            for idx, d in enumerate(clip_durations):
                if idx % 3 == 0:
                    duration = d.find_element_by_tag_name('p').text
                    durations.append(duration)
            for duration in durations:
                min_sec = duration.split(":")
                mins += int(min_sec[0])
                secs += int(min_sec[1])
                if secs > 60:
                    mins += 1
                    secs = secs - 60
            for clip in clips:
                link = clip.get_attribute("href")
                links.append(link)
            self.driver.execute_script("arguments[0].scrollIntoView();", clips[len(clips)-1])

        mins = 0
        secs = 0
        i = 0
        final_links = []
        final_titles = []
        final_streamers = []
        while mins < 10:
            min_sec = durations[i].split(":")
            mins += int(min_sec[0])
            secs += int(min_sec[1])
            if secs > 60:
                mins += 1
                secs = secs - 60
            final_links.append(links[i])
            final_titles.append(titles[i])
            final_streamers.append(streamers[i])
            i += 1
            
        return (final_links, final_titles, final_streamers)

    def custom_clips(self):
        streamers = []
        titles = []
        for link in LINKS:
            self.driver.get(link)
            sleep(3)
            title = self.driver.find_element_by_class_name("tw-ellipsis.tw-font-size-4.tw-line-clamp-2.tw-strong.tw-word-break-word").text
            streamer = self.driver.find_element_by_class_name("tw-c-text-base.tw-font-size-4.tw-line-height-heading.tw-strong").text
            streamers.append(streamer)
            titles.append(title)
        return (LINKS, titles, streamers)

    def download_clips(self, links):
        self.driver.get("https://clipr.xyz/")
        sleep(1)
        file_num = 0
        for link in links:
            self.driver.find_element_by_id("clip_url").send_keys(link)
            self.driver.find_element_by_class_name("clipr-button").click()
            sleep(1)
            buttons = self.driver.find_elements_by_class_name("clipr-button")
            buttons[1].click()
            while len(os.listdir("clips/")) < len(links) and file_num != len(os.listdir("clips/")) -1:
                sleep(1)
            file_num += 1
            self.driver.find_element_by_class_name("clipr-link").click()
            all_downloaded = False
            while all_downloaded == False:
                all_downloaded = True
                for name in os.listdir("clips/"):
                    if name.endswith("crdownload"):
                        all_downloaded = False
        self.driver.quit()
        

def edit_video(titles, streamers):
    clip_path = "clips/"
    paths = [os.path.join(clip_path, fname) for fname in os.listdir(clip_path)]
    files = sorted(paths, key=os.path.getctime)
    for idx, file in enumerate(files):
        print(file + " " + titles[idx] + " " + streamers[idx])
    clips = []
    for file in files:
        clip = (VideoFileClip(file)).resize(width=1920)
        clips.append(clip)
    final_clips = []
    for idx, clip in enumerate(clips):
        text = streamers[idx]+"- "+titles[idx]
        if len(text) > 70:
            text = text[:70] + "..."
        txt_clip = TextClip(text,fontsize=50,color='white')
        txt_clip = txt_clip.set_pos('bottom').set_duration(3)
        final_clips.append(CompositeVideoClip([clip, txt_clip]))
    final = concatenate_videoclips(final_clips,  method="compose")
    print("rendering...")
    final.write_videofile("final.mp4", fps=clip.fps,
                      audio_bitrate="1000k", bitrate="4000k", logger=None)
    print("finished")
        

def upload_video(streamers):
    CLIENT_SECRET_FILE = 'client_secret.json'
    API_NAME = 'youtube'
    API_VERSION = 'v3'
    SCOPES = ['https://www.googleapis.com/auth/youtube.upload']

    now = datetime.datetime.now()
    upload_date = now.strftime("%B %d, %Y")

    title = 'Top '+GAME_NAME+' Clips of the Week! | Twitch '+upload_date
    tags = ['Twitch','Twitch.tv','livestream','highlights','best of','clips',\
            'streamer']
    desc_streamers = ''
    for idx, streamer in enumerate(streamers):
        if streamer not in tags:
            tags.append(streamer)
            if idx == len(streamers) - 1:
                desc_streamers = desc_streamers + 'and ' + streamer
            else:
                desc_streamers = desc_streamers + streamer + ', '
    desc = 'Top '+GAME_NAME+' clips from this week! Featuring: '+desc_streamers
    if len(LINKS) > 0:
        title = 'Twitch Highlights | '+upload_date
        desc = 'Twitch highlights from '+upload_date+'! Featuring: '+desc_streamers

    socket.setdefaulttimeout(1200)
    service = Create_Service(CLIENT_SECRET_FILE, API_NAME, API_VERSION, SCOPES)
    request_body = {
        'snippet': {
            'categoryI': 20,
            'title': title,
            'description': desc,
            'tags': tags
        },
        'status': {
            'privacyStatus': 'public',
            'selfDeclaredMadeForKids': False
        },
        'notifySubscribers': True
    }
    mediaFile = MediaFileUpload('final.mp4')
    response_upload = service.videos().insert(
        part='snippet,status',
        body=request_body,
        media_body=mediaFile
    ).execute()
    


clip_downloader = clip_downloader()
info = None
if len(LINKS) > 0:
    info = clip_downloader.custom_clips()
else:
    info = clip_downloader.get_links()
clip_downloader.download_clips(info[0])
edit_video(info[1], info[2])
upload_video(info[2])
