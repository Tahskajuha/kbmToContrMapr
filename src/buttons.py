from evdev import ecodes

BUTTON_MAP = {
    ecodes.KEY_SPACE: ecodes.BTN_NORTH,
    ecodes.KEY_LEFTSHIFT: ecodes.BTN_EAST,
    ecodes.KEY_RIGHTSHIFT: ecodes.BTN_EAST,
    ecodes.BTN_LEFT: ecodes.BTN_SOUTH,
    ecodes.BTN_RIGHT: ecodes.BTN_WEST,
    ecodes.KEY_I: ecodes.BTN_DPAD_UP,
    ecodes.KEY_J: ecodes.BTN_DPAD_LEFT,
    ecodes.KEY_K: ecodes.BTN_DPAD_DOWN,
    ecodes.KEY_L: ecodes.BTN_DPAD_RIGHT,
    ecodes.KEY_F: ecodes.BTN_TL,
    ecodes.KEY_R: ecodes.ABS_Z,
    ecodes.BTN_SIDE: ecodes.BTN_TR,
    ecodes.BTN_EXTRA: ecodes.ABS_RZ,
    ecodes.KEY_ENTER: ecodes.BTN_START,
    ecodes.BTN_MIDDLE: ecodes.BTN_THUMBR,
    ecodes.KEY_E: ecodes.BTN_THUMBL,
    ecodes.KEY_LEFTALT: ecodes.BTN_SELECT,
}


def handle_button(event, gamepad):
    if event.type != ecodes.EV_KEY or event.value == 2:
        return
    button = BUTTON_MAP.get(event.code)
    if button is None:
        return

    if button in (ecodes.ABS_Z, ecodes.ABS_RZ):
        gamepad.write(ecodes.EV_ABS, button, 255 if event.value else 0)
    else:
        gamepad.write(ecodes.EV_KEY, button, event.value)

    gamepad.syn()
