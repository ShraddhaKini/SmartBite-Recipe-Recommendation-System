# SmartBite – Ingredient-Based Recipe Recommendation System

SmartBite is a web app that recommends recipes from the ingredients you already have. You type in your ingredients, choose a diet, a maximum cooking time and a minimum number of ingredient matches, and it returns the best-matching recipes from a dataset of 231,636 recipes.

## Features

- Matches your ingredients against the recipe dataset and returns the 12 best matches.
- Python HTTP server with a `/recommend` API that filters by diet (any, vegetarian, vegan, non-vegetarian), maximum cooking time and minimum ingredient matches, then ranks results by ingredient overlap.
- A trained MLP neural network classifier (scikit-learn, with StandardScaler) predicts high-rated recipes (ratings 4–5) and is used as a supporting ranking signal. The model file is optional; without it, ingredient-based recommendations still work.
- Plain HTML, CSS and JavaScript front end.

## Tech stack

Python, scikit-learn, pandas, joblib, JavaScript, HTML and CSS.

## Getting started

1. Install [Git LFS](https://git-lfs.com/) **before cloning**, because the recipe dataset (`recipes_for_website.json`, about 243 MB) is stored with Git LFS. If you already cloned without it, run `git lfs pull`.
2. Install the dependencies:
   ```bash
   python -m pip install -r requirements.txt
   ```
3. Start the server:
   ```bash
   python server.py
   ```
4. Open http://127.0.0.1:8000 in your browser and keep the terminal open. Stop the server with `Ctrl+C`.

## Project structure

```
SmartBite/
├── server.py                    HTTP server and /recommend API
├── index.html                   Web page
├── style.css                    Styling
├── script.js                    Front-end logic
├── recipes_for_website.json     Recipe dataset (Git LFS)
├── smartbite_best_model.joblib  Trained model (optional ranking signal)
├── requirements.txt
└── README.txt                   Original setup notes
```

## Diet filters

- **Any:** no dietary filter.
- **Vegetarian:** excludes recognised meat, poultry, fish and seafood ingredients and explicit non-vegetarian tags.
- **Vegan:** additionally excludes common egg, dairy and honey ingredients.
- **Non-vegetarian:** requires a recognised meat, poultry, fish or seafood ingredient, or a non-vegetarian tag.

Diet filters rely on ingredient lists and tags, so they cannot guarantee dietary safety where the source data is incomplete. SmartBite is not an allergy-safety tool.

## Author

Shraddha Kini
