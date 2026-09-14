import hid
import sys
import time
import math
import queue
import threading
import webbrowser
import json
from pathlib import Path
import tkinter as tk
from tkinter import messagebox, ttk
from PIL import Image, ImageTk
import vgamepad as vg

# ============================================================
# KREO HIVE 75 HE Gamepad Emulator
# ============================================================

VID = 0x28E9
PID = 0x3201
REPORT_ID_COMMAND = 6
REPORT_ID_TRAVEL = 7
OUTPUT_USAGE_PAGE = 0xFF87
OUTPUT_USAGE = 0x0020
INPUT_USAGE_PAGE = 0xFF88
INPUT_USAGE = 0x0021
TRAVEL_SCALE = 0.01
MAX_TRAVEL_MM = 3.50
BUTTON_PRESS_THRESHOLD = 0.10

# Controller response tuning.
DEADZONE = 0.02
SENSITIVITY = 1.00
CURVE = 1.35
STEERING_SATURATION = 1.00

# Trigger inputs use a configurable response curve.
PEDAL_DEADZONE = 0.02
PEDAL_CURVE = 1.60

stop_requested = threading.Event()
status_callback = None
toggle_callback = None
console_mode = True

APP_NAME = "KH75 HE Gamepad Emulator"
AUTHOR_NAME = "RishikRVR"
GITHUB_URL = "https://github.com/RishikRVR"

# Saved beside the application script. Mapping and racing settings persist
# across closing and reopening the GUI.
CONFIG_FILE = Path(__file__).with_name("KH75HE-GPE_config.json")
def load_user_config():
    try:
        if CONFIG_FILE.exists():
            with CONFIG_FILE.open("r", encoding="utf-8") as file:
                data = json.load(file)
            mapping = data.get("mapping", {})
            settings = data.get("settings", {})
            return (
                mapping if isinstance(mapping, dict) else {},
                settings if isinstance(settings, dict) else {},
            )
    except Exception as error:
        print(f"Warning: could not load saved configuration: {error}")
    return {}, {}
def save_user_config(mapping, settings):
    try:
        with CONFIG_FILE.open("w", encoding="utf-8") as file:
            json.dump(
                {
                    "mapping": {str(k): int(v) for k, v in mapping.items()},
                    "settings": {str(k): str(v) for k, v in settings.items()},
                },
                file,
                indent=2,
            )
    except Exception as error:
        print(f"Warning: could not save configuration: {error}")
SAVED_MAPPING, SAVED_SETTINGS = load_user_config()
KEY_NAMES = {
    0: "ESC", 1: "F1", 2: "F2", 3: "F3", 4: "F4", 5: "F5", 6: "F6", 7: "F7", 8: "F8", 9: "F9", 10: "F10", 11: "F11", 12: "F12", 13: "PRTSC",
    15: "`", 16: "1", 17: "2", 18: "3", 19: "4", 20: "5", 21: "6", 22: "7", 23: "8", 24: "9", 25: "0", 26: "-", 27: "=", 28: "BACKSPACE", 29: "HOME",
    30: "TAB",  31: "Q", 32: "W", 33: "E", 34: "R", 35: "T", 36: "Y", 37: "U", 38: "I", 39: "O", 40: "P", 41: "[", 42: "]", 43: "\\", 44: "DEL",
    45: "CAPSLOCK", 46: "A", 47: "S", 48: "D", 49: "F", 50: "G", 51: "H", 52: "J", 53: "K", 54: "L", 55: ";", 56: "'", 58: "ENTER", 59: "PAGE UP",
    60: "L SHIFT", 62: "Z", 63: "X", 64: "C", 65: "V", 66: "B", 67: "N", 68: "M", 69: ",", 70: ".", 71: "/", 72: "R SHIFT", 73: "UP", 74: "PGDN",
    75: "L CTRL", 76: "WINDOWS", 77: "L ALT", 81: "SPACE", 84: "R ALT", 85: "FN", 86: "R CTRL", 87: "L ARROW", 88: "D ARROW", 89: "R ARROW",
}
# ============================================================
# Configurable virtual-controller mapping
# ============================================================
DEFAULT_KEY_MAP = {
    "Left stick left": 46,
    "Left stick right": 48,
    "Right trigger": 32,
    "Left trigger": 47,
    "Left stick up": 35,
    "Left stick down": 50,
    "Right stick up": 38,
    "Right stick left": 52,
    "Right stick down": 53,
    "Right stick right": 54,
    "A button": 81,
    "B button": 60,
    "X button": 31,
    "Y button": 33,
    "Left bumper": 34,
    "Right bumper": 49,
    "Back": 30,
    "Start": 58,
    "Left stick click": 64,
    "Right stick click": 65,
    "D-pad up": 73,
    "D-pad left": 87,
    "D-pad down": 88,
    "D-pad right": 89,
    "Stop Program": 12,
}
# ============================================================
# Controller presets
# ===========================================================
PRESETS = {
    # Everyday controller layout. Every physical key is assigned to only
    # one virtual control in the preset.
    "Normal": {
        "Left stick left": 46, "Left stick right": 48,
        "Right trigger": 32, "Left trigger": 47,
        "Left stick up": 31, "Left stick down": 33,
        "Left stick click": 64,
        "Right stick up": 35, "Right stick left": 52,
        "Right stick down": 53, "Right stick right": 54,
        "Right stick click": 65,
        "A button": 81, "B button": 60, "X button": 34, "Y button": 36,
        "Left bumper": 37, "Right bumper": 38,
        "Back": 30, "Start": 58,
        "D-pad up": 73, "D-pad left": 87,
        "D-pad down": 88, "D-pad right": 89,
        "Stop Program": 12,
    },
    # Racing profile. It deliberately keeps the racing inputs separate from
    # the other virtual controls so one physical key cannot drive two controls.
    "Racing": {
        "Left stick left": 46, "Left stick right": 48,
        "Right trigger": 32, "Left trigger": 47,
        "Left stick up": 31, "Left stick down": 33,
        "Left stick click": 64,
        "Right stick up": 35, "Right stick left": 52,
        "Right stick down": 53, "Right stick right": 54,
        "Right stick click": 65,
        "A button": 81, "B button": 60, "X button": 34, "Y button": 36,
        "Left bumper": 37, "Right bumper": 38,
        "Back": 30, "Start": 58,
        "D-pad up": 73, "D-pad left": 87,
        "D-pad down": 88, "D-pad right": 89,
        "Stop Program": 12,
    },
    # FPS layout: WASD remains movement, IJKL is the right stick.
    # Other controls use distinct keys.
    "FPS": {
        "Left stick left": 46, "Left stick right": 48,
        "Right trigger": 32, "Left trigger": 47,
        "Left stick up": 31, "Left stick down": 33,
        "Left stick click": 64,
        "Right stick up": 38, "Right stick left": 52,
        "Right stick down": 53, "Right stick right": 54,
        "Right stick click": 65,
        "A button": 81, "B button": 60, "X button": 34, "Y button": 36,
        "Left bumper": 37, "Right bumper": 35,
        "Back": 30, "Start": 58,
        "D-pad up": 73, "D-pad left": 87,
        "D-pad down": 88, "D-pad right": 89,
        "Stop Program": 12,
    },
}
KEY_MAP = DEFAULT_KEY_MAP.copy()
for _control, _key_id in SAVED_MAPPING.items():
    try:
        _key_id = int(_key_id)
    except (TypeError, ValueError):
        continue
    if _control in KEY_MAP and _key_id in KEY_NAMES:
        KEY_MAP[_control] = _key_id
BUTTON_CONTROL_MAP = {
    "A button": vg.XUSB_BUTTON.XUSB_GAMEPAD_A,
    "B button": vg.XUSB_BUTTON.XUSB_GAMEPAD_B,
    "X button": vg.XUSB_BUTTON.XUSB_GAMEPAD_X,
    "Y button": vg.XUSB_BUTTON.XUSB_GAMEPAD_Y,
    "Left bumper": vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_SHOULDER,
    "Right bumper": vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_SHOULDER,
    "Back": vg.XUSB_BUTTON.XUSB_GAMEPAD_BACK,
    "Start": vg.XUSB_BUTTON.XUSB_GAMEPAD_START,
    "Left stick click": vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_THUMB,
    "Right stick click": vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_THUMB,
    "D-pad up": vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_UP,
    "D-pad left": vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_LEFT,
    "D-pad down": vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_DOWN,
    "D-pad right": vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_RIGHT,
}
def mapped_keys():

    return set(KEY_MAP.values())
# ============================================================
# HID
# ============================================================
def find_hid_device(usage_page, usage):
    devices = hid.enumerate(VID, PID)
    for device in devices:
        if (
            device.get("usage_page") == usage_page
            and device.get("usage") == usage
        ):
            return device
    return None
# ============================================================
# Kreo Travel Test command
# ============================================================
def send_travel_command(device, start):
    # Kreo:
    # 0x36 = magnetic axis simulation/travel test
    # byte 7:
    # 0x01 = enter
    # 0x00 = exit
    value = 0x01 if start else 0x00
    packet = [
        REPORT_ID_COMMAND,
        0x36,
        0x00,
        0x00,
        0x38,
        0x6E,
        0x00,
        0x00,
        value,
    ]
    packet += [0x00] * (64 - len(packet))
    return device.write(packet)
# ============================================================
# Kreo travel decoder
# ============================================================
# IMPORTANT:
# A Report 7 travel value consists of two 6-bit pieces.
# First report:
#     key + low 6 bits
# Second report from the same key:
#     key + high 6 bits
# Then:
#     raw = (high << 6) | low
#     travel = raw * 0.01
# We keep the pending value PER KEY.
# This is important for the gamepad use case because W/A/S/D
# reports may be interleaved.
# ============================================================
class TravelDecoder:
    def __init__(self):
        self.pending_low = {}
    def decode(self, packet):
        if len(packet) < 2:
            return None
        key = packet[0]
        byte1 = packet[1]
        # Kreo uses bit 6 as the travel-data flag.
        if (byte1 & 0x40) == 0:
            return None
        six_bits = byte1 & 0x3F
        if key not in self.pending_low:
            self.pending_low[key] = six_bits
            return None
        low = self.pending_low.pop(key)
        raw_value = (
            (six_bits << 6)
            |
            low
        )
        travel_mm = raw_value * TRAVEL_SCALE
        # Sanity check
        if travel_mm < 0.0:
            return None
        if travel_mm > 4.0:
            return None
        return key, travel_mm, raw_value
# ============================================================
# Helpers
# ============================================================
def clamp(value, low=-1.0, high=1.0):
    if value < low:
        return low
    if value > high:
        return high
    return value
def travel_to_axis(travel_mm):
    value = apply_response_curve(
        travel_mm,
        DEADZONE,
        SENSITIVITY,
        CURVE
    )
    return clamp(
        value / max(STEERING_SATURATION, 0.01),
        0.0,
        1.0
    )
def travel_to_pedal(travel_mm):
    return apply_response_curve(
        travel_mm,
        PEDAL_DEADZONE,
        1.0,
        PEDAL_CURVE
    )
def apply_response_curve(travel_mm, deadzone, sensitivity, curve):
    if travel_mm <= 0.0:
        return 0.0
    value = clamp(
        travel_mm / MAX_TRAVEL_MM,
        0.0,
        1.0
    )
    if value <= deadzone:
        return 0.0
    value = (value - deadzone) / (1.0 - deadzone)
    value = math.pow(value, curve)
    value *= sensitivity
    return clamp(value, 0.0, 1.0)
# ============================================================
# Gamepad controller
# ============================================================
class AnalogGamepad:
    def __init__(self):
        self.gamepad = vg.VX360Gamepad()
        self.last_x = None
        self.last_left_y = None
        self.last_throttle = None
        self.last_brake = None
        self.last_right_x = None
        self.last_right_y = None
        self.last_buttons = set()
    def update(self, x, left_y, throttle, brake, right_x, right_y, buttons):
        x = clamp(x)
        left_y = clamp(left_y)
        throttle = clamp(throttle, 0.0, 1.0)
        brake = clamp(brake, 0.0, 1.0)
        right_x = clamp(right_x)
        right_y = clamp(right_y)
        buttons = set(buttons)
        # Only send when changed.
        if (
            self.last_x is not None
            and
            abs(x - self.last_x) < 0.0005
            and
            abs(left_y - self.last_left_y) < 0.0005
            and
            abs(throttle - self.last_throttle) < 0.0005
            and
            abs(brake - self.last_brake) < 0.0005
            and
            abs(right_x - self.last_right_x) < 0.0005
            and
            abs(right_y - self.last_right_y) < 0.0005
            and
            buttons == self.last_buttons
        ):
            return
        self.gamepad.left_joystick_float(
            x_value_float=x,
            y_value_float=left_y
        )
        self.gamepad.right_trigger_float(throttle)
        self.gamepad.left_trigger_float(brake)
        self.gamepad.right_joystick_float(
            x_value_float=right_x,
            y_value_float=right_y
        )
        for button in self.last_buttons - buttons:
            self.gamepad.release_button(button=button)
        for button in buttons - self.last_buttons:
            self.gamepad.press_button(button=button)
        self.gamepad.update()
        self.last_x = x
        self.last_left_y = left_y
        self.last_throttle = throttle
        self.last_brake = brake
        self.last_right_x = right_x
        self.last_right_y = right_y
        self.last_buttons = buttons
    def center(self):
        self.gamepad.left_joystick_float(
            x_value_float=0.0,
            y_value_float=0.0
        )
        self.gamepad.right_trigger_float(0.0)
        self.gamepad.left_trigger_float(0.0)
        self.gamepad.right_joystick_float(
            x_value_float=0.0,
            y_value_float=0.0
        )
        for button in self.last_buttons:
            self.gamepad.release_button(button=button)
        self.gamepad.update()
        self.last_x = 0.0
        self.last_left_y = 0.0
        self.last_throttle = 0.0
        self.last_brake = 0.0
        self.last_right_x = 0.0
        self.last_right_y = 0.0
        self.last_buttons = set()
# ============================================================
# Calculate controller controls
# ============================================================
def calculate_controls(travels):
    # travels are already normalized 0.0 -> 1.0
    w = travel_to_pedal(travels.get(KEY_MAP["Right trigger"], 0.0) * MAX_TRAVEL_MM)
    a = travel_to_axis(travels.get(KEY_MAP["Left stick left"], 0.0) * MAX_TRAVEL_MM)
    s = travel_to_pedal(travels.get(KEY_MAP["Left trigger"], 0.0) * MAX_TRAVEL_MM)
    d = travel_to_axis(travels.get(KEY_MAP["Left stick right"], 0.0) * MAX_TRAVEL_MM)
    # X axis
    # A = left
    # D = right
    x = d - a
    left_y = (
        travels.get(KEY_MAP["Left stick up"], 0.0) - travels.get(KEY_MAP["Left stick down"], 0.0)
    )
    return clamp(x), clamp(left_y), w, s
def calculate_extra_controls(travels):
    right_x = (
        travels.get(KEY_MAP["Right stick right"], 0.0) - travels.get(KEY_MAP["Right stick left"], 0.0)
    )
    right_y = (
        travels.get(KEY_MAP["Right stick up"], 0.0) - travels.get(KEY_MAP["Right stick down"], 0.0)
    )
    magnitude = math.sqrt(
        (right_x * right_x) + (right_y * right_y)
    )
    if magnitude > 1.0:
        right_x /= magnitude
        right_y /= magnitude
    buttons = {
        button
        for control, button in BUTTON_CONTROL_MAP.items()
        if travels.get(KEY_MAP[control], 0.0) >= BUTTON_PRESS_THRESHOLD
    }
    return clamp(right_x), clamp(right_y), buttons
# ============================================================
# Display
# ============================================================
def display(travels, x, throttle, brake):
    print(
        "\r"
        f"W {travels[KEY_MAP['Right trigger']] * MAX_TRAVEL_MM:4.2f} "
        f"A {travels[KEY_MAP['Left stick left']] * MAX_TRAVEL_MM:4.2f} "
        f"S {travels[KEY_MAP['Left trigger']] * MAX_TRAVEL_MM:4.2f} "
        f"D {travels[KEY_MAP['Left stick right']] * MAX_TRAVEL_MM:4.2f} "
        f"| "
        f"Left Stick X {x:+.3f} "
        f"RT {throttle:.3f} "
        f"LT {brake:.3f}",
        end="",
        flush=True
    )
# ============================================================
# STOP MODE
# ============================================================
def stop_mode():
    output_info = find_hid_device(
        OUTPUT_USAGE_PAGE,
        OUTPUT_USAGE
    )
    if output_info is None:
        error = "Kreo Report 6 interface not found."
        print(f"ERROR: {error}")
        if status_callback is not None:
            status_callback("error", error)
            status_callback("stopped")
        return
    device = hid.device()
    try:
        device.open_path(
            output_info["path"]
        )
        print(
            "Sending Kreo Travel Test STOP..."
        )
        result = send_travel_command(
            device,
            False
        )
        print(
            f"STOP command sent ({result} bytes)"
        )
        time.sleep(0.25)
    finally:
        try:
            device.close()
        except Exception:
            pass
# ============================================================
# Main
# ============================================================
def main():
    global toggle_callback
    if "--stop" in sys.argv:
        stop_mode()
        return
    # --------------------------------------------------------
    # Locate interfaces
    # --------------------------------------------------------
    output_info = find_hid_device(
        OUTPUT_USAGE_PAGE,
        OUTPUT_USAGE
    )
    input_info = find_hid_device(
        INPUT_USAGE_PAGE,
        INPUT_USAGE
    )
    if output_info is None:
        error = "Kreo Report 6 interface not found."
        print(f"ERROR: {error}")
        if status_callback is not None:
            status_callback("error", error)
            status_callback("stopped")
        return
    if input_info is None:
        error = "Kreo Report 7 interface not found."
        print(f"ERROR: {error}")
        if status_callback is not None:
            status_callback("error", error)
            status_callback("stopped")
        return
    output_device = hid.device()
    input_device = hid.device()
    gamepad = None
    try:
        # ----------------------------------------------------
        # Open HID interfaces
        # ----------------------------------------------------
        output_device.open_path(
            output_info["path"]
        )
        input_device.open_path(
            input_info["path"]
        )
        # ----------------------------------------------------
        # Enter Travel Test
        # ----------------------------------------------------
        print()
        print("Hive 75 HE connected.")
        print("Entering Travel Test...")
        result = send_travel_command(
            output_device,
            True
        )
        print(
            f"START command sent ({result} bytes)"
        )
        # ----------------------------------------------------
        # Create gamepad
        # ----------------------------------------------------
        gamepad = AnalogGamepad()
        # ----------------------------------------------------
        # Initial state
        # ----------------------------------------------------
        travels = {
            key: 0.0
            for key in mapped_keys()
        }
        decoder = TravelDecoder()
        toggle_ready = True
        last_display = 0.0
        # ----------------------------------------------------
        # Start centered
        # ----------------------------------------------------
        gamepad.center()
        print()
        print()
        print("============================================")
        print(f"       {APP_NAME}")
        print("============================================")
        print()
        print("Movement Left / Right -> Xbox Left Stick X")
        print("Right trigger input -> Xbox Right Trigger")
        print("Secondary trigger input -> Xbox Left Trigger")
        print()
        print("Travel range: 0.00 - 3.50 mm")
        print()
        print("Run with --stop from another CMD to exit")
        print("Travel Test if necessary.")
        print()
        print()
        # ====================================================
        # Main loop
        # ====================================================
        while not stop_requested.is_set():
            # ------------------------------------------------
            # Read Report 7
            # ------------------------------------------------
            data = input_device.read(
                64,
                20
            )
            if data:
                # ------------------------------------------------
                # HIDAPI returns:
                # data[0] = Report ID
                # data[1:] = Report payload
                # ------------------------------------------------
                if data[0] == REPORT_ID_TRAVEL:
                    payload = data[1:]
                    # ------------------------------------------------
                    # Report 7 contains the travel bytes.
                    # We only need complete 2-byte records.
                    # ------------------------------------------------
                    if len(payload) >= 2:
                        packet = payload[:2]
                        result = decoder.decode(
                            packet
                        )
                        if result is not None:
                            key, travel_mm, raw_value = result
                            # ----------------------------------------
                            # Only mapped keys affect the virtual gamepad.
                            # ----------------------------------------
                            if key in travels:
                                normalized = clamp(
                                    travel_mm / MAX_TRAVEL_MM,
                                    0.0,
                                    1.0
                                )
                                # ------------------------------------
                                # HARD ZERO
                                # ------------------------------------
                                if travel_mm <= 0.001:
                                    normalized = 0.0
                                travels[key] = normalized
                                if key == KEY_MAP["Stop Program"]:
                                    if normalized < BUTTON_PRESS_THRESHOLD:
                                        toggle_ready = True
                                    elif toggle_ready:
                                        # F12 is a shortcut for the GUI Stop action.
                                        if toggle_callback:
                                            toggle_callback()
                                        toggle_ready = False
                                    continue
                                # ------------------------------------
                                # Calculate controller controls
                                # ------------------------------------
                                x, left_y, throttle, brake = calculate_controls(
                                    travels
                                )
                                right_x, right_y, buttons = calculate_extra_controls(
                                    travels
                                )
                                # ------------------------------------
                                # Send to Xbox controller
                                # ------------------------------------
                                gamepad.update(
                                    x,
                                    left_y,
                                    throttle,
                                    brake,
                                    right_x,
                                    right_y,
                                    buttons
                                )
            # ====================================================
            # Display
            # ====================================================
            now = time.monotonic()
            if now - last_display >= 0.05:
                x, left_y, throttle, brake = calculate_controls(
                    travels
                )
                if console_mode:
                    display(
                        travels,
                        x,
                        throttle,
                        brake
                    )
                if status_callback is not None:
                    status_callback(
                        "input",
                        travels.copy(),
                        x,
                        throttle,
                        brake
                    )
                last_display = now
    except KeyboardInterrupt:
        print()
        print()
        print("Stopping...")
    except Exception as error:
        print()
        print()
        print("ERROR:")
        print(error)
        if status_callback is not None:
            status_callback("error", str(error))
    finally:
        # ====================================================
        # ALWAYS center Xbox controller
        # ====================================================
        if gamepad is not None:
            try:
                gamepad.center()
            except Exception:
                pass
        # ====================================================
        # ALWAYS exit Kreo Travel Test
        # ====================================================
        try:
            send_travel_command(
                output_device,
                False
            )
            time.sleep(0.25)
        except Exception:
            pass
        # ====================================================
        # Close devices
        # ====================================================
        try:
            input_device.close()
        except Exception:
            pass
        try:
            output_device.close()
        except Exception:
            pass
        print()
        print("HID devices closed.")
        print("Done.")
        if status_callback is not None:
            status_callback("stopped")
        toggle_callback = None
# ============================================================
# Desktop GUI
# ============================================================
class GamepadControlApp:
    def __init__(self, root):
        self.root = root
        self.root.title(APP_NAME)
        try:
            if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
                icon_path = Path(sys._MEIPASS) / "KH75HE-GPE.png"
            else:
                icon_path = Path(__file__).with_name("KH75HE-GPE.png")
            if icon_path.exists():
                self.window_icon = tk.PhotoImage(file=str(icon_path))
                self.root.iconphoto(True, self.window_icon)
        except Exception:
            self.window_icon = None
        self.root.geometry("1060x650")
        self.root.minsize(1060, 650)
        self.root.resizable(True, True)
        self.events = queue.Queue()
        self.worker = None
        self.settings = {
            "Left Stick Deadzone": tk.StringVar(value=SAVED_SETTINGS.get("Left Stick Deadzone", str(DEADZONE))),
            "Left Stick Sensitivity": tk.StringVar(value=SAVED_SETTINGS.get("Left Stick Sensitivity", str(SENSITIVITY))),
            "Left Stick Response Curve": tk.StringVar(value=SAVED_SETTINGS.get("Left Stick Response Curve", str(CURVE))),
            "Left Stick Saturation": tk.StringVar(value=SAVED_SETTINGS.get("Left Stick Saturation", str(STEERING_SATURATION))),
            "Trigger Deadzone": tk.StringVar(value=SAVED_SETTINGS.get("Trigger Deadzone", str(PEDAL_DEADZONE))),
            "Trigger Response Curve": tk.StringVar(value=SAVED_SETTINGS.get("Trigger Response Curve", str(PEDAL_CURVE))),
        }
        self.mapping_vars = {
            control: tk.StringVar(value=self.format_key(KEY_MAP[control]))
            for control in KEY_MAP
        }
        self.state_text = tk.StringVar(value="Stopped")
        self.input_text = tk.StringVar(
            value="Left Stick L 0.00  Left Stick R 0.00  RT 0.00  LT 0.00 mm"
        )
        self.output_text = tk.StringVar(
            value="Left Stick X +0.000  RT 0.000  LT 0.000"
        )
        frame = ttk.Frame(root, padding=16)
        frame.grid()
        # Response settings + status/credits + preset selector
        settings_area = ttk.Frame(frame)
        settings_area.grid(row=2, column=0, columnspan=4, sticky="ew")
        settings_frame = ttk.LabelFrame(
            settings_area, text="Controller Response Settings", padding=8
        )
        settings_frame.grid(row=0, column=0, sticky="nw")
        self.entries = []
        for row, (label, variable) in enumerate(self.settings.items()):
            ttk.Label(settings_frame, text=label).grid(
                row=row, column=0, sticky="w", padx=(0, 8), pady=2
            )
            entry = ttk.Entry(settings_frame, textvariable=variable, width=12)
            entry.grid(row=row, column=1, sticky="e", pady=2)
            self.entries.append(entry)
        # Status and credits are shown beside the response settings,
        # immediately to the left of the Controller Preset.
        info_frame = ttk.Frame(settings_area, padding=(4, 2, 0, 0))
        info_frame.grid(row=0, column=3, sticky="nw", padx=(4, 0))
        # Project branding sits above the emulation status.
        # The logo is slightly larger, with the title and description beside it.
        if getattr(self, "window_icon", None) is not None:
            # Resize the logo with Pillow instead of PhotoImage.subsample().
            # subsample() can drop leftover edge pixels when the source
            # dimensions are not evenly divisible, which can crop the artwork.
            icon_path = Path(sys._MEIPASS) / "KH75HE-GPE.png" if (
                getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS")
            ) else Path(__file__).with_name("KH75HE-GPE.png")
            logo_image = Image.open(icon_path).convert("RGBA")
            source_width, source_height = logo_image.size
            # Keep the full aspect ratio and fit the logo within this box.
            max_logo_width = 80
            max_logo_height = 80
            scale = min(
                max_logo_width / source_width,
                max_logo_height / source_height,
            )
            logo_size = (
                max(1, round(source_width * scale)),
                max(1, round(source_height * scale)),
            )
            logo_image = logo_image.resize(logo_size, Image.Resampling.LANCZOS)
            self.app_logo = ImageTk.PhotoImage(logo_image)
            ttk.Label(info_frame, image=self.app_logo).grid(
                row=0, column=0, rowspan=3, sticky="nw", padx=(0, 10)
            )
        title_frame = ttk.Frame(info_frame)
        title_frame.grid(row=0, column=1, rowspan=2, sticky="nw")
        ttk.Label(
            title_frame, text=APP_NAME, font=("Segoe UI", 14, "bold")
        ).grid(row=0, column=0, sticky="w")
        ttk.Label(
            title_frame,
            text="A Simple, Easy To Use Gamepad Emulation Tool For Kreo Hive75 HE\n",
        ).grid(row=1, column=0, sticky="w", pady=(2, 0))
        self.status_label = ttk.Label(
            info_frame, text="Emulation Status: " + self.state_text.get()
        )
        self.status_label.grid(
            row=2, column=0, columnspan=2, sticky="w", pady=(8, 0)
        )
        ttk.Label(info_frame, textvariable=self.input_text).grid(
            row=3, column=0, columnspan=2, sticky="w", pady=(6, 0)
        )
        ttk.Label(info_frame, textvariable=self.output_text).grid(
            row=4, column=0, columnspan=2, sticky="w"
        )
        ttk.Label(info_frame, text=f"Author: {AUTHOR_NAME}").grid(
            row=5, column=0, columnspan=2, sticky="w", pady=(8, 0)
        )
        github = ttk.Label(
            info_frame,
            text=f"Github Profile: {GITHUB_URL}",
            foreground="blue",
            cursor="hand2",
        )
        github.grid(row=6, column=0, columnspan=2, sticky="w")
        github.bind("<Button-1>", lambda _event: webbrowser.open(GITHUB_URL))
        preset_frame = ttk.LabelFrame(
            settings_area, text="Controller Preset", padding=8
        )
        preset_frame.grid(row=0, column=1, sticky="nw", padx=(12, 0))
        ttk.Label(preset_frame, text="Profile").grid(
            row=0, column=0, sticky="w", padx=(0, 8)
        )
        self.preset_var = tk.StringVar(value="Custom")
        self.preset_combo = ttk.Combobox(
            preset_frame,
            textvariable=self.preset_var,
            values=["Normal", "Racing", "FPS", "Custom"],
            state="readonly",
            width=18,
        )
        self.preset_combo.grid(row=0, column=1, sticky="w")
        self.preset_combo.bind("<<ComboboxSelected>>", self.apply_preset)
        ttk.Label(
            preset_frame,
            text="Normal is recommended for everyday controller use.\n\nRacing preset is tuned for racing and car sim games.\n\nFPS preset is tuned for FPS, RPG and open world games.\n\nNote: These presets are AI generated.",
        ).grid(row=1, column=0, columnspan=2, sticky="w", pady=(8, 0))
        # Custom key mapper
        mapper = ttk.LabelFrame(frame, text="Custom Key Mapper", padding=8)
        mapper.grid(row=4, column=0, columnspan=3, sticky="ew", pady=(10, 0))
        ttk.Label(mapper, text="You will not be limited to use fixed key mapping, because i'm not Kreo to leave it half cooked.\nFeel free to customize key mapping as per your comfort.\n").grid(
            row=0, column=0, columnspan=7, sticky="w", pady=(0, 8)
        )
        groups = [
            ("Movement / Triggers", ("Left stick left", "Left stick right", "Right trigger", "Left trigger")),
            ("Left Stick", ("Left stick up", "Left stick down", "Left stick click")),
            ("Right Stick", ("Right stick up", "Right stick left", "Right stick down", "Right stick right", "Right stick click")),
            ("D-Pad", ("D-pad up", "D-pad left", "D-pad down", "D-pad right")),
            ("Face Buttons", ("A button", "B button", "X button", "Y button")),
            ("Shoulders / System", ("Left bumper", "Right bumper", "Back", "Start")),
            ("Emulation", ("Stop Program",)),
        ]
        # Keep every physical key in every dropdown.  This includes the full
        # Kreo KEY_NAMES table rather than only currently assigned keys.
        self.all_key_options = [
            f"{name} [{key_id}]" for key_id, name in sorted(KEY_NAMES.items())
        ]
        for column, (group_name, group_controls) in enumerate(groups):
            group = ttk.LabelFrame(mapper, text=group_name, padding=6)
            group.grid(row=1, column=column, sticky="n", padx=(0 if column == 0 else 4, 0))
            for row, control in enumerate(group_controls):
                ttk.Label(group, text=control).grid(
                    row=row * 2, column=0, sticky="w", pady=(1, 0)
                )
                combo = ttk.Combobox(
                    group,
                    textvariable=self.mapping_vars[control],
                    values=self.all_key_options,
                    state="readonly",
                    width=17
                )
                combo.grid(row=row * 2 + 1, column=0, sticky="ew", pady=(0, 4))
                combo.bind("<<ComboboxSelected>>", self.mark_custom_preset)
        map_buttons = ttk.Frame(mapper)
        map_buttons.grid(row=2, column=0, columnspan=len(groups), sticky="w", pady=(10, 0))
        ttk.Button(map_buttons, text="Apply Mapping", command=self.apply_mapping).grid(
            row=0, column=0, padx=(0, 6)
        )
        ttk.Button(map_buttons, text="Reset Mapping", command=self.reset_mapping).grid(
            row=0, column=1
        )
        controls = ttk.Frame(frame)
        controls.grid(row=5, column=0, columnspan=3, sticky="ew", pady=(14, 8))
        self.start_button = ttk.Button(
            controls, text="Start", command=self.start
        )
        self.start_button.grid(row=0, column=0, padx=(0, 6))
        self.stop_button = ttk.Button(
            controls, text="Stop", command=self.stop, state="disabled"
        )
        self.stop_button.grid(row=0, column=1, padx=(0, 6))
        ttk.Button(
            controls, text="Reset Response Defaults", command=self.reset_defaults
        ).grid(row=0, column=2)
        root.protocol("WM_DELETE_WINDOW", self.close)
        self.poll_events()
    @staticmethod
    def key_options():
        return [f"{name} [{key_id}]" for key_id, name in KEY_NAMES.items()]
    @staticmethod
    def format_key(key_id):
        return f"{KEY_NAMES.get(key_id, 'Unknown')} [{key_id}]"
    @staticmethod
    def parse_key(value):
        try:
            return int(value.rsplit("[", 1)[1].rstrip("]"))
        except (IndexError, ValueError):
            raise ValueError(f"Invalid key selection: {value}")
    def validate_mapping(self, new_map, show_warning=True):
        reverse = {}
        for control, key_id in new_map.items():
            reverse.setdefault(key_id, []).append(control)
        duplicates = [
            f"{self.format_key(key_id)} -> {', '.join(controls)}"
            for key_id, controls in reverse.items()
            if len(controls) > 1
        ]
        if duplicates and show_warning:
            return messagebox.askyesno(
                "Duplicate key assignments",
                "Some keys are assigned to multiple controls:\n\n"
                + "\n".join(duplicates)
                + "\n\nApply anyway?",
                parent=self.root,
            )
        return not duplicates
    def apply_preset(self, _event=None):
        """Load a built-in controller profile into the mapper."""
        preset_name = self.preset_var.get()
        if preset_name == "Custom":
            return
        preset = PRESETS.get(preset_name)
        if preset is None:
            return
        # Built-in presets must be conflict-free.
        if not self.validate_mapping(preset, show_warning=False):
            messagebox.showerror(
                "Invalid preset",
                f"The {preset_name} preset contains overlapping key assignments.",
                parent=self.root,
            )
            self.preset_var.set("Custom")
            return
        for control, key_id in preset.items():
            if control in self.mapping_vars:
                self.mapping_vars[control].set(self.format_key(key_id))
        # Presets also choose sensible response behavior.
        if preset_name == "Racing":
            defaults = ("0.02", "1.00", "1.35", "1.00", "0.02", "1.60")
        elif preset_name == "FPS":
            defaults = ("0.03", "1.00", "1.00", "1.00", "0.02", "1.00")
        else:  # Normal
            defaults = ("0.02", "1.00", "1.00", "1.00", "0.02", "1.00")
        for variable, value in zip(self.settings.values(), defaults):
            variable.set(value)
        self.apply_mapping(show_message=False)
    def mark_custom_preset(self, *_args):
        if self.preset_var.get() != "Custom":
            self.preset_var.set("Custom")
    def save_current_config(self):
        save_user_config(
            KEY_MAP,
            {label: variable.get() for label, variable in self.settings.items()},
        )
    def apply_mapping(self, show_message=True):
        global KEY_MAP
        try:
            new_map = {
                control: self.parse_key(var.get())
                for control, var in self.mapping_vars.items()
            }
        except ValueError as error:
            messagebox.showerror("Invalid mapping", str(error), parent=self.root)
            return
        if not self.validate_mapping(new_map, show_warning=True):
            return
        KEY_MAP = new_map
        save_user_config(
            KEY_MAP,
            {label: variable.get() for label, variable in self.settings.items()},
        )
        if show_message:
            self.state_text.set("Mapping applied and saved")
            self.status_label.configure(text="Emulation Status: " + self.state_text.get())
    def reset_mapping(self):
        self.preset_var.set("Custom")
        for control, variable in self.mapping_vars.items():
            variable.set(self.format_key(DEFAULT_KEY_MAP[control]))
        self.apply_mapping()
    def read_settings(self):
        ranges = (
            ("Left Stick Deadzone", 0.0, 0.95),
            ("Left Stick Sensitivity", 0.01, 3.0),
            ("Left Stick Response Curve", 0.10, 4.0),
            ("Left Stick Saturation", 0.01, 2.0),
            ("Trigger Deadzone", 0.0, 0.95),
            ("Trigger Response Curve", 0.10, 4.0),
        )
        values = []
        for label, minimum, maximum in ranges:
            try:
                value = float(self.settings[label].get())
            except ValueError:
                raise ValueError(f"{label} must be a number.")
            if not minimum <= value <= maximum:
                raise ValueError(
                    f"{label} must be between {minimum} and {maximum}."
                )
            values.append(value)
        return values
    def toggle_program(self):
        """Start/stop shortcut: exactly the same actions as the GUI buttons."""
        if self.worker is not None and self.worker.is_alive():
            self.stop()
        else:
            self.start()
    def start(self):
        global DEADZONE, SENSITIVITY, CURVE, STEERING_SATURATION
        global PEDAL_DEADZONE, PEDAL_CURVE, status_callback, toggle_callback, console_mode
        try:
            (
                DEADZONE, SENSITIVITY, CURVE, STEERING_SATURATION,
                PEDAL_DEADZONE, PEDAL_CURVE
            ) = self.read_settings()
            save_user_config(
                KEY_MAP,
                {label: variable.get() for label, variable in self.settings.items()},
            )
            self.apply_mapping()
        except ValueError as error:
            messagebox.showerror("Invalid setting", str(error), parent=self.root)
            return
        stop_requested.clear()
        status_callback = lambda *event: self.events.put(event)
        toggle_callback = lambda: self.events.put(("toggle_program",))
        console_mode = False
        self.start_button.configure(state="disabled")
        self.stop_button.configure(state="normal")
        for entry in self.entries:
            entry.configure(state="disabled")
        self.state_text.set("Starting controller...")
        self.status_label.configure(text="Emulation Status: " + self.state_text.get())
        self.worker = threading.Thread(target=main, daemon=True)
        self.worker.start()
    def stop(self):
        if self.worker is not None and self.worker.is_alive():
            stop_requested.set()
            self.state_text.set("Stopping controller...")
            self.status_label.configure(text="Emulation Status: " + self.state_text.get())
            self.stop_button.configure(state="disabled")
    def reset_defaults(self):
        defaults = ("0.02", "1.00", "1.35", "1.00", "0.02", "1.60")
        for variable, value in zip(self.settings.values(), defaults):
            variable.set(value)
    def poll_events(self):
        try:
            while True:
                event = self.events.get_nowait()
                if event[0] == "input":
                    _, travels, x, throttle, brake = event
                    self.state_text.set("Running")
                    self.status_label.configure(text="Emulation Status: " + self.state_text.get())
                    self.input_text.set(
                        "Left Stick L {:.2f}  Left Stick R {:.2f}  RT {:.2f}  LT {:.2f} mm".format(
                            travels.get(KEY_MAP["Left stick left"], 0.0) * MAX_TRAVEL_MM,
                            travels.get(KEY_MAP["Left stick right"], 0.0) * MAX_TRAVEL_MM,
                            travels.get(KEY_MAP["Right trigger"], 0.0) * MAX_TRAVEL_MM,
                            travels.get(KEY_MAP["Left trigger"], 0.0) * MAX_TRAVEL_MM,
                        )
                    )
                    self.output_text.set(
                        "Left Stick X {:+.3f}  RT {:.3f}  LT {:.3f}".format(
                            x, throttle, brake
                        )
                    )
                elif event[0] == "toggle_program":
                    self.toggle_program()
                elif event[0] == "error":
                    self.state_text.set("Error")
                    self.status_label.configure(text="Emulation Status: " + self.state_text.get())
                    messagebox.showerror(
                        "Controller error", event[1], parent=self.root
                    )
                elif event[0] == "stopped":
                    self.state_text.set("Stopped")
                    self.status_label.configure(text="Emulation Status: " + self.state_text.get())
                    self.start_button.configure(state="normal")
                    self.stop_button.configure(state="disabled")
                    for entry in self.entries:
                        entry.configure(state="normal")
        except queue.Empty:
            pass
        self.root.after(50, self.poll_events)
    def close(self):
        save_user_config(
            KEY_MAP,
            {label: variable.get() for label, variable in self.settings.items()},
        )
        if self.worker is not None and self.worker.is_alive():
            self.stop()
            self.root.after(100, self.close)
            return
        self.root.destroy()
def launch_gui():
    root = tk.Tk()
    GamepadControlApp(root)
    root.mainloop()

if __name__ == "__main__":
    if "--stop" in sys.argv:
        stop_mode()
    elif "--console" in sys.argv:
        main()
    else:
        launch_gui()