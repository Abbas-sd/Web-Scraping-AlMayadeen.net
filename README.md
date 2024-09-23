Blame
webscraper
Al Mayadeen Article Scraper

Author
Name: Abbas safeydeen

Overview

This Python project is designed to scrape articles from the Al Mayadeen website and save it into a json files then store them into a database.After that we made a flaskAPI App that countains endpoints for the url that can retrieve data.Then we used amcharts for visualizing the data in a proper way.

in the task one folder a python script (web-scraping.py) is designed to extracts URLs from the website's sitemap, retrieves article URLs, and scrapes essential information from each article. The scraped data is stored in the articals folder.
in the articals folder also their is another script (Data_Storage.py) is responsible for storing the data into a mongodb database.

Features
The script is capable of scraping the following data from each article:

URL: The link to the article.
Post ID: A unique identifier for the article.
Title: The title of the article.
Keywords: Keywords associated with the article.
Thumbnail: The URL of the article's thumbnail image.
Publication Date: The date when the article was published.
Last Updated Date: The date when the article was last updated.
Author: The name of the article's author.
Full Article Text: The complete text content of the article.

How It Works
Sitemap Retrieval: The script first fetches all URLs from the main sitemap of the Al Mayadeen website.
Article URL Extraction: It retrieves the article URLs from the individual sitemap URLs.
Article Scraping: The script scrapes the necessary data for each article URL.
Data Storage: The scraped data is saved into a JSON files.

Configuration
Dependencies
requests: This is for making HTTP requests to fetch webpage content.
BeautifulSoup (bs4): For parsing and extracting data from HTML and XML documents.
JSON: For saving the scraped data in JSON format.
Usage
To run the script, simply execute it in your Python environment. The script will print the scraped data for each article to the console and save all the data in the articles.json file.

Example command to run the script:

python web-scarpping.py
Customization
Change the Number of Articles: Modify the value of __numberOfUrls to scrape a different number of articles. __numberOfUrls = 10000  # Change to the desired number of articles to scrape

Output
The output file articles.json will be saved in the same directory as the script. It contains the JSON representation of the scraped article data, formatted with indentation for readability.

Error Handling
The script includes basic error handling for HTTP requests. If an error occurs during the fetching of URLs or article content, an error message will be returned and printed to the console.

<<<<<<< HEAD
task two:
in folder task 2 we created API flask app that is connected to the database where are the data stored.
the libraries we used are:
logging
flask / Flask, jsonify, request
pymongo / MongoClient, errors
datetime / datetime, timedelta
flask_pymongo / PyMongo
flask_cors /CORS

this app contains more than 30 endpoints that you can see through it the collected data you want.
examples of endpoints:
1- /top_keywords: it retrieves the top 10 keywords are repeated in the article.
2- /top_authors: it retrieves the top 10 authors of the articles.
3- /articles_by_date: it retrieves how many articles are published at the dates.
4- /articles_by_word_count: it retrieves the numbers of words of the articles and how many times are repeated.
5- /articles_by_keyword/<keyword>: it retrieves the articles with specific keyword the user input.
6- /articles_by_author/<author_name>: it retrieves the articles with specific author the user input.
7- /article_details/<postid>: it retrieves the articles with specific postid the user input.
8- /articles_by_year/<year>: it retrieves the articles with specific date the user input.
9- /longest_articles: it retrieves the longest articles.
10- /shortest_articles: it retrieves the shortest articles.
11- /articles_with_thumbnail: it retrieves the articles that contains thumbnail.
12- /articles_by_language: it retrieves the  language of the written articles.
and more...

there is error handling for every possible error such as the user write somthing wrong or other things.


