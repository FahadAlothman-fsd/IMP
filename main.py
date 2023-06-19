import dearpygui.dearpygui as dpg

dpg.create_context()


def callback(sender, app_data, user_data):
    print("Sender: ", sender)
    print("App Data: ", app_data)


def folder_callback(sender, app_data):
    print("OK was clicked.")
    print("Sender: ", sender)
    print("App Data: ", app_data)


def cancel_callback(sender, app_data):
    print("Cancel was clicked.")
    print("Sender: ", sender)
    print("App Data: ", app_data)


dpg.add_file_dialog(
    directory_selector=True,
    show=False,
    callback=folder_callback,
    tag="folder_dialog_id",
    cancel_callback=cancel_callback,
    width=700,
    height=400,
)


with dpg.file_dialog(
    directory_selector=False,
    show=False,
    callback=callback,
    cancel_callback=cancel_callback,
    id="file_dialog_id",
    width=700,
    height=400,
):
    print(dpg.get_file_dialog_info("folder_dialog_id"))

    dpg.add_file_extension(
        "Source files (*.mp3 *.wav *.ogg){.mp3,.wav,.ogg}", color=(0, 255, 255, 255)
    )
    dpg.add_file_extension(".mp3", color=(255, 0, 255, 255), custom_text="[mp3]")
    dpg.add_file_extension(".wav", color=(0, 255, 0, 255), custom_text="[wav]")
    dpg.add_file_extension(".ogg", color=(0, 0, 255, 255), custom_text="[ogg]")


with dpg.window(label="Tutorial", width=800, height=300):
    dpg.add_button(
        label="File Selector", callback=lambda: dpg.show_item("file_dialog_id")
    )
    dpg.add_button(
        label="Directory Selector", callback=lambda: dpg.show_item("folder_dialog_id")
    )


dpg.create_viewport(title="Custom Title", width=800, height=600)
dpg.setup_dearpygui()
dpg.show_viewport()
dpg.start_dearpygui()
dpg.destroy_context()
