#!/usr/bin/env python3

from bs4 import BeautifulSoup
from bs4.element import ResultSet
import requests
import PySimpleGUI as sg
import threading
import time
from datetime import datetime
import math
import configparser
import os
from playsound import playsound
import json

dirname = os.path.dirname(__file__)
config_filename = os.path.join(dirname, 'config.txt')
notif_sound_filename = os.path.join(dirname, 'notif.wav')
configParser = configparser.RawConfigParser()
configParser.read(config_filename)

# Paste Session ID HERE
id_mw = configParser.get('base-config', 'id_mw')
color_green = "#2bbd5d"
color_red = "#e62020"
color_red_bg = "#ffbaba"
color_yellow_bg = "#ffd857"
color_green_bg = "#b2ff96"

hour_offset = int(configParser.get('base-config', 'hour_offset'))
min_in_h = 60
s_in_min = 60
s_in_h = s_in_min * 60
default_spawn_time = 17 * s_in_h + 30 * s_in_min
default_random_time = s_in_h
custom_spawn_map = {
    "Ketra's Commander Tayr": {"spawn_time": 8 * s_in_h, "random_time": 2 * s_in_h},
    "Ketra's Hero Hekaton": {"spawn_time": 8 * s_in_h, "random_time": 2 * s_in_h},
    "Varka's Commander Mos": {"spawn_time": 8 * s_in_h, "random_time": 2 * s_in_h},
    "Baium": {"spawn_time": 120 * s_in_h, "random_time": 2 * s_in_h, "is_epic": True},
    "Zaken": {"spawn_time": 47 * s_in_h + 30 * s_in_min, "random_time": 60 * s_in_min, "is_epic": True},
    "Core": {"spawn_time": 35 * s_in_h + 30 * s_in_min, "random_time": 60 * s_in_min, "is_epic": True},
    "Orfen": {"spawn_time": 35 * s_in_h + 30 * s_in_min, "random_time": 60 * s_in_min, "is_epic": True},
    "Queen Ant": {"spawn_time": 23 * s_in_h + 30 * s_in_min, "random_time": 60 * s_in_min, "is_epic": True},
    "Valakas": {"spawn_time": 264 * s_in_h, "random_time": 0, "is_epic": True},
    "Longhorn Golkonda": {"spawn_time": 8 * s_in_h, "random_time": 0},
    "Shilen's Messenger Cabrio": {"spawn_time": 8 * s_in_h, "random_time": 0},
    "Flame of Splendor Barakiel": {"spawn_time": 8 * s_in_h, "random_time": 10 * s_in_min},
}

custom_name_map = {
    "Flamestone Giant":   "Flamestone",
    "Ancient Weird Drake": "Ancient D",
    "Queen Ant": "AQ",
    "Hestia, Guardian Deity of the Hot Springs": "Hestia",
}
ignore_rb_below_lvl = int(configParser.get(
    'base-config', 'ignore_rb_below_lvl'))
ignore_rb_above_lvl = int(configParser.get(
    'base-config', 'ignore_rb_above_lvl'))
ignore_list = json.loads(configParser.get('base-config', 'ignore_list'))
allow_list = json.loads(configParser.get('base-config', 'allow_list'))

ALIVE_KEY = 'listboxAlive'
DEAD_KEY = 'listboxDead'
ALIVE_TEXT_KEY = 'aliveText'
DEAD_TEXT_KEY = 'deadText'

# GLOBAL STATE
window = sg.Window("Live RB Info", font=("TkFixedFont"))
error = ''
new_spawn = False
rb_data = []
alive_data = []
dead_data = []


def main():
    initWindow()
    updateList()
    window.read()


def updateWindowWithData():
    global alive_data, dead_data
    listbox_alive = window[ALIVE_KEY]
    listbox_dead = window[DEAD_KEY]
    if error != '':
        listbox_dead.update([])
        listbox_alive.update([])
        text_alive = window[ALIVE_TEXT_KEY]
        text_dead = window[DEAD_TEXT_KEY]
        text_alive.update(error)
        text_dead.update(error)
    update_alive_data()
    alive_text = list(map(lambda rb: rb["text"], alive_data))
    listbox_alive.update(alive_text)
    for i in range(len(alive_data)):
        bg = alive_data[i]["bg"]
        if bg is not None:
            listbox_alive.Widget.itemconfig(i, bg=bg)
    update_dead_data()
    dead_text = list(map(lambda rb: rb["text"], dead_data))
    listbox_dead.update(dead_text)
    for i in range(len(dead_data)):
        bg = dead_data[i]["bg"]
        if bg is not None:
            listbox_dead.Widget.itemconfig(i, bg=bg)
    window.refresh()


def initWindow():
    alive_column = [
        [sg.Text("Alive", text_color=color_green,
                 key=ALIVE_TEXT_KEY, size=(25, 1))],
        [sg.Listbox(key=ALIVE_KEY, values=[], size=(37, 30))]
    ]
    dead_column = [
        [sg.Text("Respawning", text_color=color_red,
                 key=DEAD_TEXT_KEY, size=(25, 1))],
        [sg.Listbox(key=DEAD_KEY, values=[], size=(72, 30),)]
    ]
    layout = [
        [sg.Column(alive_column),
         sg.VSeperator(),
         sg.Column(dead_column)]
    ]
    window.Layout(layout)
    window.Finalize()


def update_alive_data():
    global rb_data, alive_data
    alive_data = [rb for rb in rb_data if rb['status'] == 'Alive']
    alive_data.sort(key=lambda x: x.get('spawned_time'), reverse=True)
    alive_data = list(map(lambda rb: format_alive_rb_string(rb), alive_data))


def format_alive_rb_string(rb):
    f = "{: <2}lv {: <10} - {: <5} for {: <4} min"
    lvl = rb['lvl']
    name = rb['name']
    minutes = int((time.time() - rb['spawned_time']) / s_in_min)
    bg = None
    if minutes <= 5:
        bg = color_green_bg
    return {"text": f.format(lvl, name, 'Alive', minutes), "bg": bg}


def update_dead_data():
    global rb_data, dead_data
    dead_data = [rb for rb in rb_data if rb['status'] != 'Alive']
    dead_data.sort(key=lambda x: x.get('time_till_spawn'))
    dead_data = list(map(lambda rb: format_dead_rb_string(rb), dead_data))


def format_dead_rb_string(rb):
    f = "{}lv {: <10} - left {:0>2d}:{:0>2d} - random {:0>2d}:{:0>2d} - spawn start {:0>2d}/{:0>2d} {:0>2d}:{:0>2d}"
    lvl = rb['lvl']
    name = rb['name']
    time_till_spawn = rb['time_till_spawn']
    spawn_random_time = rb['spawn_random_time']
    left_hh = max(int(time_till_spawn/s_in_h), 0)
    left_mm = max(int(math.fmod(time_till_spawn/s_in_min, min_in_h)), 0)
    random_hh = int((spawn_random_time) / s_in_h)
    random_mm = int(((spawn_random_time) / s_in_min) % min_in_h)
    bg = None
    if time_till_spawn <= 0:
        bg = color_yellow_bg
        random_hh = int((spawn_random_time + time_till_spawn) / s_in_h)
        random_mm = int(
            ((spawn_random_time + time_till_spawn) / s_in_min) % min_in_h)
    spawn_start_dt = datetime.fromtimestamp(
        rb['spawn_start_time'])

    return {"text": f.format(lvl, name, left_hh, left_mm, random_hh, random_mm,
                             spawn_start_dt.month, spawn_start_dt.day,
                             spawn_start_dt.hour, spawn_start_dt.minute), "bg": bg}


def notify_new_raid():
    playsound(notif_sound_filename)


def updateList():
    global new_spawn
    thread = threading.Timer(60.0, updateList)
    thread.daemon = True
    thread.start()
    fetch_data()
    updateWindowWithData()
    if new_spawn:
        new_spawn = False
        notify_new_raid()


def fetch_data():
    global rb_data, error
    cookies = {
        'PHPSESSID': '1395e9de8925589f0441ea31221b8673',
        '_fbp': 'fb.1.1602499220334.475332614',
        '__cfduid': 'da3292ac53acf5a393c582d2bc1ce0a261608156963',
        'utm_source': '	lineage2dex.com',
        'fixed': 'elem346%2Celem306',
        'id_mw': id_mw}
    url = 'https://lineage2dex.com/cabinet/rating'

    data = requests.get(url, cookies=cookies).text
    html = BeautifulSoup(data, 'html.parser')
    raids_div = html.find('div', {'id': 'RAID'})
    if raids_div is None:
        rb_data = []
        error = "Error! Add new id_mw"
    else:
        raid_trs = raids_div.find('tbody').findAll('tr')
        raids = [parse_tr(tr) for tr in raid_trs]
        update_rb_data(raids)
        error = ''


def update_rb_data(raids):
    global rb_data, new_spawn
    old_data = rb_data
    rb_data = []
    for rb in raids:
        rb_name = rb['name']
        lvl = int(rb['lvl'])
        if (lvl < ignore_rb_below_lvl or lvl > ignore_rb_above_lvl or rb_name in ignore_list) and rb_name not in allow_list:
            continue
        short_name = rb_name.split()[-1]
        if rb_name in custom_name_map:
            short_name = custom_name_map[rb_name]
        new_rb_data = {'nr': rb['nr'], 'name': short_name,
                       'lvl': rb['lvl'], 'status': rb['status']}
        if (new_rb_data['status'] == 'Alive'):
            old_rb_data = next(
                (x for x in old_data if x["nr"] == rb['nr'] and x["status"] == rb['status']), None)
            if old_rb_data == None:  # check if new spawn happened
                new_spawn = True
                new_rb_data['spawned_time'] = time.time()
            else:
                new_rb_data['spawned_time'] = old_rb_data['spawned_time']
            new_rb_data['time_till_spawn'] = 0
            new_rb_data['spawn_started'] = False
            new_rb_data['spawn_random_time'] = 0
            new_rb_data['spawn_start_time'] = 0
        else:
            death_ms = datetime.strptime(
                rb['status'], "%y/%m/%d %H:%M").timestamp()
            death_ms = death_ms + hour_offset * s_in_h
            min_spawn_ms = default_spawn_time
            spawn_random_time = default_random_time
            if rb_name in custom_spawn_map:
                min_spawn_ms = custom_spawn_map[rb_name]["spawn_time"]
                spawn_random_time = custom_spawn_map[rb_name]["random_time"]
            spawn_start_time = death_ms + min_spawn_ms
            new_rb_data['spawned_time'] = 0
            new_rb_data['spawn_start_time'] = spawn_start_time
            new_rb_data['time_till_spawn'] = spawn_start_time - time.time()
            new_rb_data['spawn_random_time'] = spawn_random_time
            new_rb_data['spawn_started'] = False
        rb_data.append(new_rb_data)


def parse_tr(tr):
    tds = tr.findAll('td')
    nr = tds[0].text
    name = tds[1].text
    lvl = tds[2].text
    status = tds[3].find('span').text
    item = {'nr': nr, 'name': name, 'lvl': lvl, 'status': status}
    return item


if __name__ == "__main__":
    main()
