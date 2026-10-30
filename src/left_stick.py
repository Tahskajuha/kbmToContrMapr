import threading
import time
from dataclasses import dataclass, field
from evdev import ecodes
from collections import deque
import math

TICK_RATES = {
    1: 20,
    2: 30,
    3: 45,
    4: 60,
    5: 75,
}

KEY_ANGLES = {
    ecodes.KEY_W: 270,
    ecodes.KEY_A: 180,
    ecodes.KEY_S: 90,
    ecodes.KEY_D: 0,
}

ACCEPTED_BUTTON_SET = {ecodes.KEY_W, ecodes.KEY_A, ecodes.KEY_S, ecodes.KEY_D}


@dataclass
class lsmode:
    state: int = 0
    pressedSet: set = field(default_factory=set)
    pressedQueue: deque = field(default_factory=deque)
    speed: int = 1
    angleDelta: int = 5
    targetAngle: int = None
    currentAngle: int = 270
    currentMagnitude: int = 0
    magnitudeDelta: int = 2048
    targetMagnitude: int = 0
    movementPhase: int = 1  # 1 -> rotate, 2 -> retract, 3 -> extend

    stop_event: threading.Event = field(default_factory=threading.Event, init=False)
    queue_thread: threading.Thread = field(init=False)

    def cycle_state(self, keyboard):
        self.state = {0: 2, 2: 1, 1: 0}[self.state]
        self.pressedSet.clear()
        self.pressedQueue.clear()
        self.targetAngle = None
        self.currentAngle = 270
        self.currentMagnitude = 0
        self.targetMagnitude = 0
        self.set_mag_phase(1)
        keyboard.set_led(ecodes.LED_CAPSL, int(self.state in (1, 2)))
        keyboard.set_led(ecodes.LED_SCROLLL, int(self.state == 2))

    def cycle_speed(self, increase: bool):
        self.speed = (
            {1: 2, 2: 3, 3: 4, 4: 5, 5: 1}[self.speed]
            if increase
            else {1: 5, 5: 4, 4: 3, 3: 2, 2: 1}[self.speed]
        )

    def set_mag_phase(self, newPhase: int):
        self.movementPhase = newPhase if newPhase in (1, 2, 3) else 1

    def start(self, keyboard, gamepad):
        self.queue_thread = threading.Thread(
            target=queue_worker, args=(self, keyboard, gamepad), daemon=True
        )
        self.queue_thread.start()

    def stop(self):
        self.stop_event.set()
        self.queue_thread.join()


def set_mode(pressed_set, gamepad):
    x = int(ecodes.KEY_D in pressed_set) - int(ecodes.KEY_A in pressed_set)
    y = int(ecodes.KEY_S in pressed_set) - int(ecodes.KEY_W in pressed_set)

    if x != 0 and y != 0:
        x *= 0.7071
        y *= 0.7071

    gamepad.write(ecodes.EV_ABS, ecodes.ABS_X, int(x * 32767))
    gamepad.write(ecodes.EV_ABS, ecodes.ABS_Y, int(y * 32767))
    gamepad.syn()


def queue_worker(lsmode_obj, keyboard, gamepad):
    tick_num = 0
    led_state = 0
    last_speed = None
    next_tick = time.monotonic()

    while not lsmode_obj.stop_event.is_set():
        speed = lsmode_obj.speed

        if speed != last_speed:
            last_speed = speed
            tick_num = 0
            led_state = int(speed == 5)
            keyboard.set_led(ecodes.LED_NUML, led_state)
            next_tick = time.monotonic()

        tick_rate = TICK_RATES[speed]
        tick_interval = 1.0 / tick_rate
        next_tick += tick_interval
        delay = max(0, next_tick - time.monotonic())

        if lsmode_obj.stop_event.wait(delay):
            break

        tick_num += 1
        if speed in (2, 3, 4) and tick_num % 16 == 0:
            led_state = 1 - led_state

        keyboard.set_led(ecodes.LED_NUML, led_state)

        if lsmode_obj.state in (1, 2):
            if lsmode_obj.targetAngle is None and lsmode_obj.pressedQueue:
                lsmode_obj.targetAngle = KEY_ANGLES[lsmode_obj.pressedQueue.popleft()]
                lsmode_obj.targetMagnitude = 32767 if lsmode_obj.state == 2 else 16383
            if lsmode_obj.targetAngle is not None:
                if lsmode_obj.movementPhase == 1:
                    diff = (
                        lsmode_obj.targetAngle - lsmode_obj.currentAngle + 180
                    ) % 360 - 180
                    if lsmode_obj.currentMagnitude == 0:
                        lsmode_obj.currentAngle = lsmode_obj.targetAngle
                        lsmode_obj.set_mag_phase(3)
                    elif diff == 0:
                        lsmode_obj.targetAngle = None
                    elif abs(diff) == 180:
                        lsmode_obj.set_mag_phase(2)
                    elif abs(diff) <= lsmode_obj.angleDelta:
                        lsmode_obj.currentAngle = lsmode_obj.targetAngle
                    elif diff > 0:
                        lsmode_obj.currentAngle += lsmode_obj.angleDelta
                    else:
                        lsmode_obj.currentAngle -= lsmode_obj.angleDelta
                    lsmode_obj.currentAngle %= 360

                elif lsmode_obj.movementPhase == 2:
                    lsmode_obj.currentMagnitude = max(
                        0, lsmode_obj.currentMagnitude - lsmode_obj.magnitudeDelta
                    )
                    if lsmode_obj.currentMagnitude == 0:
                        lsmode_obj.currentAngle = lsmode_obj.targetAngle
                        lsmode_obj.set_mag_phase(3)
                elif lsmode_obj.movementPhase == 3:
                    lsmode_obj.currentMagnitude = min(
                        lsmode_obj.targetMagnitude,
                        lsmode_obj.currentMagnitude + lsmode_obj.magnitudeDelta,
                    )
                    if lsmode_obj.currentMagnitude == lsmode_obj.targetMagnitude:
                        lsmode_obj.set_mag_phase(1)

                x = int(
                    lsmode_obj.currentMagnitude
                    * math.cos(math.radians(lsmode_obj.currentAngle))
                )
                y = int(
                    lsmode_obj.currentMagnitude
                    * math.sin(math.radians(lsmode_obj.currentAngle))
                )
                gamepad.write(ecodes.EV_ABS, ecodes.ABS_X, x)
                gamepad.write(ecodes.EV_ABS, ecodes.ABS_Y, y)
                gamepad.syn()

        if time.monotonic() > next_tick + tick_interval:
            next_tick = time.monotonic()

    keyboard.set_led(ecodes.LED_NUML, 0)


def handle_left_stick(lsmode_obj, event, gamepad, keyboard):
    if event.type == ecodes.EV_REL and event.code == ecodes.REL_WHEEL:
        lsmode_obj.cycle_speed(True if event.value == 1 else False)
        return
    if event.type != ecodes.EV_KEY or event.value == 2:
        return
    if event.code == ecodes.KEY_CAPSLOCK and event.value == 1:
        lsmode_obj.cycle_state(keyboard)
        gamepad.write(ecodes.EV_ABS, ecodes.ABS_X, 0)
        gamepad.write(ecodes.EV_ABS, ecodes.ABS_Y, 0)
        gamepad.syn()
        return
    if event.code not in ACCEPTED_BUTTON_SET:
        return
    if lsmode_obj.state == 0:
        lsmode_obj.pressedSet.add(
            event.code
        ) if event.value == 1 else lsmode_obj.pressedSet.discard(event.code)
        set_mode(lsmode_obj.pressedSet, gamepad)
    elif event.value == 1:
        lsmode_obj.pressedQueue.append(event.code)
