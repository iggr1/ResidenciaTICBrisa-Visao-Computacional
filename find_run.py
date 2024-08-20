from filters_interface import show_filters_interface
from find_images import find_images
from show_results import show_results

def on_receive_filters(filters):
    found_images = find_images(filters)
    show_results(found_images)
    
show_filters_interface(on_receive_filters)