import dearpygui.dearpygui as dpg

dpg.create_context()

width, height, channels, data = dpg.load_image("pause.png")
print(type(width), height, channels, data)
with dpg.texture_registry(show=True):
    dpg.add_static_texture(width=300, height=300, default_value=data, tag="texture_tag")

with dpg.window(label="Tutorial"):
    dpg.add_image("texture_tag")


dpg.create_viewport(title="Custom Title", width=800, height=600)
dpg.setup_dearpygui()
dpg.show_viewport()
dpg.start_dearpygui()
dpg.destroy_context()
