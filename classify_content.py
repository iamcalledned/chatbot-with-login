import re

def classify_content(message_content):
    # Patterns that might indicate a shopping list
    shopping_list_pattern = re.compile(r'^\s*[-*]?\s*\d*\s*\w+', re.MULTILINE)

    # Patterns that are more typical in recipes
    recipe_pattern = re.compile(r'\b(cook|bake|stir|chop|preheat|mix|cup|teaspoon|tablespoon)\b', re.IGNORECASE)

    # Check for recipe characteristics
    if recipe_pattern.search(message_content):
        return "recipe"

    # Check for shopping list characteristics
    elif shopping_list_pattern.search(message_content):
        return "shopping_list"

    return "other"

