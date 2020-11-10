import requests
import time
import argparse

from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
from multiprocessing import Pool, Queue, Process, Manager

max_depth = 0
num_workers = 10

def is_valid(url):
    """
    Checks whether `url` is a valid URL.
    """
    parsed = urlparse(url)
    return bool(parsed.netloc) and bool(parsed.scheme)


def get_all_website_links(url):
    """
    Returns all URLs that is found on `url` in which it belongs to the same website
    """
    # all URLs of `url`
    urls = set()
    # domain name of the URL without the protocol
    domain_name = urlparse(url).netloc
    soup = BeautifulSoup(requests.get(url).content, "html.parser")
    for a_tag in soup.findAll("a"):
        href = a_tag.attrs.get("href")
        if href == "" or href is None:
            # href empty tag
            continue
        # join the URL if it's relative (not absolute link)
        href = urljoin(url, href)

        parsed_href = urlparse(href)
        # remove URL GET parameters, URL fragments, etc.
        href = parsed_href.scheme + "://" + parsed_href.netloc + parsed_href.path

        if not is_valid(href):
            # not a valid URL
            continue
        if domain_name not in href:
            # external link, skipping
            continue

        urls.add(href)
    return urls


def worker(q,d):

    while True:

        try:
            item = q.get(timeout=2)
        except:
            break

        url = item[0]
        cur_depth = item[1]

        if cur_depth > max_depth:
            continue

        if url == 'done':
            break

        links = get_all_website_links(url)

        for link in links:
            if link not in d:
                q.put((link, cur_depth+1))

        d[url] = cur_depth
        print(f'{url}, {cur_depth}')


def crawl(start_url):
    """
    Crawls a web page and extracts all links.
    """

    m = Manager()
    q = m.Queue()
    d = m.dict()

    # Create a group of parallel workers and start them
    workers_list = []
    for i in range(num_workers):
        process = Process(target=worker, args=(q,d))
        workers_list.append(process)
        process.start()

    q.put((start_url, 0))

    [process.join() for process in workers_list]

    print(d)
    print(len(d))


def main():
    global max_depth
    global num_workers

    parser = argparse.ArgumentParser(description="Link Extractor Tool with Python")
    parser.add_argument("url", help="The URL to extract links from.")
    parser.add_argument("-m", "--max-depth", help="Number of max depth to crawl, default is 10.", default=10, type=int)
    parser.add_argument("-w", "--num-workers", help="Number of workers, default is 10.", default=10, type=int)

    args = parser.parse_args()
    url = args.url
    max_depth = args.max_depth
    num_workers = args.num_workers

    crawl(url)

#    print("[+] Total URLs:", len(internal_urls))


if __name__ == "__main__":

    main()
