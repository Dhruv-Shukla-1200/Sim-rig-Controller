# Sim Wheel — Setup & Run Guide

Turns an Android phone into a racing wheel for a Windows PC: the phone sends steering (tilt), throttle, brake, gear and handbrake inputs over USB or Wi-Fi, and the PC feeds them into a virtual joystick (vJoy) that racing games read as a real controller.

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
   | Number of buttons | **at least 3** (we use button 1 = gear up, 2 = gear down, 3 = handbrake, held from the on-screen HANDBRAKE button) |
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

The app's package name is `com.example.simwheel` (the server uses this to open it on the phone automatically).

## 7. Set up your game (once per game)

1. Start the game with the phone app running and the server running (Part 2), so vJoy is receiving input.
2. In the game's controller settings, choose the **vJoy Device**.
3. Bind the controls by moving them when the game asks:
   - Steering → tilt the phone left/right
   - Throttle → move the throttle slider
   - Brake → move the brake slider
   - Gear up / gear down → tap the gear buttons
   - Handbrake → hold the HANDBRAKE button
4. Run the game's wheel calibration if it offers one.

Games can be fussy about axes that start at their extreme (throttle and brake rest at zero). If a pedal seems stuck at full or has the wrong direction, use the game's axis *invert* option and recalibrate.

---

# Part 2 — Running it

After the one-time setup, this is the whole routine.

## Every session

1. *(If you're using a real game: start it and get onto the track first, so it sees vJoy.)*
2. **Plug the phone in** by USB. USB debugging stays enabled from setup.
3. **Start the server** in a terminal in the project root:
   ```powershell
   python server/main.py
   ```
4. Watch the terminal. A healthy USB start looks like this:
   ```
   ====================================================
     SIM RIG CONTROLLER - WEBSOCKET SERVER
     Dashboard : http://localhost:8080
     Pair code : 2025   (Wi-Fi mode only)
     Wi-Fi addr: 192.168.1.15:8080
     USB mode  : automatic (plug in the phone, tunnel is set up for you)
     vJoy      : on
   ====================================================
   [adb] Phone detected over USB
   [adb] USB tunnel ready (tcp:8080 -> this laptop)
   [adb] App launched on phone
   [ws:phone] Connected via usb from 127.0.0.1
   ```
   The last line appears once the phone app connects.
5. **Check the phone.** In the app, tap **☰** and choose **USB**. The status should read **Connected · USB**.
6. Open **`http://localhost:8080`** in a browser. The Phone chip should say *Phone connected via USB*, and the wheel, pedals and latency readout should move live.
7. Open vJoy Monitor, or just launch your game. Tilting the phone and moving the sliders should move the axes live.
8. Drive.

**Wi-Fi instead of USB:** make sure the phone and laptop are on the same network, tap **☰** → **Wi-Fi** in the app, enter the `Wi-Fi addr` and `Pair code` printed in the terminal, and tap **Join**.

## What the server does for you

You no longer run adb commands by hand. While the server is running, it checks every few seconds:

| Used to be manual | Now automatic |
|---|---|
| `adb devices` | checks whether a phone is attached and authorised |
| `adb reverse tcp:8080 tcp:8080` | sets up the USB tunnel, and sets it up again if you unplug and replug |
| Opening the app on the phone | opens it the first time the phone appears (skip with `--no-auto-launch`) |
| vJoy connection | opens vJoy Device 1; if vJoy is missing it runs dashboard-only |

Useful flags:

```powershell
python server/main.py --no-vjoy          # dashboard only, no vJoy
python server/main.py --code 1234        # fixed Wi-Fi pair code
python server/main.py --no-adb           # do not run adb (Wi-Fi only, or set up USB by hand)
python server/main.py --no-auto-launch   # set up USB but do not open the app
```

If you use `--no-adb`, set up the USB tunnel yourself with `adb reverse tcp:8080 tcp:8080`. USB mode expects the default port 8080.

## Stopping

Press **Ctrl+C** in the terminal. vJoy is reset to neutral (steering centred, throttle and brake at zero, buttons released) so the game doesn't get stuck on full throttle.

If the **phone is unplugged or the app is closed** mid-session, the server also resets vJoy to neutral automatically and waits for the phone to reconnect. Plug in, and the app reconnects by itself (it retries every second).

## Short version

```
Plug in phone  →  python server/main.py  →  ☰ → USB in the app  →  drive
```

---

# Troubleshooting

| Symptom | Likely cause and fix |
|---|---|
| Server prints `adb not found` | adb isn't installed or isn't on PATH. USB auto-setup is off (Wi-Fi still works). Redo step 4 (PATH option, or set `ADB_PATH` in `server/common/config.py`, or set `ANDROID_HOME`). After editing PATH, reopen the terminal and restart the server. |
| Server prints `No phone attached over USB` | Phone not detected. Check the cable (use a data cable), USB debugging is on, the phone is unlocked, and you accepted the "Allow USB debugging?" prompt. Try another USB port. Run `adb devices` yourself to see what it reports. |
| Server prints `Phone found but not authorised` | Accept the debugging prompt on the phone. If it never appears: Developer options → *Revoke USB debugging authorizations*, then unplug and plug in again. |
| `adb reverse failed` | An old adb server is stuck, or more than one device is attached. Run `adb kill-server`, then `adb start-server`. The server retries every 3 seconds. |
| `ModuleNotFoundError: No module named 'pyvjoy'` | `pyvjoy` isn't installed in the Python you're running. Use `python -m pip install -r server/requirements.txt` so pip and python match. The server still runs dashboard-only without it. |
| vJoy errors (cannot acquire device, DLL not found) | vJoy isn't installed, Device 1 isn't enabled in *Configure vJoy*, another program is controlling Device 1, or a restart is needed after install. Test just this layer with `python server/common/vjoy_output.py`. |
| Phone shows "Waiting for controller…" in USB mode | Check the server log says `USB tunnel ready`. If it doesn't, see the adb rows above. The app retries every second, so it connects as soon as the tunnel is up. |
| Phone shows "Wrong pair code" | Wi-Fi mode: re-enter the 4-digit code shown in the terminal and on the dashboard. USB mode needs no code. |
| Wi-Fi mode won't connect | Phone and laptop must be on the same network, and some networks block device-to-device traffic. Allow Python through Windows Firewall (Private networks), or use USB / a phone hotspot. |
| Server says connected but vJoy Monitor doesn't move | Check you're looking at Device 1, and that the axes (X/Y/Z) are enabled in *Configure vJoy*. |
| Game doesn't see the controller | Make sure the server is running and the phone is connected *before* the game scans for controllers. Restart the game if needed, and select the vJoy Device in its controller settings. |
| Steering feels inverted or off-centre | Use the game's invert option, or tap **Recenter** in the app while holding the phone in your normal driving position. |
| `Address already in use` / port 8080 error | A previous server is still running. Close it (or the terminal running it) and try again. |
| App doesn't launch automatically | Non-fatal. Open it by hand on the phone. The rest still works. |

---

# Quick reference

**Project files (`server/`)**

| File | Purpose |
|---|---|
| `server/main.py` | Entry point (`python server/main.py`) |
| `server/websocket/ws_server.py` | WebSocket server, HTTP file server for the dashboard / game, USB auto-setup loop |
| `server/websocket/test_client.py` | Simulated phone client for testing without the app |
| `server/common/adb_utils.py` | adb helpers: device state, USB tunnel, launch the app |
| `server/common/vjoy_output.py` | Writes values to the vJoy device (run it alone to test vJoy) |
| `server/common/config.py` | Port, vJoy ranges, button numbers, adb path, app name |
| `server/common/mapping.py` | Converts input ranges to vJoy's 0–32768 axis range |
| `server/requirements.txt` | Python dependencies (`pyvjoy`, `aiohttp`) |

**Key values**

| Item | Value |
|---|---|
| Port | `8080` (dashboard, USB and Wi-Fi) |
| vJoy device | `1` |
| Phone app package | `com.example.simwheel` |
| Axes | X = steering, Y = throttle, Z = brake |
| Buttons | 1 = gear up, 2 = gear down, 3 = handbrake |
