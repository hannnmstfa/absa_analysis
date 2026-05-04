import os

def optimize_engine():
    with open('engine.py', 'r', encoding='utf-8') as f:
        text = f.read()

    # Fix stopwords
    text = text.replace('"tidak","ga","gak","nggak",', '')
    text = text.replace('"kurang",', '')

    # Fix GridSearch for Pipeline
    old_nb = '''"Naive Bayes": Pipeline([
                            ("tfidf", TfidfVectorizer(**vectorizer)),
                            ("clf", MultinomialNB(alpha=0.6)),
                        ]),'''
    new_nb = '''"Naive Bayes": GridSearchCV(Pipeline([
                            ("tfidf", TfidfVectorizer(**vectorizer)),
                            ("clf", MultinomialNB()),
                        ]), param_grid={'clf__alpha': [0.1, 0.5, 1.0, 2.0]}, cv=3, scoring='f1_weighted', n_jobs=1),'''
    text = text.replace(old_nb, new_nb)

    old_svm = '''"SVM": Pipeline([
                            ("tfidf", TfidfVectorizer(**vectorizer)),
                            ("clf", LinearSVC(random_state=42, max_iter=5000, class_weight="balanced")),
                        ]),'''
    new_svm = '''"SVM": GridSearchCV(Pipeline([
                            ("tfidf", TfidfVectorizer(**vectorizer)),
                            ("clf", LinearSVC(random_state=42, max_iter=5000, class_weight="balanced")),
                        ]), param_grid={'clf__C': [0.1, 0.5, 1.0, 5.0]}, cv=3, scoring='f1_weighted', n_jobs=1),'''
    text = text.replace(old_svm, new_svm)

    with open('engine.py', 'w', encoding='utf-8') as f:
        f.write(text)

def optimize_rfa():
    with open('run_full_analysis.py', 'r', encoding='utf-8') as f:
        text = f.read()

    # Add GridSearchCV import if missing
    if 'GridSearchCV' not in text:
        text = text.replace('from sklearn.model_selection import train_test_split, cross_val_score',
                            'from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV')

    # Add class_weight to SVM
    text = text.replace('LinearSVC(random_state=42, max_iter=2000)', 'LinearSVC(random_state=42, max_iter=2000, class_weight="balanced")')

    # Add GridSearchCV wrapping
    text = text.replace('nb = MultinomialNB()', "nb = GridSearchCV(MultinomialNB(), param_grid={'alpha': [0.1, 0.5, 1.0, 2.0]}, cv=3, scoring='f1_weighted')")
    text = text.replace('svm = LinearSVC(random_state=42, max_iter=2000, class_weight="balanced")', "svm = GridSearchCV(LinearSVC(random_state=42, max_iter=2000, class_weight='balanced'), param_grid={'C': [0.1, 0.5, 1.0, 5.0]}, cv=3, scoring='f1_weighted')")

    # In cross val pipeline
    text = text.replace('Pipeline([(\'tfidf\', tfidf),(\'clf\', MultinomialNB())])', 'GridSearchCV(Pipeline([(\'tfidf\', tfidf),(\'clf\', MultinomialNB())]), param_grid={\'clf__alpha\': [0.1, 0.5, 1.0, 2.0]}, cv=3)')
    text = text.replace('Pipeline([(\'tfidf\', tfidf),(\'clf\', LinearSVC(random_state=42, max_iter=2000, class_weight="balanced"))])', 'GridSearchCV(Pipeline([(\'tfidf\', tfidf),(\'clf\', LinearSVC(random_state=42, max_iter=2000, class_weight="balanced"))]), param_grid={\'clf__C\': [0.1, 0.5, 1.0, 5.0]}, cv=3)')

    with open('run_full_analysis.py', 'w', encoding='utf-8') as f:
        f.write(text)

optimize_engine()
optimize_rfa()
print("Optimization complete.")
