import resource_lister.menu.menu_processor as menu_processor
def main():
    args = menu_processor.setup_args()
    menu_processor.process(args)