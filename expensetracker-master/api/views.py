# api/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
import joblib
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
import os

# Define paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(BASE_DIR, 'dataset.csv')
MODEL_PATH = os.path.join(BASE_DIR, 'model.pkl')
VECTORIZER_PATH = os.path.join(BASE_DIR, 'vectorizer.pkl')

# Preprocess text function
def preprocess_text(text):
    stop_words = set(stopwords.words('english'))
    tokens = word_tokenize(text.lower())
    tokens = [t for t in tokens if t.isalnum() and t not in stop_words]
    return ' '.join(tokens)

# Ensure NLTK data is downloaded once (do this outside requests)
import nltk
nltk.download('punkt')
nltk.download('stopwords')
nltk.download('punkt_tab')


class PredictCategory(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user_input = request.data.get('description')
        if not user_input:
            return Response({'error': 'No description provided'}, status=status.HTTP_400_BAD_REQUEST)

        # Load saved model and vectorizer
        if not os.path.exists(MODEL_PATH) or not os.path.exists(VECTORIZER_PATH):
            return Response({'error': 'Model or vectorizer not found. Train model first.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        model = joblib.load(MODEL_PATH)
        tfidf_vectorizer = joblib.load(VECTORIZER_PATH)

        # Preprocess input
        user_input_clean = preprocess_text(user_input)
        user_vector = tfidf_vectorizer.transform([user_input_clean])

        predicted_category = model.predict(user_vector)

        return Response({'predicted_category': predicted_category[0]}, status=status.HTTP_200_OK)


class UpdateDataset(APIView):
    # permission_classes = [IsAuthenticated]  # Uncomment if you want authentication

    def post(self, request):
        new_data = request.data.get('new_data')
        if not new_data or 'description' not in new_data or 'category' not in new_data:
            return Response({'error': 'Invalid data format'}, status=status.HTTP_400_BAD_REQUEST)

        # Load dataset
        if os.path.exists(DATA_PATH):
            data = pd.read_csv(DATA_PATH)
        else:
            data = pd.DataFrame(columns=['description', 'category', 'clean_description'])

        # Append new row
        new_row = {
            'description': new_data['description'],
            'category': new_data['category'],
            'clean_description': preprocess_text(new_data['description'])
        }
        data = pd.concat([data, pd.DataFrame([new_row])], ignore_index=True)

        # Save updated dataset
        data.to_csv(DATA_PATH, index=False)

        try:
            # Retrain model
            tfidf_vectorizer = TfidfVectorizer()
            X = tfidf_vectorizer.fit_transform(data['clean_description'])
            model = RandomForestClassifier()
            model.fit(X, data['category'])

            # Save model and vectorizer
            joblib.dump(model, MODEL_PATH)
            joblib.dump(tfidf_vectorizer, VECTORIZER_PATH)

            return Response({'message': 'Dataset updated and model retrained successfully'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': f'Model training failed: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
