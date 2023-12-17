import spacy
from spacy.matcher import Matcher
from name_recipe import name_recipe

async def parse_recipe_with_spacy(recipe_text):
    # Splitting the text into two parts: ingredients and instructions
    parts = recipe_text.split('**Instructions:**')

    ingredients_part = parts[0]
    instructions_part = parts[1] if len(parts) > 1 else ""

    # Further processing to clean up the ingredients section
    ingredients = ingredients_part.replace('**Ingredients:**', '').strip()

    # Cleaning up and splitting the instructions into steps
    instructions = [step.strip() for step in instructions_part.split('\n') if step.strip()]
    title = name_recipe(recipe_text)
    return {
        'ingredients': ingredients,
        'instructions': instructions
    }