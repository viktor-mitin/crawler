import requests
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup

import multiprocessing
import time

# initialize the set of links (unique links)
internal_urls = set()

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
#        if href in internal_urls:
#            # already in the set
#            print(f'already')
#            continue
        if domain_name not in href:
            # external link, skipping
            continue

        urls.add(href)
        internal_urls.add(href)
    return urls


def crawl(url, cur_depth=0, cur_proc=0):
    """
    Crawls a web page and extracts all links.
    params:
        cur_depth (int): current depth
    """
    if cur_depth > max_depth:
        return

    links = get_all_website_links(url)

    if not links:
        return

    out_file = open(f"{cur_depth}_proc{cur_proc}.txt", "w")

    pool = multiprocessing.Pool(processes=4)
    jobs = []
    cur_proc=0

    for link in links:
        print(link, file=out_file)

#        crawl(link, cur_depth=cur_depth+1)
#        proc = multiprocessing.Process(target=crawl, args=(link, cur_depth+1, cur_proc))

        proc = pool.apply_async(func=crawl, args=(link, cur_depth+1, cur_proc,))
        jobs.append(proc)
        cur_proc += 1

    while(not all([p.ready() for p in jobs])):
        time.sleep(1)

    # Safely terminate the pool
    pool.close()
    pool.join()


    out_file.close()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Link Extractor Tool with Python")
    parser.add_argument("url", help="The URL to extract links from.")
    parser.add_argument("-m", "--max-depth", help="Number of max depth to crawl, default is 10.", default=10, type=int)

    args = parser.parse_args()
    url = args.url
    max_depth = args.max_depth

    crawl(url)

    print("[+] Total URLs:", len(internal_urls))

    domain_name = urlparse(url).netloc

    # save the internal links to a file
    with open(f"{domain_name}_internal_links.txt", "w") as f:
        for internal_link in internal_urls:
            print(internal_link.strip(), file=f)

