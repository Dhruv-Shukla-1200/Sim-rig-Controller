# Sim Wheel — Setup & Run Guide

Turns an Android phone into a racing wheel for a Windows PC: the phone sends steering (tilt), throttle, brake and gear buttons over USB, and the PC feeds them into a virtual joystick (vJoy) that racing games read as a real controller.

This guide has two parts:

- **Part 1 — One-time setup.** Do this once per PC (and once per phone).
- **Part 2 — Running it.** The routine every time you want to drive.

---

## Requirements

- A **Windows PC** (vJoy is Windows-only)
- An **Android phone** (Android 8.0 / API 26 or newer) and a **USB cable that carries data** (some cheap cables only charge)
- The Sim Wheel app installed on the phone (see step 6)

---

# Part 1 — One-time setup

## 1. Install Python

1. Download Python from <https://www.python.org/downloads/>.
2. During install, tick **"Add python.exe to PATH"**.
3. Check it worked — open a terminal (PowerShell) and run:
   ```powershell
   python --version
   ```

> **Version note:** older packages like `pyvjoy` can break on very new Python releases. If `pip install pyvjoy` or `import pyvjoy` fails, install Python 3.11 or 3.12 alongside your current one and use that for this project. Multiple Python versions can coexist.

## 2. Install vJoy (the virtual joystick driver)

1. Download and install **vJoy**, and approve the driver install prompts. A restart may be needed afterwards.
2. Open **Configure vJoy** from the Start menu.
3. Select **Device 1** and set it up like this:

   | Setting | Value |
   |---|---|
   | Axes | Enable **X**, **Y**, **Z** |
   | Number of buttons | **at least 3** (we use button 1 = gear up, 2 = gear down, 3 = handbrake, which is unused for now) |
   | Force feedback | Not needed |

4. Click **Apply**.
5. Open **vJoy Monitor** (also installed with vJoy) and leave it handy. It's your visual check that inputs are arriving.

The axis mapping the code uses:

| Input | vJoy output |
|---|---|
| Steering | X axis |
| Throttle | Y axis |
| Brake | Z axis |
| Gear up | Button 1 |
| Gear down | Button 2 |

## 3. Get the project and install the Python dependency

1. Open a terminal in the project root or the `server/` directory.
2. Install the required Python dependencies:
   ```powershell
   pip install -r server/requirements.txt
   ```
   (This installs `pyvjoy` and `aiohttp`. If you have several Python versions, run `python -m pip install -r server/requirements.txt` so it installs into the same Python you'll run the project with.)

3. **Test vJoy on its own** before involving the phone. With vJoy Monitor open:
   ```powershell
   python server/common/vjoy_output.py
   ```
   You should see the X axis jump left, then right, the Y axis move to 50%, and button 1 flash. If that works, the PC side is healthy. The axis moves in **jumps**, not a smooth sweep. That is expected.

## 4. Install ADB (Android platform-tools)

ADB lets the PC talk to the phone over USB. The project uses it to create the USB tunnel the phone connects through.

1. Download **SDK Platform-Tools for Windows** from Google's Android developer site and unzip it somewhere permanent (for example `C:\platform-tools`). If you have Android Studio installed, you already have it at
   `C:\Users\<you>\AppData\Local\Android\Sdk\platform-tools`.
2. Make the project able to find `adb.exe`. Pick **one**:

   **Option A: add it to PATH (works everywhere)**
   - Windows search → *Edit the system environment variables* → *Environment Variables*
   - Under *User variables*, select `Path` → *Edit* → *New* → paste the folder that **contains** `adb.exe` → OK
   - **Close and reopen your terminal**, then check:
     ```powershell
     adb version
     ```

   **Option B: point the project straight at it.** In `server/common/config.py` change:
   ```python
   ADB_PATH = "adb"
   ```
   to the full path (the `r` before the quotes matters on Windows):
   ```python
   ADB_PATH = r"C:\platform-tools\adb.exe"
   ```

## 5. Set up the phone for USB debugging

1. On the phone: **Settings → About phone**, tap **Build number** 7 times to unlock Developer options.
2. **Settings → Developer options → USB debugging → ON**.
3. Plug the phone into the PC.
4. A prompt "Allow USB debugging?" appears on the phone. Tick *Always allow from this computer* and tap **Allow**.
5. Check the PC can see it:
   ```powershell
   adb devices
   ```
   Your phone should be listed with the status `device`. If it says `unauthorized`, accept the prompt on the phone; if the list is empty, see Troubleshooting.

## 6. Install the Sim Wheel app on the phone

Your teammate builds the app in Android Studio. Either:

- they run it onto your phone from Android Studio, **or**
- they build an APK and you install it with:
  ```powershell
  adb install path\to\app-debug.apk
  ```

The app's package name is `com.example.simwheel` (the PC uses this to launch it automatically).

## 7. Set up your game (once per game)

1. Start the game with the phone app running and `main.py` running (Part 2), so vJoy is receiving input.
2. In the game's controller settings, choose the **vJoy Device**.
3. Bind the controls by moving them when the game asks:
   - Steering → tilt the phone left/right
   - Throttle → move the throttle slider
   - Brake → move the brake slider
   - Gear up / gear down → tap the gear buttons
4. Run the game's wheel calibration if it offers one.

Games can be fussy about axes that start at their extreme (throttle and brake rest at zero). If a pedal seems stuck at full or has the wrong direction, use the game's axis *invert* option and recalibrate.

---

# Part 2 — Running it

After the one-time setup, this is the whole routine.

## Every session

1. **Plug the phone in** by USB. USB debugging stays enabled from setup.
2. *(If you're using the haptics/dashboard features with a real game: start the game and get onto the track first.)*
3. **Start the PC server.** In your terminal run:
   ```powershell
   # For Wired mode (USB ADB tunnel + low-latency TCP):
   python server/main.py --mode wired

   # OR for WebSocket mode (Browser game/dashboard + Wi-Fi/USB WebSocket):
   python server/main.py --mode ws
   ```
4. Watch the terminal. A healthy start looks like this:
   ```
   Device connected: <your device id>   device
   Port 5555 reversed (phone -> laptop).
   App launched on phone.
   Listening on 0.0.0.0:5555...
   Connected: ('127.0.0.1', 5xxxx)
   ```
   The last line appears once the phone app connects.
5. **Check the phone.** The app should open on its own (if it doesn't, open it by hand) and show **"PC: connected"**.
6. Open vJoy Monitor, or just launch your game. Tilting the phone and moving the sliders should move the axes live.
7. Drive.

## What `main.py` does for you

Running `main.py` automatically replaces the manual steps from before:

| Used to be manual | Now automatic |
|---|---|
| `adb devices` | checks a phone is connected |
| `adb reverse tcp:5555 tcp:5555` | sets up the USB tunnel |
| Opening the app on the phone | launches it (falls back to manual if it can't) |
| Starting the server | starts it and connects to vJoy |

## Stopping

Press **Ctrl+C** in the terminal. You should see `Shutting down...`, and vJoy is reset to neutral (steering centred, throttle and brake at zero, buttons released) so the game doesn't get stuck on full throttle.

If the **phone is unplugged or the app is closed** mid-session, the PC also resets vJoy to neutral automatically and waits for the phone to reconnect. You don't have to restart anything. Plug in, open the app, and it reconnects.

## Short version

```
Plug in phone  →  double-click run.bat  →  drive
```

---

# Optional: haptics and dashboard

If you've added the haptic feedback and live dashboard features (see `haptics-and-dashboard-guide.md`), set `GAME` in `desktop/config.py`:

```python
GAME = "fake"   # simulated data, for testing without a game
GAME = "acc"    # Assetto Corsa Competizione
GAME = "r3e"    # RaceRoom
```

Start the game first, get onto the track, then run `main.py`.

---

# Troubleshooting

| Symptom | Likely cause and fix |
|---|---|
| `adb not found at 'adb'` | adb isn't installed or isn't on PATH. Redo step 4 (PATH option, or set `ADB_PATH` in `config.py`). After editing PATH, reopen the terminal. |
| `No device found` | Phone not detected. Check the cable (use a data cable), USB debugging is on, the phone is unlocked, and you accepted the "Allow USB debugging?" prompt. Try another USB port. Run `adb devices` yourself to see what it reports. |
| `adb devices` shows `unauthorized` | Accept the debugging prompt on the phone. If it never appears, unplug, then in Developer options choose *Revoke USB debugging authorizations*, then plug in again. |
| `adb reverse failed` | The phone dropped off, or an old adb server is stuck. Run `adb kill-server`, then `adb start-server`, then run `main.py` again. |
| `ModuleNotFoundError: No module named 'pyvjoy'` | `pyvjoy` isn't installed in the Python you're running. Use `python -m pip install -r requirements.txt` so pip and python match. |
| Errors when connecting to vJoy (cannot acquire device, DLL not found) | vJoy isn't installed, Device 1 isn't enabled in *Configure vJoy*, another program is already controlling Device 1, or a restart is needed after install. Re-run `python vjoy_output.py` to test just this layer. |
| Phone shows "PC: not connected" | `main.py` isn't running, or the `adb reverse` step failed. Check the terminal output. The app retries about every second, so it should connect as soon as the PC side is ready. |
| Terminal says `Connected` but vJoy Monitor doesn't move | Check you're looking at Device 1, and that the axes (X/Y/Z) are enabled in *Configure vJoy*. |
| Game doesn't see the controller | Make sure `main.py` is running and the phone is connected *before* the game scans for controllers. Restart the game if needed, and select the vJoy Device in its controller settings. |
| Steering feels inverted or off-centre | Use the game's invert option, or tap **Recenter** in the app while holding the phone in your normal driving position. |
| Ctrl+C seems slow to respond | It can take up to about a second while waiting for a connection. That's expected. |
| `Address already in use` / port 5555 error | A previous `main.py` is still running. Close it (or the terminal that's running it) and try again. |
| App doesn't launch automatically | Non-fatal. Open it by hand on the phone. The rest still works. |

---

# Quick reference

**Project files (`server/`)**

| File | Purpose |
|---|---|
| `server/main.py` | Unified entry point (`--mode wired` or `--mode ws`) |
| `server/wired/adb_utils.py` | Runs the adb commands (device check, reverse, launch app) |
| `server/wired/tcp_server.py` | Low-latency TCP socket receiver for phone packets |
| `server/wired/main_wired.py` | Direct entry point for wired USB connection |
| `server/websocket/ws_server.py` | WebSocket server + HTTP file server for dashboard / game |
| `server/websocket/test_client.py` | Simulated phone client for WebSocket testing |
| `server/common/vjoy_output.py` | Writes values to the vJoy device (run it alone to test vJoy) |
| `server/common/config.py` | Ports, vJoy ranges, button numbers, adb path, app name |
| `server/common/mapping.py` | Converts input ranges to vJoy's 0–32768 axis range |
| `server/requirements.txt` | Python dependencies (`pyvjoy`, `aiohttp`) |

**Key values**

| Item | Value |
|---|---|
| Port | `5555` |
| vJoy device | `1` |
| Phone app package | `com.example.simwheel` |
| Axes | X = steering, Y = throttle, Z = brake |
| Buttons | 1 = gear up, 2 = gear down |
