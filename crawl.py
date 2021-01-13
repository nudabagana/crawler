#!/usr/bin/env python3

from bs4 import BeautifulSoup
from bs4.element import ResultSet
import requests
import PySimpleGUI as sg

# Paste Session ID HERE
id_mw = 'mmoweb_5ffc6b3841c842.73487910'

ALIVE_KEY = 'listboxAlive'

def main():
    rb_data = get_data()
    alive_data = [rb for rb in rb_data if rb['status'] == 'Alive']
    table_values = list(map(lambda rb : "{}lvl - {} - {}".format(rb['lvl'], rb['name'], rb['status']), alive_data))
    layout = [
             [sg.Text("RB Alive")],
             [ sg.Listbox(key=ALIVE_KEY, values=table_values, size=(50, 25))]
             ]
    window = sg.Window("Live RB Info", layout, font="20")

    window.Finalize()

    # listbox = window['Listbox']
    # index = listbox.GetIndexes()
    # listbox.Widget.itemconfig(0, fg='red', bg='light blue')
    window.read()


def get_data():
    cookies = {
            'PHPSESSID': '1395e9de8925589f0441ea31221b8673',
            '_fbp': 'fb.1.1602499220334.475332614',
            '__cfduid': 'da3292ac53acf5a393c582d2bc1ce0a261608156963',
            'utm_source': '	lineage2dex.com',
            'fixed': 'elem346%2Celem306',
            'id_mw': id_mw }
    url = 'https://lineage2dex.com/cabinet/rating'

    data = requests.get(url, cookies=cookies).text
    html = BeautifulSoup(data, 'html.parser')
    raids_div = html.find('div', {'id': 'RAID'})
    if raids_div is None:
        return []
    else:
        raid_trs = raids_div.find('tbody').findAll('tr')
        raids = [parse_tr(tr) for tr in raid_trs]
        return raids

        # for raid in raids:
        #     text = " ".join([x for x in raid.values()])
        #     print(text)

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
