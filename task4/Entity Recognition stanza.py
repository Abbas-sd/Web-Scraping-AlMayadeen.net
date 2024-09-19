import stanza
from pymongo import MongoClient

# Initialize Stanza for Arabic with NER
stanza.download('ar')
nlp = stanza.Pipeline('ar', processors='tokenize,ner')

# MongoDB setup
client = MongoClient("mongodb://localhost:27017/")
db = client['Almayadeen-NPL']  # Database name
articles_collection = db['Articles']  # Collection name


def extract_entities(text):
    # Process the text with the pipeline
    doc = nlp(text)

    # Initialize empty lists for different entity types
    people = []
    locations = []
    organizations = []

    # Iterate through the entities detected by Stanza
    for ent in doc.ents:
        if ent.type == 'PER':  # Person
            people.append(ent.text)
        elif ent.type == 'LOC':  # Location
            locations.append(ent.text)
        elif ent.type == 'ORG':  # Organization
            organizations.append(ent.text)

    return {
        'per': people,  # People
        'loc': locations,  # Locations
        'org': organizations  # Organizations
    }


# Fetch all articles and update each with named entities
articles = articles_collection.find({})  # You can apply filters here if needed

for article in articles:
    full_text = article.get('full_text', '')
    if full_text:
        # Extract entities from the full_text
        entities = extract_entities(full_text)

        # Update the article in MongoDB with the extracted entities
        articles_collection.update_one(
            {'_id': article['_id']},  # Match the article by its ID
            {'$set': {'entities': entities}}  # Add or update the 'entities' field
        )
        print(f"Updated article {article['post_id']} with entities: {entities}")
