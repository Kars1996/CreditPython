<h1 align="center">⚡ Credit - Copyright Manager 📝 <i>(v2.2.7)</i></h1>
<p align="center">Consider giving this a ⭐ to show your support! <3</p>

---

Welcome to **Credit**, an elegant CLI tool that automatically manages copyright notices across your codebase! This tool makes it effortless to add, update, and maintain consistent copyright notices in your source files.

## ✨ Features

- **🌈 Multi-Language Support** - Works with JavaScript, TypeScript, Python, Go, C/C++, Java, C#, Ruby, and PHP
- **🔄 Automatic Updates** - Automatically updates copyright years in existing notices
- **🚀 Batch Processing** - Process entire directories at once with a single command
- **🧠 Smart Placement** - Intelligently places notices based on file type and structure
- **🎨 Rich Console Output** - Beautiful, colorful console interface powered by Rich
- **⚙️ Configurable** - Customize with your name, GitHub handle, and preferred directory
- **👀 Preview Mode** - See what changes will be made before applying them
- **🔍 Selective Processing** - Filter by language or file type
- **🛠️ Powerful CLI** - Comprehensive command-line interface with helpful options

## 🚀 Installation

### Method 1: Direct Installation
```bash
# Install the script system-wide
python credit.py --install

# Or clone the repository and run
git clone https://github.com/kars1996/credit.git
cd credit
python credit.py --install
```

### Method 2: Manual Installation
Simply download the `credit.py` script and run it with Python:

```bash
# Install dependencies
pip install rich colorama

# Run the script
python credit.py
```

## 🌟 Quick Start

Add copyright notices to all supported files in a directory:

```bash
# Use the default directory or specify one
credit
# or
credit ./src

# Process only TypeScript files
credit -l typescript

# Force update all copyright notices
credit --force
```

## 📋 Usage Examples

```bash
# Preview changes without applying them
credit --preview ./lib

# Process a specific file
credit --file ./src/main.js

# Configure your credentials
credit --setup

# View current configuration
credit --config

# Get detailed help
credit --detailed-help
```

## ⚙️ Configuration

Credit stores your configuration in `~/.credit.conf` (Unix/Mac) or in your user directory on Windows.

You can set your default preferences by running:

```bash
credit --setup
```

This will prompt you for:
- Your name
- Your GitHub handle
- Default directory to process

## 🔍 Supported Languages

Credit currently supports the following languages:

- JavaScript (.js, .jsx)
- TypeScript (.ts, .tsx)
- Python (.py)
- Go (.go)
- C (.c, .h)
- C++ (.cpp, .hpp, .cc, .hh)
- Java (.java)
- C# (.cs)
- Ruby (.rb)
- PHP (.php)

## 🧩 Ignoring Files

To exclude specific files from processing, add this comment at the top of the file:

```javascript
// credit-ignore
```

Or for Python:

```python
# credit-ignore
```

## 🔧 Command Options

| Option | Description |
|--------|-------------|
| `-d, --directory DIR` | Specify directory to process |
| `-f, --force` | Force update copyright notices |
| `-y, --yes` | Skip confirmation prompt |
| `-l, --language LANG` | Process only specific language files |
| `--no-recursive` | Don't search subdirectories |
| `--info` | Show supported languages and extensions |
| `--preview` | Preview changes without applying them |
| `--file FILE` | Process a single file |
| `--setup` | Configure your settings |
| `--config` | View current configuration |
| `--username NAME` | Override username for this run |
| `--github HANDLE` | Override GitHub handle for this run |
| `--version` | Show version information |
| `--detailed-help` | Show detailed help message |

## 🖥️ Sample Output

When processing files, you'll see beautiful progress indicators and a summary table showing:

- Number of files processed
- Copyright notices added
- Copyright notices updated
- Files skipped (up-to-date)
- Files ignored
- Files with errors

## 🤝 Contributing

Contributions are welcome! Feel free to open issues or submit pull requests.

## 📄 License

Credit is available under the MIT license. See the LICENSE file for more information.

---

Created with ❤️ by [Kars](https://github.com/kars1996)

<p align="center">Keep your code properly credited! ✨</p>
