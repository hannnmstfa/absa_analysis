import os

def super_optimize_engine():
    with open('engine.py', 'r', encoding='utf-8') as f:
        text = f.read()

    # Change MultinomialNB to ComplementNB
    text = text.replace('from sklearn.naive_bayes import MultinomialNB', 'from sklearn.naive_bayes import MultinomialNB, ComplementNB')
    text = text.replace('("clf", MultinomialNB())', '("clf", ComplementNB())')
    
    # Expand vectorizer
    old_vec = '''                    vectorizer = {
                        "max_features": 8000,
                        "ngram_range": (1, 2),
                        "sublinear_tf": True,
                    }'''
    new_vec = '''                    vectorizer = {
                        "max_features": 8000,
                        "ngram_range": (1, 3),
                        "sublinear_tf": True,
                        "min_df": 2,
                    }'''
    text = text.replace(old_vec, new_vec)

    # Expand GridSearchCV param grid
    text = text.replace("param_grid={'clf__alpha': [0.1, 0.5, 1.0, 2.0]}", "param_grid={'clf__alpha': [0.01, 0.1, 0.5, 1.0, 2.0]}")
    text = text.replace("param_grid={'clf__C': [0.1, 0.5, 1.0, 5.0]}", "param_grid={'clf__C': [0.01, 0.1, 1.0, 10.0]}")

    with open('engine.py', 'w', encoding='utf-8') as f:
        f.write(text)

super_optimize_engine()
print("Super optimization complete.")
