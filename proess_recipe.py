import spacy
from spacy.matcher import Matcher
from name_recipe import name_recipe
import re

async def parse_recipe_with_spacy(recipe_text):
    # Removing newlines, tabs, and excess whitespace
    cleaned_text = re.sub(r'\s+', ' ', recipe_text).strip()

    # Splitting the text into parts based on the headings
    ingredients_marker = "Ingredients:"
    instructions_marker = "Instructions:"
    ingredients_part, instructions_part = "", ""

    if ingredients_marker in cleaned_text:
        parts = cleaned_text.split(ingredients_marker)
        ingredients_part = parts[1].split(instructions_marker)[0]

    if instructions_marker in cleaned_text:
        parts = cleaned_text.split(instructions_marker)
        instructions_part = parts[1] if len(parts) > 1 else ""

    # Clean up ingredients and instructions
    ingredients = ingredients_part.strip()
    instructions = instructions_part.strip()

    # Get the title
    title = name_recipe(recipe_text)
    print("Title:", title)

    return {
        'title': title,
        'ingredients': ingredients,
        'instructions': instructions
    }
