#!/usr/bin/env python3
import os
import re
import sys
import time
import argparse
from datetime import datetime
from colorama import init
from rich.console import Console
from rich.panel import Panel
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    TaskProgressColumn,
)
from rich.table import Table
from rich.markdown import Markdown
from rich import box
import shutil
import configparser
import platform
import statistics

init()

console = Console()

if platform.system() == "Windows":
    CONFIG_FILE = os.path.join(os.path.expanduser("~"), ".credit.conf")
else:
    CONFIG_FILE = os.path.expanduser("~/.credit.conf")

VERSION = "2.3.0"

CURRENT_YEAR = datetime.now().year
AQUA = "#00FFFF"

DEFAULT_USERNAME = "Kars"
DEFAULT_GITHUB = "github.com/kars1996"
DEFAULT_DIRECTORY = "./src"


def get_config():
    config = configparser.ConfigParser()
    if os.path.exists(CONFIG_FILE):
        config.read(CONFIG_FILE)
        if "DEFAULT" in config:
            return {
                "username": config["DEFAULT"].get("username", DEFAULT_USERNAME),
                "github": config["DEFAULT"].get("github", DEFAULT_GITHUB),
                "directory": config["DEFAULT"].get("directory", DEFAULT_DIRECTORY),
            }
    return {
        "username": DEFAULT_USERNAME,
        "github": DEFAULT_GITHUB,
        "directory": DEFAULT_DIRECTORY,
    }


config = get_config()
USERNAME = config["username"]
GITHUB = config["github"]
DEFAULT_DIRECTORY = config["directory"]

# Debug metrics storage
FILE_PROCESSING_TIMES = {}

SUPPORTED_EXTENSIONS = {
    "javascript": [".js", ".jsx"],
    "typescript": [".ts", ".tsx"],
    "golang": [".go"],
    "python": [".py"],
    "c": [".c", ".h"],
    "cpp": [".cpp", ".hpp", ".cc", ".hh"],
    "java": [".java"],
    "csharp": [".cs"],
    "ruby": [".rb"],
    "php": [".php"],
}

COMMENT_STYLES = {
    "javascript": {
        "block_start": "/*",
        "block_end": "*/",
        "line": "//",
    },
    "typescript": {
        "block_start": "/*",
        "block_end": "*/",
        "line": "//",
    },
    "golang": {
        "block_start": "/*",
        "block_end": "*/",
        "line": "//",
    },
    "python": {
        "block_start": '"""',
        "block_end": '"""',
        "line": "#",
    },
    "c": {
        "block_start": "/*",
        "block_end": "*/",
        "line": "//",
    },
    "cpp": {
        "block_start": "/*",
        "block_end": "*/",
        "line": "//",
    },
    "java": {
        "block_start": "/*",
        "block_end": "*/",
        "line": "//",
    },
    "csharp": {
        "block_start": "/*",
        "block_end": "*/",
        "line": "//",
    },
    "ruby": {
        "block_start": "=begin",
        "block_end": "=end",
        "line": "#",
    },
    "php": {
        "block_start": "/*",
        "block_end": "*/",
        "line": "//",
    },
}

IGNORE_PATTERN = r"(?://|#|/\*)\s*credit-ignore"


def get_copyright_template(language):
    """Get the appropriate copyright template for the language."""
    style = COMMENT_STYLES.get(language, COMMENT_STYLES["javascript"])

    if language == "python":
        return f"""{style["block_start"]}
Copyright © {{year}} {{name}} ({{github}})

Not to be shared, replicated, or used without prior consent.
Contact me for any enquiries
{style["block_end"]}"""
    else:
        return f"""{style["block_start"]}
Copyright © {{year}} {{name}} ({{github}})

Not to be shared, replicated, or used without prior consent.
Contact me for any enquiries
{style["block_end"]}"""


def get_language_from_extension(extension):
    """Determine the language based on file extension."""
    for language, extensions in SUPPORTED_EXTENSIONS.items():
        if extension in extensions:
            return language
    return "javascript"  # Default to JavaScript


def find_files(directory, extensions, recursive=True):
    """Find all files with the specified extensions in the given directory."""
    matched_files = []

    if recursive:
        for root, dirs, files in os.walk(directory):
            for file in files:
                if any(file.endswith(ext) for ext in extensions):
                    matched_files.append(os.path.join(root, file))
    else:
        for file in os.listdir(directory):
            file_path = os.path.join(directory, file)
            if os.path.isfile(file_path) and any(
                file.endswith(ext) for ext in extensions
            ):
                matched_files.append(file_path)

    return matched_files


def should_ignore_file(content):
    """Check if a file should be ignored based on the ignore comment."""
    return bool(re.search(IGNORE_PATTERN, content))


def check_existing_copyright(content, language):
    """Check if a file already has a copyright notice and extract its year."""
    style = COMMENT_STYLES.get(language, COMMENT_STYLES["javascript"])

    block_start_escaped = re.escape(style["block_start"])
    block_end_escaped = re.escape(style["block_end"])
    line_escaped = re.escape(style["line"])

    patterns = [
        f"{block_start_escaped}\\s*Copyright © (\\d{{4}}).*?{USERNAME}.*?{block_end_escaped}",
        f"{block_start_escaped}\\s*Copyright \\(c\\) (\\d{{4}}).*?{USERNAME}.*?{block_end_escaped}",
        f"{line_escaped} Copyright © (\\d{{4}}).*?{USERNAME}",
        f"{line_escaped} Copyright \\(c\\) (\\d{{4}}).*?{USERNAME}",
    ]

    for pattern in patterns:
        match = re.search(pattern, content, re.DOTALL)
        if match:
            return True, match.group(1), match.group(0)

    return False, None, None


def detect_import_blocks(content, language):
    """
    Detect complete import blocks, handling multi-line imports.
    Returns the position after the last import statement.
    """
    if language in ["javascript", "typescript"]:
        import_patterns = [
            # Standard imports: import X from 'Y'
            r'import\s+[\w\s{},*]+\s+from\s+[\'"].*?[\'"];?',
            # Dynamic imports: import('X')
            r'import\s*\([\'"].*?[\'"]\)',
            # Require: const X = require('Y')
            r'(?:const|let|var)\s+[\w\s{}]+\s*=\s*require\s*\([\'"].*?[\'"]\);?',
            # Import type: import type { X } from 'Y'
            r'import\s+type\s+[\w\s{},*]+\s+from\s+[\'"].*?[\'"];?',
        ]
        
        combined_pattern = '|'.join(f'({p})' for p in import_patterns)
        
        all_imports = list(re.finditer(combined_pattern, content, re.DOTALL | re.MULTILINE))
        
        if not all_imports:
            return 0
        
        imports_to_check = []
        
        for import_match in all_imports:
            start_pos = import_match.start()
            end_pos = import_match.end()
            
            # Check if this import is inside a comment block or string
            in_comment = False
            for pattern in [r'/\*.*?\*/', r'//.*?(?:\n|$)', r'".*?"', r"'.*?'"]:
                comment_matches = list(re.finditer(pattern, content, re.DOTALL))
                for comment_match in comment_matches:
                    comment_start = comment_match.start()
                    comment_end = comment_match.end()
                    if comment_start <= start_pos and end_pos <= comment_end:
                        in_comment = True
                        break
                if in_comment:
                    break
            
            if not in_comment:
                imports_to_check.append((start_pos, end_pos))
        
        # If we have valid imports, find the last one
        if imports_to_check:
            # Sort by end position to find the last one
            imports_to_check.sort(key=lambda x: x[1])
            _, last_import_end = imports_to_check[-1]
            
            match = re.search(r'\S', content[last_import_end:])
            if match:
                return last_import_end + match.start()
            else:
                return last_import_end
        
        return 0
    
    elif language == "python":
        import_patterns = [
            r'^import\s+.*?$',  # import x
            r'^from\s+.*?\s+import\s+.*?$',  # from x import y
        ]
        
        combined_pattern = '|'.join(import_patterns)
        all_imports = list(re.finditer(combined_pattern, content, re.MULTILINE))
        
        if not all_imports:
            return 0
            
        all_imports.sort(key=lambda x: x.end())
        last_import_end = all_imports[-1].end()
        
        newline_count = 0
        index = last_import_end
        
        while index < len(content):
            if content[index].isspace():
                if content[index] == '\n':
                    newline_count += 1
                    if newline_count > 1:  # Two consecutive newlines end the import block
                        break
                index += 1
            else:
                break
        
        return index
    
    # Default fallback for other languages
    else:
        imports_pattern = r'^import.*?$|^.*?from.*?import.*?$'
        matches = list(re.finditer(imports_pattern, content, re.MULTILINE))
        
        if matches:
            last_import_end = matches[-1].end()
            return last_import_end
        
        return 0


def add_or_update_copyright(
    file_path, force_update=False, custom_username=None, custom_github=None
):
    """Add or update copyright notice in a file."""
    start_time = time.time()
    
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            content = file.read()
    except UnicodeDecodeError:
        try:
            with open(file_path, "r", encoding="latin-1") as file:
                content = file.read()
        except Exception as e:
            return "error", f"Encoding error: {str(e)}"
    except Exception as e:
        return "error", str(e)

    if should_ignore_file(content):
        FILE_PROCESSING_TIMES[file_path] = time.time() - start_time
        return "ignored", None

    _, extension = os.path.splitext(file_path)
    language = get_language_from_extension(extension)

    username = custom_username or USERNAME
    github = custom_github or GITHUB

    has_copyright, year, old_notice = check_existing_copyright(content, language)

    if has_copyright and year == str(CURRENT_YEAR) and not force_update:
        FILE_PROCESSING_TIMES[file_path] = time.time() - start_time
        return "skipped", None

    copyright_notice = get_copyright_template(language).format(
        year=CURRENT_YEAR, name=username, github=github
    )

    if has_copyright:
        modified_content = content.replace(old_notice, copyright_notice)

        with open(file_path, "w", encoding="utf-8") as file:
            file.write(modified_content)

        FILE_PROCESSING_TIMES[file_path] = time.time() - start_time
        return "updated", year

    if language == "python" and content.startswith("#!"):
        shebang_end = content.find("\n") + 1
        modified_content = (
            content[:shebang_end]
            + "\n"
            + copyright_notice
            + "\n\n"
            + content[shebang_end:]
        )
    else:
        imports_end = detect_import_blocks(content, language)

        if imports_end > 0:
            modified_content = (
                content[:imports_end]
                + "\n\n"
                + copyright_notice
                + "\n\n"
                + content[imports_end:].lstrip()
            )
        else:
            modified_content = copyright_notice + "\n\n" + content

    with open(file_path, "w", encoding="utf-8") as file:
        file.write(modified_content)

    FILE_PROCESSING_TIMES[file_path] = time.time() - start_time
    return "added", None


def print_header():
    """Print a styled header for the CLI tool."""
    console.print("")
    console.print(
        Panel(
            "[bold white]COPYRIGHT NOTICE MANAGER[/bold white]",
            subtitle=f"[italic]v{VERSION}[/italic]",
            border_style=AQUA,
            expand=False,
            title="[bold white]𝕂ars[/bold white]",
        )
    )


def get_all_extensions():
    """Get all supported file extensions."""
    all_extensions = []
    for extensions in SUPPORTED_EXTENSIONS.values():
        all_extensions.extend(extensions)
    return all_extensions


def print_stats(stats):
    """Print statistics of the operation."""
    table = Table(title="Operation Summary", border_style=AQUA)

    table.add_column("Category", style="dim")
    table.add_column("Count", justify="right", style="bold")

    table.add_row("Files processed", str(stats["total"]))
    table.add_row("Copyright notices added", str(stats["added"]), style="green")
    table.add_row("Copyright notices updated", str(stats["updated"]), style="blue")
    table.add_row("Files skipped (up-to-date)", str(stats["skipped"]), style=AQUA)
    table.add_row("Files ignored", str(stats["ignored"]), style="yellow")
    table.add_row("Files with errors", str(stats["errors"]), style="red")

    console.print("\n")
    console.print(table)


def print_debug_stats():
    """Print debug statistics about file processing times."""
    if not FILE_PROCESSING_TIMES:
        console.print("[yellow]No timing data available.[/yellow]")
        return
    
    times = list(FILE_PROCESSING_TIMES.values())
    total_time = sum(times)
    avg_time = total_time / len(times)
    
    longest_file = max(FILE_PROCESSING_TIMES.items(), key=lambda x: x[1])
    
    table = Table(title="Processing Time Statistics", border_style=AQUA)
    
    table.add_column("Metric", style="dim")
    table.add_column("Value", style="bold")
    
    table.add_row("Total processing time", f"{total_time:.4f} seconds")
    table.add_row("Average time per file", f"{avg_time:.4f} seconds")
    table.add_row("Median time", f"{statistics.median(times):.4f} seconds")
    if len(times) > 1:
        table.add_row("Standard deviation", f"{statistics.stdev(times):.4f} seconds")
    table.add_row("Minimum time", f"{min(times):.4f} seconds")
    table.add_row("Maximum time", f"{max(times):.4f} seconds")
    table.add_row("Longest file", os.path.relpath(longest_file[0]))
    table.add_row("Longest file time", f"{longest_file[1]:.4f} seconds")
    
    console.print("\n")
    console.print(table)
    
    if len(FILE_PROCESSING_TIMES) > 5:
        top_files = sorted(FILE_PROCESSING_TIMES.items(), key=lambda x: x[1], reverse=True)[:5]
        
        detail_table = Table(title="Top 5 Longest Processing Files", border_style=AQUA)
        detail_table.add_column("File", style="dim")
        detail_table.add_column("Time (seconds)", style="bold")
        
        for file_path, proc_time in top_files:
            detail_table.add_row(os.path.relpath(file_path), f"{proc_time:.4f}")
        
        console.print("\n")
        console.print(detail_table)


def create_config(username, github, directory):
    """Create a configuration file with the provided settings."""
    config = configparser.ConfigParser()
    config["DEFAULT"] = {"username": username, "github": github, "directory": directory}

    with open(CONFIG_FILE, "w") as configfile:
        config.write(configfile)

    console.print(f"[green]Configuration saved to {CONFIG_FILE}[/green]")


def print_config():
    """Print the current configuration."""
    table = Table(title="Current Configuration", border_style=AQUA)

    table.add_column("Setting", style="dim")
    table.add_column("Value", style="bold")

    table.add_row("Username", USERNAME)
    table.add_row("GitHub", GITHUB)
    table.add_row("Default Directory", DEFAULT_DIRECTORY)
    table.add_row("Config File", CONFIG_FILE)

    console.print("\n")
    console.print(table)


def print_help():
    """Print detailed help information about the tool with enhanced styling."""
    console.print("")
    console.print(
        Panel(
            "[bold white]COPYRIGHT NOTICE MANAGER - DETAILED HELP[/bold white]",
            border_style=AQUA,
            expand=False,
        )
    )

    console.print(
        Panel(
            "[bold]credit[/bold] [directory] [options]",
            title="[bold]BASIC SYNTAX[/bold]",
            border_style=AQUA,
            padding=(1, 2),
        )
    )

    console.print(
        Markdown(
            "A tool to automatically add or update copyright notices in source code files.\n"
        )
    )

    examples_table = Table(
        show_header=False, box=box.SIMPLE, padding=(0, 1), expand=True
    )
    examples_table.add_column(style="bold cyan", justify="right")
    examples_table.add_column(style="white")

    examples_table.add_row("credit ./src", "Process all files in the src directory")
    examples_table.add_row("credit", "Process files in the default directory")
    examples_table.add_row("credit -l typescript", "Process only TypeScript files")
    examples_table.add_row("credit --force", "Force update all copyright notices")
    examples_table.add_row(
        "credit --preview ./lib", "Preview changes to files in the lib directory"
    )
    examples_table.add_row(
        "credit --setup", "Configure your username and GitHub handle"
    )
    examples_table.add_row(
        "credit --debug", "Show timing statistics after processing"
    )

    console.print(
        Panel(
            examples_table,
            title="[bold]EXAMPLES[/bold]",
            border_style=AQUA,
            padding=(1, 2),
        )
    )

    options_table = Table(show_header=True, box=box.SIMPLE, expand=True)
    options_table.add_column("Option", style="bold cyan")
    options_table.add_column("Description")

    options_table.add_row("-d, --directory DIR", "Specify the directory to process")
    options_table.add_row("-f, --force", "Force update of copyright notices")
    options_table.add_row("-y, --yes", "Skip confirmation prompt")
    options_table.add_row(
        "-l, --language LANG", "Process only files of a specific language"
    )
    options_table.add_row("--no-recursive", "Don't search subdirectories")
    options_table.add_row("--info", "Show supported languages and extensions")
    options_table.add_row("--preview", "Preview changes without applying them")
    options_table.add_row("--file FILE", "Process a single file")
    options_table.add_row("--setup", "Set up your configuration")
    options_table.add_row("--config", "View current configuration")
    options_table.add_row("--username NAME", "Override username for this run")
    options_table.add_row("--github HANDLE", "Override GitHub handle for this run")
    options_table.add_row("--version", "Show version information")
    options_table.add_row("--detailed-help", "Show this detailed help message")
    options_table.add_row("--install", "Install as system command")
    options_table.add_row("--debug", "Show processing time statistics")

    console.print(
        Panel(
            options_table,
            title="[bold]OPTIONS[/bold]",
            border_style=AQUA,
            padding=(1, 2),
        )
    )

    console.print(
        Panel(
            "Add the comment [bold cyan]// credit-ignore[/bold cyan] at the top of any file to exclude it from processing.",
            title="[bold]FILE EXCLUSION[/bold]",
            border_style=AQUA,
            padding=(1, 2),
        )
    )

    config_text = f"""
Your current configuration is stored at [italic]{CONFIG_FILE}[/italic]

[bold]Current settings:[/bold]
• Username: [cyan]{USERNAME}[/cyan]
• GitHub: [cyan]{GITHUB}[/cyan]
• Default Directory: [cyan]{DEFAULT_DIRECTORY}[/cyan]
    """

    console.print(
        Panel(
            config_text,
            title="[bold]CONFIGURATION[/bold]",
            border_style=AQUA,
            padding=(1, 2),
        )
    )

    console.print(
        Panel(
            f"[italic]Credit v{VERSION} - Created by Kars (github.com/kars1996)[/italic]",
            border_style=AQUA,
            expand=False,
        )
    )


def print_version():
    """Print the version information."""
    table = Table(show_header=False, box=box.SIMPLE)

    table.add_column(style="dim")
    table.add_column(style="bold")

    table.add_row("Credit Version", VERSION)
    table.add_row("Python Version", platform.python_version())
    table.add_row("System", platform.system())

    console.print("\n")
    console.print(table)


def preview_changes(files, force_update=False):
    """Preview changes without applying them."""
    table = Table(title="Preview of Changes", border_style=AQUA)

    table.add_column("File", style="dim")
    table.add_column("Action", style="bold")

    for file_path in files:
        relative_path = os.path.relpath(file_path)

        try:
            with open(file_path, "r", encoding="utf-8") as file:
                content = file.read()
        except Exception:
            table.add_row(relative_path, "[red]Cannot read file[/red]")
            continue

        if should_ignore_file(content):
            table.add_row(relative_path, "[yellow]Will be ignored[/yellow]")
            continue

        _, extension = os.path.splitext(file_path)
        language = get_language_from_extension(extension)

        has_copyright, year, _ = check_existing_copyright(content, language)

        if has_copyright and year == str(CURRENT_YEAR) and not force_update:
            table.add_row(relative_path, "[cyan]Up to date[/cyan]")
        elif has_copyright:
            table.add_row(
                relative_path, f"[blue]Will update ({year} → {CURRENT_YEAR})[/blue]"
            )
        else:
            table.add_row(relative_path, "[green]Will add copyright[/green]")

    console.print("\n")
    console.print(table)


def update_system_path_permanently(path_to_add):
    """Update the system PATH environment variable permanently."""
    if platform.system() == "Windows":
        try:
            import winreg

            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER, r"Environment", 0, winreg.KEY_READ
            )
            try:
                path, _ = winreg.QueryValueEx(key, "PATH")
                paths = path.split(";")
                if path_to_add in paths:
                    winreg.CloseKey(key)
                    return True, "Path already exists in PATH"
            except WindowsError:
                path = ""
            winreg.CloseKey(key)

            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER, r"Environment", 0, winreg.KEY_WRITE
            )
            if path:
                new_path = f"{path};{path_to_add}"
            else:
                new_path = path_to_add

            winreg.SetValueEx(key, "PATH", 0, winreg.REG_EXPAND_SZ, new_path)
            winreg.CloseKey(key)

            try:
                import ctypes

                HWND_BROADCAST = 0xFFFF
                WM_SETTINGCHANGE = 0x001A
                SMTO_ABORTIFHUNG = 0x0002
                result = ctypes.c_long()
                SendMessageTimeoutW = ctypes.windll.user32.SendMessageTimeoutW
                SendMessageTimeoutW(
                    HWND_BROADCAST,
                    WM_SETTINGCHANGE,
                    0,
                    ctypes.c_wchar_p("Environment"),
                    SMTO_ABORTIFHUNG,
                    5000,
                    ctypes.byref(result),
                )
            except Exception:
                pass  # It's okay if this fails

            return True, "Successfully added to PATH"
        except Exception as e:
            return False, str(e)
    else:
        # For Unix-like systems, this is typically done by adding to .bashrc, .zshrc, etc.
        return False, "Not implemented for this platform"


def main():
    parser = argparse.ArgumentParser(
        prog="credit",
        description="Add or update copyright notices in code files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Use 'credit --detailed-help' to see complete documentation.
        """,
    )

    parser.add_argument(
        "directory",
        nargs="?",
        help="Path to the source directory (default: from config or ./src)",
        default=None,
    )
    parser.add_argument(
        "-d",
        "--directory",
        dest="dir_option",
        help="Path to the source directory (alternative to positional arg)",
        default=None,
    )
    parser.add_argument(
        "-f",
        "--force",
        help="Force update of copyright notices even if year is current",
        action="store_true",
    )
    parser.add_argument(
        "-y", "--yes", help="Skip confirmation prompt", action="store_true"
    )
    parser.add_argument(
        "-l",
        "--language",
        help="Specify language to process (e.g., typescript, golang)",
        choices=list(SUPPORTED_EXTENSIONS.keys()),
        default="all",
    )
    parser.add_argument(
        "--no-recursive", help="Don't search subdirectories", action="store_true"
    )
    parser.add_argument(
        "--info",
        help="Show supported languages and file extensions",
        action="store_true",
    )
    parser.add_argument("--file", help="Process a single file", default=None)
    parser.add_argument(
        "--preview", help="Preview changes without applying them", action="store_true"
    )
    parser.add_argument(
        "--setup", help="Set up your configuration", action="store_true"
    )
    parser.add_argument(
        "--config", help="Show current configuration", action="store_true"
    )
    parser.add_argument(
        "--version", help="Show version information", action="store_true"
    )
    parser.add_argument(
        "--detailed-help", help="Show detailed help with examples", action="store_true"
    )
    parser.add_argument(
        "--username", help="Override username for this run", default=None
    )
    parser.add_argument(
        "--github", help="Override GitHub handle for this run", default=None
    )
    parser.add_argument(
        "--debug", help="Show processing time statistics", action="store_true"
    )

    args = parser.parse_args()

    if args.detailed_help:
        print_header()
        print_help()
        return

    if args.version:
        print_version()
        return

    if args.config:
        print_header()
        print_config()
        return

    if args.setup:
        print_header()
        username = input(f"Enter your name [{USERNAME}]: ") or USERNAME
        github = input(f"Enter your GitHub handle [{GITHUB}]: ") or GITHUB
        directory = (
            input(f"Enter default directory [{DEFAULT_DIRECTORY}]: ")
            or DEFAULT_DIRECTORY
        )
        create_config(username, github, directory)
        return

    if args.info:
        print_header()
        console.print(
            Panel(
                "\n".join(
                    [
                        f"[bold]{lang.capitalize()}[/bold]: {', '.join(exts)}"
                        for lang, exts in SUPPORTED_EXTENSIONS.items()
                    ]
                ),
                title="Supported Languages",
                border_style=AQUA,
            )
        )
        return

    print_header()

    directory = args.directory or args.dir_option or DEFAULT_DIRECTORY

    if args.file:
        if not os.path.isfile(args.file):
            console.print(
                f"[bold red]Error:[/bold red] {args.file} is not a valid file."
            )
            return

        files = [args.file]
    else:
        if not os.path.isdir(directory):
            console.print(
                f"[bold red]Error:[/bold red] {directory} is not a valid directory."
            )
            return

        if args.language == "all":
            extensions = get_all_extensions()
        else:
            extensions = SUPPORTED_EXTENSIONS[args.language]

        files = find_files(directory, extensions, not args.no_recursive)

    if not files:
        console.print(f"[yellow]No matching files found in {directory}.[/yellow]")
        return

    console.print(f"Found [bold]{len(files)}[/bold] files to process.")

    if args.preview:
        preview_changes(files, args.force)
        return

    if not args.yes:
        proceed = input("Do you want to process these files? (y/n): ")
        if proceed.lower() != "y":
            console.print("[red]Operation cancelled.[/red]")
            return

    stats = {
        "total": len(files),
        "added": 0,
        "updated": 0,
        "skipped": 0,
        "ignored": 0,
        "errors": 0,
    }

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(bar_width=None),
        TaskProgressColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("[cyan]Processing files...", total=len(files))

        for file_path in files:
            relative_path = os.path.relpath(file_path)
            status, extra_info = add_or_update_copyright(
                file_path, args.force, args.username, args.github
            )

            if status in stats:
                stats[status] += 1

            if status == "added":
                progress.update(
                    task, description=f"[green]Added copyright to {relative_path}"
                )
            elif status == "updated":
                progress.update(
                    task,
                    description=f"[blue]Updated copyright ({extra_info} → {CURRENT_YEAR}) in {relative_path}",
                )
            elif status == "skipped":
                progress.update(
                    task, description=f"[cyan]Skipped {relative_path} (up to date)"
                )
            elif status == "ignored":
                progress.update(
                    task,
                    description=f"[yellow]Ignored {relative_path} (credit-ignore found)",
                )
            elif status == "error":
                progress.update(
                    task,
                    description=f"[red]Error processing {relative_path}: {extra_info}",
                )

            progress.update(task, advance=1)

    print_stats(stats)
    if args.debug:
        print_debug_stats()


def install_script():
    """Install the script as a system command."""
    script_path = os.path.abspath(__file__)

    if platform.system() == "Windows":
        user_bin_dir = os.path.join(os.path.expanduser("~"), "bin")
        os.makedirs(user_bin_dir, exist_ok=True)

        script_dest = os.path.join(user_bin_dir, "credit.py")
        batch_path = os.path.join(user_bin_dir, "credit.bat")

        shutil.copy2(script_path, script_dest)

        with open(batch_path, "w") as f:
            f.write(f'@echo off\npython "{script_dest}" %*')

        success, message = update_system_path_permanently(user_bin_dir)

        if success:
            console.print(f"[green]Script installed at {script_dest}[/green]")
            console.print(f"[green]Batch file created at {batch_path}[/green]")
            console.print(f"[green]{message}[/green]")
            console.print(
                "[yellow]You may need to restart your command prompt for the changes to take effect.[/yellow]"
            )
        else:
            console.print(f"[red]Error adding to PATH: {message}[/red]")
            console.print(f"[yellow]Script installed at {script_dest}[/yellow]")
            console.print(f"[yellow]Batch file created at {batch_path}[/yellow]")
            console.print(
                "[yellow]To use from any directory, add this directory to your PATH manually:[/yellow]"
            )
            console.print(f"[blue]{user_bin_dir}[/blue]")
    else:
        # For Unix-like systems
        dest_path = "/usr/local/bin/credit"
        try:
            shutil.copy(script_path, dest_path)
            os.chmod(dest_path, 0o755)
            console.print(f"[green]Successfully installed at {dest_path}[/green]")
        except PermissionError:
            console.print("[red]Permission denied. Try running with sudo.[/red]")
            console.print(
                f"[yellow]To install, run: sudo cp {script_path} {dest_path} && sudo chmod +x {dest_path}[/yellow]"
            )
        except Exception as e:
            console.print(f"[red]Error installing: {str(e)}[/red]")

            user_bin = os.path.expanduser("~/bin")
            os.makedirs(user_bin, exist_ok=True)
            user_dest = os.path.join(user_bin, "credit")

            try:
                shutil.copy(script_path, user_dest)
                os.chmod(user_dest, 0o755)
                console.print(f"[green]Successfully installed at {user_dest}[/green]")

                if user_bin not in os.environ.get("PATH", "").split(":"):
                    console.print(
                        "[yellow]Add this line to your .bashrc or .zshrc file:[/yellow]"
                    )
                    console.print(f'[blue]export PATH="$PATH:{user_bin}"[/blue]')
            except Exception as e2:
                console.print(
                    f"[red]Error installing to user directory: {str(e2)}[/red]"
                )


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--install":
        install_script()
    else:
        try:
            main()
        except KeyboardInterrupt:
            console.print("\n[yellow]Process interrupted by user.[/yellow]")
            sys.exit(1)
        except Exception as e:
            console.print(
                f"\n[bold red]An unexpected error occurred:[/bold red] {str(e)}"
            )
            sys.exit(1)
