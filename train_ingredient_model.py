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

    # Regular expression pattern to match the quantity and unit
    pattern = r'^([\d\s¼½¾/-]+(?:\([\d\s.]+\))?)([a-zA-Z.]+)?\s*(.*)'
    match = re.match(pattern, cleaned_ingredient)
    
    if match:
        quantity, unit, ingredient_name = match.groups(default='')
        quantity = quantity.strip()
        unit = unit.strip() if unit else None
        ingredient_name = ingredient_name.strip() if ingredient_name else None
    else:
        # Fallback for other cases
        quantity, unit, ingredient_name = None, None, cleaned_ingredient

    # Calculate positions for each entity
    entities = []
    if quantity:
        entities.append((0, len(quantity), "QUANTITY"))
    if unit:
        start = len(quantity) + 1
        entities.append((start, start + len(unit), "UNIT"))
    if ingredient_name:
        start_index = len(quantity) + 1  # Start after quantity
        start_index += len(unit) + 1 if unit else 0  # Add length of unit if present
        entities.append((start_index, start_index + len(ingredient_name), "INGREDIENT"))

    processed_data = {"text": cleaned_ingredient, "entities": entities}
    print(processed_data)
    return processed_data


ingredient_texts = extract_ingredients()
#train_data = [process_ingredient(text) for text in ingredient_texts]
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
