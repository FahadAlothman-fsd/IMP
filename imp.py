import dearpygui.dearpygui as dpg
import ntpath
import json
from mutagen.mp3 import MP3
from mutagen.oggvorbis import OggVorbis
from mutagen.wave import WAVE
import pygame
import time
import os
import random
from datetime import datetime, date as dt, timedelta
import atexit
from prayertimes import PrayTimes
from threading import Thread

# from typing import Literal


BACKGROUND_COLOR = (17, 17, 34, 255)
SECTION_BG_COLOR = (89, 27, 79, 255)
BUTTON_COLOR = (111, 34, 101)
TEXT_COLOR = (225, 204, 153, 255)
_DEFAULT_MUSIC_VOLUME = 0.5


dpg.create_context()
prayTimes = PrayTimes()
prayTimes.setMethod("Makkah")
global state, paused_for_prayer, loop, date, clock, prayers, timezone, current_prayer, song_length, volume, config, songs, paused_for_additonal_time
dpg.create_viewport(title="IMP", large_icon="imp.ico", small_icon="imp.ico")
pygame.mixer.init()


volume = _DEFAULT_MUSIC_VOLUME
timezone = 3
state = None
paused_for_prayer = False
paused_for_additonal_time = False
loop = -1
date = dt.today()
clock = datetime.now().time()
current_prayer = None
song_length = 1


def load_database():
    global config, songs
    # Check if the "data" directory exists
    data_dir = os.path.join(os.getcwd(), "data")
    if not os.path.exists(data_dir):
        os.mkdir(data_dir)

    # Check if the "songs.json" file exists
    songs_file = os.path.join(data_dir, "songs.json")
    config_file = os.path.join(data_dir, "config.json")
    if not os.path.exists(songs_file):
        # Create the file
        with open(songs_file, "w") as f:
            f.write(json.dumps({"songs": []}, indent=4))

    if not os.path.exists(config_file):
        # Create the file
        with open(config_file, "w") as f:
            f.write(
                json.dumps(
                    {
                        "config": {
                            "tbp": 5,
                            "latitude": 24.7136,
                            "longitude": 46.6753,
                            "timezone": 3,
                            "dst": 0,
                            "method": "Makkah",
                            "mode": "Normal",
                        },
                        "duration": {
                            "Imsak": 20,
                            "Fajr": 40,
                            "Dhuhr": 40,
                            "Asr": 40,
                            "Sunset": 25,
                            "Maghrib": 25,
                            "Isha": 40,
                        },
                        "additional_times": [],
                    },
                    indent=4,
                )
            )

    config = json.load(open(config_file, "r+"))
    # Open the "songs.json" file
    songs = json.load(open("data/songs.json", "r+"))["songs"]


load_database()
# print(config)


def get_prayer_times():
    global date, timezone, config
    times = prayTimes.getTimes(
        date,
        (config["config"]["latitude"], config["config"]["longitude"]),
        config["config"]["timezone"],
        config["config"]["dst"],
    )
    prayers = []
    prayer_times = {}
    if config["config"]["mode"] == "Normal":
        prayers = ["Fajr", "Dhuhr", "Asr", "Maghrib", "Isha"]
    elif config["config"]["mode"] == "Ramadan":
        prayers = ["Imsak", "Fajr", "Dhuhr", "Asr", "Sunset", "Maghrib", "Isha"]
    for i in prayers:
        prayer_times[i] = {"time": datetime.strptime(times[i.lower()], "%H:%M").time(), "duration": config["duration"][i]}  # type: ignore
    # prayer_times["test_prayer"] = {
    #     "time": datetime.strptime("02:38", "%H:%M").time(),
    #     "duration": 2,
    # }
    return prayer_times


prayers = get_prayer_times()

pygame.mixer.music.set_volume(0.5)


def calc_time(prayertime, timedel, op):
    if op == "+":
        return (
            datetime.combine(datetime.now().date(), prayertime)
            + timedelta(minutes=timedel)
        ).time()
    return (
        datetime.combine(datetime.now().date(), prayertime) - timedelta(minutes=timedel)
    ).time()


def render_prayers():
    global prayers
    for i in prayers:
        fourty_five_minutes_after_prayer = calc_time(
            prayers[i]["time"], prayers[i]["duration"], "+"
        )
        dpg.add_text(
            label=f"{i}",
            tag=i,
            parent="prayer_times",
            default_value=f"{i}: {prayers[i]['time'].strftime('%I:%M %p')} - {prayers[i]['duration']}m",
        )
        if clock >= fourty_five_minutes_after_prayer:
            dpg.configure_item(i, color=(137, 135, 122, 255))


def render_additional_times():
    global config
    for i in config["additional_times"]:
        # print(i, i["time"], i["duration"], "line 156")
        fourty_five_minutes_after_prayer = calc_time(
            datetime.strptime(i["time"], "%H:%M").time(), i["duration"], "+"
        )
        dpg.add_text(
            label=f"{i['name']}",
            tag=f"{i['name']}",
            parent="additional_times_text",
            default_value=f"{i['name']}: {datetime.strptime(i['time'], '%H:%M').time().strftime('%I:%M %p')} - {i['duration']}m",
        )
        if clock >= fourty_five_minutes_after_prayer:
            dpg.configure_item(f"{i['name']}", color=(137, 135, 122, 255))


def render_additional_times_inputs():
    global config
    # print(config["additional_times"])
    for index, additional_time in enumerate(config["additional_times"]):
        # print("------------\n", additional_time, index, "line 692")
        with dpg.group(
            horizontal=True,
            horizontal_spacing=10,
            parent="additional_times_inputs",
        ):
            dpg.add_input_text(
                label="Name",
                width=100,
                tag=f"name{index}",
                default_value=additional_time["name"],
            )
            dpg.add_input_text(
                width=100,
                label="Time (HH:MM) 24h",
                tag=f"time{index}",
                default_value=additional_time["time"],
            )
            dpg.add_input_int(
                min_clamped=True,
                min_value=0,
                width=100,
                step=0,
                label="Duration (minutes)",
                tag=f"duration{index}",
                default_value=additional_time["duration"],
            )
            dpg.add_button(
                label="-",
                callback=delete_time_callback,
                user_data=index,
                tag=f"delete{index}",
            )


def config_prayers():
    global prayers
    for i in prayers:
        dpg.configure_item(
            i,
            default_value=f"{i}: {prayers[i].strftime('%I:%M %p')}",
        )


def loop_callback(sender, app_data):
    global loop
    if loop == -1:
        # print("loop callback")
        loop = 0
        dpg.configure_item("loop", default_value="Loop: Off")
    else:
        loop = -1
        dpg.configure_item("loop", default_value="Loop: On")


def fade_to_pause():
    global volume
    print("fade to pause")
    while volume > 0:
        volume -= 0.01
        pygame.mixer.music.set_volume(volume)
        dpg.configure_item("volume", default_value=volume * 100)
        time.sleep(0.1)
    pygame.mixer.music.pause()


def fade_to_unpause():
    global volume
    print("fade to unpause")
    pygame.mixer.music.unpause()
    while volume < 0.5:
        volume += 0.01
        pygame.mixer.music.set_volume(volume)
        dpg.configure_item("volume", default_value=volume * 100)
        time.sleep(0.1)


def prayer_callback():
    global prayers, paused_for_prayer, clock, current_prayer, state, config, paused_for_additonal_time
    if (
        current_prayer is None
        and not paused_for_prayer
        and not paused_for_additonal_time
    ):
        for prayer in prayers:
            pause_begin = calc_time(
                prayers[prayer]["time"], config["config"]["tbp"], "-"
            )
            pause_duration = calc_time(
                prayers[prayer]["time"], prayers[prayer]["duration"], "+"
            )
            if clock >= pause_begin and clock < pause_duration:
                # print(state)
                paused_for_prayer = True
                current_prayer = prayer
                if state == "playing":
                    Thread(target=fade_to_pause).start()
                dpg.configure_item(prayer, color=(0, 255, 0, 255))
                dpg.configure_item(
                    "cstate",
                    default_value=f"State: Paused For {prayer}",
                    color=(255, 0, 0, 255),
                )
                break
    elif (
        current_prayer is not None
        and paused_for_prayer
        and not paused_for_additonal_time
    ):
        pause_duration = calc_time(
            prayers[current_prayer]["time"], prayers[current_prayer]["duration"], "+"
        )
        if clock >= pause_duration:
            paused_for_prayer = False
            if state == "playing" and not paused_for_additonal_time:
                print("fade to unpause", "line 290")
                Thread(target=fade_to_unpause).start()
            dpg.configure_item(current_prayer, color=(137, 135, 122, 255))
            current_prayer = None
            dpg.configure_item(
                "cstate",
                default_value=f"State: {state}",
                color=(255, 255, 255, 255),
            )


def additonal_times_callback():
    global paused_for_prayer, clock, current_prayer, state, config, paused_for_additonal_time
    if (
        current_prayer is None
        and not paused_for_prayer
        and not paused_for_additonal_time
    ):
        for prayer in [
            i
            for i in config["additional_times"]
            if i["name"] != "" and i["time"] != "" and i["duration"] != 0
        ]:
            pause_begin = calc_time(
                datetime.strptime(prayer["time"], "%H:%M").time(),
                config["config"]["tbp"],
                "-",
            )
            pause_duration = calc_time(
                datetime.strptime(prayer["time"], "%H:%M").time(),
                prayer["duration"],
                "+",
            )
            if clock >= pause_begin and clock < pause_duration:
                # print(state)
                paused_for_additonal_time = True
                current_prayer = prayer["name"]
                if state == "playing":
                    Thread(target=fade_to_pause, name="fade to pause").start()
                dpg.configure_item(prayer["name"], color=(0, 255, 0, 255))
                dpg.configure_item(
                    "cstate",
                    default_value=f"State: Paused For {current_prayer}",
                    color=(255, 0, 0, 255),
                )
                break
    elif (
        current_prayer is not None
        and not paused_for_prayer
        and paused_for_additonal_time
    ):
        current_prayer = [
            i for i in config["additional_times"] if i["name"] == current_prayer
        ][0]

        pause_duration = calc_time(
            datetime.strptime(current_prayer["time"], "%H:%M").time(),
            current_prayer["duration"],
            "+",
        )
        if clock >= pause_duration:
            paused_for_additonal_time = False
            if state == "playing":
                print("fade to unpause", "line 352")
                Thread(target=fade_to_unpause, name="fade to unpause").start()
            dpg.configure_item(current_prayer["name"], color=(137, 135, 122, 255))
            current_prayer = None
            dpg.configure_item(
                "cstate",
                default_value=f"State: {state}",
                color=(255, 255, 255, 255),
            )
        else:
            current_prayer = current_prayer["name"]


def clock_callback():
    global clock
    clock = datetime.now().time()
    dpg.configure_item("clock", default_value=f"Clock: {clock.strftime('%I:%M:%S %p')}")


def date_callback():
    global date, prayers
    if dt.today() > date:
        date = dt.today()
        prayers = get_prayer_times()
        dpg.configure_item("date", default_value=f"Date: {date.strftime('%d/%m/%Y')}")
        config_prayers()


def update_volume(sender, app_data):
    pygame.mixer.music.set_volume(app_data / 100.0)


def load_songs():
    for filename in songs:
        dpg.add_button(
            label=f"{ntpath.basename(filename)}",
            callback=play,
            width=-1,
            height=25,
            user_data=filename.replace("\\", "/"),
            parent="list",
        )
        dpg.add_spacer(height=2, parent="list")


def update_database(filename: str):
    data = json.load(open("data/songs.json", "r+"))
    if filename not in data["songs"]:
        data["songs"] += [filename]
    json.dump(data, open("data/songs.json", "r+"), indent=4, ensure_ascii=True)


def save_config(sender, app_data, user_data):
    global config, prayers

    # print("sender", sender)
    # print("app_data", app_data)
    # print("user_data", user_data)
    tpb = dpg.get_value("tbp")
    longitude = round(dpg.get_value("lon"), 6)
    latitude = round(dpg.get_value("lat"), 6)
    timezone = dpg.get_value("tz")
    dst = dpg.get_value("dst")
    method = dpg.get_value("method")
    mode = dpg.get_value("mode")

    # Create an object to store the values
    config_object = {
        "tbp": tpb,
        "longitude": longitude,
        "latitude": latitude,
        "timezone": timezone,
        "dst": dst,
        "method": method,
        "mode": mode,
    }
    config["config"] = config_object
    # print(config_object)

    prayTimes.setMethod(method)
    prayers = []
    prayer_times = config["duration"]

    if mode == "Normal":
        prayers = ["Fajr", "Dhuhr", "Asr", "Maghrib", "Isha"]
    elif mode == "Ramadan":
        prayers = ["Imsak", "Fajr", "Dhuhr", "Asr", "Sunset", "Maghrib", "Isha"]

    for prayer in prayers:
        prayer_times[prayer] = dpg.get_value(prayer.lower())

    # print(prayer_times)
    config["duration"] = prayer_times

    additional_times_values = []
    num_additional_times = 0
    while True:
        name = dpg.get_value(f"name{num_additional_times}")
        time = dpg.get_value(f"time{num_additional_times}")
        duration = dpg.get_value(f"duration{num_additional_times}")
        if name is None or time is None:
            break
        additional_times_values.append(
            {"name": name, "time": time, "duration": duration}
        )
        num_additional_times += 1
    # print(additional_times_values)
    config["additional_times"] = additional_times_values
    # print(config, "line 392")
    json.dump(config, open("data/config.json", "w"), indent=4, ensure_ascii=True)
    prayers = get_prayer_times()
    dpg.delete_item("prayer_times", children_only=True)
    render_prayers()
    dpg.delete_item("additional_times_text", children_only=True)
    render_additional_times()


def mode_callback(sender, app_data):
    dpg.delete_item("prayer_group", children_only=True)
    render_config_prayers(app_data)


def render_config_prayers(mode):
    global config
    prayers = []
    if mode == "Normal":
        prayers = ["Fajr", "Dhuhr", "Asr", "Maghrib", "Isha"]
    elif mode == "Ramadan":
        prayers = ["Imsak", "Fajr", "Dhuhr", "Asr", "Sunset", "Maghrib", "Isha"]

    for prayer in prayers:
        with dpg.group(horizontal=True, horizontal_spacing=10, parent="prayer_group"):
            dpg.add_input_int(
                min_clamped=True,
                min_value=0,
                width=100,
                step=0,
                label=f"{prayer} (minutes)",
                tag=prayer.lower(),
                default_value=config["duration"][prayer],
            )
        dpg.add_spacer(height=5, parent="prayer_group")


def add_time_callback(sender):
    global config
    config["additional_times"].append({"name": "", "time": "", "duration": 0})
    # print(config["additional_times"], "line 433")
    index = len(config["additional_times"]) - 1
    with dpg.group(
        horizontal=True,
        horizontal_spacing=10,
        parent="additional_times_inputs",
        tag=f"additional_time{index}",
        height=20,
    ):
        dpg.add_input_text(
            label="Name",
            width=100,
            tag=f"name{index}",
            default_value=config["additional_times"][index]["name"],
        )
        dpg.add_input_text(
            width=100,
            label="Time (HH:MM) 24h",
            tag=f"time{index}",
            default_value=config["additional_times"][index]["time"],
        )
        dpg.add_input_int(
            min_clamped=True,
            min_value=0,
            width=100,
            step=0,
            label="Duration (minutes)",
            tag=f"duration{index}",
            default_value=config["additional_times"][index]["duration"],
        )
        dpg.add_button(
            label="-",
            callback=delete_time_callback,
            user_data=index,
            tag=f"delete{index}",
        )

        # dpg.add_spacer(height=5, parent="additional_times")


def delete_time_callback(sender, user_data, index):
    global config
    config["additional_times"].pop(index)
    dpg.delete_item("additional_times_inputs", children_only=True)
    render_additional_times_inputs()


def update_track():
    global song_length
    dpg.configure_item(
        item="pos", default_value=((pygame.mixer.music.get_pos() / 1000) % song_length)
    )


def play(sender, app_data, user_data):
    global state, loop, paused_for_prayer, song_length
    if not paused_for_prayer or not paused_for_additonal_time:
        if user_data:
            pygame.mixer.music.load(user_data)
            if user_data.endswith(".mp3"):
                audio = MP3(user_data)
            if user_data.endswith(".wav"):
                audio = WAVE(user_data)
            if user_data.endswith(".ogg"):
                audio = OggVorbis(user_data)

            song_length = audio.info.length  # type: ignore
            dpg.configure_item(item="pos", max_value=audio.info.length)  # type: ignore
            pygame.mixer.music.play(loop)
            if pygame.mixer.music.get_busy():
                dpg.configure_item("play", label="Pause")
                state = "playing"
                dpg.configure_item("cstate", default_value=f"State: Playing")
                dpg.configure_item(
                    "csong", default_value=f"Now Playing : {ntpath.basename(user_data)}"
                )


def play_pause():
    global state, paused_for_prayer, loop, song_length, paused_for_additonal_time

    if state == "playing" and (not paused_for_prayer):
        if not paused_for_additonal_time:
            state = "paused"
            pygame.mixer.music.pause()
            dpg.configure_item("play", label="Play")
            dpg.configure_item("cstate", default_value=f"State: Paused")
    elif state == "paused" and (not paused_for_prayer):
        if not paused_for_additonal_time:
            state = "playing"
            pygame.mixer.music.unpause()
            dpg.configure_item("play", label="Pause")
            dpg.configure_item("cstate", default_value=f"State: Playing")
    else:
        song = json.load(open("data/songs.json", "r"))["songs"]
        if song:
            song = random.choice(song)
            pygame.mixer.music.load(song)
            if not paused_for_prayer:
                if not paused_for_additonal_time:
                    pygame.mixer.music.play(loop)
                    dpg.configure_item("play", label="Pause")
            if pygame.mixer.music.get_busy():
                state = "playing"
            if song.endswith(".mp3"):
                audio = MP3(song)
            if song.endswith(".wav"):
                audio = WAVE(song)
            if song.endswith(".ogg"):
                audio = OggVorbis(song)

                song_length = audio.info.length  # type: ignore
                # print(audio.info.length, "song_length", "line 546")  # type: ignore
                dpg.configure_item(item="pos", max_value=song_length)
                dpg.configure_item(
                    "csong", default_value=f"Now Playing : {ntpath.basename(song)}"
                )
                dpg.configure_item("cstate", default_value=f"State: Playing")


def stop():
    global state
    pygame.mixer.music.stop()
    state = None

    dpg.configure_item("cstate", default_value=f"State: {state}")
    dpg.configure_item("csong", default_value="Now Playing : ")
    dpg.configure_item("play", label="Play")
    dpg.configure_item(item="pos", max_value=100)
    dpg.configure_item(item="pos", default_value=0)


def add_files(sender, app_data):
    data = json.load(open("data/songs.json", "r"))
    filename = app_data["selections"]
    # print(filename)
    for key in filename:
        file = filename[key]
        if file.endswith(".mp3") or file.endswith(".wav") or file.endswith(".ogg"):
            if file not in data["songs"]:
                update_database(file)
                dpg.add_button(
                    label=f"{ntpath.basename(file)}",
                    callback=play,
                    width=-1,
                    height=25,
                    user_data=file.replace("\\", "/"),
                    parent="list",
                )
                dpg.add_spacer(height=2, parent="list")


def search(sender, app_data, user_data):
    songs = json.load(open("data/songs.json", "r"))["songs"]
    dpg.delete_item("list", children_only=True)
    for _, song in enumerate(songs):
        if app_data in song.lower():
            dpg.add_button(
                label=f"{ntpath.basename(song)}",
                callback=play,
                width=-1,
                height=25,
                user_data=song,
                parent="list",
            )
            dpg.add_spacer(height=2, parent="list")


def removeall():
    songs = json.load(open("data/songs.json", "r"))
    songs["songs"].clear()
    json.dump(songs, open("data/songs.json", "w"), indent=4)
    dpg.delete_item("list", children_only=True)
    load_database()


with dpg.theme(tag="base"):
    with dpg.theme_component():
        dpg.add_theme_color(dpg.mvThemeCol_WindowBg, BACKGROUND_COLOR)
        dpg.add_theme_color(dpg.mvThemeCol_Text, TEXT_COLOR)
        dpg.add_theme_color(dpg.mvThemeCol_Button, BUTTON_COLOR)
        dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (137, 142, 255, 95))
        dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, BUTTON_COLOR)
        dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 3)
        dpg.add_theme_style(dpg.mvStyleVar_ChildRounding, 4)
        dpg.add_theme_style(dpg.mvStyleVar_FramePadding, 4, 4)
        dpg.add_theme_style(dpg.mvStyleVar_WindowRounding, 4, 4)
        dpg.add_theme_style(dpg.mvStyleVar_WindowTitleAlign, 0.50, 0.50)
        dpg.add_theme_style(dpg.mvStyleVar_WindowBorderSize, 0)
        dpg.add_theme_style(dpg.mvStyleVar_WindowPadding, 10, 14)
        dpg.add_theme_color(dpg.mvThemeCol_ChildBg, SECTION_BG_COLOR)
        dpg.add_theme_color(dpg.mvThemeCol_Border, (0, 0, 0, 0))
        dpg.add_theme_color(dpg.mvThemeCol_ScrollbarBg, (0, 0, 0, 0))
        dpg.add_theme_color(dpg.mvThemeCol_TitleBgActive, (130, 142, 250))
        dpg.add_theme_color(dpg.mvThemeCol_CheckMark, (221, 166, 185))
        dpg.add_theme_color(dpg.mvThemeCol_FrameBgHovered, (172, 174, 197))

with dpg.theme(tag="slider_thin"):
    with dpg.theme_component():
        dpg.add_theme_color(dpg.mvThemeCol_FrameBgActive, (130, 142, 250, 99))
        dpg.add_theme_color(dpg.mvThemeCol_FrameBgHovered, (130, 142, 250, 99))
        dpg.add_theme_color(dpg.mvThemeCol_SliderGrabActive, (255, 255, 255))
        dpg.add_theme_color(dpg.mvThemeCol_SliderGrab, (255, 255, 255))
        dpg.add_theme_color(dpg.mvThemeCol_FrameBg, (130, 142, 250, 99))
        dpg.add_theme_style(dpg.mvStyleVar_GrabRounding, 3)
        dpg.add_theme_style(dpg.mvStyleVar_GrabMinSize, 30)

with dpg.theme(tag="slider"):
    with dpg.theme_component():
        dpg.add_theme_color(dpg.mvThemeCol_FrameBgActive, (130, 142, 250, 99))
        dpg.add_theme_color(dpg.mvThemeCol_FrameBgHovered, (130, 142, 250, 99))
        dpg.add_theme_color(dpg.mvThemeCol_SliderGrabActive, (255, 255, 255))
        dpg.add_theme_color(dpg.mvThemeCol_SliderGrab, (255, 255, 255))
        dpg.add_theme_color(dpg.mvThemeCol_FrameBg, (130, 142, 250, 99))
        dpg.add_theme_style(dpg.mvStyleVar_GrabRounding, 3)
        dpg.add_theme_style(dpg.mvStyleVar_GrabMinSize, 30)

with dpg.theme(tag="songs"):
    with dpg.theme_component():
        dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 2)
        dpg.add_theme_color(dpg.mvThemeCol_Button, (89, 89, 144, 40))
        dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (0, 0, 0, 0))

# with dpg.font_registry():
#     monobold = dpg.add_font("fonts/MonoLisa-Bold.ttf", 12)
#     head = dpg.add_font("fonts/MonoLisa-Bold.ttf", 15)


with dpg.file_dialog(
    directory_selector=False,
    show=False,
    callback=add_files,
    tag="add_files_dialog",
    width=700,
    height=400,
):
    dpg.add_file_extension(
        "Source files (*.mp3 *.wav *.ogg){.mp3,.wav,.ogg}", color=(0, 255, 255, 255)
    )
    dpg.add_file_extension(".mp3", color=(255, 0, 255, 255), custom_text="[mp3]")
    dpg.add_file_extension(".wav", color=(0, 255, 0, 255), custom_text="[wav]")
    dpg.add_file_extension(".ogg", color=(0, 0, 255, 255), custom_text="[ogg]")


with dpg.window(tag="main", label="window title"):
    with dpg.child_window(autosize_x=True, height=45, no_scrollbar=True):
        dpg.add_text(f"Now Playing : ", tag="csong")
    dpg.add_spacer(height=2)

    with dpg.window(
        tag="config_settings",
        label="Settings",
        width=800,
        height=400,
        show=False,
        pos=[200, 100],
    ):
        with dpg.tab_bar(label="Prayer Settings"):
            with dpg.tab(label="Configurations"):
                dpg.add_spacer(height=20)

                dpg.add_input_int(
                    default_value=config["config"]["tbp"],
                    step=0,
                    min_clamped=True,
                    min_value=0,
                    label="Time Before Prayer (minutes)",
                    tag="tbp",
                    width=100,
                )
                dpg.add_spacer(height=15)
                dpg.add_input_float(
                    default_value=config["config"]["longitude"],
                    step=0,
                    max_value=180,
                    min_value=-180,
                    max_clamped=True,
                    min_clamped=True,
                    format="%.6f",
                    label="Longitude",
                    tag="lon",
                    width=100,
                )
                dpg.add_spacer(height=5)
                dpg.add_input_float(
                    default_value=config["config"]["latitude"],
                    step=0,
                    format="%.6f",
                    max_value=90,
                    min_value=-90,
                    max_clamped=True,
                    min_clamped=True,
                    label="Latitude",
                    tag="lat",
                    width=100,
                )
                dpg.add_spacer(height=15)
                dpg.add_input_int(
                    default_value=config["config"]["timezone"],
                    step=0,
                    label="Timezone",
                    tag="tz",
                    width=100,
                )
                dpg.add_spacer(height=5)
                dpg.add_input_int(
                    default_value=config["config"]["dst"],
                    step=0,
                    label="DST",
                    tag="dst",
                    width=100,
                )
                dpg.add_spacer(height=15)
                dpg.add_combo(
                    label="Method",
                    tag="method",
                    items=[
                        "MWL",
                        "ISNA",
                        "Egypt",
                        "Makkah",
                        "Karachi",
                        "Tehran",
                        "Jafari",
                    ],
                    default_value=config["config"]["method"],
                    width=100,
                )
                dpg.add_spacer(height=15)
                dpg.add_combo(
                    label="Mode",
                    tag="mode",
                    items=["Normal", "Ramadan"],
                    default_value=config["config"]["mode"],
                    callback=mode_callback,
                    width=100,
                )
                dpg.add_spacer(height=20)

            with dpg.tab(label="Prayers"):
                dpg.add_text("Please pick the pause duration of each prayer")
                dpg.add_spacer(height=15)
                with dpg.group(tag="prayer_group"):
                    render_config_prayers("Normal")
                dpg.add_spacer(height=15)
                dpg.add_separator(show=True, label="Additonal Times")
                dpg.add_spacer(height=15)
                with dpg.group(tag="additional_times"):
                    dpg.add_text(default_value="Additional Times", indent=300)
                    with dpg.group(horizontal=True, horizontal_spacing=10):
                        dpg.add_button(
                            label="Add", callback=add_time_callback, width=100
                        )

                    dpg.add_spacer(height=15)
                    with dpg.group(tag="additional_times_inputs"):
                        if len(config["additional_times"]) > 0:
                            render_additional_times_inputs()

        dpg.add_separator()
        dpg.add_spacer(height=15)
        with dpg.group(horizontal=True, horizontal_spacing=10):
            dpg.add_button(label="Save", callback=save_config)
            dpg.add_button(
                label="Cancel",
                callback=lambda: dpg.hide_item("config_settings"),
            )

    with dpg.group(horizontal=True):
        with dpg.child_window(width=300, tag="sidebar"):
            dpg.add_text(f"Date: {datetime.now().strftime('%d/%m/%Y')}", tag="date")
            dpg.add_text(f"Clock: {clock.strftime('%I:%M:%S %p')}", tag="clock")
            dpg.add_spacer(height=7)
            dpg.add_separator()
            dpg.add_spacer(height=5)
            dpg.add_button(
                label="Add Files",
                width=-1,
                height=28,
                callback=lambda: dpg.show_item("add_files_dialog"),
            )
            dpg.add_button(
                label="Remove All Songs", width=-1, height=28, callback=removeall
            )
            dpg.add_button(
                label="Settings",
                width=-1,
                height=28,
                callback=lambda: dpg.show_item("config_settings"),
            )

            dpg.add_spacer(height=5)
            dpg.add_separator()
            dpg.add_spacer(height=5)
            dpg.add_text(f"State: {state}", tag="cstate")
            dpg.add_spacer(height=5)
            dpg.add_text(f"Loop: {'On' if loop == -1 else 'Off'}", tag="loop")
            dpg.add_spacer(height=5)
            dpg.add_separator()
            dpg.add_spacer(height=5)
            with dpg.group(tag="prayer_times"):
                render_prayers()
            dpg.add_spacer(height=5)
            dpg.add_separator()
            dpg.add_spacer(height=5)
            with dpg.group(tag="additional_times_text"):
                render_additional_times()

        with dpg.child_window(autosize_x=True, border=False):
            with dpg.child_window(autosize_x=True, height=50, no_scrollbar=True):
                with dpg.group(horizontal=True):
                    dpg.add_button(
                        label="Play",
                        width=65,
                        height=30,
                        tag="play",
                        callback=play_pause,
                    )
                    dpg.add_button(label="Stop", callback=stop, width=65, height=30)
                    dpg.add_button(
                        label="Loop", callback=loop_callback, width=65, height=30
                    )

                    dpg.add_slider_float(
                        tag="volume",
                        width=120,
                        height=15,
                        pos=(230, 19),
                        format="%.0f%.0%",
                        default_value=_DEFAULT_MUSIC_VOLUME * 100,
                        callback=update_volume,
                    )

            with dpg.child_window(autosize_x=True, height=50, no_scrollbar=True):
                dpg.add_slider_float(tag="pos", width=-1, pos=(10, 19), format="")

            with dpg.child_window(autosize_x=True, delay_search=True):
                with dpg.group(horizontal=True, tag="query"):
                    dpg.add_input_text(
                        hint="Search for a song", width=-1, callback=search
                    )
                dpg.add_spacer(height=5)
                with dpg.child_window(autosize_x=True, delay_search=True, tag="list"):
                    load_songs()

    dpg.bind_item_theme("volume", "slider_thin")
    dpg.bind_item_theme("pos", "slider")
    dpg.bind_item_theme("list", "songs")
    dpg.bind_item_theme("query", "songs")

dpg.bind_theme("base")
# dpg.bind_font(monobold)


def safe_exit():
    pygame.mixer.music.stop()
    pygame.quit()


prayer_callback()

app_start = dpg.get_total_time()
clock_start = app_start
date_start = app_start
atexit.register(safe_exit)
dpg.setup_dearpygui()
dpg.show_viewport()
dpg.set_primary_window("main", True)
dpg.maximize_viewport()
while dpg.is_dearpygui_running():
    tf = dpg.get_total_time()
    if tf - clock_start > 1:
        clock_start = tf
        clock_callback()
        prayer_callback()
        additonal_times_callback()

    if tf - date_start > 60:
        date_start = tf
        date_callback()
    if pygame.mixer.music.get_busy():
        update_track()

    dpg.render_dearpygui_frame()

dpg.destroy_context()
