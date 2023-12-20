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

    # Define specific rules for handling different formats
    if re.match(r'^\d', cleaned_ingredient):  # Starts with a number
        # Split at the first non-numeric/non-space character
        quantity_unit, ingredient_name = re.split(r'(?<=\d)\s*([^\d\s].*)', cleaned_ingredient, maxsplit=1)
        quantity, unit = re.match(r'(\d[\d\s/]*)([a-zA-Z.]*)', quantity_unit).groups()
    elif 'of ' in cleaned_ingredient:  # Handle cases like "2 racks of ribs"
        quantity, rest = cleaned_ingredient.split(' of ', 1)
        unit, ingredient_name = None, f'of {rest}'
    else:
        quantity, unit, ingredient_name = None, None, cleaned_ingredient  # Fallback for complex cases

    # Calculate the positions for each entity
    entities = []
    if quantity:
        entities.append((0, len(quantity), "QUANTITY"))
    if unit and unit.strip():
        start = len(quantity) + 1
        entities.append((start, start + len(unit), "UNIT"))
    if ingredient_name:
        start = len(quantity) + len(unit) + 2 if unit else len(quantity) + 1
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
