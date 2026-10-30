from evdev import ecodes
from dataclasses import dataclass


@dataclass
class m2j:
    sensitivity: float
    rel_x: int = 0
    rel_y: int = 0

    def get_joy_x(self) -> int:
        return max(-32768, min(32767, int(self.rel_x * self.sensitivity)))

    def get_joy_y(self) -> int:
        return max(-32768, min(32767, int(self.rel_y * self.sensitivity)))


def handle_right_stick(m2j_obj, event, gamepad):
    if event.type != ecodes.EV_REL:
        return

    if event.code == ecodes.REL_X:
        m2j_obj.rel_x += event.value
    elif event.code == ecodes.REL_Y:
        m2j_obj.rel_y += event.value
    else:
        return

    gamepad.write(ecodes.EV_ABS, ecodes.ABS_RX, m2j_obj.get_joy_x())
    gamepad.write(ecodes.EV_ABS, ecodes.ABS_RY, m2j_obj.get_joy_y())
    gamepad.syn()
