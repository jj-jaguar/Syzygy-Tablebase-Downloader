# Syzygy Manager v1.0

![Python](https://img.shields.io/badge/Python-3.x-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux%20%7C%20Android-lightgrey)

A robust, multi-threaded tool designed to download, resume, and verify **Syzygy Endgame Tablebases** (3-4-5-6-7 men).

![Main Menu](Screenshot%201.png)

Unlike simple downloaders, this manager features **Canonical Sorting logic**, ensuring that you can pause a download on one server (e.g., Lichess) and resume it on another (e.g., Sesse) without losing progress or corrupting your queue.

## 🚀 Key Features

* **Smart Resume:** Automatically detects existing files and resumes bytes exactly where they left off.
* **Canonical Sorting:** Enforces a universal A-Z download order, making the queue "Server Agnostic." You can switch mirrors mid-download safely.
* **Universal Sleep Prevention:** Keeps your PC/Mac awake during long downloads.
    * *Windows:* Uses native Kernel32 API.
    * *macOS:* Uses `caffeinate` background process.
    * *Android (Termux):* Uses `termux-wake-lock`.
* **Integrity Check:** Verifies file headers (Magic Bytes) and file sizes to detect corruption.
* **Multi-Mirror Support:** Built-in support for **Lichess** (Fastest/Global) and **Sesse** (Backup).
* **Auto-Update:** Automatically notifies you when a new version is released.

## 📸 Screenshots

| Generation Selection | Mirror Selection |
| :---: | :---: |
| ![Generation](Screenshot%202.png) | ![Mirror](Screenshot%203.png) |

| Download Options | Live Progress |
| :---: | :---: |
| ![Options](Screenshot%204.png) | ![Progress](Screenshot%205.png) |

## 📥 Installation

### Option 1: Run the Executable (Windows Only)
Download the latest `Syzygy Manager.exe` from the [Releases page](../../releases) and run it. No Python installation required.

### Option 2: Run from Source (All Platforms)
1.  Install [Python 3](https://www.python.org/).
2.  Clone this repository:
    ```bash
    git clone [https://github.com/jj-jaguar/Syzygy-Tablebase-Downloader.git](https://github.com/jj-jaguar/Syzygy-Tablebase-Downloader.git)
    cd Syzygy-Tablebase-Downloader
    ```
3.  Run the script:
    ```bash
    python syzygy_manager.py
    ```

## 🛠️ Usage Guide

1.  **Select Operation:** Choose between **Download/Resume** or **Verify Integrity**.
2.  **Select Generation:**
    * 3-4-5 Piece (~1 GB)
    * 6 Piece (~150 GB)
    * 7 Piece (~17 TB)
3.  **Select Mirror:** Choose your preferred download server.
4.  **Set Path:** Paste the folder path where you want the files saved.
5.  **Sleep Prevention:** Choose [Yes] to prevent your computer from sleeping during the process.

## ☕ Support the Project

If this tool helped you save time or bandwidth, consider supporting the development!

| Currency | Network | Address |
| :--- | :--- | :--- |
| **Bitcoin (BTC)** | Bitcoin / BTC | `12hpLsgfXGPoFjVf1oWsbjUMPiVaSavdTi` |
| **Ethereum (ETH)** | ERC20 | `0x11ddf9da829559a2451237fc640d245883ea2793` |
| **USDT (Tether)** | TRC20 / Tron | `TB37wTAiKme7CygZsgebhqo4P8xuwkPgpC` |

*(Please verify the Network before sending)*

## ⚖️ License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgements

* **Lichess.org** for hosting the global mirror.
* **Sesse** for the original tablebase hosting.
* **Syzygy** tablebase format by Ronald de Man.
