from pymongo import MongoClient
import json
import os

# Connect to MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client["AlMayadeen"]
collection = db["articles"]

# Path to JSON files
json_files = [
    'articles_2024_01.json',
    'articles_2024_02.json',
    'articles_2024_03.json',
    'articles_2024_04.json',
    'articles_2024_05.json',
    'articles_2024_06.json',
    'articles_2024_07.json',
    # Add more files if needed
]

for file in json_files:
    with open(file, 'r', encoding='utf-8') as f:
        articles = json.load(f)

        for article in articles:
            # Extract the word count
            full_text = article.get('full_text', '')
            word_count = len(full_text.split())

            # Update or insert the document
            collection.update_one(
                  {'post_id': article['post_id']},
                {
                    '$set': {
                        'word_count': word_count
                    }
                },
                upsert=True
            )
