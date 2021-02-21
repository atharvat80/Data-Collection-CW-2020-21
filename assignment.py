import os
import re
import json
import requests
import pandas as pd
from bs4 import BeautifulSoup

def inverted_index(text):
    text = text.split(" ")
    inverted = {}
    for word in set(text):
        inverted[word] = []
    for i in range(len(text)):
        inverted[text[i]].append(i)
    del inverted[""]
    return inverted


def search_articles(keyword):
    search_url = "https://www.bbc.co.uk/search"
    article_links = []
    page_num = 1
    while len(article_links) < 100:
        # Remember the current number of article links found so if no new additions are made, stop searching.
        current_count = len(article_links)
        # Get and parse search results
        parameters = {"q": keyword, "page" : page_num}
        response = requests.get(search_url, parameters)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, features="html.parser")
            results = soup.find_all("a", {"class": "ssrcss-vh7bxp-PromoLink"}, href=True)
            # Check if there are more than 0 results
            if results:
                # Extract article links
                for result in results:
                    if 'news' in result['href'] and len(article_links) < 100:
                        article_links.append(result['href'])
                # Now search on the next page
                if len(article_links) > current_count:
                    page_num += 1
                else:
                    break   
            else:
                break
        else:
            print("Request failed")
            break
    
    return article_links


def download_articles(keyword, article_links):
    keyword_nospace = keyword.replace(' ', '_')
    # Create a folder (if it doesn't exist) to save the articles
    if not(os.path.exists(keyword_nospace)):
        os.mkdir(keyword_nospace)
    article_dir = os.path.join(os.path.dirname(__file__), keyword_nospace)
    
    # Loop over article links extract useful information and save it
    for i in range(len(article_links)):
        response = requests.get(article_links[i])
        if response.status_code == 200: 
            file_name = f"{keyword_nospace}_{i+1}.json"
            file_path = os.path.join(article_dir, file_name)
            with open(file_path, "w", encoding="utf-8") as f:
                soup = BeautifulSoup(response.text, features="html.parser")
                # Remove unwanted tags
                for tag in ['section', 'figure', 'header', 'ul']: 
                    for s in soup.select(tag):
                        s.extract()
                article_text = soup.find("article").get_text(separator="\n")
                article_text = article_text.lower()
                article_text = re.sub('[^A-Za-z0-9 .]+', '', article_text)
                article_text = re.sub('[.]+', ' ', article_text)
                json.dump(inverted_index(article_text), f)       
        else:
            print(f"Filed to get {article_links[i]}")
        
        break ## remove this later
    print(f"\tArticles saved in {article_dir}")


def keyword_proximity():
    ...


keywords = ['DDoS'] #pd.read_excel('keywords.xlsx')['Keywords']
for keyword in keywords:
    print(f"Searching for news articles relating to {keyword}")
    article_links = search_articles(keyword)
    if article_links:
        print(f"\tFound {len(article_links)} results\n\tDownloading found articles")
        download_articles(keyword, article_links)
    else:
        print(f"No news articles relating to {keyword} were found.")
