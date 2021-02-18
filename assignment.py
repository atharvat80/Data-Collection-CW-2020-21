
# %%
import os
import requests
from bs4 import BeautifulSoup

# %%
## Problem 1
url = "https://www.bbc.co.uk/search"
keyword = "Advanced Persistent Threat"
articles = []
page_num = 1
keepSearching = True

#%%
print(f"Searching for new articles with keyword {keyword}...")
while len(articles) < 100 and keepSearching:
    # Remember the current number of articles found so if no new additions are made, stop searching.
    current_count = len(articles)
    
    # Make a GET request
    parameters = {"q": keyword, "page" : page_num}
    response = requests.get(url, parameters)
    
    # Parse the response
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, features="html.parser")
        results = soup.find_all("a", {"class": "ssrcss-vh7bxp-PromoLink"}, href=True)

        if results:
            # Extract article title and links
            for result in results:
                title = result.find('span').text
                link = result['href']
                if 'news' in link and len(articles) < 100:
                    articles.append({"title": title, "link": link})
            
            # Now search on the next page
            if len(articles) > current_count:
                page_num += 1
            else:
                keepSearching = False
                print(f"Found {len(articles)} news articles {keyword} in total.")
        
        else:
            print(f"No results for {keyword}")
            keepSearching = False
    
    else:
        print("Request failed")

#%%
# Download article content
# if articles:
#     print("Downloading the found news articles")
#     Path("/my/directory").mkdir(parents=True, exist_ok=True)

#%%
if not(os.path.exists(keyword)):
    os.mkdir(keyword)
# %%
