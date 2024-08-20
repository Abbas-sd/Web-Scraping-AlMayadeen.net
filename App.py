from flask import Flask, jsonify, request
from pymongo import MongoClient, errors

app = Flask(__name__)

# Connect to MongoDB
try:
    client = MongoClient("mongodb://localhost:27017/")
    db = client["Almayadeen"]
    collection = db["Articles"]
except errors.ConnectionError as e:
    app.logger.error(f"Database connection failed: {e}")
    collection = None

@app.route('/', methods=['GET'])
def home():
    return "Welcome to the Al Mayadeen Article API."


# Route for getting top keywords
@app.route('/top_keywords', methods=['GET'])
def top_keywords():
    try:
        pipeline = [
            {"$unwind": "$keywords"},
            {"$group": {"_id": "$keywords", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 10}
        ]
        result = list(collection.aggregate(pipeline))
        return jsonify(result)
    except Exception as e:
        app.logger.error(f"Error fetching top keywords: {e}")
        return jsonify({"error": "An error occurred while processing your request."}), 500

# Route for getting top authors
@app.route('/top_authors', methods=['GET'])
def top_authors():
    try:
        pipeline = [
            {"$group": {"_id": "$author", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 10}
        ]
        result = list(collection.aggregate(pipeline))
        return jsonify(result)
    except Exception as e:
        app.logger.error(f"Error fetching top authors: {e}")
        return jsonify({"error": "An error occurred while processing your request."}), 500

# Route for getting articles by publication date
@app.route('/articles_by_date', methods=['GET'])
def articles_by_date():
    try:
        pipeline = [
            {"$addFields": {"published_time": {"$dateFromString": {"dateString": "$publication_date"}}}},
            {"$group": {"_id": {"$dateToString": {"format": "%Y-%m-%d", "date": "$published_time"}}, "count": {"$sum": 1}}},
            {"$sort": {"_id": 1}}
        ]
        result = list(collection.aggregate(pipeline))
        return jsonify(result)
    except Exception as e:
        app.logger.error(f"Error fetching articles by date: {e}")
        return jsonify({"error": "An error occurred while processing your request."}), 500

# Route for getting articles by word count
@app.route('/articles_by_word_count', methods=['GET'])
def articles_by_word_count():
    try:
        pipeline = [
            {"$group": {"_id": "$word_count", "count": {"$sum": 1}}},
            {"$sort": {"_id": 1}}
        ]
        result = list(collection.aggregate(pipeline))
        return jsonify(result)
    except Exception as e:
        app.logger.error(f"Error fetching articles by word count: {e}")
        return jsonify({"error": "An error occurred while processing your request."}), 500

# Route for getting articles by keyword
@app.route('/articles_by_keyword/<keyword>', methods=['GET'])
def articles_by_keyword(keyword):
    try:
        # Find articles containing the specific keyword and where full_text is not null
        query = {
            "keywords": keyword,
            "full_text": {"$ne": None}
        }
        projection = {"_id": 0, "title": 1, "url": 1, "publication_date": 1, "author": 1, "full_text": 1}
        articles = list(collection.find(query, projection))

        if not articles:
            return jsonify({"message": f"No articles found with keyword '{keyword}' and non-null full_text"}), 404

        return jsonify(articles)
    except Exception as e:
        app.logger.error(f"Error fetching articles with keyword '{keyword}': {e}")
        return jsonify({"error": "An error occurred while processing your request."}), 500

# Route for getting articles by author
@app.route('/articles_by_author/<author_name>', methods=['GET'])
def articles_by_author(author_name):
    try:
        # Find articles written by the specific author
        query = {"author": author_name}
        projection = {"_id": 0, "title": 1, "url": 1, "publication_date": 1, "author": 1, "full_text": 1}
        articles = list(collection.find(query, projection))

        if not articles:
            return jsonify({"message": f"No articles found for author '{author_name}'"}), 404

        return jsonify(articles)
    except Exception as e:
        app.logger.error(f"Error fetching articles by author '{author_name}': {e}")
        return jsonify({"error": "An error occurred while processing your request."}), 500

# Route for getting article details by postid
@app.route('/article_details/<postid>', methods=['GET'])
def article_details(postid):
    try:
        # Find the article with the specified postid
        query = {"post_id": postid}
        projection = {
            "_id": 0,
            "url": 1,
            "title": 1,
            "keywords": 1,
            "publication_date": 1,
            "author": 1,
            "full_text": 1
        }
        article = collection.find_one(query, projection)

        if not article:
            return jsonify({"message": f"No article found with postid '{postid}'"}), 404

        return jsonify(article)
    except Exception as e:
        app.logger.error(f"Error fetching article details for postid '{postid}': {e}")
        return jsonify({"error": "An error occurred while processing your request."}), 500


# Route for getting the number of articles by publication year
@app.route('/articles_by_year/<year>', methods=['GET'])
def articles_by_year(year):
    try:
        # Convert the year to a date range for querying
        start_date = f"{year}-01-01T00:00:00Z"
        end_date = f"{year}-12-31T23:59:59Z"

        # Query to find articles within the specified year
        query = {
            "publication_date": {
                "$gte": start_date,
                "$lte": end_date
            }
        }

        # Count the number of articles matching the query
        article_count = collection.count_documents(query)

        return jsonify({year: f"{article_count} articles"})
    except Exception as e:
        app.logger.error(f"Error fetching articles for the year '{year}': {e}")
        return jsonify({"error": "An error occurred while processing your request."}), 500


# Route for getting the top 10 longest articles by word count
@app.route('/longest_articles', methods=['GET'])
def longest_articles():
    try:
        # Pipeline to find the top 10 longest articles by word count
        pipeline = [
            {"$sort": {"word_count": -1}},  # Sort by word count in descending order
            {"$limit": 10},  # Limit to top 10 articles
            {
                "$project": {
                    "_id": 0,
                    "full_text": 1,
                    "word_count": 1
                }
            }
        ]

        result = list(collection.aggregate(pipeline))
        return jsonify(result)
    except Exception as e:
        app.logger.error(f"Error fetching longest articles: {e}")
        return jsonify({"error": "An error occurred while processing your request."}), 500


# Route for getting the top 10 shortest articles by word count
@app.route('/shortest_articles', methods=['GET'])
def shortest_articles():
    try:
        # Pipeline to get the top 10 shortest articles by word count
        pipeline = [
            {"$match": {"word_count": {"$gt": 0}, "full_text": {"$ne": ""}}},  # Exclude articles with empty or null full_text
            {"$sort": {"word_count": 1}},  # Sort by word count in ascending order
            {"$limit": 10},  # Limit to top 10
            {"$project": {"_id": 0, "full_text": 1, "word_count": 1}}  # Project full_text and word count
        ]

        result = list(collection.aggregate(pipeline))

        # Format the response for clarity
        formatted_result = [
            {"full_text": item["full_text"], "word_count": f"{item['word_count']} words"}
            for item in result
        ]

        return jsonify(formatted_result)
    except Exception as e:
        app.logger.error(f"Error fetching shortest articles: {e}")
        return jsonify({"error": "An error occurred while processing your request."}), 500

# Route for getting articles grouped by the number of keywords they contain
@app.route('/articles_by_keyword_count', methods=['GET'])
def articles_by_keyword_count():
    try:
        # Pipeline to group articles by the number of keywords
        pipeline = [
            {"$project": {"keyword_count": {"$size": "$keywords"}}},  # Add a field for the number of keywords
            {"$group": {"_id": "$keyword_count", "count": {"$sum": 1}}},  # Group by keyword count and sum articles
            {"$sort": {"_id": 1}}  # Sort by the number of keywords in ascending order
        ]

        result = list(collection.aggregate(pipeline))

        # Format the response for clarity
        formatted_result = [
            {"keyword_count": f"{item['_id']} keywords", "article_count": f"{item['count']} articles"}
            for item in result
        ]

        return jsonify(formatted_result)
    except Exception as e:
        app.logger.error(f"Error fetching articles by keyword count: {e}")
        return jsonify({"error": "An error occurred while processing your request."}), 500


# Route for getting articles with a thumbnail image
@app.route('/articles_with_thumbnail', methods=['GET'])
def articles_with_thumbnail():
    try:
        # Query to find articles with a non-empty thumbnail field that contains a valid image URL
        query = {
            "thumbnail": {"$regex": r"https?://.*\.(jpg|jpeg|png|gif|bmp|webp)(\?.*)?$"}
        }
        projection = {"_id": 0, "title": 1, "thumbnail": 1}

        # Fetch matching articles
        result = list(collection.find(query, projection))

        # Format the response to show titles with their corresponding thumbnail URLs
        formatted_result = [
            {"title": item["title"], "thumbnail": item["thumbnail"]}
            for item in result
        ]

        return jsonify(formatted_result)
    except Exception as e:
        app.logger.error(f"Error fetching articles with thumbnails: {e}")
        return jsonify({"error": "An error occurred while processing your request."}), 500


if __name__ == '__main__':
    app.run(debug=True)