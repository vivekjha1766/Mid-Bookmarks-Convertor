
🚀 Project Name : Medium-Bookmarks-Converter
===============

#### Medium-Bookmarks-Converter : 🔖 Convert Medium saved articles to Markdown with Freedium paywall bypass. Perfect for creating datasets, develop RAG projects archiving reading lists,.

![Maintenance](https://img.shields.io/badge/Maintained%3F-yes-purple.svg)
![Contributions](https://img.shields.io/badge/contributions-welcome-brightgreen.svg)
![Development Time](https://img.shields.io/badge/Development%20Time-%20Approx%201%20hour%2030%20min-blue.svg)

<img width="1911" height="920" alt="medium" src="https://github.com/user-attachments/assets/7e3f81c4-de63-4139-8ceb-656243e729cd" />

> [!NOTE]
> **Before using the tool:**
> 1. Create a `data` directory in the project root
> 2. Inside `data`, create a `bookmarks` folder
> 3. Place all your exported Medium bookmark HTML files in data/bookmarks/
> 4. Or if you don't want to create then , specify -i flag . For more info : check `command line options` section of README


## Table of Contents

* [📌 Overview](#-overview)
* [✨ Features](#-features)
* [📚 Requirements](#-requirements)
* [📥 Installation](#-installation)
* [🚀 Usage](#-usage)
* [📋 Command Line Options](#-command-line-options)
* [📄 License](#-license)
* [🙃 Why I Created This](#-why-i-created-this)
* [📞 Contact](#-contact)

## 📌 Overview

**Medium-Bookmarks-Converter** (Medium Bookmarks to Readable) transforms your Medium bookmark exports into clean Markdown files with automatic Freedium mirror links, making your saved articles accessible without Medium's paywall.

**Key Capabilities:**
* Automatic filename cleaning (removes hashes, IDs, and junk)
* Converts Medium links to Freedium mirrors
* Generates organized category files
* Removes duplicate articles across categories
* Beautiful CLI with progress tracking

## ✨ Features


- **Duplicate Detection** - Identifies and removes repeated articles across categories
- **Medium → Freedium** - Automatically converts all Medium links to `freedium-mirror.cfd`
- **Default Mode** - All categories + Reading List in one file
- **Categories Only** (`-c`) - Excludes Reading List
- **Deduplicated** (`-cr`) - All categories with duplicate removal


## 📚 Requirements

* **Python 3.7+**

## 📥 Installation

### Quick Install

```bash
# Clone the repository
git clone https://github.com/gigachad80/Medium-Bookmarks-Converter
cd Medium-Bookmarks-Converter

# Install dependencies
pip install -r requirements.txt

# Run the script
python medium_exporter.py -i data/bookmarks -d output/

```

## 🚀 Usage

### Basic Usage

```bash
# Default: All categories + Reading List
python medium_exporter.py -i lists/ -d output/
# Output: medium_bookmark_list.md

# Categories only (exclude Reading List)
python medium_exporter.py -i lists/ -d output/ -c
# Output: combined.md

# All categories with duplicate removal
python medium_exporter.py -i lists/ -d output/ -cr
# Output: combined-reading-sorted.md

# Custom output filename
python medium_exporter.py -i lists/ -o my-bookmarks.md -d output/

# Show help
python medium_exporter.py -h
```

### Workflow Example

```bash
# 1. Export your Medium exports ( THML files) a
# 2. Place HTML files in data/bookmarks/
# 3. Run the converter
python medium_exporter.py -i data/bookmarks -d output/ -cr

# 4. Check output/categories/ for individual files
# 5. Check output/combined-reading-sorted.md for combined file
```

## 📋 Command Line Options

| Flag | Description | Default | Example |
|------|-------------|---------|---------|
| `-i`, `--input` | Input directory with HTML files | `data/bookmarks` | `-i lists/` |
| `-o`, `--output` | Custom output filename | Auto-generated | `-o bookmarks.md` |
| `-d`, `--dir` | Output directory | Current directory | `-d output/` |
| `-c`, `--categories-only` | Exclude Reading List | `False` | `-c` |
| `-cr`, `--categories-with-reading-remove-duplicates` | Remove duplicates | `False` | `-cr` |
| `-h`, `--help` | Show help menu | - | `-h` |


## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.


## 🙃 Why I Created This

I created this to store my Medium reading list and build a knowledge base - essentially a second brain for organizing and accessing valuable articles without Medium's paywall restrictions.

## 📞 Contact

📧 Email: **pookielinuxuser@tutamail.com**
💡 Built something cool ? If you've created any RAG projects or knowledge base systems using this tool, feel free to share with me , I'd love to see what you've built!

---

**Made with 🐍 Python** - Clean, organized, and accessible bookmark management.

First release : 17th January 2026

Last updated : !7th January 2026
