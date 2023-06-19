import dearpygui.dearpygui as dpg
import ntpath
import json
from mutagen.mp3 import MP3
import pygame
import time
import random
from datetime import datetime, date as dt, timedelta
import atexit
from prayertimes import PrayTimes


COORDINATES = (24.7136, 46.6753)
MINUTES_BEFORE_PRAYER = 1
MINUTES_AFTER_PRAYER = 0


BACKGROUND_COLOR = (14, 41, 84, 100)
SECTION_BG_COLOR = (31, 110, 140, 120)
BUTTON_COLOR = (195, 129, 84)
TEXT_COLOR = (255, 255, 255, 255)


dpg.create_context()
prayTimes = PrayTimes()
prayTimes.setMethod("Makkah")
dpg.create_viewport(
    title="Islamic Music Player", large_icon="icon.ico", small_icon="icon.ico"
)
pygame.mixer.init()


global state, paused_for_prayer, loop, date, clock, prayers, timezone, current_prayer, song_length
timezone = int(time.tzname[0])
state = None
paused_for_prayer = False
loop = -1
date = dt.today()
clock = datetime.now().time()
current_prayer = None
song_length = 1


def get_prayer_times():
    global date, timezone
    times = prayTimes.getTimes(date, COORDINATES, timezone)
    prayers = {}
    for i in ["Fajr", "Dhuhr", "Asr", "Maghrib", "Isha"]:
        prayers[i] = datetime.strptime(times[i.lower()], "%H:%M").time()  # type: ignore
    prayers["test"] = datetime.strptime("00:35", "%H:%M").time()
    return prayers


prayers = get_prayer_times()

_DEFAULT_MUSIC_VOLUME = 0.5
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
            prayers[i], MINUTES_AFTER_PRAYER, "+"
        )
        dpg.add_text(
            label=f"{i}: {prayers[i]}",
            tag=i,
            parent="sidebar",
            default_value=f"{i}: {prayers[i].strftime('%I:%M %p')}",
        )
        if clock >= fourty_five_minutes_after_prayer:
            dpg.configure_item(i, color=(137, 135, 122, 255))


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
        print("loop callback")
        loop = 0
        dpg.configure_item("loop", default_value="Loop: Off")
    else:
        loop = -1
        dpg.configure_item("loop", default_value="Loop: On")


def prayer_callback():
    global prayers, paused_for_prayer, clock, current_prayer, state
    if current_prayer is None and not paused_for_prayer:
        for prayer in prayers:
            five_minutes_before_prayer = calc_time(
                prayers[prayer], MINUTES_BEFORE_PRAYER, "-"
            )
            fourty_five_minutes_after_prayer = calc_time(
                prayers[prayer], MINUTES_AFTER_PRAYER, "+"
            )
            if (
                clock >= five_minutes_before_prayer
                and clock < fourty_five_minutes_after_prayer
            ):
                print(state)
                paused_for_prayer = True
                current_prayer = prayer
                if state == "playing":
                    print("pause for prayer")
                    pygame.mixer.music.pause()
                dpg.configure_item(prayer, color=(0, 255, 0, 255))
                dpg.configure_item(
                    "cstate",
                    default_value=f"State: Paused For {prayer}",
                    color=(255, 0, 0, 255),
                )
                break
    elif current_prayer is not None and paused_for_prayer:
        five_minutes_before_prayer = calc_time(
            prayers[current_prayer], MINUTES_BEFORE_PRAYER, "-"
        )
        fourty_five_minutes_after_prayer = calc_time(
            prayers[current_prayer], MINUTES_AFTER_PRAYER, "+"
        )
        if clock >= fourty_five_minutes_after_prayer:
            paused_for_prayer = False
            if state == "playing":
                pygame.mixer.music.unpause()
            dpg.configure_item(current_prayer, color=(137, 135, 122, 255))
            current_prayer = None
            dpg.configure_item(
                "cstate",
                default_value=f"Current State: {state}",
                color=(255, 255, 255, 255),
            )


def clock_callback():
    global clock
    clock = datetime.now().time()
    dpg.configure_item("clock", default_value=f"Clock: {clock.strftime('%I:%M:%S %p')}")


def date_callback():
    global date, prayers
    if datetime.today().date() > date:
        date = datetime.today()
        prayers = get_prayer_times()
        dpg.configure_item("date", default_value=f"Date: {date.strftime('%d/%m/%Y')}")
        config_prayers()


def update_volume(sender, app_data):
    pygame.mixer.music.set_volume(app_data / 100.0)


def load_database():
    songs = json.load(open("data/songs.json", "r+"))["songs"]
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


def update_track():
    global song_length
    dpg.configure_item(
        item="pos", default_value=((pygame.mixer.music.get_pos() / 1000) % song_length)
    )


def play(sender, app_data, user_data):
    global state, loop, paused_for_prayer, song_length
    if not paused_for_prayer:
        if user_data:
            pygame.mixer.music.load(user_data)
            audio = MP3(user_data)
            song_length = audio.info.length
            dpg.configure_item(item="pos", max_value=audio.info.length)
            pygame.mixer.music.play(loop)
            if pygame.mixer.music.get_busy():
                dpg.configure_item("play", label="Pause")
                state = "playing"
                dpg.configure_item("cstate", default_value=f"State: Playing")
                dpg.configure_item(
                    "csong", default_value=f"Now Playing : {ntpath.basename(user_data)}"
                )


def play_pause():
    global state, paused_for_prayer, loop, song_length

    if state == "playing" and not paused_for_prayer:
        state = "paused"
        pygame.mixer.music.pause()
        dpg.configure_item("play", label="Play")
        dpg.configure_item("cstate", default_value=f"State: Paused")
    elif state == "paused" and not paused_for_prayer:
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
                pygame.mixer.music.play(loop)
                dpg.configure_item("play", label="Pause")
            if pygame.mixer.music.get_busy():
                state = "playing"
                audio = MP3(song)
                song_length = audio.info.length
                print(audio.info.length, "song_length")
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
    for key in filename:
        file = filename[key]
        if file.endswith(".mp3" or ".wav" or ".ogg"):
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

with dpg.font_registry():
    monobold = dpg.add_font("fonts/MonoLisa-Bold.ttf", 12)
    head = dpg.add_font("fonts/MonoLisa-Bold.ttf", 15)


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

    with dpg.group(horizontal=True):
        with dpg.child_window(width=300, tag="sidebar"):
            dpg.add_text(f"Date: {datetime.now().strftime('%d/%m/%Y')}", tag="date")
            dpg.add_text(f"Clock: {clock.strftime('%I:%M:%S %p')}", tag="clock")

            dpg.add_spacer(height=2)

            dpg.add_spacer(height=5)
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
            dpg.add_spacer(height=5)
            dpg.add_separator()
            dpg.add_spacer(height=5)
            dpg.add_text(f"State: {state}", tag="cstate")
            dpg.add_spacer(height=5)
            dpg.add_text(f"Loop: {'On' if loop == -1 else 'Off'}", tag="loop")
            dpg.add_spacer(height=5)
            dpg.add_separator()
            dpg.add_spacer(height=5)
            render_prayers()

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
                    load_database()

    dpg.bind_item_theme("volume", "slider_thin")
    dpg.bind_item_theme("pos", "slider")
    dpg.bind_item_theme("list", "songs")
    dpg.bind_item_theme("query", "songs")

dpg.bind_theme("base")
dpg.bind_font(monobold)


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
    if tf - date_start > 3600:
        date_start = tf
        date_callback()
    if pygame.mixer.music.get_busy():
        update_track()

    dpg.render_dearpygui_frame()

dpg.destroy_context()
