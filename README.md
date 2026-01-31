# Calibre Multi-Store Amazon ASIN Fetcher

A powerful metadata source plugin for **Calibre** designed to automatically retrieve **ASIN** identifiers by searching across multiple international Amazon stores (IT, COM, UK, DE, FR, ES). It is especially useful when standard metadata sources fail to find a book's unique Amazon identifier.

## ✨ Features
- **Multi-Store Search:** Automatically checks Kindle versions across different regional stores, including Italy, USA, UK, Germany, France, and Spain.
- **Smart Validation:** Uses a weighted scoring system to verify results by comparing titles and authors, preventing false positives.
- **Anti-Bot Protection:** Implements rotating User-Agents and randomized delays to minimize the risk of IP throttling or bans.
- **Automated Releases:** Built-in GitHub Actions workflow to package the plugin into a ready-to-use ZIP file with every new version tag.

## 🚀 Installation
1. Download the latest `ASINFetchervX.X.X.zip` from the [Releases](../../releases) section.
2. Open **Calibre**.
3. Navigate to **Preferences** -> **Plugins**.
4. Click on **Load plugin from file** and select the downloaded `.zip` file.
5. **Restart** Calibre to activate the plugin.

## 📖 How to Use
1. Select one or more books in your Calibre library.
2. Click on **Edit Metadata** -> **Download metadata and covers**.
3. The plugin will search the configured Amazon stores. If a relevant match is found, the `amazon` identifier (ASIN) will be added to your book's metadata.

## ⚠️ Disclaimer & Legal Notes
This software is provided for **educational and personal use only**. 
- The plugin performs scraping of public Amazon pages.
- The author is not responsible for any violations of Amazon's Terms of Service or for any IP bans resulting from intensive usage.
- Please use this tool responsibly and with moderation.

## 📄 License
Distributed under the **MIT License**. See the [LICENSE](LICENSE) file for more details.
