SMARTBITE — FOOD AND RECIPE RECOMMENDATION SYSTEM

SETUP
1. Extract this ZIP.
2. Copy recipes_for_website.json exported from your Phase 3 Colab notebook into this folder beside server.py.
3. smartbite_best_model.joblib is optional for the supporting Phase 2 ranking signal. If it is not present or cannot load, ingredient-based recommendations still work.
4. Open Command Prompt in this folder.
5. Run: python -m pip install -r requirements.txt
6. Run: python server.py
7. Open http://127.0.0.1:8000 and keep Command Prompt open.
8. Stop with Ctrl+C.

DIET FILTERS
Any: no dietary filter.
Vegetarian: excludes recognized meat, poultry, fish and seafood ingredients and explicit non-vegetarian tags.
Vegan: additionally excludes common eggs, dairy and honey ingredients.
Non-vegetarian: requires recognized meat, poultry, fish, seafood, or a non-vegetarian tag.

Important: ingredient/tag rules cannot guarantee dietary safety if the source dataset has missing or vague ingredient information. Check recipe details manually. This is not an allergy-safety tool.

DATA FILE
recipes_for_website.json is required and must be exported from your Phase 3 notebook. Expected recipe objects have fields such as name, ingredients (list), minutes, n_steps, n_ingredients, steps (list), tags (list). `instructions` is also accepted as a steps field.

The Phase 2 model predicts high-rating category based on recipe attributes. Ingredient similarity is the recommendation method; the model is only a supporting ranking signal.
