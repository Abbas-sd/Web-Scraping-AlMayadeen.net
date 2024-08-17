from dataclasses import dataclass
from typing import List, Optional
import requests
from bs4 import BeautifulSoup
import json

# Step 1: Define the Data Model
@dataclass
class Article:
    url: str
    post_id: str
    title: str
    keywords: List[str]
    thumbnail: str
    publication_date: str
    last_updated_date: Optional[str]
    author: Optional[str]
    full_text: str
    article_type: str


# Step 2: Implement the Sitemap Parser
class SitemapParser:
    def __init__(self, sitemap_url: str):
        self.sitemap_url = sitemap_url

    def get_article_urls(self) -> List[str]:
        response = requests.get(self.sitemap_url)
        soup = BeautifulSoup(response.content, 'xml')
        return [loc.text for loc in soup.find_all('loc')]


# Step 3: Implement the Article Scraper
class ArticleScraper:
    def scrape_article(self, url: str) -> Optional[Article]:
        response = requests.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')

        # Extract metadata from the <script> tag with type=text/tawsiyat
        metadata_script = soup.find('script', type='text/tawsiyat')
        metadata = json.loads(metadata_script.string) if metadata_script else {}

        # Filter for articles where type is "article"
        if metadata.get('type') != 'article':
            return None

        # Extract article content from <p> tags
        '''
        paragraphs = soup.find_all('p')
        full_text = "\n".join([p.get_text() for p in paragraphs])
        '''
        '''
        # Target the main content div, this will depend on the page structure
        article_div = soup.find('div', {'class': 'p-content'})  # Adjust class based on actual site

        # Extract paragraphs within this div
        paragraphs = article_div.find_all('p')
        full_text = '\n'.join([para.get_text() for para in paragraphs])
        '''

        # Target the first div with either class 'p-content' or 'lg_para summary'
        article_div = soup.select_one('div.p-content, div.lg_para summary, lg_para')

        if article_div:
            # Extract paragraphs within this div
            paragraphs = article_div.find_all('p')
            full_text = '\n'.join([para.get_text() for para in paragraphs])
        else:
            full_text = ''

        # Creating an Article instance with extracted data
        return Article(
            url=url,
            post_id=metadata.get('postid', ''),
            title=metadata.get('title', ''),
            keywords=metadata.get('keywords', '').split(','),
            thumbnail=metadata.get('thumbnail', ''),
            publication_date=metadata.get('published_time', ''),
            last_updated_date=metadata.get('last_updated', ''),
            author=metadata.get('author', ''),
            full_text=full_text,
            article_type=metadata.get('type', '')
        )


# Step 4: Implement the File Utility
class FileUtility:
    def save_to_json(self, articles: List[Article], year: str, month: str):
        data = [article.__dict__ for article in articles if article]
        filename = f'articles_{year}_{month}.json'
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)


# Step 5: Main Script
def main():
    sitemap_url = 'https://www.almayadeen.net/sitemaps/all/sitemap-2024-7.xml'
    sitemap_parser = SitemapParser(sitemap_url)

    article_urls = sitemap_parser.get_article_urls()

    articles = []
    scraper = ArticleScraper()

    for url in article_urls:
        try:
            article = scraper.scrape_article(url)
            if article:
                articles.append(article)
        except Exception as e:
            print(f"Error scraping {url}: {e}")

    file_utility = FileUtility()
    file_utility.save_to_json(articles, year='2024', month='07')


if __name__ == "__main__":
    main()