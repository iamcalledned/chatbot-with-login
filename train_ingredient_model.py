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
def process_ingredient(ingredient):
    cleaned_ingredient = ingredient.lstrip('- ').strip()

    # Define common units of measurement and common ingredient names
    common_units = ['cup', 'teaspoon', 'tablespoon', 'ounce', 'pound', 'gram', 'kg', 'ml', 'liter']
    common_ingredients = ['onion', 'carrots', 'celery', 'pepper', 'garlic']

    # Regular expression pattern to match the quantity and unit
    pattern = r'^([\d\s¼½¾/-]+(?:\([\d\s.]+\))?)([a-zA-Z.]+)?\s*(.*)'
    match = re.match(pattern, cleaned_ingredient)

    if match:
        quantity, potential_unit, ingredient_name = match.groups(default='')
        quantity = quantity.strip()

        # Check if the potential unit is in the list of common units
        # and if the following word is not a common ingredient
        unit = None
        if potential_unit.strip().lower() in common_units:
            next_word = ingredient_name.split()[0] if ingredient_name else ''
            if next_word.lower() not in common_ingredients:
                unit = potential_unit.strip()

        # Adjust ingredient name if unit is not recognized
        if not unit:
            ingredient_name = (potential_unit + ' ' if potential_unit else '') + ingredient_name
    else:
        quantity, unit, ingredient_name = None, None, cleaned_ingredient

    # Calculate positions for each entity
    entities = []
    quantity_len = len(quantity) if quantity else 0
    unit_len = len(unit) if unit else 0

    if quantity:
        entities.append((0, quantity_len, "QUANTITY"))
    if unit:
        start = quantity_len + 1
        entities.append((start, start + unit_len, "UNIT"))
    if ingredient_name:
        start_index = quantity_len + unit_len + 1 if unit else quantity_len + 1
        entities.append((start_index, start_index + len(ingredient_name), "INGREDIENT"))

    processed_data = {"text": cleaned_ingredient, "entities": entities}
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
