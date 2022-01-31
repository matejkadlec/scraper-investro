from urllib.request import Request, urlopen
from bs4 import BeautifulSoup
from xml.dom.minidom import parseString
from tqdm import tqdm
from urllib.parse import urlparse
import os.path
from datetime import datetime
from template import post_template


content_data = []
count = 0
authors = {'Marek Feder': [7, "marekfeder", "feder@investro.com", "Marek", "Feder"],
           'Walfir Technologies': [11, "walfirtech", "snirc@investro.com", "Walfir", "Technologies"],
           'Vlastimil Bijota': [10, "vlastimilbijota", "bijota@sankasystems.com", "Vlastimil", "Bijota"],
           'Jakub Kralovanský': [5, "jakubkralovansky", "kralovansky@investro.com", "Jakub", "Kralovanský"],
           'Slavomír Kanuk': [9, "slavomirkanuk", "slavomir.kanuk@gmail.com", "Slavomír", "Kanuk"],
           'Jan Sedlacik': [6, "jansedlacik", "sedlacik@imfrontman.com", "Jan", "Sedlacik"],
           'Peter Rehak': [8, "peterrehak", "rehak@investro.com", "Peter", "Rehak"],
           'Tomáš Drdla': [3, "jsme@webotvurci.cz", "jsme@webotvurci.cz", "Tomáš", "Drdla"]}
span_caption = False
span_author = False


def parse_sitemap(base_url):
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
        if "/market-movers/" in url:
            parse_message(url)
        else:
            parse_post(url)

    with open("messages.xml", "a", encoding="UTF-8") as text_file:
        text_file.write("\n</data>")
    with open("posts.xml", "a", encoding="UTF-8") as text_file:
        text_file.write("\n</data>")


def parse_message(url):
    html = urlopen(Request(url)).read().decode('utf-8')
    doc = parseString(html)

    # title
    title = doc.getElementsByTagName("title")[0].firstChild.nodeValue
    index = post_template.find('</Title>')
    post = post_template[:index] + title[:-15] + post_template[index:]

    # content
    h1 = doc.getElementsByTagName("h1")[0].firstChild.nodeValue
    message = doc.getElementsByTagName("h2")[0]
    h2 = message.firstChild.nodeValue
    p = message.parentNode.lastChild.firstChild.nodeValue
    content = f"<h1>{h1}</h1>\n<h2>{h2}</h2>\n<p>{p}</p>"
    index = post.find(']]></Content>')
    post = post[:index] + content + post[index:]

    # excerpt
    index = post.find('</Excerpt>')
    post = post[:index] + p + post[index:]

    # date published
    date = doc.getElementsByTagName("h1")[0].parentNode.parentNode.lastChild.firstChild.firstChild.firstChild \
        .firstChild.firstChild.nodeValue
    parts = date.split(' ')
    day = parts[0].zfill(2)
    month = parts[1].split(',')[0]
    datetime_object = datetime.strptime(month, "%B")
    month = str(datetime_object.month).zfill(2)
    year = "2022" if month == "01" else "2021"
    index = post.find('</Date>')
    post = post[:index] + f"{year}-{month}-{day}" + post[index:]

    # post type
    index = post.find('</PostType>')
    post = post[:index] + "market-movers" + post[index:]

    # permalink
    index = post.find('</Permalink>')
    post = post[:index] + url + post[index:]

    # category
    parsed_url = urlparse(url)
    full_path = os.path.split(parsed_url.path)
    path = os.path.split(full_path[0])
    index = post.find('</Categories>')
    post = post[:index] + path[1] + post[index:]

    # slug
    index = post.find('</Slug>')
    post = post[:index] + full_path[1] + post[index:]

    # author
    try:
        author = doc.getElementsByTagName("h1")[0].parentNode.parentNode.lastChild.firstChild.firstChild.lastChild \
            .firstChild.nodeValue
    except Exception:
        author = "Tomáš Drdla"
    index = post.find('</AuthorID>')
    post = post[:index] + str(authors[author][0]) + post[index:]
    index = post.find('</AuthorUsername>')
    post = post[:index] + authors[author][1] + post[index:]
    index = post.find('</AuthorEmail>')
    post = post[:index] + authors[author][2] + post[index:]
    index = post.find('</AuthorFirstName>')
    post = post[:index] + authors[author][3] + post[index:]
    index = post.find('</AuthorLastName>')
    post = post[:index] + authors[author][4] + post[index:]

    meta_nodes = doc.getElementsByTagName("meta")
    # _yoast_wpseo_metadesc, _yoast_wpseo_opengraph-description
    for node in meta_nodes:
        if node.getAttribute("name") == "description":
            index = post.find('</_yoast_wpseo_metadesc>')
            post = post[:index] + node.getAttribute("content")[:-15] + post[index:]
            index = post.find('</_yoast_wpseo_opengraph-description>')
            post = post[:index] + node.getAttribute("content")[:-15] + post[index:]

    # _yoast_wpseo_title, _yoast_wpseo_opengraph-title
    index = post.find('</_yoast_wpseo_title>')
    post = post[:index] + title + post[index:]
    index = post.find('</_yoast_wpseo_opengraph-title>')
    post = post[:index] + title + post[index:]

    with open("messages.xml", "a", encoding="UTF-8") as text_file:
        text_file.write("\n" + post)


def parse_post(url):
    global content_data
    global authors
    html = urlopen(Request(url)).read().decode('utf-8')
    doc = parseString(html)

    # title
    title = doc.getElementsByTagName("title")[0].firstChild.nodeValue
    index = post_template.find('</Title>')
    post = post_template[:index] + title[:-15] + post_template[index:]

    # excerpt & content
    article = doc.getElementsByTagName("article")[0]
    full_content = get_content(article)
    index = post.find('</Excerpt>')
    post = post[:index] + full_content[1] + post[index:]
    index = post.find(']]></Content>')
    content = ""
    for element in full_content[3:]:
        content += element + "\n" if element[-1] == ">" and element != "<p>" and not element.endswith("</strong>") else element
    post = post[:index] + content + post[index:]

    # meta nodes fo date, author and tags
    meta_nodes = doc.getElementsByTagName("meta")

    # meta tags
    for node in meta_nodes:
        # date published
        if node.getAttribute("property") == "article:published_time":
            index = post.find('</Date>')
            post = post[:index] + node.getAttribute("content")[:10] + post[index:]
        # author
        if node.getAttribute("property") == "article:author":
            author = node.getAttribute("content")
            index = post.find('</AuthorID>')
            post = post[:index] + str(authors[author][0]) + post[index:]
            index = post.find('</AuthorUsername>')
            post = post[:index] + authors[author][1] + post[index:]
            index = post.find('</AuthorEmail>')
            post = post[:index] + authors[author][2] + post[index:]
            index = post.find('</AuthorFirstName>')
            post = post[:index] + authors[author][3] + post[index:]
            index = post.find('</AuthorLastName>')
            post = post[:index] + authors[author][4] + post[index:]
        # image url
        if node.getAttribute("property") == "og:image":
            index = post.find('</ImageURL>')
            post = post[:index] + node.getAttribute("content") + post[index:]
            index = post.find('</ImageFeatured>')
            post = post[:index] + node.getAttribute("content") + post[index:]
            index = post.find('</_yoast_wpseo_opengraph-image>')
            post = post[:index] + node.getAttribute("content") + post[index:]
        # image title
        if node.getAttribute("property") == "og:image:alt":
            index = post.find('</ImageTitle>')
            post = post[:index] + node.getAttribute("content") + post[index:]
        # date modified
        if node.getAttribute("property") == "article:modified_time":
            index = post.find('</PostModifiedDate>')
            post = post[:index] + node.getAttribute("content")[:10] + post[index:]
        # _yoast_wpseo_metadesc, _yoast_wpseo_opengraph-description
        if node.getAttribute("name") == "description":
            index = post.find('</_yoast_wpseo_metadesc>')
            post = post[:index] + node.getAttribute("content")[:-15] + post[index:]
            index = post.find('</_yoast_wpseo_opengraph-description>')
            post = post[:index] + node.getAttribute("content")[:-15] + post[index:]

    # post type
    index = post.find('</PostType>')
    post = post[:index] + "post" + post[index:]

    # permalink
    index = post.find('</Permalink>')
    post = post[:index] + url + post[index:]

    # category
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

    # _yoast_wpseo_title, _yoast_wpseo_opengraph-title
    index = post.find('</_yoast_wpseo_title>')
    post = post[:index] + title + post[index:]
    index = post.find('</_yoast_wpseo_opengraph-title>')
    post = post[:index] + title + post[index:]

    with open("posts.xml", "a", encoding="UTF-8") as text_file:
        text_file.write("\n" + post)
    content_data = []


def get_content(root):
    global content_data
    global span_caption
    global span_author
    for node in root.childNodes:
        if node.nodeValue:
            # add class to quote, author and image caption
            if node.parentNode.localName == "span":
                if span_caption:
                    content_data.append(f"<{node.parentNode.localName} class=\"img-caption\">{node.nodeValue}</{node.parentNode.localName}>")
                    span_caption = False
                elif span_author:
                    content_data.append(f"<{node.parentNode.localName} class=\"quote-author\">{node.nodeValue}</{node.parentNode.localName}>")
                    span_author = False
                else:
                    content_data.append(f"<{node.parentNode.localName} class=\"post-quote\">{node.nodeValue}</{node.parentNode.localName}>")
                    span_author = True
            # add href to link
            elif node.parentNode.localName == "a":
                content_data.append(f"<{node.parentNode.localName} href=\"{node.parentNode.getAttribute('href')}\">{node.nodeValue}</{node.parentNode.localName}>")
            else:
                content_data.append(f"<{node.parentNode.localName}>{node.nodeValue}</{node.parentNode.localName}>")
        # extract content of 'p' element separately
        elif node.tagName and node.tagName == "p":
            content_data.append("<p>")
            for p_child in node.childNodes:
                if p_child.nodeValue:
                    content_data.append(f"{p_child.nodeValue}")
                else:
                    get_content(p_child)
            content_data.append("</p>")
            continue
        # add src and alt to image
        elif node.tagName == "img":
            content_data.append(f"<{node.tagName} src=\"{node.getAttribute('src')}\" alt=\"{node.getAttribute('alt')}\">")
            span_caption = True
        # repeat for each child node with child nodes
        if len(node.childNodes) > 0:
            get_content(node)
    return content_data
