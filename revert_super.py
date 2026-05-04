import os

def revert_super_optimize():
    with open('engine.py', 'r', encoding='utf-8') as f:
        text = f.read()

    # Revert ComplementNB to MultinomialNB
    text = text.replace('("clf", ComplementNB())', '("clf", MultinomialNB())')
    
    # Revert vectorizer min_df and ngram_range
    bad_vec = '''                    vectorizer = {
                        "max_features": 8000,
                        "ngram_range": (1, 3),
                        "sublinear_tf": True,
                        "min_df": 2,
                    }'''
    good_vec = '''                    vectorizer = {
                        "max_features": 8000,
                        "ngram_range": (1, 2),
                        "sublinear_tf": True,
                    }'''
    text = text.replace(bad_vec, good_vec)

    with open('engine.py', 'w', encoding='utf-8') as f:
        f.write(text)

revert_super_optimize()
print("Reverted.")
