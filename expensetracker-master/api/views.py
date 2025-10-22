# api/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics.pairwise import cosine_similarity
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
import nltk
import os

# Download necessary NLTK data once
nltk.download('punkt')
nltk.download('stopwords')

DATASET_PATH = os.path.join(os.path.dirname(__file__), '../dataset.csv')

# Preprocessing function
def preprocess_text(text):
    stop_words = set(stopwords.words('english'))
    tokens = word_tokenize(text.lower())
    tokens = [t for t in tokens if t.isalnum() and t not in stop_words]
    return ' '.join(tokens)


class PredictCategory(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            user_input = request.data.get('description', '')
            if not user_input:
                return Response({'error': 'Description is required.'}, status=status.HTTP_400_BAD_REQUEST)

            if not os.path.exists(DATASET_PATH):
                return Response({'error': 'Dataset not found.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            # Load dataset
            data = pd.read_csv(DATASET_PATH)
            if 'clean_description' not in data.columns:
                data['clean_description'] = data['description'].apply(preprocess_text)

            # TF-IDF and model
            tfidf_vectorizer = TfidfVectorizer()
            X = tfidf_vectorizer.fit_transform(data['clean_description'])
            model = RandomForestClassifier()
            model.fit(X, data['category'])

            # Preprocess user input
            processed_input = preprocess_text(user_input)
            user_vector = tfidf_vectorizer.transform([processed_input])

            # Find closest match using cosine similarity
            similarities = cosine_similarity(user_vector, X)
            closest_index = similarities.argmax()
            predicted_category = model.predict(X[closest_index])

            return Response({'predicted_category': predicted_category[0]}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UpdateDataset(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            new_data = request.data.get('new_data', {})
            if 'description' not in new_data or 'category' not in new_data:
                return Response({'error': 'Invalid data format'}, status=status.HTTP_400_BAD_REQUEST)

            new_description = new_data['description']
            new_category = new_data['category']

            # Load existing dataset
            if os.path.exists(DATASET_PATH):
                data = pd.read_csv(DATASET_PATH)
            else:
                data = pd.DataFrame(columns=['description', 'category', 'clean_description'])

            # Append new data
            new_row = {
                'description': new_description,
                'category': new_category,
                'clean_description': preprocess_text(new_description)
            }
            data = pd.concat([data, pd.DataFrame([new_row])], ignore_index=True)

            # Save updated dataset
            data.to_csv(DATASET_PATH, index=False)

            return Response({'message': 'Dataset updated successfully'}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({'error': f'Model training failed: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
