from transformers import pipeline
from pymongo import MongoClient

# Load the sentiment analysis pipeline using the CAMeLBERT-DA SA model
try:
    sa_pipeline = pipeline('text-classification', model='CAMeL-Lab/bert-base-arabic-camelbert-da-sentiment')
except Exception as e:
    print(f"Error loading model: {e}")
    sa_pipeline = None  # Set to None or handle as needed

# Connect to MongoDB
try:
    client = MongoClient('mongodb://localhost:27017/')
    db = client['Almayadeen-NPL']
    collection = db['Articles']
except Exception as e:
    print(f"Error connecting to MongoDB: {e}")

# Function to analyze sentiment using CAMeLBERT-DA and return the sentiment and score
def analyze_sentiment_camelbert(full_text):
    if sa_pipeline is None:
        print("Sentiment analysis pipeline not loaded.")
        return None

    try:
        # Use the pipeline to get the sentiment analysis
        results = sa_pipeline(full_text)

        # Extract the label and score
        sentiment_label = results[0]['label']
        sentiment_score = results[0]['score']

        sentiment_data = {
            'sentiment': sentiment_label,
            'sentiment_score': float(sentiment_score)
        }
        return sentiment_data
    except Exception as e:
        print(f"Error analyzing sentiment: {e}")
        return None

# Fetch all articles from the collection
articles = collection.find()

# Iterate over the articles and analyze sentiment for those with non-empty full_text
for article in articles:
    full_text = article.get('full_text', '').strip()
    if full_text:  # Only analyze if full_text is not empty
        sentiment_data = analyze_sentiment_camelbert(full_text)
        if sentiment_data:
            try:
                # Update the article document with sentiment data
                collection.update_one(
                    {'_id': article['_id']},
                    {'$set': {'sentiment': sentiment_data['sentiment'], 'sentiment_score': sentiment_data['sentiment_score']}}
                )
                print(f"Updated article ID {article['_id']} with sentiment data.")
            except Exception as e:
                print(f"Error updating article {article['_id']}: {e}")
    else:
        print(f"Skipping article ID {article['_id']} due to empty full_text.")
