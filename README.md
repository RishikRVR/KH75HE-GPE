# KH75HE-GPE: Kreo Hive75 HE Gamepad Emulator
<p align="center">
  <img src="KH75HE-GPE.png" alt="KH75HE GPE Logo" width="250">
</p>
A lightweight Windows utility that turns the <b>Kreo Hive 75 HE</b>
Hall-effect keyboard into a virtual <b>Xbox 360 controller</b>.

Instead of treating a key as simply pressed or released, the program
reads the keyboard's Hall-effect travel data and uses the actual key
depth as an analog value. This makes it possible to use the Hive 75 HE
for applications and games that expect analog controller input.

> **Project status:** Experimental / personal project\
> **Platform:** Windows\
> **Keyboard:** Kreo Hive 75 HE\
> **Virtual controller:** Xbox 360 / XInput

------------------------------------------------------------------------

## What does it do?

The Hive 75 HE can report how far a magnetic switch has moved. This
program reads that travel information directly from the keyboard and
converts it into virtual controller inputs.

For example:

-   Pressing **A** slightly can produce a small left-stick movement.
-   Pressing **A** farther produces a stronger left-stick movement.
-   Releasing the key brings the value back toward zero.
-   The same idea can be used for the triggers and other analog
    controls.

This is different from a normal keyboard-to-controller mapper, where a
key usually has only two states:

``` text
Normal keyboard:
Released -> 0
Pressed  -> 1

KH75 HE Gamepad Emulator:
Released -> 0.00
Partial press -> 0.20
More press   -> 0.60
Full press   -> 1.00
```

The exact response depends on the configured response curve and the
physical travel reported by the keyboard.

------------------------------------------------------------------------

## Features

### Analog Hall-effect input

Reads the Hive 75 HE's native magnetic travel data instead of relying
only on normal keyboard key events.

### Xbox controller emulation

Creates a virtual Xbox 360 controller using `vgamepad`, allowing games
that support XInput controllers to see the keyboard as a gamepad.

### Custom key mapping

The GUI lets you choose which physical Hive 75 HE key controls each
virtual Xbox input.

Mappings are organised into groups such as:

-   Left Stick
-   Right Stick
-   D-Pad
-   Face Buttons
-   Shoulders / System
-   Triggers
-   Emulation controls

The available keyboard keys are displayed by name and Kreo key ID.

### Controller response settings

The application provides configurable response controls for:

-   Left Stick Deadzone
-   Left Stick Sensitivity
-   Left Stick Response Curve
-   Left Stick Saturation
-   Trigger Deadzone
-   Trigger Response Curve

This makes it possible to tune the controller for different games and
different preferences.

### Presets

Built-in profiles are available for common use cases:

-   **Normal** --- general-purpose controller-style mapping
-   **Racing** --- stronger progressive analog response
-   **FPS** --- keyboard-oriented movement and right-stick controls
-   **Custom** --- manually configured mapping

Selecting a preset also applies suitable response settings.

### Configuration persistence

Your mapping and response settings are saved automatically to:

``` text
KH75HE-GPE_config.json
```

The file is stored beside the Python application, so your configuration
survives restarting the program.

### GUI and console modes

The program can be used through the graphical interface or directly from
the command line.

The GUI is intended to make configuration and everyday use easier, while
console mode is useful for testing and troubleshooting.

## Tested Games

The following games have been tested successfully with **KH75HE-GPE**:

- Forza Horizon 5
- Forza Horizon 6
- Grand Theft Auto V
- Red Dead Redemption 2

### Test System

**OS:** Windows 11 Enterprise LTSC IoT  
**Motherboard:** ASUS TUF GAMING B760M-E D4  
**CPU:** Intel Core i5-12400F  
**RAM:** 32 GB DDR4 3200 MHz  
**GPU:** NVIDIA GeForce RTX 3050 8 GB GDDR6 OC

## Resource Usage

During testing, KH75HE-GPE used approximately:

- **RAM:** 16.2 MB average
- **CPU:** 0.3% average
- **CPU Peak:** 1.0%

These results indicate that the emulator has a very low system overhead and should not have a noticeable impact on gaming performance under normal conditions.

> **Note:** Resource usage may vary depending on the system, background applications, game, and configuration. The figures above are based on tests performed on the hardware listed above. 

------------------------------------------------------------------------

# How it works

The program communicates with the Hive 75 HE through two vendor-defined
HID interfaces.

At a high level, the data flow is:

``` text
Kreo Hive 75 HE
       |
       v
Hall-effect travel data
       |
       v
HID Report 7
       |
       v
Travel decoder
       |
       v
0.00 - 3.50 mm
       |
       v
Response curve / normalization
       |
       v
Virtual Xbox 360 controller
       |
       v
Game / application
```

The program also sends a Kreo HID command to place the keyboard into its
magnetic-axis travel test mode.

------------------------------------------------------------------------

## Kreo travel data

The Hive 75 HE identifies individual keys with internal numeric IDs.

For example:

  Key     Kreo ID
  ----- ---------
  W            32
  A            46
  S            47
  D            48

The keyboard reports travel using two 6-bit pieces of data.

The program reconstructs those pieces into a raw travel value and then
applies the keyboard's scale:

``` text
raw value × 0.01 = travel in millimetres
```

The useful travel range used by the application is:

``` text
0.00 mm - 3.50 mm
```

The decoder keeps pending data **per key**, which is important because
reports from different keys can be interleaved while several keys are
being pressed.

------------------------------------------------------------------------

# Getting Started

There are two ways to use **KH75 HE Gamepad Emulator**. If you only want to use the application, the compiled release is the easiest option. If you want to modify, debug, or develop the project, you can run it directly from source.

## Option 1 — Compiled Release

The compiled release is for users who simply want to use the emulator without setting up a Python environment.

Download the latest compiled Windows release from the project's **Releases** page and extract it somewhere convenient.

You do **not** need to install:

- Python
- `hidapi`
- `vgamepad`
- Python packages

The application is packaged with PyInstaller.

> **Important:** The virtual Xbox 360 controller still depends on a compatible **ViGEmBus** installation on Windows. The Python environment is bundled into the executable, but the virtual-controller driver is a Windows system component and cannot be bundled into the application.

Once the required driver is installed:

1. Connect the Kreo Hive 75 HE.
2. Run `KH75 HE Gamepad Emulator.exe`.
3. Choose a preset or configure your own mapping.
4. Adjust the controller response settings if required.
5. Press **Start**.
6. Test the virtual controller in Windows or in your target game.

Your configuration is saved beside the executable:

```text
KH75HE-GPE_config.json
```

This is the recommended option if you just want to use the application.

## Option 2 — Run from Source

The source version is useful if you want to modify the application, troubleshoot a problem, experiment with the HID protocol, or contribute to development.

### Requirements

#### Hardware

- Kreo Hive 75 HE keyboard
- Windows PC

The program is specifically written around the HID protocol exposed by the Hive 75 HE.

It is **not** a generic Hall-effect keyboard driver.

#### Software

You need:

- Python 3
- `hidapi` / Python `hid`
- `vgamepad`
- A working **ViGEmBus** installation
- Tkinter (normally included with standard Windows Python installations)

Install the Python packages with:

```bash
pip install hidapi vgamepad
```

If your Python installation does not include Tkinter, install a standard Windows Python distribution that includes it.

### Run from source

From the project directory:

```bash
python KH75HE-GPE.py
```

The graphical interface should open.

For troubleshooting or direct testing:

```bash
python KH75HE-GPE.py --console
```

To send the command used to exit the keyboard's magnetic-axis travel-test mode:

```bash
python KH75HE-GPE.py --stop
```

## Which option should I use?

| If you want to... | Use |
| --- | --- |
| Just use the emulator | **Compiled Release** |
| Avoid installing Python and packages | **Compiled Release** |
| Change the source code | **Run from Source** |
| Debug HID communication | **Run from Source** |
| Develop new features | **Run from Source** |
| Experiment with the keyboard protocol | **Run from Source** |

The compiled release is the simplest choice for normal users. The source version is mainly for people who want to work on the project itself.

------------------------------------------------------------------------

# Using the GUI

## 1. Choose a preset

Start with **Normal** if you simply want a general-purpose virtual
controller.

Use:

-   **Racing** for progressive throttle/trigger-style input
-   **FPS** for keyboard-oriented movement
-   **Custom** when you want complete control over the mapping

You can change individual mappings after selecting a preset.

------------------------------------------------------------------------

## 2. Adjust controller response

### Left Stick Deadzone

Controls how much initial movement is ignored.

A larger value means the stick will not react to very small travel
values.

Example:

``` text
0.00 -> almost no deadzone
0.02 -> small deadzone
0.10 -> noticeable deadzone
```

### Left Stick Sensitivity

Controls how quickly travel reaches the requested stick output.

Higher values make the stick respond more aggressively.

### Left Stick Response Curve

Controls the relationship between physical key travel and virtual stick
output.

A curve around `1.0` is relatively direct.

Higher values make the early part of the movement softer and reserve
more output for deeper presses.

### Left Stick Saturation

Controls the travel level at which the stick reaches full output.

### Trigger Deadzone

Ignores very small trigger travel.

### Trigger Response Curve

Controls how trigger output increases as the key is pressed deeper.

------------------------------------------------------------------------

# Custom mapping

Each virtual controller input can be assigned to a Hive 75 HE key.

For example, a traditional keyboard-style layout can be:

``` text
W -> Left Stick Up
A -> Left Stick Left
S -> Left Stick Down
D -> Left Stick Right
```

You can also assign Hall-effect keys to analog triggers:

``` text
Z -> Left Trigger
X -> Right Trigger
```

The exact mapping is completely configurable.

## Duplicate assignments

The application checks for duplicate physical-key assignments.

If the same keyboard key is assigned to multiple controller controls,
the GUI warns you before applying the mapping.

Duplicate assignments are allowed if you explicitly choose to continue,
but they can make the resulting controller behaviour confusing.

------------------------------------------------------------------------

# Presets vs Custom mode

Presets are intended as convenient starting points rather than universal
layouts.

For a particular game, it is usually better to:

1.  Select the closest preset.
2.  Change the required keys.
3.  Adjust the response settings.
4.  Apply the mapping.
5.  Test the controller in Windows or in the target game.

When you manually change a preset, the mapping becomes a custom
configuration.

------------------------------------------------------------------------

# Understanding analog input

One of the main reasons to use this project with the Hive 75 HE is the
difference between **key state** and **key travel**.

A normal keyboard mapper might do this:

``` text
A pressed
    |
    +----> Left stick = -1.0
```

The Hall-effect approach can do this:

``` text
A pressed 10%
    |
    +----> Left stick = -0.10

A pressed 50%
    |
    +----> Left stick = -0.50

A pressed 100%
    |
    +----> Left stick = -1.00
```

This can be useful for games where gradual controller input is
beneficial.

------------------------------------------------------------------------


# Development History — How the Project Was Built

This section documents the complete development journey from the original idea to the working emulator.

## Define the goal

The original goal was to make the Kreo Hive 75 HE behave like an analog controller by using the Hall-effect switches' actual travel depth.

The target was:

```text
Key travel -> proportional analog controller input
```

instead of:

```text
Key pressed -> digital button
```

The first target was WASD movement on the left analog stick.

## Identify the keyboard

The Hive 75 HE was identified as:

```text
Manufacturer: I-CHIP
Product:      HIVE 75 HE

VID: 0x28E9
PID: 0x3201
```

The keyboard exposes vendor-defined HID interfaces in addition to its normal keyboard and mouse interfaces.

## Investigate Kreo's own software

Kreo Kontrol uses WebHID. Its JavaScript bundle was inspected so the keyboard protocol could be understood from Kreo's own implementation rather than guessed.

The main bundle was found at:

```text
https://he.kreo-tech.com/assets/index-BqufFdb1.js
```

This source contained the code Kreo itself uses to communicate with and decode the keyboard.

## Discover the magnetic-axis command

The source contained the magnetic-axis command:

```text
0x36
```

It was identified as the command for entering and leaving the magnetic-axis button simulation/travel test.

The two operations are:

```text
0x36 + 0x01 -> start travel test
0x36 + 0x00 -> stop travel test
```

This was a key discovery because it meant firmware modification was unnecessary.

## Identify the important HID reports

Inspection of the HID descriptor showed:

```text
Report ID 6 -> vendor command/output report
Report ID 7 -> vendor travel/input report
```

Report 7 became the main source of analog key travel data.

## Capture real HID traffic

Kreo's WebHID `sendReport()` calls were instrumented to observe what the official software actually sent.

The magnetic-axis packets contained:

```text
54 decimal = 0x36
```

and matched the command discovered in the JavaScript source.

This confirmed that the reverse-engineered command was being used by Kreo's own software.

## Reverse-engineer Report 7

The Kreo JavaScript revealed that travel is encoded using two 6-bit pieces.

The important reconstruction is effectively:

```text
((second_byte & 0x3F) << 6) | previous_6_bit_value
```

The resulting value is multiplied by:

```text
0.01
```

Therefore:

```text
raw value × 0.01 = travel in millimetres
```

The working range used by the application is:

```text
0.00 mm - 3.50 mm
```

## Discover the key IDs

The travel reports identify keys using Kreo-specific numeric IDs.

Important IDs include:

```text
W = 32
A = 46
S = 47
D = 48
```

A complete key-name table was then built for use by the custom mapper.

## Verify the decoder with real values

Captured Report 7 data was compared with values printed by Kreo's own decoder.

Examples included:

```text
[32,84]  -> 0.20 mm
[32,91]  -> 0.27 mm
[32,99]  -> 0.35 mm
[32,106] -> 0.42 mm
```

Values continued through the travel range, confirming that the keyboard was exposing continuous analog depth.

## Handle interleaved reports

Reports from multiple keys can be interleaved.

The decoder therefore could not simply assume that every two incoming bytes belonged to one fixed pair.

The implementation preserves the decoder state per key so simultaneous key presses can be handled correctly.

## Build the first Python HID reader

A Python HID reader was created to:

1. Find the Hive 75 HE using its VID/PID.
2. Open the appropriate HID interface.
3. Enter magnetic-axis travel mode.
4. Read Report 7.
5. Decode key IDs and travel.
6. Convert travel to millimetres.
7. Display the values for testing.

This established a working direct path from the keyboard to Python.

## Add virtual Xbox controller emulation

`vgamepad` was installed and used to create a virtual Xbox 360 controller.

A separate test confirmed that the virtual controller appeared correctly and that its left stick could be moved programmatically.

## Connect analog travel to the virtual stick

Travel was normalized from approximately:

```text
0.00 - 3.50 mm
```

to:

```text
0.0 - 1.0
```

The WASD relationship was implemented as:

```text
A -> Left Stick Left
D -> Left Stick Right
W -> Left Stick Up
S -> Left Stick Down
```

Diagonal movement was also handled so the combined stick magnitude remained controlled.

## Fix key-release behaviour

Early versions sometimes failed to return a controller value to zero after a key was released.

Different decoder approaches were tested before settling on the protocol-faithful stateful travel decoder.

The important lesson was that the Hive's vendor reports should not be treated like ordinary keyboard press/release events.

## Remove the artificial timeout

A temporary no-data timeout was tested:

```text
NO_DATA_TIMEOUT = 0.50
```

It caused a serious problem: holding a key for longer than the timeout could reset its value even though the key was still physically held.

The timeout was removed.

The working implementation deliberately does **not** reset held keys merely because no new travel report arrives for an arbitrary amount of time.

## Develop the racing response

A racing-oriented response was added as an early advanced profile.

The initial tuning included:

```text
Left Stick Deadzone:       0.02
Left Stick Sensitivity:    1.00
Left Stick Response Curve: 1.35
```

Progressive trigger-style curves were also introduced for deeper key travel.

## Turn the experiment into a general controller emulator

The project was redesigned so it was not tied to racing.

The GUI was reorganized around standard controller concepts:

```text
Left Stick
Right Stick
D-Pad
Face Buttons
Shoulders / System
Triggers
Emulation
```

## Add custom key mapping

A custom mapper was added so virtual controller inputs could be assigned to physical Hive keys.

The mapper was split into dedicated controller sections instead of one large undifferentiated list.

The available Hive key IDs were exposed by name, making the full keyboard easier to map.

Duplicate physical-key assignments are detected and reported.

## Add controller response settings

The GUI gained general response controls:

```text
Left Stick Deadzone
Left Stick Sensitivity
Left Stick Response Curve
Left Stick Saturation
Trigger Deadzone
Trigger Response Curve
```

These settings control the relationship between physical key travel and virtual controller output.

## Add presets

Four starting profiles were added:

```text
Normal
Racing
FPS
Custom
```

The purpose of presets is to provide useful starting configurations while still allowing individual mappings to be edited.

## Add persistent configuration

Mappings and response settings were saved to:

```text
KH75HE-GPE_config.json
```

This file is stored beside the Python script.

Deleting the JSON file resets the application to its built-in defaults.

## Add GUI Start/Stop control

The emulator was given GUI Start and Stop controls so the program could remain open while controller processing was started or stopped.

## Add a key as the Stop shortcut

F12 was added as a shortcut for the GUI Stop action to let users switch back to normal keyboard mode.

It is a **program shortcut**, not an Xbox controller button:

```text
F12
 |
 +--> Start emulator if stopped
 |
 +--> Stop emulator if running
```

## Generalize the terminology

Early versions contained racing-specific names such as:

```text
Steer left
Steer right
Throttle
Brake / reverse
```

These were changed to controller-oriented names such as:

```text
Left stick left
Left stick right
Right trigger
Left trigger
```

This made the application feel like a general controller emulator instead of a racing-only tool.


## Keep firmware untouched

Throughout development, the decision was made not to flash or modify the keyboard firmware.

The final approach uses the existing vendor HID interface and commands already exposed by the keyboard.

---

# Troubleshooting

## Keyboard is not detected

Check:

```bash
python -c "import hid; print(hid.enumerate(0x28E9, 0x3201))"
```

Also make sure another application is not exclusively holding the relevant HID interface.

## Virtual controller does not appear

Check:

```bash
pip show vgamepad
```

Then verify that a compatible ViGEmBus driver is installed and working.

## Keyboard remains in travel-test mode

Run:

```bash
python KH75HE-GPE.py --stop
```

Then restart the application.

---

# Credits

**KH75 HE Gamepad Emulator**

Author: **RishikRVR**

GitHub:

https://github.com/RishikRVR

---

# Project architecture

The main script is divided into several logical parts.

### HID discovery

Finds the Hive 75 HE interfaces using:

``` text
VID = 0x28E9
PID = 0x3201
```

The application looks for the vendor-defined HID interfaces used for
command output and travel input.

### Travel-test command

The Kreo magnetic-axis command is:

``` text
0x36
```

The application uses it to enter and leave the keyboard's travel-test
mode.

### Travel decoder

`TravelDecoder` reconstructs the two-part travel report and converts it
to millimetres.

### Input normalization

The travel value is converted from:

``` text
0.00 - 3.50 mm
```

to:

``` text
0.0 - 1.0
```

before controller response processing.

### Response processing

Deadzone, sensitivity, curve and saturation are applied before the final
virtual-controller values are generated.

### Virtual gamepad

`vgamepad` receives the calculated stick, trigger and button states and
exposes them as an Xbox 360 controller.

### GUI

Tkinter provides the configuration interface and displays the current
input/output state.

------------------------------------------------------------------------

# Configuration file

The application automatically creates:

``` text
KH75HE-GPE_config.json
```

Example structure:

``` json
{
  "mapping": {
    "Left stick left": 46,
    "Left stick right": 48
  },
  "settings": {
    "Left Stick Deadzone": "0.02",
    "Left Stick Sensitivity": "1.00"
  }
}
```

You normally do not need to edit this file manually.

If you want to completely reset the saved configuration, close the
application and delete the JSON configuration file. The next launch will
use the built-in defaults.

------------------------------------------------------------------------

# Safety and limitations

This project communicates directly with a specific keyboard's
vendor-defined HID interface.

That means:

-   It is specific to the Kreo Hive 75 HE protocol.
-   Future keyboard firmware updates could change the protocol.
-   It is not guaranteed to work with other Hall-effect keyboards.
-   Some games may reject virtual controllers or use anti-cheat systems
    that interfere with virtual input devices.
-   Controller behaviour can vary between games.
-   ViGEmBus is discontinued software, so long-term compatibility is not
    guaranteed.

No keyboard firmware modification is required by this project.

The application communicates with the keyboard through HID commands and
reads its existing travel reports.

------------------------------------------------------------------------

# Development notes

The project was built by reverse-engineering the Hive 75 HE's HID
communication.

Important protocol observations include:

``` text
Keyboard VID:              0x28E9
Keyboard PID:              0x3201

Command report ID:         6
Travel report ID:          7

Travel scale:              0.01
Maximum travel used:       3.50 mm

Magnetic-axis command:     0x36
```

The travel decoder reconstructs the keyboard's two-part 6-bit travel
value and associates it with the corresponding Kreo key ID.

The project deliberately avoids firmware flashing.

------------------------------------------------------------------------

# Credits

**KH75 HE Gamepad Emulator**

Author: **RishikRVR**

GitHub:

https://github.com/RishikRVR

The project uses:

-   Python
-   hidapi / Python HID
-   vgamepad
-   ViGEmBus
-   Tkinter

------------------------------------------------------------------------

# Disclaimer

This is an experimental community/personal project and is not affiliated
with Kreo.

Use it at your own risk. The software communicates with the keyboard
using vendor-specific HID commands, and compatibility may change with
future firmware or software updates.
