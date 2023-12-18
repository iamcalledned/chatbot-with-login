import re

async def classify_content(message_content):
    # Check for the presence of specific phrases
    recipe_for_header = re.search(r'a recipe for:', message_content, re.IGNORECASE)
    ingredients_header = re.search(r'Ingredients:', message_content, re.IGNORECASE)
    directions_header = re.search(r'Directions:', message_content, re.IGNORECASE)

    # Determine if it is a recipe by the presence of all three headers
    if recipe_for_header and ingredients_header and directions_header:
        return "recipe"
    else:
        return "other"