import spacy
from spacy.matcher import Matcher

def parse_recipe_with_spacy(recipe_text):
    # Load SpaCy model
    nlp = spacy.load("en_core_web_sm")
    doc = nlp(recipe_text)

    # Variables to hold the sections of the recipe
    title = None
    ingredients = []
    instructions = []
    mode = None

    # Iterate over sentences to find the title
    for sent in doc.sents:
        text = sent.text.strip()
        if '**ingredients**' in text.lower():
            break
        if title is None and text and not text.startswith('-') and len(text) < 100:
            title = text
            continue
        if '**instructions**' in text.lower():
            mode = 'instructions'
            continue
        if mode == 'instructions':
            instructions.append(text)
        else:
            ingredients.append(text)

    # Remove empty strings and the title from ingredients and instructions
    ingredients = [i for i in ingredients if i and i != title]
    instructions = [i for i in instructions if i and i != title]

    return {
        'title': title,
        'ingredients': ingredients,
        'instructions': instructions
    }