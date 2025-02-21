import logging
from flask import Flask, jsonify, request
from pymongo import MongoClient, errors
from datetime import datetime, timedelta
from flask_pymongo import PyMongo
from flask_cors import CORS
import re
from bson import ObjectId
from collections import Counter
import pytz

app = Flask(__name__)
CORS(app)
# Configure MongoDB URI
app.config['MONGO_URI'] = 'mongodb://localhost:27017/Mama'

mongo = PyMongo(app)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
# Connect to MongoDB
try:
    client = MongoClient("mongodb://localhost:27017/")
    db = client["Almayadeen-NPL"]
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
            {"$match": {"word_count": {"$ne": ""}}},  # Ensure word_count is not an empty string
            {
                "$addFields": {
                    "word_count_int": {"$toInt": "$word_count"}  # Convert word_count to an integer
                }
            },
            {"$match": {"word_count_int": {"$gt": 0}}},  # Filter articles with word_count greater than 0
            {"$group": {"_id": "$word_count_int", "count": {"$sum": 1}}},  # Group by the integer word_count
            {"$sort": {"_id": 1}}  # Sort by word_count
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
    # Step 1: Update existing records to convert `word_count` to integer
    result = collection.update_many(
        {"word_count": {"$type": "string"}},
        [{"$set": {"word_count": {"$toInt": "$word_count"}}}]
    )


    # Step 2: Query to get the top 10 longest articles
    pipeline = [
        {"$addFields": {"word_count": {"$toInt": "$word_count"}}},  # Ensure `word_count` is an integer
        {"$sort": {"word_count": -1}},  # Sort by `word_count` in descending order
        {"$limit": 10},  # Limit to the top 10 articles
        {"$project": {
            "_id": 0,
            "full_text": 1,
            "post_id": 1,
            "author": 1,
            "word_count": 1
        }}
    ]

    articles = list(collection.aggregate(pipeline))

    return jsonify(articles)
# Route for getting the top 10 shortest articles by word count
@app.route('/shortest_articles', methods=['GET'])
def shortest_articles():
    pipeline = [
        # Exclude articles with empty full_text
        {"$match": {"full_text": {"$ne": ""}}},
        # Convert word_count from string to integer
        {"$addFields": {"word_count_int": {"$toInt": "$word_count"}}},
        # Sort by word_count_int in ascending order
        {"$sort": {"word_count_int": 1}},
        # Limit to top 10 results
        {"$limit": 10},
        # Project only the fields you want in the response
        {"$project": {"_id": 0, "post_id": 1, "author": 1, "full_text": 1, "word_count": 1}}
    ]

    results = list(collection.aggregate(pipeline))
    return jsonify(results)
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
        projection = {"_id": 0, "full_text": 1, "thumbnail": 1}

        # Fetch matching articles
        result = list(collection.find(query, projection))

        # Format the response to show full_text with their corresponding thumbnail URLs
        formatted_result = [
            {"full_text": item["full_text"], "thumbnail": item["thumbnail"]}
            for item in result
        ]

        return jsonify(formatted_result)
    except Exception as e:
        app.logger.error(f"Error fetching articles with thumbnails: {e}")
        return jsonify({"error": "An error occurred while processing your request."}), 500

@app.route('/articles_by_language', methods=['GET'])
def articles_by_language():
    try:
        # Pipeline to group articles by language and count the number of articles in each language
        pipeline = [
            {"$group": {"_id": "$lang", "article_count": {"$sum": 1}}},
            {"$sort": {"article_count": -1}}  # Sort by article count in descending order
        ]

        result = list(collection.aggregate(pipeline))

        # Format the response to be more descriptive
        formatted_result = [
            f"{item['_id']} ({item['article_count']} articles)"
            for item in result
        ]

        return jsonify(formatted_result)
    except Exception as e:
        app.logger.error(f"Error fetching articles by language: {e}")
        return jsonify({"error": "An error occurred while processing your request."}), 500
@app.route('/articles_by_classes', methods=['GET'])
def articles_by_classes():
    try:
        # Pipeline to count articles by class where key is 'class2'
        pipeline = [
            {"$unwind": "$classes"},  # Unwind the classes array
            {"$match": {"classes.key": "class2"}},  # Match only documents where the key is 'class2'
            {"$group": {
                "_id": "$classes.value",  # Group by the 'value' field in classes where key is 'class2'
                "article_count": {"$sum": 1}  # Count the number of articles in each class
            }},
            {"$sort": {"article_count": -1}},  # Sort by the article count in descending order
            {"$project": {
                "_id": 0,  # Exclude the _id field from the results
                "class": "$_id",  # Rename the grouped field to 'class'
                "article_count": {"$concat": [{"$toString": "$article_count"}, " articles"]}  # Format article count
            }}
        ]

        result = list(collection.aggregate(pipeline))

        return jsonify(result)
    except Exception as e:
        app.logger.error(f"Error fetching articles by class: {e}")
        return jsonify({"error": "An error occurred while processing your request."}), 500

@app.route('/recent_articles', methods=['GET'])
def recent_articles():
    try:
        # Pipeline to get the 10 most recent articles based on the publication date
        pipeline = [
            {"$sort": {"publication_date": -1}},  # Sort by publication date in descending order
            {"$limit": 10},  # Limit to the top 10
            {"$project": {"_id": 0, "title": 1, "publication_date": 1}}  # Project title and publication date
        ]

        result = list(collection.aggregate(pipeline))

        # Format the response to show titles with their corresponding publication dates
        formatted_result = [
            {
                "title": item["title"],
                "publication_date": format_publication_date(item["publication_date"])
            }
            for item in result
        ]

        return jsonify(formatted_result)
    except Exception as e:
        app.logger.error(f"Error fetching recent articles: {e}")
        return jsonify({"error": "An error occurred while processing your request."}), 500

def format_publication_date(pub_date):
    """Helper function to format the publication date for readability."""
    date_obj = datetime.strptime(pub_date, "%Y-%m-%dT%H:%M:%S%z")
    return date_obj.strftime("%B %d, %Y")  # Example format: "August 19, 2024"

@app.route('/top_classes', methods=['GET'])
def top_classes():
    try:
        # Pipeline to get the top 10 most frequent classes
        pipeline = [
            {"$unwind": "$classes"},  # Unwind the classes array to consider each class individually
            {"$group": {
                "_id": "$classes.value",  # Group by the class value
                "class_count": {"$sum": 1}  # Count the occurrences of each class
            }},
            {"$sort": {"class_count": -1}},  # Sort by count in descending order
            {"$limit": 10},  # Limit to top 10
            {"$project": {"_id": 0, "class": "$_id", "class_count": 1}}  # Project class and its count
        ]

        result = list(collection.aggregate(pipeline))

        # Format the response for clarity
        formatted_result = [
            {"class": item["class"], "class_count": f"{item['class_count']} occurrences"}
            for item in result
        ]

        return jsonify(formatted_result)
    except Exception as e:
        app.logger.error(f"Error fetching top classes: {e}")
        return jsonify({"error": "An error occurred while processing your request."}), 500

@app.route('/articles_with_video', methods=['GET'])
def articles_with_video():
    try:
        # Query to find articles where video_duration is not null
        query = {"video_duration": {"$ne": None}}
        projection = {"_id": 0, "title": 1, "video_duration": 1}

        # Fetch matching articles
        result = list(collection.find(query, projection))

        # Format the response to show titles with their corresponding video duration
        formatted_result = [
            {"title": item["title"], "video_duration": f"{item['video_duration']} seconds"}
            for item in result
        ]

        return jsonify(formatted_result)
    except Exception as e:
        app.logger.error(f"Error fetching articles with video: {e}")
        return jsonify({"error": "An error occurred while processing your request."}), 500

@app.route('/articles_updated_after_publication', methods=['GET'])
def articles_updated_after_publication():
    try:
        # Query to find articles where last_updated_date is after publication_date
        query = {
            "$expr": {
                "$gt": ["$last_updated_date", "$publication_date"]
            }
        }
        projection = {"_id": 0, "title": 1, "publication_date": 1, "last_updated_date": 1}

        # Fetch matching articles
        result = list(collection.find(query, projection))

        # Format the response to show titles with their publication and last updated dates
        formatted_result = [
            {
                "title": item["title"],
                "publication_date": item["publication_date"],
                "last_updated_date": item["last_updated_date"]
            }
            for item in result
        ]

        return jsonify(formatted_result)
    except Exception as e:
        app.logger.error(f"Error fetching articles updated after publication: {e}")
        return jsonify({"error": "An error occurred while processing your request."}), 500


@app.route('/articles_by_coverage/<coverage>', methods=['GET'])
def articles_by_coverage(coverage):
    pipeline = [
        {"$match": {"classes.key": "class5", "classes.value": coverage}},
        {"$project": {
            "full_text": 1,
            "post_id": 1,
            "author": 1,
            "_id": {"$toString": "$_id"}
        }}
    ]

    try:
        articles = list(collection.aggregate(pipeline))
        return jsonify(articles)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/popular_keywords_last_X_days/<int:X>', methods=['GET'])
def popular_keywords_last_X_days(X):
    try:
        # Calculate the datetime X days ago from now
        current_time = datetime.utcnow()
        X_days_ago = current_time - timedelta(days=X)

        logger.info(f"Fetching popular keywords from the last {X} days.")
        logger.debug(f"Current UTC time: {current_time}")
        logger.debug(f"Datetime {X} days ago: {X_days_ago}")

        # MongoDB Aggregation Pipeline
        pipeline = [
            {
                '$addFields': {
                    'publication_date_parsed': {
                        '$dateFromString': {
                            'dateString': '$publication_date',
                            'onError': None,
                            'onNull': None
                        }
                    }
                }
            },
            {
                '$match': {
                    'publication_date_parsed': {
                        '$gte': X_days_ago
                    }
                }
            },
            {
                '$unwind': '$keywords'
            },
            {
                '$group': {
                    '_id': '$keywords',
                    'count': {'$sum': 1}
                }
            },
            {
                '$sort': {'count': -1}
            },
            # Optional: Limit to top N keywords
            # {'$limit': 10}
        ]

        # Execute the aggregation pipeline
        results = list(collection.aggregate(pipeline))

        logger.debug(f"Aggregation results: {results}")

        # Format the response
        response = [
            {'keyword': result['_id'], 'count': result['count']}
            for result in results
        ]

        logger.info(f"Found {len(response)} keywords.")

        return jsonify(response), 200

    except Exception as e:
        logger.error(f"Error occurred: {e}", exc_info=True)
        return jsonify({'error': 'An error occurred while processing your request.'}), 500
@app.route('/articles_by_month/<int:year>/<int:month>', methods=['GET'])
def articles_by_month(year, month):
    try:
        # Validate month and year
        if month < 1 or month > 12:
            return jsonify({"error": "Invalid month. It should be between 1 and 12."}), 400

        # Pipeline to aggregate articles by month and year
        pipeline = [
            {
                "$match": {
                    "publication_date": {
                        "$gte": f"{year}-{month:02d}-01T00:00:00+03:00",
                        "$lt": f"{year}-{month + 1:02d}-01T00:00:00+03:00"
                    }
                }
            },
            {
                "$count": "total_articles"
            }
        ]

        result = list(collection.aggregate(pipeline))
        total_articles = result[0]['total_articles'] if result else 0

        # Format the response
        month_name = ["January", "February", "March", "April", "May", "June",
                      "July", "August", "September", "October", "November", "December"][month - 1]
        formatted_result = {
            "month": f"{month_name} {year}",
            "article_count": f"{total_articles} articles"
        }

        return jsonify(formatted_result)
    except Exception as e:
        app.logger.error(f"Error fetching articles by month: {e}")
        return jsonify({"error": "An error occurred while processing your request."}), 500


@app.route('/articles_by_word_count_range/<int:min_word_count>/<int:max_word_count>', methods=['GET'])
def articles_by_word_count_range(min_word_count, max_word_count):
    try:
        # Ensure valid range
        if min_word_count < 0 or max_word_count < min_word_count:
            return jsonify({"error": "Invalid word count range."}), 400

        # Pipeline to filter articles by word count range
        pipeline = [
            {
                "$match": {
                    "word_count": {
                        "$gte": min_word_count,  # Minimum word count
                        "$lte": max_word_count   # Maximum word count
                    }
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "title": 1,
                    "word_count": 1
                }
            }
        ]

        result = list(collection.aggregate(pipeline))

        # Format the result
        formatted_result = [
            {
                "title": item["title"],
                "word_count": f"{item['word_count']} words"
            }
            for item in result
        ]

        return jsonify({
            "range": f"Articles between {min_word_count} and {max_word_count} words",
            "count": len(formatted_result),
            "articles": formatted_result
        })
    except Exception as e:
        app.logger.error(f"Error fetching articles by word count range: {e}")
        return jsonify({"error": "An error occurred while processing your request."}), 500

@app.route('/articles_with_specific_keyword_count/<int:count>', methods=['GET'])
def articles_with_specific_keyword_count(count):
    try:
        # Ensure valid keyword count
        if count < 0:
            return jsonify({"error": "Invalid keyword count."}), 400

        # Pipeline to filter by specific keyword count
        pipeline = [
            {
                "$match": {
                    "$expr": {
                        "$eq": [{ "$size": "$keywords" }, count]  # Match documents with the exact number of keywords
                    }
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "title": 1,
                    "keywords": 1
                }
            }
        ]

        result = list(collection.aggregate(pipeline))

        # Format the result
        formatted_result = [
            {
                "title": item["title"],
                "keyword_count": len(item["keywords"])
            }
            for item in result
        ]

        return jsonify({
            "count": len(formatted_result),
            "articles": formatted_result
        })
    except Exception as e:
        app.logger.error(f"Error fetching articles with specific keyword count: {e}")
        return jsonify({"error": "An error occurred while processing your request."}), 500

@app.route('/articles_by_specific_date/<date>', methods=['GET'])
def articles_by_specific_date(date):
    try:
        # Validate date format
        try:
            date_obj = datetime.strptime(date, '%Y-%m-%d')
            start_date = date_obj.strftime('%Y-%m-%dT%H:%M:%S')
            end_date = (date_obj + timedelta(days=1)).strftime('%Y-%m-%dT%H:%M:%S')
        except ValueError:
            return jsonify({"error": "Invalid date format. Please use YYYY-MM-DD."}), 400

        # Log the date range for debugging
        app.logger.debug(f"Start Date: {start_date}, End Date: {end_date}")

        # Query to find articles published on the specific date
        query = {
            "publication_date": {"$gte": start_date, "$lt": end_date}
        }

        # Fetch articles matching the query
        result = list(collection.find(query))

        # Log the result count for debugging
        app.logger.debug(f"Number of articles found: {len(result)}")

        # Format the response
        formatted_result = [
            {"url": item.get("url"), "title": item.get("title"), "publication_date": item.get("publication_date")}
            for item in result
        ]

        # Response
        count = len(formatted_result)
        response = {
            "date": date,
            "count": count,
            "articles": formatted_result
        }

        return jsonify(response)
    except Exception as e:
        app.logger.error(f"Error fetching articles by date: {e}")
        return jsonify({"error": "An error occurred while processing your request."}), 500

@app.route('/articles_containing_text/<text>', methods=['GET'])
def articles_containing_text(text):
    # Perform the query to find articles containing the specified text
    query = {
        'full_text': {'$regex': text, '$options': 'i'}  # Case-insensitive search
    }

    # Fetch the articles from MongoDB
    articles = collection.find(query, {'_id': 0, 'full_text': 1, 'post_id': 1, 'author': 1})

    # Convert the cursor to a list of dictionaries
    articles_list = list(articles)

    return jsonify(articles_list)

@app.route('/articles_with_more_than/<int:word_count>', methods=['GET'])
def articles_with_more_than(word_count):
    try:
        # Query to find articles with word count greater than the specified number
        query = {
            "$expr": {
                "$gt": [
                    {"$toInt": "$word_count"},  # Convert word_count to integer
                    word_count
                ]
            }
        }
        projection = {"_id": 0, "title": 1, "word_count": 1, "full_text": 1}

        # Fetch matching articles
        result = list(collection.find(query, projection))

        # Format the response to show titles and word count of the matching articles
        formatted_result = [
            {
                "title": item["title"],
                "word_count": f"{item['word_count']} words",
                "full_text_snippet": item["full_text"][:200]  # Show first 200 characters as a snippet
            }
            for item in result
        ]

        return jsonify(formatted_result)
    except Exception as e:
        app.logger.error(f"Error fetching articles with more than {word_count} words: {e}")
        return jsonify({"error": "An error occurred while processing your request."}), 500
@app.route('/articles_grouped_by_coverage', methods=['GET'])
def articles_grouped_by_coverage():
    # MongoDB aggregation pipeline
    pipeline = [
        {"$unwind": "$classes"},
        {"$match": {"classes.key": "class5"}},
        {"$group": {"_id": "$classes.value", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]

    # Execute the aggregation pipeline
    result = list(collection.aggregate(pipeline))

    # Format the response
    response = [{"coverage_category": item["_id"], "article_count": item["count"]} for item in result]

    return jsonify(response), 200

@app.route('/articles_by_title_length', methods=['GET'])
def articles_by_title_length():
    try:
        # Aggregate articles and group by title length
        pipeline = [
            {"$project": {"title": 1}},  # Project only the title field
            {"$addFields": {"title_length": {"$size": {"$split": ["$title", " "]}}}},  # Calculate word count in title
            {"$group": {"_id": "$title_length", "count": {"$sum": 1}}},  # Group by title length and count articles
            {"$sort": {"_id": 1}}  # Sort by title length
        ]

        result = list(collection.aggregate(pipeline))

        # Format the response
        formatted_result = [
            {"title_length": f"Titles with {item['_id']} words", "count": f"{item['count']} articles"}
            for item in result
        ]

        return jsonify(formatted_result)
    except Exception as e:
        app.logger.error(f"Error fetching articles by title length: {e}")
        return jsonify({"error": "An error occurred while processing your request."}), 500

@app.route("/articles_last_X_hours/<int:hour>", methods=["GET"])
def articles_last_X_hours(hour):
    # Calculate the date and time X hours ago
    date_X_hours_ago = datetime.utcnow() - timedelta(hours=hour)

    # MongoDB aggregation pipeline
    pipeline = [
        {
            "$project": {
                "title": 1,
                "published_time": {
                    "$dateFromString": {"dateString": "$published_time"}
                },
                "_id": 0,
            }
        },
        {
            "$match": {
                "published_time": {"$gte": date_X_hours_ago}
            }
        }
    ]

    # Execute the aggregation pipeline
    result = list(collection.aggregate(pipeline))

    # Return the result as JSON
    return jsonify(result)

@app.route('/articles_by_sentiment/<sentiment>', methods=['GET'])
def get_articles_by_sentiment(sentiment):
    if sentiment not in ['positive', 'neutral', 'negative']:
        return jsonify({"error": "Invalid sentiment value. Choose from 'positive', 'neutral', or 'negative'."}), 400

    articles = collection.find({"sentiment": sentiment},
                               {"_id": 0, "title": 1, "author": 1, "publication_date": 1, "full_text": 1})

    result = []
    for article in articles:
        result.append(article)

    return jsonify(result), 200
@app.route('/articles_by_entity/<entity>', methods=['GET'])
def get_articles_by_entity(entity):
    try:
        # Query MongoDB for articles mentioning the entity in per, loc, or org, with a projection to include only the specified fields
        articles = collection.find({
            '$or': [
                {'entities.per': {'$regex': entity, '$options': 'i'}},
                {'entities.loc': {'$regex': entity, '$options': 'i'}},
                {'entities.org': {'$regex': entity, '$options': 'i'}}
            ]
        }, {
            'author': 1,
            'entities': 1,
            'full_text': 1,
            'post_id': 1,
            'url': 1
        })

        # Convert the cursor to a list and process it
        articles_list = []
        for article in articles:
            # Convert ObjectId to string for JSON serialization
            article['_id'] = str(article['_id'])
            articles_list.append(article)

        # Return the articles as a JSON response
        return jsonify(articles_list), 200

    except Exception as e:
        return jsonify({"error": f"Failed to query articles: {str(e)}"}), 500

@app.route('/most_negative_articles', methods=['GET'])
def most_positive_articles():
    try:
        # Query MongoDB to find the top 10 positive articles
        top_articles = list(collection.find(
            {"sentiment_score": {"$exists": True}}  # Ensure sentiment_score field exists
        ).sort("sentiment_score", -1).limit(10))   # Sort by sentiment_score in descending order and limit to 10

        # Format the articles and return the desired fields
        result = []
        for article in top_articles:
            result.append({
                "url": article.get("url"),
                "title": article.get("title"),
                "author": article.get("author"),
                "sentiment_score": article.get("sentiment_score"),
                "publication_date": article.get("publication_date"),
                "full_text": article.get("full_text")
            })

        return jsonify(result), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/most_positive_articles', methods=['GET'])
def most_negative_articles():
    try:
        # Query MongoDB to find the top 10 negative articles
        negative_articles = list(collection.find(
            {"sentiment_score": {"$exists": True}}  # Ensure sentiment_score field exists
        ).sort("sentiment_score", 1).limit(10))   # Sort by sentiment_score in ascending order and limit to 10

        # Format the articles and return the desired fields
        result = []
        for article in negative_articles:
            result.append({
                "url": article.get("url"),
                "title": article.get("title"),
                "author": article.get("author"),
                "sentiment_score": article.get("sentiment_score"),
                "publication_date": article.get("publication_date"),
                "full_text": article.get("full_text")
            })

        return jsonify(result), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Sentiment Trend Analysis
def sentiment_trends():
    pipeline = [
        {
            "$addFields": {
                "publication_date_converted": {
                    "$dateFromString": {
                        "dateString": "$publication_date"  # No need to specify format
                    }
                }
            }
        },
        {
            "$group": {
                "_id": {
                    "$dateToString": {
                        "format": "%Y-%m-%d",
                        "date": "$publication_date_converted"
                    }
                },
                "positive_count": {
                    "$sum": { "$cond": [{ "$eq": ["$sentiment", "positive"] }, 1, 0] }
                },
                "negative_count": {
                    "$sum": { "$cond": [{ "$eq": ["$sentiment", "negative"] }, 1, 0] }
                },
                "neutral_count": {
                    "$sum": { "$cond": [{ "$eq": ["$sentiment", "neutral"] }, 1, 0] }
                }
            }
        },
        { "$sort": { "_id": 1 } }  # Sort by date
    ]
    return list(collection.aggregate(pipeline))

# Keyword Trend Analysis
def keyword_trends(keyword):
    pipeline = [
        {
            "$match": { "keywords": keyword }
        },
        {
            "$addFields": {
                "publication_date_converted": {
                    "$dateFromString": {
                        "dateString": "$publication_date",
                        "format": "%Y-%m-%dT%H:%M:%S%z"
                    }
                }
            }
        },
        {
            "$group": {
                "_id": {
                    "$dateToString": { "format": "%Y-%m-%d", "date": "$publication_date_converted" }
                },
                "keyword_count": { "$sum": 1 }
            }
        },
        { "$sort": { "_id": 1 } }  # Sort by date
    ]
    return list(collection.aggregate(pipeline))

# API to fetch sentiment trends
@app.route('/sentiment_trends', methods=['GET'])
def get_sentiment_trends():
    trends = sentiment_trends()
    return jsonify(trends)


# API to fetch keyword trends
@app.route('/keyword_trends/<keyword>', methods=['GET'])
def get_keyword_trends(keyword):
    trends = keyword_trends(keyword)
    return jsonify(trends)

if __name__ == '__main__':
    app.run(debug=True)