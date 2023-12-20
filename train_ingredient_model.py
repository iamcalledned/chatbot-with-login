import mysql.connector
import re
import spacy
from spacy.training import Example
from config import Config
import os

# Database configuration
DB_CONFIG = {
    "host": Config.DB_HOST,
    "port": Config.DB_PORT,
    "user": Config.DB_USER,
    "password": Config.DB_PASSWORD,
    "db": Config.DB_NAME,
}

# Function to extract ingredient data from the database
def extract_ingredients():
    ingredients = []
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor()
        cursor.execute("SELECT item FROM ingredients")
        ingredients = [ingredient[0] for ingredient in cursor.fetchall()]
    except mysql.connector.Error as e:
        print(f"Error connecting to MySQL: {e}")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
            print("MySQL connection is closed")
    return ingredients

# Function to process ingredient text and create annotations
def process_ingredient(ingredient):
    cleaned_ingredient = ingredient.lstrip('- ').strip()
    
    # Split the ingredient text into segments
    segments = re.split(r'(\d+[\d\s/]*[\.\d\s/]*\s*[a-zA-Z]*)\s*([a-zA-Z.]+)?', cleaned_ingredient)
    segments = [seg.strip() for seg in segments if seg.strip()]

    quantity, unit, ingredient_name = None, None, None

    # Analyze each segment and classify them
    if len(segments) > 0:
        # Assume the first segment is the quantity
        quantity = segments[0]
        # Check if the second segment can be a unit
        if len(segments) > 1 and any(char.isalpha() for char in segments[1]):
            unit = segments[1]
            ingredient_name = ' '.join(segments[2:])
        else:
            ingredient_name = ' '.join(segments[1:])

    entities = []
    if quantity:
        entities.append((0, len(quantity), "QUANTITY"))
    if unit:
        start = len(quantity) + 1 if quantity else 0
        entities.append((start, start + len(unit), "UNIT"))
    if ingredient_name:
        start = len(cleaned_ingredient) - len(ingredient_name)
        entities.append((start, len(cleaned_ingredient), "INGREDIENT"))

    processed_data = {"text": cleaned_ingredient, "entities": entities}
    print(processed_data)
    return processed_data

# Extract and process ingredients
ingredient_texts = extract_ingredients()
train_data = [process_ingredient(text) for text in ingredient_texts]

# Load a blank spaCy model
nlp = spacy.blank("en")

# Create a new NER pipeline component
ner = nlp.add_pipe("ner", last=True)

# Add entity labels to the NER component
for example in train_data:
    for ent in example['entities']:
        ner.add_label(ent[2])  # Add label for each entity


# Training the NER model
other_pipes = [pipe for pipe in nlp.pipe_names if pipe != "ner"]
with nlp.disable_pipes(*other_pipes):
    optimizer = nlp.begin_training()
    for itn in range(10):  # Number of training iterations
        losses = {}
        for example in train_data:
            doc = nlp.make_doc(example['text'])
            ents = []
            for start, end, label in example['entities']:
                span = doc.char_span(start, end, label=label)
                if span is not None:  # Ensure the span is valid
                    ents.append(span)
            if ents:  # Proceed only if there are valid entities
                example_data = Example.from_dict(doc, {"entities": ents})
                nlp.update([example_data], drop=0.5, losses=losses)
        print("Losses", losses)


# Save the trained model
model_path = os.path.expanduser("~/chatbot-with-login/model")

nlp.to_disk(model_path)
