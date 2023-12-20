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
    print(cleaned_ingredient)
    pattern = r'^(\d+\s*\d*[/\d]*\s*[a-zA-Z]*[\s\d]*[a-zA-Z]*)?\s*([a-zA-Z.]+)?\s*(\(.*?\))?\s*(.*)'
    match = re.match(pattern, cleaned_ingredient)

    if match:
        quantity = match.group(1).strip() if match.group(1) else None
        unit = match.group(2).strip() if match.group(2) else None
        additional_info = match.group(3).strip() if match.group(3) else None
        ingredient_name = match.group(4).strip()

        if quantity and additional_info:
            quantity = f"{quantity} {additional_info}"

        # Further refinement or fallback logic here if needed

        entities = []
        if quantity:
            entities.append((0, len(quantity), "QUANTITY"))
        if unit:
            start = len(quantity) + 1 if quantity else 0
            entities.append((start, start + len(unit), "UNIT"))
        if ingredient_name:
            start = len(cleaned_ingredient) - len(ingredient_name)
            entities.append((start, len(cleaned_ingredient), "INGREDIENT"))
        
        print({"text": cleaned_ingredient, "entities": entities})

        return {"text": cleaned_ingredient, "entities": entities}  
    
    else:
        # Fallback logic if regex match fails
        print({"text": cleaned_ingredient, "entities": [("INGREDIENT",)]})
        return {"text": cleaned_ingredient, "entities": [("INGREDIENT",)]}

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
