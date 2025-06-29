from functools import wraps
import time
from bs4 import BeautifulSoup
import os
from colorama import init, Fore
import asyncio
import aiohttp
from pydub import AudioSegment

clip_crawler = r"""

 ______   __  __             ______                                     __                     
/      \ |  \|  \           /      \                                   |  \                    
|  $$$$$$\| $$ \$$  ______  |  $$$$$$\  ______    ______   __   __   __ | $$  ______    ______  
| $$   \$$| $$|  \ /      \ | $$   \$$ /      \  |      \ |  \ |  \ |  \| $$ /      \  /      \  
| $$      | $$| $$|  $$$$$$\| $$      |  $$$$$$\  \$$$$$$\| $$ | $$ | $$| $$|  $$$$$$\|  $$$$$$\ 
| $$   __ | $$| $$| $$  | $$| $$   __ | $$   \$$ /      $$| $$ | $$ | $$| $$| $$    $$| $$   \$$ 
| $$__/  \| $$| $$| $$__/ $$| $$__/  \| $$      |  $$$$$$$| $$_/ $$_/ $$| $$| $$$$$$$$| $$       
\$$    $$| $$| $$| $$    $$ \$$    $$| $$       \$$    $$ \$$   $$   $$| $$ \$$     \| $$    
 \$$$$$$  \$$ \$$| $$$$$$$   \$$$$$$  \$$        \$$$$$$$  \$$$$$\$$$$  \$$  \$$$$$$$ \$$       
                   | $$                                                                          
                   | $$                                                                          
                   \$$                                                                                                                                       
"""

init(autoreset=True)  

def print_red(text):
    print(Fore.RED + text)

def print_green(text):
    print(Fore.GREEN + text)

def print_blue(text):
    print(Fore.BLUE + text)

def time_it(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        result = await func(*args, **kwargs)
        end_time = time.time()
        print_green(f'{func.__name__} finished in {end_time - start_time:.2f} seconds')
        return result
    return wrapper

def cleanup_output_folder():
    """
    Checks if the output folder is empty, if not, asks the user if they want to clear it.
    """
    has_files = any(files for _, _, files in os.walk('output'))
    if has_files:
        print_blue(r"You're output folder isn't empty, would you like me to clear it and continue? y/n")
        should_clear = input().strip().lower()
        if should_clear == 'y':
            for filename in os.listdir('output'):
                file_path = os.path.join('output', filename)
                try:
                    if os.path.isfile(file_path) or os.path.islink(file_path):
                        os.unlink(file_path)
                except Exception as e:
                    print_red(f'Failed to delete {file_path}. Reason: {e}')
            print_green('Output folder cleared.')
        else:
            print_green('Done for now...')
            exit()
            
async def download_file(session, src, i):
    """
    Downloads a single file from a URL and returns 1 on success, 0 on failure.
    """
    if src is None:
        return 0
    filename = os.path.basename(f'file {i}')
    filepath = f'output/{filename}.mp3'
    try:
        async with session.get(src) as response:
            response.raise_for_status() 
            content = await response.read()
            with open(filepath, 'wb') as f:
                f.write(content)
    except Exception as e:
        print_red(f"Fail: src=[{src}], i=[{i}], error=[{repr(e)}]")
        return 0
    else:
        print_green(f'Success: src=[{src}], i=[{i}], filepath=[{filepath}]')
        return 1

@time_it
async def download_all_files(url):
    """
    Finds and downloads all audio files from a given page URL.
    Returns the number of files successfully downloaded.
    """
    print_blue(f"Requesting page {url}...")
    tasks = []
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url) as response:
                response.raise_for_status()
                html = await response.text()
        except Exception as e:
            print_red(f"Failed to fetch page {url}. Reason: {e}")
            return 0
            
        soup = BeautifulSoup(html, 'html.parser')
        
        sources = soup.find_all(['audio', 'source'])
        print_blue(f"Found {len(sources)} potential files. Starting downloads...")

        async with asyncio.TaskGroup() as tg:
            for i, tag in enumerate(sources):
                # tag_type = tag.name
                src = tag.get('src')
                task = tg.create_task(download_file(session, src, i))
                tasks.append(task)
    
    results = [task.result() for task in tasks]
    return sum(results)

def merge_mp3_files():
    """
    Finds all .mp3 files in a folder, merges them in numerical order, and exports a single file.
    """
    try:
        mp3_files = [f for f in os.listdir('output') if f.endswith('.mp3')]
        if not mp3_files:
            print_red("No .mp3 files found in the output folder to merge.")
            return

        combined_filename = os.path.join('output', 'combined.mp3')
        combined_audio = AudioSegment.empty()

        for filename in mp3_files:
            combined_audio += AudioSegment.from_mp3(os.path.join('output', filename))

        combined_audio.export(combined_filename, format="mp3")
        print_green(f"Successfully merged {len(mp3_files)} files into {combined_filename}")

    except Exception as e:
        print_red(f"An error occurred during merging: {repr(e)}")
        print_red("Please ensure FFmpeg is installed and accessible in your system's PATH.")


def main():
    print_red(clip_crawler)

    print_blue("Checking to see if output folder is clear...")
    cleanup_output_folder()

    print_blue("Enter the URL of the page you want to scrape: ")
    url = input()
    # url = "https://www.101soundboards.com/boards/34605-gandalf#google_vignette"

    print_blue("Downloading audio files...")
    files_downloaded = asyncio.run(download_all_files(url))
    print_green(f"Found {files_downloaded} files, extracted to output/")

    print_blue("Merging audio files into combined.mp3...")
    merge_mp3_files()
    
    print_blue("Press Enter to exit...")
    input()

if __name__ == "__main__":
    main()