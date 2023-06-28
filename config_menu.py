import dearpygui.dearpygui as dpg
from typing import Literal

dpg.create_context()

warlock_colors = {
    "Background": (17, 17, 34),
    "Text": (225, 204, 153),
    "Button": (111, 34, 101),
    "ButtonHovered": (156, 48, 142),
    "ButtonActive": (89, 27, 79),
    "Separator": (89, 27, 79),
    # Add more colors as needed
}


global prayer_times, additonal_times
additonal_times = [{"name": "test", "time": 20}]
prayer_times = {
    "Imsak": 20,
    "Fajr": 40,
    "Dhuhr": 40,
    "Asr": 40,
    "Sunset": 25,
    "Maghrib": 25,
    "Isha": 40,
}


def save_config(sender, app_data, user_data):
    # print("sender", sender)
    # print("app_data", app_data)
    # print("user_data", user_data)
    longitude = round(dpg.get_value("lon"), 6)
    latitude = round(dpg.get_value("lat"), 6)
    timezone = dpg.get_value("tz")
    dst = dpg.get_value("dst")
    method = dpg.get_value("method")
    mode = dpg.get_value("mode")

    # Create an object to store the values
    config_object = {
        "longitude": longitude,
        "latitude": latitude,
        "timezone": timezone,
        "dst": dst,
        "method": method,
        "mode": mode,
    }
    print(config_object)

    additional_times_values = []
    print(dpg.get_item_children("additional_times"))
    num_additional_times = 0
    while True:
        name = dpg.get_value(f"name{num_additional_times}")
        time = dpg.get_value(f"time{num_additional_times}")
        if name is None or time is None:
            break
        additional_times_values.append({"name": name, "time": time})
        num_additional_times += 1
    print(additional_times_values)


def save_prayers(sender, app_data, user_data):
    print("sender", sender)
    print("app_data", app_data)
    print("user_data", user_data)


def mode_callback(sender, app_data: Literal["Normal", "Ramadan"]):
    print("sender", sender)
    print("app_data", app_data)
    dpg.delete_item("prayer_group", children_only=True)
    render_config_prayers(app_data)


def render_config_prayers(mode: Literal["Normal", "Ramadan"]):
    global prayer_times
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
                label=prayer,
                default_value=prayer_times[prayer],
            )
        dpg.add_spacer(height=5, parent="prayer_group")


def add_time_callback(sender):
    global additonal_times
    additonal_times.append({"name": "", "time": 0})
    index = len(additonal_times) - 1
    with dpg.group(horizontal=True, horizontal_spacing=10, parent="additional_times"):
        dpg.add_input_text(
            label="Name",
            width=100,
            tag=f"name{index}",
            default_value=additonal_times[index]["name"],
        )
        dpg.add_input_int(
            min_clamped=True,
            min_value=0,
            width=100,
            step=0,
            label="Time",
            tag=f"time{index}",
            default_value=additonal_times[index]["time"],
        )
    dpg.add_spacer(height=5, parent="additional_times")


with dpg.window(label="Config", tag="config", width=400, height=400):
    dpg.add_text("This is a text")
    dpg.add_button(label="Show", callback=lambda: dpg.show_item("config_settings"))
    dpg.add_button(label="Cancel")

    with dpg.window(
        tag="config_settings",
        label="Settings",
        width=400,
        height=400,
        show=False,
        pos=[200, 100],
    ):
        with dpg.tab_bar(label="Prayer Settings"):
            with dpg.tab(label="Configurations"):
                dpg.add_input_float(
                    default_value=0.0,
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
                    default_value=0.0,
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
                    default_value=0, step=0, label="Timezone", tag="tz", width=100
                )
                dpg.add_spacer(height=5)
                dpg.add_input_int(
                    default_value=0, step=0, label="DST", tag="dst", width=100
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
                    default_value="Makkah",
                    width=100,
                )
                dpg.add_spacer(height=15)
                dpg.add_combo(
                    label="Mode",
                    tag="mode",
                    items=["Normal", "Ramadan"],
                    default_value="Normal",
                    callback=mode_callback,
                    width=100,
                )
                dpg.add_spacer(height=15)
                dpg.add_separator()
                dpg.add_spacer(height=15)

            with dpg.tab(label="Prayers"):
                dpg.add_text("Please pick the pause duration of each prayer")
                dpg.add_spacer(height=15)
                with dpg.group(tag="prayer_group"):
                    render_config_prayers("Normal")
                dpg.add_spacer(height=15)
                dpg.add_separator()
                dpg.add_spacer(height=15)
                with dpg.group(tag="additional_times"):
                    dpg.add_button(
                        label="Add Additional Time", callback=add_time_callback
                    )
                    dpg.add_spacer(height=15)
                    for index, time in enumerate(additonal_times):
                        with dpg.group(
                            horizontal=True,
                            horizontal_spacing=10,
                            parent="additional_times",
                        ):
                            dpg.add_input_text(
                                label="Name",
                                width=100,
                                tag=f"name{index}",
                                default_value=time["name"],
                            )
                            dpg.add_input_int(
                                min_clamped=True,
                                min_value=0,
                                width=100,
                                step=0,
                                label="Time",
                                tag=f"time{index}",
                                default_value=time["time"],
                            )
                        dpg.add_spacer(height=5, parent="additional_times")

        with dpg.group(horizontal=True, horizontal_spacing=10):
            dpg.add_button(label="Lave", callback=save_config)
            dpg.add_button(
                label="Cancel",
                callback=lambda: dpg.hide_item("config_settings"),
            )


dpg.create_viewport(title="Custom Title", width=800, height=600)
dpg.setup_dearpygui()
dpg.show_viewport()
dpg.set_primary_window("config", True)
dpg.start_dearpygui()
dpg.destroy_context()
