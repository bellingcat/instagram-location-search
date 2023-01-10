from instagram_locations.instagram_locations import main


def start():
    try:
        main()
    except KeyboardInterrupt as ctrlc:
        raise KeyboardInterrupt(ctrlc) from ctrlc
    except Exception as err:
        raise Exception(err) from err
