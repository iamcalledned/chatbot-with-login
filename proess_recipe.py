import spacy
from spacy.matcher import Matcher

def parse_recipe_with_spacy(recipe_text):
    # Load SpaCy model
    nlp = spacy.load("en_core_web_sm")

    # Cleaning up the text by replacing multiple newline characters with a single newline
    cleaned_text = '\n'.join([line.strip() for line in recipe_text.split('\n') if line.strip()])

    doc = nlp(cleaned_text)

    # Matcher for potential recipe titles (proper nouns or noun phrases)
    matcher = Matcher(nlp.vocab)
    title_pattern = [{"POS": "PROPN"}, {"POS": "NOUN", "OP": "?"}]
    matcher.add("RECIPE_TITLE", [title_pattern])

    # Variables to hold the sections of the recipe
    title = None
    ingredients = []
    instructions = []
    mode = None

    # Iterate over sentences to find the title
    for sent in doc.sents:
        if matcher(sent.as_doc()):
            title = sent.text.strip()
            break  # Assuming the first match is the title

    # Process the rest of the text for ingredients and instructions
    lines = cleaned_text.split('\n')
    for line in lines:
        line = line.strip()

        if line.lower().startswith('**ingredients:**'):
            mode = 'ingredients'
        elif line.lower().startswith('**instructions:**'):
            mode = 'instructions'
        elif line:  # If the line is not empty
            if mode == 'ingredients':
                ingredients.append(line)
            elif mode == 'instructions':
                instructions.append(line)

    return {
        'title': title,
        'ingredients': ingredients,
        'instructions': instructions
    }

