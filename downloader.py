import sys
import requests
from bs4 import BeautifulSoup
import os
import subprocess
from urllib.parse import urljoin, urlparse

def print_help():
    print("Usage: python downloader.py <link>")
    print("This script downloads a chapter of a web novel from the provided link and continues to the next chapters until the last chapter.")
    print("Arguments:")
    print("  <link>    The URL to the chapter of the web novel to download.")

def download_chapter(link):
    try:
        response = requests.get(link)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        print(f"Failed to download the chapter: {e}")
        sys.exit(1)

def extract_next_chapter_link(html_content, base_url):
    soup = BeautifulSoup(html_content, 'html.parser')
    nav_buttons_div = soup.find('div', class_='row nav-buttons')
    if nav_buttons_div:
        col_div = nav_buttons_div.find('div', class_='col-lg-offset-6')
        if col_div:
            next_chapter_link = col_div.find('a', href=True)
            if next_chapter_link:
                return urljoin(base_url, next_chapter_link['href'])
    return None

def parse_novel_name(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    novel_name = soup.find('h2', class_='font-white').get_text().strip()
    return novel_name

def parse_chapter(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    chapter_inner = soup.find_all('div', class_='chapter-inner')
    chapter_content = soup.find_all('div', class_='chapter-content')

    parsed_content = ''
    for div in chapter_inner + chapter_content:
        for p in div.find_all('p'):
            parsed_content += p.get_text() + '\n'

    return parsed_content.strip()  # Strip any leading/trailing whitespace

def save_parsed_content(content, filename):
    with open(filename, 'a', encoding='utf-8') as file:
        if file.tell() != 0:  # Check if file is not empty
            file.write('\n' * 3)  # Add 3 newlines between chapters
        file.write(content)

def convert_to_epub(input_file, output_file):
    try:
        subprocess.run(['ebook-convert', input_file, output_file])
        print(f"Conversion to EPUB successful. Output file: {output_file}")
    except FileNotFoundError:
        print("Error: 'ebook-convert' command not found. Make sure Calibre is installed and in your PATH.")
        sys.exit(1)

def main():
    if len(sys.argv) != 2:
        print_help()
        sys.exit(1)

    link = sys.argv[1]

    if not link:
        print_help()
        sys.exit(1)

    # Download the first chapter to get the novel name
    html_content = download_chapter(link)
    novel_name = parse_novel_name(html_content)
    print(f"Novel name: {novel_name}")

    # Use novel name for filenames without quotes
    output_txt_file = f"{novel_name.replace(' ', '_')}.txt"
    output_epub_file = f"{novel_name.replace(' ', '_')}.epub"

    # Clear the output file if it exists
    if os.path.exists(output_txt_file):
        os.remove(output_txt_file)

    # Extract base URL
    parsed_url = urlparse(link)
    base_url = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path.rsplit('/', 1)[0]}/"

    while link:
        html_content = download_chapter(link)
        next_chapter_link = extract_next_chapter_link(html_content, base_url)
        
        if next_chapter_link:
            print(f"Next chapter link: {next_chapter_link}")
        else:
            print("Last chapter reached.")
        
        parsed_content = parse_chapter(html_content)
        save_parsed_content(parsed_content, output_txt_file)
        
        if not next_chapter_link:
            break
        
        link = next_chapter_link

    # After all chapters are downloaded and parsed, convert to EPUB
    convert_to_epub(output_txt_file, output_epub_file)

    print(f"All chapters have been parsed and saved to {output_txt_file}.")
    print(f"The EPUB file has been generated: {output_epub_file}")

if __name__ == '__main__':
    main()