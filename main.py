"""
Title  : Data Collection and Cleaning Coursework
Author : Atharva Tidke
"""
import time
import string
import warnings
import itertools
import requests 
import numpy as np
import pandas as pd
import seaborn as sns
from bs4 import BeautifulSoup
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_distances
from add_data import download_add_data

warnings.filterwarnings(action = 'ignore')


# ------------------------------------------------------------------------------------------------------
#  Setup
# ------------------------------------------------------------------------------------------------------
def read_keywords():
    try:
        keywords = pd.read_excel('keywords.xlsx')['Keywords']
    except Exception as e:
        print("Following exception occurred while reading keywords.xlsx\n", e)
        exit()
    else:
        keywords = [keyword.lower() for keyword in keywords]
        return keywords


# ------------------------------------------------------------------------------------------------------
#  Problem 1. Finding relevent articles
# ------------------------------------------------------------------------------------------------------
def search_articles(keyword):
    """
        Search for articles related to `keyword` on BBC News
    """
    search_url = "https://www.bbc.co.uk/search"
    article_links = []
    page_num = 1
    keepSearching = True
    while keepSearching:
        current_count = len(article_links)
        response = requests.get(search_url, {"q": keyword, "page" : page_num})
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, features="html.parser")
            links = soup.find_all("a", href=True)
            for link in links:
                class_name = link.get('class')
                if class_name is not None and 'PromoLink' in class_name[0] and '/news/' in link['href']:
                    article_links.append(link['href'])  
            # If no new links were added stop searching
            if len(article_links) == current_count or len(article_links) > 100:
                keepSearching = False
        else:
            print("Request failed")
            break
        
        page_num += 1

    return article_links


# ------------------------------------------------------------------------------------------------------
#  Problem 2. Scraping and saving useful information from webpages
# ------------------------------------------------------------------------------------------------------
def clean_text(text):
    """
        Returns cleaned provided text by removing punctuation and any characters that are 
        not alpha numeric and then converting it to lowercase
    """
    table = str.maketrans('', '', string.punctuation)
    words = [word.translate(table).lower() for word in text.split() if word.isalpha()]
    return ' '.join(words)


def get_article_text(link):
    """
        Scrapes and returns the cleaned article text of the given link
    """
    response = requests.get(link)
    article_text = ''
    if response.status_code == 200: 
        try:
            soup = BeautifulSoup(response.text, features="html.parser")
            text = soup.find("article").get_text(separator=" ")
        except:
            pass
        else:
            heading = soup.find(id="main-heading")
            heading = heading.get_text().lower() if heading is not None else ''
            article_text = heading + ' ' + text.lower()
            article_text = clean_text(article_text)  
    else:
        print(f"Filed to get {link}")
    
    return article_text

# ------------------------------------------------------------------------------------------------------
# Problem 1 and 2 combined - the following function first collects the links of articles that are 
# relevent to the given list of keywords (as required for Prob 1) and then downloads and saves the 
# useful data from these articles in 'bbc_article_data.csv' (as required for Prob 2)
# ------------------------------------------------------------------------------------------------------
def download_BBC_news(keywords):
    """
    Download the top 100 articles related to the given list of keywords from BBC News
    """
    print("Downloading news articles from BBC News")
    with open('bbc_article_data.csv', 'w', encoding='utf-8') as f:
        f.write(f"keyword,article_url,article_content\n")
        for i, keyword in enumerate(keywords):
            print(f"({i+1}/{len(keywords)}) Searching for news articles with the keyword '{keyword}'")
            article_links = search_articles(keyword)
            if article_links:
                print(f"\tFound {len(article_links)} results\n\tDownloading found articles")
                for link in article_links:
                    article_text = get_article_text(link)
                    if article_text != '':
                        f.write(f"{keyword},{link},{article_text}\n")
            else:
                print(f"No news articles relating to {keyword} were found.")
        print("Completed\n")


# ------------------------------------------------------------------------------------------------------
#  Problem 3. Calculate semantic distance between keywords
# ------------------------------------------------------------------------------------------------------
def vectorise(data):
    """
    Convert a list of strings into a TF-IDF vector
    """
    stopwords = []
    with open('stopwords.txt', 'r', encoding='utf-8') as f:
        stopwords = list(set(f.read().splitlines()))

    vectorizer = TfidfVectorizer(stop_words=stopwords, use_idf=True)
    return vectorizer.fit_transform(data).toarray()


def calc_cosine_dist(vector):
    """
    Calculate the cosine distance between the given list of vectors
    """
    vectorised = vectorise(vector)
    return pd.DataFrame(
        data=cosine_distances(vectorised), 
        index=keywords, 
        columns=keywords
    )


# ------------------------------------------------------------------------------------------------------
#  Problem 4. Visualise the semantic distance between keywords
# ------------------------------------------------------------------------------------------------------
def plot_heatmap(df, title):
    """
    Plot given dataframe as a heatmap
    """
    now = time.strftime("%Y%m%d-%H%M%S")
    with sns.axes_style("white"):
        heatmap = sns.heatmap(df,
            xticklabels=df.columns, yticklabels=df.columns,
            annot=True, fmt=".2f", linewidths=0, 
            cmap=sns.color_palette("flare", as_cmap=True))
        heatmap.set_title(title, y=1.05)
        heatmap.get_figure().savefig(f'plot_{now}.png', bbox_inches="tight", dpi=300)


# ------------------------------------------------------------------------------------------------------
#    Running this script
# ------------------------------------------------------------------------------------------------------
choice_msg = [
    "Would you like to search and download articles from BBC?\n(Answer no if already downloaded)",
    "Would you like to download additional data from Hacker News?\n(Answer no if already downloaded)",
    "Would you like to use additional data to calculate semantic distance between keywords?"
]


def choice(question):
    print('\n' + question)
    choice = input("[y/n] ").strip().lower()
    if choice == 'y':
        return True
    else:
        return False


if __name__ == "__main__":
    ## 0. Read list of keywords
    print("\nReading keywords")
    keywords = read_keywords()
    print("Successfully read following keywords:\n", '- ' + '\n - '.join(keywords))

    ## Problem 1/2
    if choice(choice_msg[0]):
        download_BBC_news(keywords)
    
    if choice(choice_msg[1]):
        # num_articles specifies how many articles to download for each keyword
        download_add_data(keywords, num_articles=100)

    ## Problem 3
    print("\nProcessing saved data")
    try:
        bbc_data_df = pd.read_csv("bbc_article_data.csv")
    except Exception as e:
        print("\nFollowing exception occurred while reading bbc_article_data.csv\n", e)
        print("Check if 'bbc_article_data.csv' exists in the current folder.\
            Otherwise, rerun the script and answer yes when asked to download data from BBC News.")
        exit()
    
    # Group the saved articles in data files by keywords and combine all articles relating to 
    # a keyword into a single string => bbc_data and add_data will contain len(keywords) strings 
    # each, where each string is a concatnation of articles relating to a particular keyword.
    bbc_data, add_data = [], []
    for keyword in keywords:
        bbc_data += [' '.join(bbc_data_df.loc[bbc_data_df.keyword == keyword, 'article_content'].tolist())]
    print("BBC news data successfully loaded and processed")
    
    if choice(choice_msg[2]): 
        try:   
            add_data_df = pd.read_csv("add_data.csv")
        except Exception as e:
            print("\nFollowing exception occurred while reading saved additional data\n", e)
            print("Falling back to using data downloaded from BBC only")
            add_data = []
        else: 
            for keyword in keywords:
                add_data += [' '.join(
                    add_data_df.loc[add_data_df.keyword == keyword, 'article_content'].tolist())]
            print("Additional data successfully loaded and processed")
    
    print("\nCalculating semantic distance between keywords")
    # Calculate cosine distance of processed saved data - First combine the data obtained from BBC News
    # with additional data obtained from Hacker News (stored in combined_data). Then, calculate the 
    # pairwise cosine distance between the 10 strings (each of which relates to a specific keyword)
    # and save it in 'distances.xlsx'
    dist = None 
    if add_data:
        combined_data = [x + y for x,y in zip(bbc_data, add_data)]
        dist = calc_cosine_dist(combined_data)
    else:
        dist = calc_cosine_dist(bbc_data)
    dist.to_excel("distances.xlsx")
    print("Results saved to distances.xlsx")


    # 4. Visualise the distance between keywords
    print("\nPlotting the semantic distance as a heatmap")
    plot_heatmap(dist, "Semantic Distance of Keywords")
    print("Plot saved\nFinished.\n")
