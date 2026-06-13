import glob
from markdownify import markdownify
import os
import re
import argparse
import shutil
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn
from rich.panel import Panel


console = Console()


def print_banner():
    """Display a colorful ASCII banner"""
    banner = r"""
___  _________ _____ 
|  \/  || ___ \  __ \
| .  . || |_/ / |  \/
| |\/| || ___ \ | __ 
| |  | || |_/ / |_\ \
\_|  |_/\____/ \____/
    """
    console.print(banner, style="bold cyan")


def clean_filename(filename):
    """
    UNIVERSAL filename cleaner - removes all types of junk patterns
    
    Handles:
    - Hashes: AI-ML--6851b6a2a63c.html -> AI-ML.html
    - Underscores with hash: Blockchain_daa83bf87e0f.html -> Blockchain.html
    - Parentheses with numbers: Topic (12345).html -> Topic.html
    - Multiple separators: Topic--Part-1--hash123.html -> Topic--Part-1.html
    - Reading list variants: Reading-list-predefined_cd70b3ab863c_READING_LIST.html -> Reading-list.html
    """
    name = filename.replace('.html', '').strip()
    
    # Special case: Any reading list variant
    if 'reading' in name.lower() and 'list' in name.lower():
        return "Reading-list.html"
    
    # Remove common junk patterns (order matters!)
    
    # 1. Remove _READING_LIST, _ARCHIVE, etc.
    name = re.sub(r'_[A-Z_]+$', '', name)
    
    # 2. Remove predefined/system keywords
    name = re.sub(r'-predefined', '', name, flags=re.IGNORECASE)
    name = re.sub(r'-exported?', '', name, flags=re.IGNORECASE)
    name = re.sub(r'-archive', '', name, flags=re.IGNORECASE)
    
    # 3. Remove patterns like (numbers) or [numbers]
    name = re.sub(r'\s*[\(\[][0-9a-f]+[\)\]]', '', name)
    
    # 4. Remove underscore or dash followed by long hash (8+ chars of hex/alphanum)
    name = re.sub(r'[_-][a-f0-9]{8,}', '', name)
    
    # 5. Remove double-dash followed by hash
    name = re.sub(r'--[a-f0-9]+', '', name)
    
    # 6. Remove dates like -2024-01-07, -20240107
    name = re.sub(r'-\d{4}-?\d{2}-?\d{2}', '', name)
    
    # 7. Remove trailing numbers like -123, -v2, etc (but keep meaningful ones)
    name = re.sub(r'-v?\d+$', '', name)
    
    # 8. Remove any remaining lone numbers/letters at the end
    name = re.sub(r'[-_][a-z0-9]{1,3}$', '', name, flags=re.IGNORECASE)
    
    # Clean up multiple dashes/underscores
    name = re.sub(r'[-_]{2,}', '-', name)
    
    # Remove trailing/leading dashes or underscores
    name = name.strip('-_')
    
    # If nothing left, use a default
    if not name or len(name) < 2:
        name = "Untitled"
    
    return name + '.html'

def rename_html_files(bookmarks_dir):
    """
    Rename all HTML files in the directory to clean names
    Returns mapping of old_path -> new_path
    """
    file_list = list(glob.glob(os.path.join(bookmarks_dir, "*.html")))
    
    if not file_list:
        return {}
    
    console.print("\n[bold cyan]🔄 Cleaning HTML filenames...[/bold cyan]\n")
    
    rename_map = {}
    seen_names = {}
    
    for old_path in file_list:
        old_filename = os.path.basename(old_path)
        new_filename = clean_filename(old_filename)
        
        if new_filename in seen_names:
            seen_names[new_filename] += 1
            base_name = new_filename.replace('.html', '')
            new_filename = f"{base_name}-{seen_names[new_filename]}.html"
        else:
            seen_names[new_filename] = 1
        
        new_path = os.path.join(bookmarks_dir, new_filename)
        
        if old_path == new_path:
            rename_map[old_path] = new_path
            console.print(f"[dim]✓ {old_filename} (already clean)[/dim]")
            continue
        
        try:
            shutil.move(old_path, new_path)
            rename_map[old_path] = new_path
            console.print(f"[green]✓[/green] {old_filename:50} -> [cyan]{new_filename}[/cyan]")
        except Exception as e:
            console.print(f"[red]✗ Error renaming {old_filename}: {e}[/red]")
            rename_map[old_path] = old_path
    
    return rename_map


def extract_category_name(filename):
    """
    Extract category name from clean filename
    """
    name = filename.replace('.html', '')
    
    if 'reading-list' in name.lower():
        return "Reading List", "reading-list.md"
    
    display_name = name.replace('-', ' ').replace('_', ' ').strip().title()
    clean_filename = name.lower().replace(' ', '-').replace('_', '-') + '.md'
    
    return display_name, clean_filename


def convert_medium_links_to_freedium(markdown_content):
    """
    Finds all Markdown links pointing to medium.com and converts them
    to freedium.cfd links.
    """
    pattern = re.compile(r'\[([^\]]+)\]\((https?:\/\/(?:www\.)?(?:[a-zA-Z0-9-]+\.)*medium\.com(?:\/[^\s)]*)?)\)')

    def replace_link(match):
        link_text = match.group(1)
        original_url = match.group(2)
        freedium_url = f"https://freedium-mirror.cfd/{original_url}"
        return f"[{link_text}]({freedium_url})"

    converted_content = pattern.sub(replace_link, markdown_content)
    return converted_content


def extract_unique_links(content):
    """
    Extract unique article URLs from markdown content
    Returns set of URLs
    """
    pattern = r'\[([^\]]+)\]\((https?://[^)]+)\)'
    matches = re.findall(pattern, content)
    return {url for _, url in matches}


def remove_duplicate_articles(all_content_dict):
    """
    Remove duplicate articles across categories
    Keep first occurrence, remove from later categories
    Returns cleaned content dict and stats
    """
    seen_urls = set()
    cleaned_content = {}
    duplicates_removed = {}
    
    for category, content in all_content_dict.items():
        lines = content.split('\n')
        cleaned_lines = []
        category_duplicates = 0
        
        i = 0
        while i < len(lines):
            line = lines[i]
            
            # Check if line contains a link
            link_match = re.search(r'\[([^\]]+)\]\((https?://[^)]+)\)', line)
            
            if link_match:
                url = link_match.group(2)
                if url in seen_urls:
                    # Skip this article (and potential next lines until next article)
                    category_duplicates += 1
                    i += 1
                    continue
                else:
                    seen_urls.add(url)
                    cleaned_lines.append(line)
            else:
                cleaned_lines.append(line)
            
            i += 1
        
        cleaned_content[category] = '\n'.join(cleaned_lines)
        duplicates_removed[category] = category_duplicates
    
    return cleaned_content, duplicates_removed


def main():
    parser = argparse.ArgumentParser(
        description='Convert Medium bookmarks to Markdown with Freedium links',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Default: All categories + Reading List
  python script.py -i lists/ -d output/
  Output: medium_bookmark_list.md
  
  # Categories only (exclude Reading List)
  python script.py -i lists/ -d output/ -c
  Output: combined.md
  
  # Categories + Reading List with duplicate removal
  python script.py -i lists/ -d output/ -cr
  Output: combined-reading-sorted.md
        """
    )
    parser.add_argument(
        '-i', '--input',
        default='data/bookmarks',
        help='Input directory containing HTML bookmark files (default: data/bookmarks)'
    )
    parser.add_argument(
        '-o', '--output',
        default=None,
        help='Custom output filename (optional, overrides auto-naming)'
    )
    parser.add_argument(
        '-d', '--dir',
        default='.',
        help='Output directory (default: current directory)'
    )
    parser.add_argument(
        '-c', '--categories-only',
        action='store_true',
        help='Combine only custom categories, exclude Reading List (output: combined.md)'
    )
    parser.add_argument(
        '-cr', '--categories-with-reading-remove-duplicates',
        action='store_true',
        help='Combine all categories with Reading List and remove duplicates (output: combined-reading-sorted.md)'
    )
    
    args = parser.parse_args()
    bookmarks_dir = args.input
    output_dir = args.dir
    custom_output = args.output
    categories_only = args.categories_only
    remove_dupes = args.categories_with_reading_remove_duplicates

    # Determine output filename based on flags
    if custom_output:
        # User provided custom name
        combined_output_filename = custom_output
    elif categories_only:
        # -c flag: combined.md
        combined_output_filename = "combined.md"
    elif remove_dupes:
        # -cr flag: combined-reading-sorted.md
        combined_output_filename = "combined-reading-sorted.md"
    else:
        # Default: medium_bookmark_list.md
        combined_output_filename = "medium_bookmark_list.md"

    if os.path.dirname(combined_output_filename):
        combined_output_path = combined_output_filename
    else:
        combined_output_path = os.path.join(output_dir, combined_output_filename)

    print_banner()
    
    if not os.path.exists(bookmarks_dir):
        console.print(f"\n[bold red]✗[/bold red] Error: Bookmarks directory not found at [yellow]{bookmarks_dir}[/yellow]", style="red")
        console.print("[dim]Please make sure your HTML bookmark file(s) are in the specified folder[/dim]")
        exit(1)

    os.makedirs(output_dir, exist_ok=True)
    categories_dir = os.path.join(output_dir, 'categories')
    os.makedirs(categories_dir, exist_ok=True)

    rename_map = rename_html_files(bookmarks_dir)
    if not rename_map:
        console.print(f"\n[bold red]✗[/bold red] No HTML files found in [yellow]{bookmarks_dir}[/yellow]", style="red")
        exit(1)

    file_list = list(glob.glob(os.path.join(bookmarks_dir, "*.html")))
    
    def sort_key(filepath):
        filename = os.path.basename(filepath)
        if 'reading-list' in filename.lower():
            return (1, filename)
        return (0, filename)
    
    file_list.sort(key=sort_key)

    if not file_list:
        console.print(f"\n[bold red]✗[/bold red] No HTML files found in [yellow]{bookmarks_dir}[/yellow]", style="red")
        exit(1)

    # Display mode information
    if categories_only:
        console.print("\n[bold yellow]⚙️  Mode: Categories Only (excluding Reading List)[/bold yellow]")
        console.print(f"[bold yellow]📄 Output: {combined_output_filename}[/bold yellow]")
    elif remove_dupes:
        console.print("\n[bold yellow]⚙️  Mode: All Categories + Reading List (with duplicate removal)[/bold yellow]")
        console.print(f"[bold yellow]📄 Output: {combined_output_filename}[/bold yellow]")
    else:
        console.print("\n[bold yellow]⚙️  Mode: All Categories + Reading List (default)[/bold yellow]")
        console.print(f"[bold yellow]📄 Output: {combined_output_filename}[/bold yellow]")

    console.print(f"\n[bold green]✓[/bold green] Found [bold cyan]{len(file_list)}[/bold cyan] HTML bookmark file(s) to process\n")

    all_content_dict = {}  # For duplicate removal
    all_content = []  # For combined file
    category_files = []
    total_links = 0
    total_medium_links = 0
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        console=console
    ) as progress:
        
        task = progress.add_task("[cyan]Processing bookmarks...", total=len(file_list))
        
        for file_path in file_list:
            filename = os.path.basename(file_path)
            category_name, category_filename = extract_category_name(filename)
            
            # Skip Reading List if -c flag is used
            if categories_only and 'reading-list' in filename.lower():
                console.print(f"[dim]⊘ Skipping {category_name} (categories-only mode)[/dim]")
                progress.advance(task)
                continue
            
            progress.update(task, description=f"[cyan]Processing [yellow]{category_name}[/yellow]")
            
            try:
                with open(file_path, "r", encoding="utf-8") as html_file:
                    html_content = html_file.read()

                md_text = markdownify(html_content)
                
                links_found = len(re.findall(r'\[([^\]]+)\]\(([^)]+)\)', md_text))
                medium_links = len(re.findall(r'medium\.com', md_text))
                total_links += links_found
                total_medium_links += medium_links

                parts = md_text.split("###", 1)
                if len(parts) > 1:
                    content = parts[1].strip()
                else:
                    content = md_text.strip()

                converted_content = convert_medium_links_to_freedium(content)
                
                # Store in dict for duplicate removal
                all_content_dict[category_name] = converted_content
                
                # Save individual category file
                category_file_path = os.path.join(categories_dir, category_filename)
                with open(category_file_path, "w", encoding="utf-8") as cat_file:
                    cat_file.write(f"# {category_name}\n\n{converted_content}")
                
                category_files.append({
                    'name': category_name,
                    'filename': category_filename,
                    'links': links_found,
                    'medium_links': medium_links
                })

            except Exception as e:
                console.print(f"[bold red]✗[/bold red] Error processing [yellow]{filename}[/yellow]: {e}")
            
            progress.advance(task)

    # Handle duplicate removal if -cr flag is used
    duplicates_stats = {}
    if remove_dupes:
        console.print("\n[bold cyan]🔍 Removing duplicate articles...[/bold cyan]")
        all_content_dict, duplicates_stats = remove_duplicate_articles(all_content_dict)
        
        total_duplicates = sum(duplicates_stats.values())
        if total_duplicates > 0:
            console.print(f"[bold green]✓[/bold green] Removed [bold yellow]{total_duplicates}[/bold yellow] duplicate articles\n")
            for cat, count in duplicates_stats.items():
                if count > 0:
                    console.print(f"  [dim]• {cat}: {count} duplicates removed[/dim]")

    # Build combined content
    for category_name, content in all_content_dict.items():
        combined_section = f"\n# {category_name}\n\n{content}\n\n---\n"
        all_content.append(combined_section)

    console.print("\n[bold cyan]💾 Saving files...[/bold cyan]\n")
    
    try:
        # Add table of contents
        toc_title = "Medium Bookmarks"
        if categories_only:
            toc_title += " - Custom Categories"
        elif remove_dupes:
            toc_title += " - All Categories (Deduplicated)"
        else:
            toc_title += " - All Categories"
            
        toc = f"# {toc_title}\n\n## Table of Contents\n\n"
        for cat in category_files:
            anchor = cat['name'].lower().replace(' ', '-')
            toc += f"- [{cat['name']}](#{anchor})\n"
        toc += "\n---\n"
        
        combined_content = toc + "\n".join(all_content)
        
        with open(combined_output_path, "w", encoding="utf-8") as text_file:
            text_file.write(combined_content)
        
        link_count = len(re.findall(r'freedium-mirror\.cfd', combined_content))
        
        # Print summary table
        console.print("[bold cyan]📊 Files Created:[/bold cyan]\n")
        console.print("[bold]Category[/bold] | [bold]Filename[/bold] | [bold]Links[/bold] | [bold]Medium Links[/bold]")
        console.print("-" * 80)
        for cat in category_files:
            console.print(
                f"[yellow]{cat['name'][:20]:20}[/yellow] | "
                f"[cyan]{cat['filename'][:30]:30}[/cyan] | "
                f"[green]{cat['links']:5}[/green] | "
                f"[green]{cat['medium_links']:12}[/green]"
            )
        
        # Build success message
        success_msg = f"[bold green]✓ Successfully created {len(category_files)} category files[/bold green]\n"
        success_msg += f"[bold cyan]📁 Category files: {categories_dir}[/bold cyan]\n"
        success_msg += f"[bold cyan]🔗 Total links found: {total_links}[/bold cyan]\n"
        success_msg += f"[bold cyan]🔗 Converted {link_count} Medium links to Freedium[/bold cyan]\n"
        
        if remove_dupes and sum(duplicates_stats.values()) > 0:
            success_msg += f"[bold magenta]🔄 Duplicates removed: {sum(duplicates_stats.values())}[/bold magenta]\n"
        
        success_msg += f"[bold yellow]📄 Combined file: {combined_output_filename}[/bold yellow]\n"
        success_msg += f"[bold yellow]📊 Total size: {len(combined_content):,} characters[/bold yellow]"
        
        success_panel = Panel(
            success_msg,
            title="[bold green]Success![/bold green]",
            border_style="green"
        )
        console.print("\n")
        console.print(success_panel)
        console.print("\n[dim]✨ HTML files have been renamed to clean names[/dim]")
        console.print("[dim]✨ Check the 'categories' folder for individual category files[/dim]\n")
        
    except Exception as e:
        console.print(f"\n[bold red]✗[/bold red] Error saving files: {e}", style="red")
        exit(1)


if __name__ == "__main__":
    main()
