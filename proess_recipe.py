import re
from name_recipe import name_recipe

async def process_recipe(recipe_content):
    # Function to find and concatenate multiple sections
    lines = recipe_content.split('\n')
    title, ingredients, instructions = '', [], []

    # Flags to identify which part of the message is being read
    reading_ingredients = False
    reading_instructions = False

    for line in lines:
        if line.startswith('A recipe for:'):
            title = line.split(':', 1)[1].strip()
            reading_ingredients = False
            reading_instructions = False
        elif 'Ingredients:' in line:
            reading_ingredients = True
            reading_instructions = False
        elif 'Directions:' in line or 'Instructions:' in line:
            reading_instructions = True
            reading_ingredients = False
        elif reading_ingredients:
            ingredients.append(line.strip())
        elif reading_instructions:
            instructions.append(line.strip())

    # Remove empty strings from lists
    ingredients = [i for i in ingredients if i]
    instructions = [i for i in instructions if i]

    return {
        'title': title,
        'ingredients': ingredients,
        'instructions': instructions
    }
