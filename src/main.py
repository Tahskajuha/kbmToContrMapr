from evdev import InputDevice, UInput, AbsInfo, ecodes
from select import select
from buttons import handle_button

keyboard = InputDevice("/dev/input/event9")
mouse = InputDevice("/dev/input/event12")

keyboard.grab()
mouse.grab()

virt_controller = UInput(
    {
        ecodes.EV_KEY: [
            ecodes.BTN_SOUTH,
            ecodes.BTN_EAST,
            ecodes.BTN_WEST,
            ecodes.BTN_NORTH,
            ecodes.BTN_DPAD_UP,
            ecodes.BTN_DPAD_DOWN,
            ecodes.BTN_DPAD_LEFT,
            ecodes.BTN_DPAD_RIGHT,
            ecodes.BTN_TL,
            ecodes.BTN_TR,
            ecodes.BTN_TL2,
            ecodes.BTN_TR2,
            ecodes.BTN_SELECT,
            ecodes.BTN_START,
            ecodes.BTN_THUMBL,
            ecodes.BTN_THUMBR,
            ecodes.BTN_MODE,
        ],
        ecodes.EV_ABS: [
            (ecodes.ABS_X, AbsInfo(0, -32768, 32767, 0, 0, 0)),
            (ecodes.ABS_Y, AbsInfo(0, -32768, 32767, 0, 0, 0)),
            (ecodes.ABS_Z, AbsInfo(0, 0, 255, 0, 0, 0)),
            (ecodes.ABS_RX, AbsInfo(0, -32768, 32767, 0, 0, 0)),
            (ecodes.ABS_RY, AbsInfo(0, -32768, 32767, 0, 0, 0)),
            (ecodes.ABS_RZ, AbsInfo(0, 0, 255, 0, 0, 0)),
            (ecodes.ABS_HAT0X, AbsInfo(0, -1, 1, 0, 0, 0)),
            (ecodes.ABS_HAT0Y, AbsInfo(0, -1, 1, 0, 0, 0)),
        ],
    },
    name="Virtual Microsoft X-Box 360 Gamepad",
    vendor=0x045E,
    product=0x028E,
    version=1,
)

try:
    devices = {
        keyboard.fd: keyboard,
        mouse.fd: mouse,
    }
    while True:
        ready, _, _ = select(list(devices), [], [])
        for fd in ready:
            device = devices[fd]
            for event in device.read():
                handle_button(event, virt_controller)
except KeyboardInterrupt:
    print("\nExiting...")
finally:
    virt_controller.close()
    keyboard.ungrab()
    keyboard.close()
    mouse.ungrab()
    mouse.close()
