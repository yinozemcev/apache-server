from requests import get
from bs4 import BeautifulSoup
import logging
from os import mkdir
from os.path import join, exists, dirname
from urllib.request import urlretrieve
from urllib.parse import quote, unquote
import configparser

def size_to_MB(size):
    """
    Convert sizes like 110K, 514 , 1.2G to megabytes
    """
    prefixes = {' ': 2**(-20), #Apache uses space for size in bytes
                'K': 2**(-10),
                'M': 1,
                'G': 2**10}
    return float(size[:-1]) * prefixes[size[-1]]
def get_page(url):
    try:
        response = get(url)
        page = BeautifulSoup(response.text, 'lxml')
        return page
    except Exception as e:
        logging.error(e)

def get_elements(page):
    """
    Find all <tr> elements then remove first 3 rows(attribute names, separator, parent directory)
    and last row - another separator
    """
    try:
        rows = page.findAll('tr')[3:-1]  
        return rows
    except Exception as e:
        logging.error(e)

def parse(url, depth, path):
    global total_size
    if depth > 0:
        page = get_page(url)
        rows = get_elements(page)
        for row in rows:
            img, name, last_modified, size, desc = row.findAll('td')
            href = unquote(name.a.get('href')) #decode from URL-encoded and get readable filename
            if href.endswith('/'): #this href is a directory
                logging.info(f'New directory! {href}')
                parse(url + href, depth - 1, join(path, href))
            else: #this href is a file
                try:
                    logging.info(f'Download new file {unquote(href)}')
                    filepath = join(path, href)
                    if not exists(path): #create dir if it doesn't exists
                        mkdir(path)
                    if not exists(filepath): #download files only if it doesn't exists
                        urlretrieve(url, filepath)
                        total_size += size_to_MB(size.text)
                    logging.info(f'Downloaded {unquote(href)} ({size.text})')
                except Exception as e:
                    logging.error(e)

def read_cfg():
    """
    Config file must contain  'default' section with 'url' variable (Apache Server URL)
    Also config can contain variables 'depth' (search depth, by default 1)
    and 'path' (path to save files, by default directory with script)

    config.ini structure:

    [default]
    url = YOURURL
    depth = SEARCHDEPTH
    path = SAVEPATH
    
    """
    config = configparser.RawConfigParser()
    config.read('config.ini', encoding = 'utf-8')
    default = config['default']
    url = quote(default['url'], safe = ':/%?=') #quote to get URL-encoded adresses
    depth = int(default.get('depth', 1))
    path = default.get('path', join(dirname(__file__), 'output/'))
    return (url, depth, path)

total_size = 0
def main():
    global total_size
    logging.basicConfig(filename='parser.log',
                    level = logging.INFO,
                    encoding='utf-8',
                    format='[%(asctime)s] %(message)s',
                    datefmt='%d/%m/%Y %H:%M:%S')
    url, depth, path = read_cfg()
    parse(url, depth, path)
    logging.info(f'{total_size} MB downloaded')
    

if __name__ == '__main__':
    main()
