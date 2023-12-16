import spacy
from spacy.matcher import Matcher
from spacy.tokens import Span
from spacy.language import Language

def set_custom_boundaries(doc):
    # Custom boundary logic to prevent sentence segmentation at bullet points
    for token in doc[:-1]:
        if token.text in ("-"):
            doc[token.i+1].is_sent_start = False
    return doc

@Language.component("set_custom_boundaries")
def set_custom_boundaries_component(doc):
    return set_custom_boundaries(doc)


def parse_recipe_with_spacy(recipe_text):
    # Load SpaCy model and add custom boundary settings
    nlp = spacy.load("en_core_web_sm")
    nlp.add_pipe("set_custom_boundaries", before="parser")

    # Process the recipe text
    doc = nlp(recipe_text)

    # Variables to hold the sections of the recipe
    title = None
    ingredients = []
    instructions = []
    mode = None

    # Extract title - assuming it's the first noun phrase or sequence of proper nouns
    for np in doc.noun_chunks:
        if np.start == 0:
            title = np.text
            break

    # Process the rest of the text for ingredients and instructions
    lines = recipe_text.split('\n')
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