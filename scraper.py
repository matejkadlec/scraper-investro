from urllib.request import Request, urlopen
from bs4 import BeautifulSoup
from xml.dom.minidom import parseString
from tqdm import tqdm
from urllib.parse import urlparse
import os.path
import re
from template import post_template


content_data = []
xml = """<?xml version="1.0" encoding="UTF-8"?>
<data>"""
count = 0


def parse_sitemap(base_url):
    global xml
    global count
    # get sitemap as xml
    req = Request(base_url)
    sitemap = urlopen(req).read()
    soup = BeautifulSoup(sitemap, features="html.parser")

    # find all urls
    urls = []
    url_tags = soup.find_all("url")

    # append links to lists
    for url_tag in url_tags:
        urls.append(url_tag.findNext("loc").text)

    # remove unused urls
    urls = list(filter(("https://investro.com").__ne__, urls))
    urls = urls[6:]

    # parse html of all posts
    for url in tqdm(urls):
        parse_post(url)

    with open("test.xml", "a", encoding="UTF-8") as text_file:
        text_file.write("\n</data>")


def parse_post(url):
    global content_data
    html = urlopen(Request(url)).read().decode('utf-8')
    doc = parseString(html)

    # title
    title = doc.getElementsByTagName("title")[0].firstChild.nodeValue
    index = post_template.find('</Title>')
    post = post_template[:index] + title + post_template[index:]

    # excerpt & content
    article = doc.getElementsByTagName("article")[0]
    full_content = get_content(article)
    index = post.find('</Excerpt>')
    post = post[:index] + full_content[0][3:][:-4] + post[index:]
    index = post.find(']]></Content>')
    content = ""
    for element in full_content[1:]:
        content += element + "\n"
    post = post[:index] + content + post[index:]

    # meta nodes fo date, author and tags
    meta_nodes = doc.getElementsByTagName("meta")

    # date published
    for node in meta_nodes:
        if node.getAttribute("property") == "article:published_time":
            index = post.find('</Date>')
            post = post[:index] + node.getAttribute("content")[:10] + post[index:]

    # author
    index = post.find('</AuthorID>')
    post = post[:index] + "1" + post[index:]
    index = post.find('</AuthorUsername>')
    post = post[:index] + "matej" + post[index:]
    index = post.find('</AuthorEmail>')
    post = post[:index] + "matej@webotvurci.cz" + post[index:]

    # permalink
    index = post.find('</Permalink>')
    post = post[:index] + url + post[index:]

    # image url
    match = re.search(r'\{background-image:url\(https://cdn.investro.com/images/large/.*\)', html)
    if not match:
        match = re.search(r'\{background-image:url\(https://investro.com/article/.*\)', html)
    result = match.group()
    img_url = result.split("(", 1)[1][:-1]
    index = post.find('</ImageURL>')
    post = post[:index] + img_url + post[index:]

    # image title
    index = post.find('</ImageTitle>')
    post = post[:index] + img_url.rsplit('/', 1)[-1].split(".", 1)[0] + post[index:]

    # image featured
    index = post.find('</ImageFeatured>')
    post = post[:index] + img_url + post[index:]

    # categories
    parsed_url = urlparse(url)
    path = os.path.split(parsed_url.path)
    index = post.find('</Categories>')
    post = post[:index] + path[0][1:] + post[index:]

    # tags
    tags = ""
    for node in meta_nodes:
        if node.getAttribute("property") == "article:tag":
            tags += "|" + node.getAttribute("content")
    index = post.find('</Tags>')
    post = post[:index] + tags[1:] + post[index:]

    # slug
    index = post.find('</Slug>')
    post = post[:index] + path[1] + post[index:]

    # date modified
    for node in meta_nodes:
        if node.getAttribute("property") == "article:modified_time":
            index = post.find('</PostModifiedDate>')
            post = post[:index] + node.getAttribute("content")[:10] + post[index:]

    with open("test.xml", "a", encoding="UTF-8") as text_file:
        text_file.write("\n" + post)
    content_data = []


def get_content(root):
    global content_data
    for node in root.childNodes:
        if node.nodeValue:
            content_data.append(f"<{node.parentNode.localName}>{node.nodeValue}</{node.parentNode.localName}>")
        elif node.tagName == "img":
            content_data.append(f"<{node.tagName} src=\"{node.getAttribute('src')}\" alt=\"{node.getAttribute('alt')}\">")
        if len(node.childNodes) > 0:
            get_content(node)
    return content_data