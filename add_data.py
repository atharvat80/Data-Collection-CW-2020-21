"""
Title  : Data Collection and Cleaning Coursework
Author : htrf88
"""

import requests, string
from bs4 import BeautifulSoup


def clean_text(text):
    table = str.maketrans('', '', string.punctuation)
    words = [word.translate(table).lower() for word in text.split() if word.isalpha()]
    return ' '.join(words)


def get_article_text(url):
    res = requests.get(url)
    text = ''
    if res.status_code == 200:
        soup = BeautifulSoup(res.text, features="html.parser")
        for s in soup.select('a'):
            s.extract()
        try:
            text = soup.find("article").get_text(separator=" ").lower()
        except:
            pass
        else:
            text = clean_text(text)

    return text


def get_articles(keyword, num_articles):
    article_links = []
    page = 0
    search_url = "https://hndex.org/"
    while page < (num_articles//10):
        res = requests.get(search_url, {"q": keyword, "page": page})
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, features="html.parser")
            cached_article_links = soup.find_all("a", href=True)[1:-1]
            for i in range(2, len(cached_article_links), 3):
                article_links.append(search_url[:-1] + cached_article_links[i]['href'])
            page += 1
        else:
            break

    return article_links


def download_add_data(keywords, num_articles=100):
    data_file = open("add_data.csv", "w", encoding="utf-8")
    data_file.write(f"keyword,article_url,article_content\n")
    
    try:
        article_links = {}
        print("\nSearching and downloading additional data, press ctrl + c to stop.")
        for i, keyword in enumerate(keywords):
            print(f"({i+1}/{len(keywords)}) Searching for news articles with the keyword '{keyword}'")
            article_links = get_articles(keyword, num_articles)  
            print(f"\tFound {len(article_links)} articles\n\tDownloading found articles")
            for link in article_links:
                article_text = get_article_text(link)
                if article_text != '':
                    data_file.write(f"{keyword},{link},{article_text}\n")
  
    except KeyboardInterrupt:
        print("Operation interupped via keyboard interrupt")
        data_file.close()
    
    else:
        print("Additional data downloaded and saved to add_data.csv")
        data_file.close()

