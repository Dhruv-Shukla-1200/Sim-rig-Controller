# Sim Wheel — Anything but a Game Controller

> **Turn your Android phone into a real-time racing wheel and pedal box** — streams sensor data at 60 Hz to a live browser dashboard and into Windows racing simulators via a virtual joystick driver (vJoy).

Built for the **"Anything but a Game Controller"** project challenge.

---

## Table of Contents

1. [About the Project](#1-about-the-project)
2. [Features](#2-features)
3. [Tech Stack](#3-tech-stack)
4. [System Architecture](#4-system-architecture)
5. [Pairing & Connection Modes](#5-pairing--connection-modes)
6. [Latency Approach & Performance](#6-latency-approach--performance)
7. [Full Setup Guide](#7-full-setup-guide)
8. [How to Play & Calibrate](#8-how-to-play--calibrate)
9. [Project File Reference](#9-project-file-reference)
10. [Building & Exporting the APK](#10-building--exporting-the-apk)
11. [Troubleshooting](#11-troubleshooting)

---

## 1. About the Project

Sim Wheel replaces a traditional gamepad or keyboard with an Android smartphone held in landscape mode like a real steering wheel. The phone's built-in rotation vector sensor drives steering; touch sliders on the left and right edges act as the brake and throttle pedals; large paddle-style buttons handle gear shifts; and a press-and-hold button works as the handbrake.

The phone streams all inputs over a WebSocket connection to a Python server running on a Windows laptop. The server simultaneously:
- **Feeds a vJoy virtual joystick driver** so desktop racing titles (Forza Motorsport, Assetto Corsa, Assetto Corsa Competizione, RaceRoom, etc.) read it as a real game controller.
- **Serves a browser-based dashboard** at `http://localhost:8080` showing live steering angle, pedal bars, latency graphs, gear indicator lights, and a playable top-down canvas racing mini-game.

### How the sensors are used

| Sensor | Used for | How |
|---|---|---|
| **Gyroscope + accelerometer (+ magnetometer where present)** | **Steering** | The app reads Android's `TYPE_ROTATION_VECTOR`. Android describes this as a software sensor, usually computed by fusing the gyroscope, accelerometer and magnetometer. The gyroscope gives fast, smooth rotation, and the accelerometer's gravity reading stops it drifting. The app converts the result to a tilt angle with `atan2`. |
| **Accelerometer (read directly)** | **Drop / free-fall safety** | `DropDetector.kt` listens to `TYPE_ACCELEROMETER`. At rest the magnitude is about 9.8 m/s². In free fall it falls close to zero. If it stays below 2.5 m/s² for 80 ms, the app treats it as a drop, releases all controls and sends all-zero packets for 1.5 s. |

**Why the fused rotation vector instead of hand-filtering the raw gyro and accelerometer?** Android's fusion is tuned per device, and in our tests it gave steady steering with little jitter or drift. A hand-written filter would add code without a clear gain. The raw accelerometer is still read directly where fusion doesn't help: detecting a fall.

---

## 2. Features

### Android App (SimWheel)

| Feature | Detail |
|---|---|
| **Tilt Steering** | Uses `Sensor.TYPE_ROTATION_VECTOR` (Android's fusion of gyroscope, accelerometer and usually magnetometer) + `atan2` over full ±180° range. Stays locked at max (±1.0) past 90° — no fold-back. |
| **Auto Re-center** | First sensor reading auto-calibrates neutral. Tap **Recenter Wheel** any time. |
| **Throttle & Brake Sliders** | Continuous vertical touch sliders. Release = spring-to-zero for stuck throttle prevention. |
| **Gear Shift Paddles** | Pulse buttons for Gear Up and Gear Down, sent as boolean events. |
| **Handbrake Button** | Press-and-hold button under Gear Down. Sent as `handbrake` and mapped to vJoy button 3; releasing it releases the handbrake. |
| **Drop Safety** | Accelerometer free-fall detection. If the phone is dropped or thrown, all inputs are released and zero packets are sent for 1.5 s, and the app shows "Drop detected · inputs released". |
| **Dual Connection Mode** | Toggle between **USB** (ADB reverse, zero-config) and **Wi-Fi** (4-digit room code pairing). |
| **Live RTT Display** | Shows round-trip ping in milliseconds on the phone. |
| **Safety Zero Packet** | On pause, disconnect or a detected drop the app immediately sends all-zeros to prevent stuck throttle. |
| **Vibration Haptics** | Phone vibrates when the car hits an obstacle in the browser mini-game. |
| **Locked Landscape** | Screen orientation permanently locked to landscape — no accidental rotation. |
| **Persistent Prefs** | Remembers last Wi-Fi address and connection mode between sessions (`SharedPreferences`). |

### Web Dashboard & Browser Game (`http://localhost:8080`)

| Feature | Detail |
|---|---|
| **Live Steering Wheel** | Rotating SVG wheel mirrors phone tilt in real time. |
| **Pedal Meters** | Animated vertical fill bars for throttle (green) and brake (red). |
| **Gear Indicator Lamps** | Light up for 250 ms on each gear shift pulse. |
| **Handbrake Lamp** | Lights up while the handbrake is held; in the mini-game the handbrake stops the car hard. |
| **Latency Panel** | Large RTT readout (green/amber/red) + jitter value + rolling 60-sample sparkline graph. |
| **Connection Status Chips** | Real-time server / phone / vJoy status pills in the header. |
| **Pairing Panel** | Displays LAN IPs, pair code, and ADB command automatically. |
| **Canvas Mini-Game** | Top-down driving game: physics car, road with animated curbs, spawning cone obstacles, speed/distance/hit counter. |

### Server

| Feature | Detail |
|---|---|
| **Single Entry Point** | `python server/main.py` starts the dashboard, the phone connection (USB and Wi-Fi) and vJoy together. |
| **USB Auto-Setup** | While running, the server watches for the phone. Once a phone is attached and authorised it runs `adb reverse tcp:8080 tcp:8080` and opens the app. Unplug and replug is handled automatically. |
| **WebSocket Hub** | `aiohttp` async WebSocket server — phone and dashboard share one event loop. |
| **Active Ping/Pong** | Server pings phone every second; computes RTT + jitter; broadcasts to dashboard sparkline. |
| **Packet Sanitizer** | Validates and clamps all incoming values before they touch vJoy. |
| **vJoy Fallback** | Auto-detects if vJoy is absent and runs in dashboard-only mode — no crash. |
| **Windows asyncio Fix** | Uses `WindowsSelectorEventLoopPolicy` (required by aiohttp) for clean Ctrl+C on Python 3.8+. |
| **Vibrate Relay** | Dashboard sends vibrate command → server forwards to phone over the phone WebSocket. |

---

## 3. Tech Stack

| Layer | Technology |
|---|---|
| **Android App** | Kotlin, Jetpack Compose, OkHttp WebSockets, Android Sensor API (`TYPE_ROTATION_VECTOR` for steering, `TYPE_ACCELEROMETER` for drop detection) |
| **Server** | Python 3.10+, `aiohttp` (async WebSocket + HTTP in one event loop) |
| **Browser Dashboard & Game** | Vanilla HTML5, CSS3, Canvas 2D API, native WebSockets — zero external dependencies |
| **PC Game Integration** | `pyvjoy` → vJoy virtual joystick driver (Windows only, optional) |
| **USB Tunnel** | ADB (`adb reverse`) for USB mode; direct Wi-Fi socket for wireless mode |

---

## 4. System Architecture

```
        +---------------------------------------------+
        |          Android Phone (SimWheel App)        |
        |  Rotation Vector Sensor  ->  Steering        |
        |  Touch Vertical Sliders  ->  Throttle/Brake  |
        |  Pulse Paddle Buttons    ->  Gear Up/Down    |
        |  Hold Button             ->  Handbrake       |
        |  Accelerometer           ->  Drop safety     |
        |  Vibrator Motor          <-  Haptic Events   |
        +---------------------------------------------+
                             |
           WebSocket (JSON, ~60 Hz)
           Mode A: USB  ->  adb reverse tcp:8080 tcp:8080
           Mode B: Wi-Fi -> ws://<laptop-ip>:8080/ws/phone?code=XXXX
                             |
                             v
        +---------------------------------------------+
        |      Python Server  (server/main.py)         |
        |  aiohttp async WebSocket hub                 |
        |  - Validates & sanitizes packets             |
        |  - Computes RTT latency + jitter             |
        |  - Broadcasts telemetry to dashboard         |
        |  - Relays vibrate commands to phone          |
        +---------------------------------------------+
                            |
            +---------------+---------------+
            v                               v
+------------------------+   +--------------------------------+
|  vJoy Virtual Joystick |   |  Browser Dashboard & Game      |
|  X  = Steering         |   |  http://localhost:8080          |
|  Y  = Throttle         |   |  - Live wheel + pedal gauges   |
|  Z  = Brake            |   |  - Top-down canvas race game   |
|  Btn 1 = Gear Up       |   |  - Real-time latency sparkline |
|  Btn 2 = Gear Down     |   |  - Pairing code + LAN IPs      |
|  Btn 3 = Handbrake     |   |  - Connection status chips     |
|  (Forza, AC, ACC, R3E) |   +--------------------------------+
+------------------------+
```

---

## 5. Pairing & Connection Modes

The app features a segmented USB / Wi-Fi toggle. Both modes use the same WebSocket protocol (`ws://.../ws/phone`).

### Mode A — USB (Recommended, Lowest Latency)

1. Plug the phone into your laptop with a **data USB cable** (USB debugging on, see Step 4).
2. Start the server. It detects the phone, runs `adb reverse tcp:8080 tcp:8080` for you, and opens the app on the phone. You type no adb commands. If you unplug and replug, it sets the tunnel up again.
3. In the SimWheel app tap **☰** and choose **USB**.
4. The phone connects to `127.0.0.1:8080`. The server auto-identifies loopback — **no code needed**.

> **Manual fallback:** start the server with `--no-adb` and run `adb reverse tcp:8080 tcp:8080` yourself. USB mode expects the default port 8080.

> **Why it's faster:** data never leaves the USB cable. No Wi-Fi stack, no router, no RF. Typical RTT ≈ 2–5 ms.

### Mode B — Wi-Fi (Wireless, No Cable)

1. Make sure your phone and laptop are on the **same Wi-Fi network**.
2. Start the server — it prints the laptop's LAN IP(s) and a random 4-digit pair code.
3. In the SimWheel app tap **☰**, choose **Wi-Fi**, and enter the laptop IP (e.g. `192.168.1.15:8080`) and the 4-digit code.
4. Tap **Join**.

> The app remembers the laptop IP via `SharedPreferences`. Next session you only need the 4-digit code (pass `--code 1234` to the server for a fixed code).

---

## 6. Latency Approach & Performance

| Technique | Effect |
|---|---|
| **WebSocket protocol** | Eliminates HTTP request/response overhead; persistent bidirectional stream. |
| **60 Hz send rate** | One JSON frame every ~16.6 ms from phone to server. |
| **TCP_NODELAY** | OkHttp (Android) and aiohttp (Python) both disable Nagle's algorithm — no packet buffering. |
| **Active RTT ping/pong** | Server sends `{"type":"ping","ts":<ms>}` every second; phone echoes; server calculates RTT + jitter. |
| **Safety zero on disconnect** | Phone and server send all-zeros on drop — prevents stuck throttle in games. |
| **vJoy state caching** | Button states are cached; only changed states written to driver — reduced I/O overhead. |

**Typical RTT:** < 5 ms (USB) · 10–30 ms (Wi-Fi, same router)

---

## 7. Full Setup Guide

### Prerequisites

| Requirement | Notes |
|---|---|
| **Windows PC** | vJoy is Windows-only. Server runs on any OS in dashboard-only mode. |
| **Python 3.10+** | 3.11 or 3.12 recommended (`pyvjoy` can fail on very new releases). |
| **Android phone** | Android 8.0+ (API 26+), with a data USB cable. |
| **vJoy** *(optional)* | Only needed for PC racing games. Dashboard + browser game work without it. |
| **ADB** | Only needed for USB mode, and the server runs it for you. Wi-Fi mode needs no ADB. |

---

### Step 1 — Install Python Dependencies

Open a terminal **in the project root**:

```powershell
pip install -r server/requirements.txt
```

This installs `aiohttp` and `pyvjoy`. If `pyvjoy` fails on your Python version, the server automatically falls back to dashboard-only mode.

> **Tip:** Use `python -m pip install -r server/requirements.txt` so pip matches the Python you'll run.

---

### Step 2 — Install vJoy (for PC racing games)

> Skip if you only want the browser game / dashboard.

1. Download and install **vJoy** (approve driver prompts; a restart may be required).
2. Open **Configure vJoy** from the Start menu → select **Device 1**:

| Setting | Value |
|---|---|
| Axes | Enable **X**, **Y**, **Z** |
| Number of Buttons | **3 or more** |
| Force Feedback | Not needed |

3. Click **Apply**.

**Axis / Button mapping:**

| Phone Input | vJoy Output |
|---|---|
| Steering tilt | X axis |
| Throttle slider | Y axis |
| Brake slider | Z axis |
| Gear Up | Button 1 |
| Gear Down | Button 2 |
| Handbrake button (hold) | Button 3 |

**Test vJoy alone:**
```powershell
python server/common/vjoy_output.py
```
Watch vJoy Monitor — X axis jumps left then right, Y axis moves to 50%, Button 1 flashes.

---

### Step 3 — Install ADB

> Skip if you only plan to use Wi-Fi mode.

1. Download **Android SDK Platform-Tools** from Google (or use Android Studio's copy: `AppData\Local\Android\Sdk\platform-tools`).
2. Add `adb.exe` to your system PATH **or** set it in `server/common/config.py`:
   ```python
   ADB_PATH = r"C:\platform-tools\adb.exe"
   ```
3. Verify: `adb version`

---

### Step 4 — Prepare Your Phone

1. **Settings → About phone** → tap **Build number** 7 times → Developer Options unlocked.
2. **Settings → Developer Options → USB Debugging → ON**.
3. Plug the phone into the PC and accept the **"Allow USB debugging?"** prompt.
4. Verify:
   ```powershell
   adb devices
   # Phone should appear with status: device
   ```

---

### Step 5 — Install the SimWheel App

**Option A — From Android Studio:**
Open `SimWheel-App/`, connect your phone, click **▶ Run**.

**Option B — Install APK:**
```powershell
adb install path\to\app-debug.apk
```

> See [Section 10](#10-building--exporting-the-apk) for how to build the APK.

---

### Step 6 — Start the Server

```powershell
# Normal start: dashboard + USB (automatic) + Wi-Fi + vJoy
python server/main.py

# Extra flags:
python server/main.py --no-vjoy          # dashboard only, no vJoy
python server/main.py --code 1234        # fixed Wi-Fi pair code
python server/main.py --no-adb           # do not run adb (Wi-Fi only / manual USB)
python server/main.py --no-auto-launch   # set up USB but do not open the app
```

Open **`http://localhost:8080`** in your browser.

---

### Step 7 — Connect the Phone

**USB:** plug in the phone (the server sets up the tunnel and opens the app) → tap **☰** → **USB**.

**Wi-Fi:** open the SimWheel app → tap **☰** → **Wi-Fi** → enter laptop IP + 4-digit code → tap **Join**.

---

### Step 8 — Bind Controls in Your Game

1. Start the game with the server running and phone connected.
2. In game controller settings, select **vJoy Device 1**.
3. Bind: steering = tilt · throttle = THROTTLE slider · brake = BRAKE slider · gears = paddle buttons.
4. Run wheel calibration if the game offers it.

---

## 8. How to Play & Calibrate

1. Hold phone in **landscape mode** like a steering wheel.
2. Tap **Recenter Wheel** at your preferred neutral (straight-ahead) angle.
3. **Tilt left/right** to steer. Locks at ±1.0 past 90° — never folds back.
4. **Right thumb** → THROTTLE (green) to accelerate.
5. **Left thumb** → BRAKE (red) to slow down.
6. Gear paddle buttons on the inner edges of each side. Hold **HANDBRAKE** (under Gear Down) to engage the handbrake.
7. Releasing any slider springs to zero. If the phone is actually dropped, the accelerometer detects the fall and all inputs are released automatically.
8. Hit a cone in the browser game → phone vibrates (220 ms haptic).

---

## 9. Project File Reference

```
Sim-rig-Controller/
├── server/
│   ├── main.py                  <- Entry point (python server/main.py)
│   ├── requirements.txt         <- pyvjoy, aiohttp
│   ├── common/
│   │   ├── adb_utils.py         <- ADB helpers: device state, reverse tunnel, app launch
│   │   ├── config.py            <- Port, vJoy ranges, ADB path, button numbers
│   │   ├── mapping.py           <- Normalises floats to vJoy 0-32768 range
│   │   └── vjoy_output.py       <- VJoyOutput class; run alone to test vJoy
│   ├── websocket/
│   │   ├── ws_server.py         <- aiohttp WebSocket hub, HTTP file server, USB auto-setup
│   │   └── test_client.py       <- Simulated phone for testing without the app
├── game/
│   └── dashboard.html           <- Single-file dashboard + canvas mini-game
├── SimWheel-App/                <- Android Studio project (Kotlin / Jetpack Compose)
│   └── app/src/main/java/com/example/simwheel/
│       ├── MainActivity.kt      <- Root UI, orientation lock, vibration
│       ├── NetworkClient.kt     <- OkHttp WebSocket, 60 Hz loop, ping/pong/vibrate
│       ├── SteeringSensor.kt    <- Rotation vector -> normalised steering float
│       ├── DropDetector.kt      <- Accelerometer free-fall detection (drop safety)
│       ├── SimWheelState.kt     <- StateFlows for throttle, brake, gear
│       └── Controls.kt          <- PedalSlider, GearButton and HandbrakeButton Composables
└── vjoy_output.py               <- Root-level backward-compat proxy (re-exports server/common)
```

**Key config values (`server/common/config.py`):**

| Item | Default |
|---|---|
| WebSocket port | `8080` |
| vJoy device ID | `1` |
| Axis range | `0x0000` – `0x8000` |
| Phone package | `com.example.simwheel` |

---

## 10. Building & Exporting the APK

### Option A — Debug APK via Android Studio (Easiest)

1. Open `SimWheel-App/` in **Android Studio**.
2. Wait for Gradle sync to finish.
3. **Build → Build App Bundle(s) / APK(s) → Build APK(s)**.
4. Click **Locate** in the notification. APK is at:
   ```
   SimWheel-App\app\build\outputs\apk\debug\app-debug.apk
   ```
5. Install:
   ```powershell
   adb install SimWheel-App\app\build\outputs\apk\debug\app-debug.apk
   ```

### Option B — Debug APK via Command Line

Requires `ANDROID_HOME` to be set (Android Studio sets this automatically):

```powershell
cd SimWheel-App
.\gradlew assembleDebug
```

Output: `SimWheel-App\app\build\outputs\apk\debug\app-debug.apk`

### Option C — Release APK (Signed, for Sharing)

1. In Android Studio: **Build → Generate Signed Bundle / APK → APK → Next**.
2. Create or select a keystore (`.jks`) file, fill in alias and passwords.
3. Select **release** build variant → **Finish**.
4. Output: `SimWheel-App\app\build\outputs\apk\release\app-release.apk`

### Installing APK via File Transfer (no cable)

1. Copy APK to phone storage via USB or Google Drive.
2. **Settings → Install unknown apps** → allow your file manager.
3. Tap the APK file on the phone.

> The app requires **Android 8.0+ (minSdk 26)**. It will not install on older devices.

---

## 11. Troubleshooting

| Symptom | Likely Cause & Fix |
|---|---|
| Server prints `adb not found` | USB auto-setup is off (Wi-Fi still works). Put `platform-tools` on PATH, set `ADB_PATH` in `server/common/config.py`, or set `ANDROID_HOME`, then restart the server. |
| Server prints `No phone attached over USB` | Charge-only cable, USB debugging off, or phone locked. Run `adb devices` to diagnose. |
| `adb devices` shows `unauthorized` | Accept debugging prompt on phone. If it never appears: Developer Options → *Revoke USB debugging authorizations* → replug. |
| `adb reverse failed` | Old adb server stuck, or more than one device attached. Run `adb kill-server`, then `adb start-server`; the server retries every 3 s. |
| `ModuleNotFoundError: pyvjoy` | pip installed into wrong Python. Use `python -m pip install -r server/requirements.txt`. |
| vJoy errors / DLL not found | vJoy not installed, Device 1 not enabled in *Configure vJoy*, or another app holds the device. Restart PC after install. |
| Phone shows "not connected" in USB mode | Check the server log says `USB tunnel ready`. If not, see the adb rows above. The app auto-retries every second. |
| vJoy Monitor doesn't move | Check Device 1 has X/Y/Z enabled in *Configure vJoy*. |
| Game doesn't see controller | Start `main.py` before launching game. Select vJoy in game's controller settings. |
| Steering inverted | Use game's axis invert, or set `direction = -1f` in `SteeringSensor.kt`. |
| Steering folds back past 90 degrees | Fixed bug — update to latest `SteeringSensor.kt`. |
| Garbled traceback / Unhandled exception on Ctrl+C | Fixed — server now uses `WindowsSelectorEventLoopPolicy`. Update `ws_server.py`. |
| Phone says "Drop detected" while driving | A very hard jolt briefly read as free fall. Raise the 80 ms hold time (`FREE_FALL_MIN_NS`) or lower the 2.5 m/s² threshold in `DropDetector.kt`. |
| `Address already in use` | Previous server still running. Close it and retry. |
| App won't install | Phone below Android 8.0 (API 26), or APK for wrong CPU ABI. |
| Gradle sync fails | JDK 11+ not installed or `JAVA_HOME` not set. |
