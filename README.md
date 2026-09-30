# Galaxy A17 Debloater & System Optimizer (SM-A175F)

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Knox Warranty](https://img.shields.io/badge/Knox%20Warranty-0x0%20(Intact)-brightgreen.svg)]()
[![Play Integrity](https://img.shields.io/badge/Play%20Integrity-Passed-brightgreen.svg)]()
[![Swiss Banking](https://img.shields.io/badge/Swiss%20Banking-Tested%20%26%20Working-blue.svg)]()
[![Android](https://img.shields.io/badge/Android-15%20%7C%2016-orange.svg)]()

A lightweight, non-destructive debloat toolkit and system optimization suite tailored specifically for the **Samsung Galaxy A17 (SM-A175F)** running One UI on Android 15/16.

---

## Key Highlights

- **Knox 0x0 Preserved**: No bootloader unlocking, no custom recovery, and zero root binaries. Knox warranty remains completely untripped (`0x0`).
- **Banking App Safety**: Fully passes Google Play Integrity (`MEETS_DEVICE_INTEGRITY`). Swiss banking and security apps (ZKB Access, Raiffeisen, Swissquote, Valiant) run without warnings or blocks.
- **OTA Update Ready (2025–2031)**: Samsung official OTA firmware upgrades install smoothly because system partition integrity is never altered.
- **100% Reversible**: Every package uninstalled for User 0 can be restored in seconds without a factory reset.

---

## Features & Optimizations

### 1. Battery Longevity (80% Protection Cap)
Enforces Samsung's Maximum Battery Protection mode (`protect_battery 3`), stopping charge cycles strictly at 80% to prevent lithium-ion degradation across 6 years of daily use.

### 2. RAM Plus (Virtual Memory) Disabled
Disables Samsung's swap paging (`ram_expand_size 0`). Eliminates constant micro-stutter, reduces background CPU cycles, and prevents premature NAND flash degradation.

### 3. Responsive UI Animations (0.5x)
Sets window, transition, and animator scales to 0.5x for snappy, zero-lag navigation across One UI.

### 4. System-Wide Encrypted DNS
Enforces AdGuard Private DNS over TLS (`dns.adguard-dns.com`) at the system level. Blocks malicious domains, ad trackers, and telemetry in all browsers and apps without battery drain.

### 5. Privacy & Telemetry Hardening
- Enables clipboard access read notifications (`show_clip_access_notification 1`).
- Disables automatic background crash reporting (`send_action_app_error 0`).
- Reduces logcat ring buffer size to 64 KiB across all channels (`logcat -G 64K`) to free kernel memory.

---

## Debloated Package Inventory

| Category | Package Name | Technical Purpose / Why Debloated |
| :--- | :--- | :--- |
| **Telemetry** | `com.sec.android.diagmonagent` | Diagnostic monitor agent logging background usage |
| **Telemetry** | `com.samsung.android.knox.analytics.uploader` | Knox telemetry and usage metric uploader |
| **Telemetry** | `com.sec.spp.push` | Samsung Push Service (marketing & promotional push alerts) |
| **Telemetry** | `com.samsung.android.rubin.app` | Rubin customization service (user habits & contextual tracking) |
| **Telemetry** | `com.samsung.android.networkdiagnostic` | Background network diagnostic logger |
| **Telemetry** | `com.sec.imslogger` | IMS / VoLTE telephony session logger |
| **Telemetry** | `com.samsung.android.dqagent` | Device quality evaluation daemon |
| **Telemetry** | `com.hiya.star` | Hiya caller-ID / spam telemetry engine |
| **Antivirus** | `com.samsung.android.sm.devicesecurity` | McAfee Device Security (redundant bloat, battery drain) |
| **Throttling** | `com.samsung.android.game.gos` | Game Optimizing Service (restricted & background-disabled) |
| **Ecosystem** | `com.samsung.android.scloud` | Samsung Cloud background synchronization |
| **Ecosystem** | `com.samsung.android.themestore` | Galaxy Theme Store background sync & push services |
| **Ecosystem** | `com.samsung.android.dynamiclock` | Dynamic Lockscreen wallpaper auto-downloader |
| **Ecosystem** | `com.samsung.android.wallpaper.live` | Live wallpaper rendering service |
| **Ecosystem** | `com.samsung.android.app.dressroom` | Wallpapers & custom lockscreen dressroom backend |
| **Ecosystem** | `com.samsung.android.forest` | Digital Wellbeing backend tracker |
| **Ecosystem** | `com.sec.android.app.personalization` | Personalization service tracker |
| **Ecosystem** | `com.samsung.android.app.parentalcare` | Parental care telemetry |
| **Ecosystem** | `com.samsung.android.app.taskedge` | Edge panel task switcher daemon |
| **Ecosystem** | `com.samsung.android.app.clipboardedge` | Edge panel clipboard history daemon |
| **Ecosystem** | `com.mygalaxy.service` | My Galaxy marketing service |
| **Ecosystem** | `com.samsung.android.aircommandmanager` | Air command daemon (redundant on non-S-Pen devices) |
| **Ecosystem** | `com.sec.android.app.billing` | Samsung Checkout / in-app billing daemon |
| **Ecosystem** | `com.samsung.android.mcfserver` | Samsung Continuity / Media Convergence Framework |
| **Ecosystem** | `com.samsung.android.mcfds` | MCF Discovery Service |
| **Ecosystem** | `com.samsung.android.mcf.autohotspot` | Samsung Auto Hotspot sync daemon |
| **Ecosystem** | `com.samsung.android.smartmirroring` | Smart View / Screen Mirroring service |
| **Ecosystem** | `com.samsung.android.app.sharelive` | Quick Share Live Sharing backend |
| **Ecosystem** | `com.sec.epdgtestapp` | Wi-Fi Calling / ePDG test utility |
| **Ecosystem** | `com.samsung.gpuwatchapp` | GPUWatch game developer debugging overlay |
| **Ecosystem** | `com.sec.android.app.wlantest` | WLAN hardware factory testing tool |
| **Ecosystem** | `com.sec.android.app.hwmoduletest` | Hardware module factory testing tool |
| **Ecosystem** | `com.sec.android.app.sbrowser` | Samsung Internet (redundant secondary browser) |
| **Ecosystem** | `com.sec.android.app.samsungapps` | Galaxy Store client (all updates handled via Play Store) |
| **Ecosystem** | `com.google.android.apps.bard` | Google Gemini / Bard preloaded stub |
| **Ecosystem** | `com.snap.camerakit.plugin.v1` | Snapchat Camera Kit integration plugin |
| **Ecosystem** | `com.google.ar.core` | Google ARCore services |
| **Ecosystem** | `com.samsung.storyservice` | Gallery story auto-generator |
| **Ecosystem** | `com.samsung.android.allshare.service.mediashare` | AllShare DLNA media share daemon |
| **Ecosystem** | `com.samsung.android.audiomirroring` | Audio mirroring service |
| **TTS Packs** | `com.samsung.SMT.lang_*` | 11 unused foreign language voice packages (ES, FR, HI, IT, KO, PT, RU, ZH) |

---

## Getting Started

### Prerequisites
1. **Enable Developer Options**: Go to `Settings` $\to$ `About phone` $\to$ `Software information` $\to$ tap **Build number** 7 times.
2. **Enable USB Debugging**: Go to `Settings` $\to$ `Developer options` $\to$ toggle **USB debugging** on.
3. Connect your Galaxy A17 to your computer via USB and allow the USB debugging prompt on the screen.

### Quick Run

#### Option A: Windows (Batch)
Double-click `debloat.bat`, then double-click `optimize.bat`.

#### Option B: Windows (PowerShell)
```powershell
.\debloat.ps1
.\optimize.ps1
```

#### Option C: Linux / macOS / WSL (Bash)
```bash
chmod +x debloat.sh
./debloat.sh
```

---

## Restoring Packages

If you ever wish to restore all uninstalled packages back to their factory state:
```powershell
.\restore.ps1
```
Or for individual packages:
```bash
adb shell cmd package install-existing <package_name>
```

---

## License
MIT License. Free to use, adapt, and distribute.
