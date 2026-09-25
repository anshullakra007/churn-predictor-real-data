import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report
import joblib
import os
from huggingface_hub import HfApi

from sqlalchemy import create_engine
from dotenv import load_dotenv

def fetch_crm_data():
    load_dotenv()
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        raise ValueError("DATABASE_URL not found in environment.")
    
    print("Connecting to PostgreSQL to fetch CRM data...")
    engine = create_engine(db_url)
    
    # Assuming 'customers' is the raw data table
    query = 'SELECT * FROM customers'
    df = pd.read_sql(query, engine)
    
    print("Cleaning data...")
    # Drop duplicates
    df = df.drop_duplicates()
    
    # Imputation for missing values
    for col in df.columns:
        if df[col].dtype == 'object':
            df[col] = df[col].fillna(df[col].mode()[0])
        else:
            df[col] = df[col].fillna(df[col].median())
            
    return df

def train_and_save_model():
    print("Fetching real data from database...")
    df = fetch_crm_data()
    
    os.makedirs('../data', exist_ok=True)
    df.to_csv('../data/real_churn_data.csv', index=False)
    
    print("Preparing data for training...")
    # Encode categorical
    df = pd.get_dummies(df, columns=['Geography', 'Gender'], drop_first=True)
    
    # Drop unnecessary columns if they exist (like 'RowNumber', 'CustomerId', 'Surname')
    cols_to_drop = ['RowNumber', 'CustomerId', 'Surname', 'Exited']
    X = df.drop([c for c in cols_to_drop if c in df.columns], axis=1)
    
    if 'Exited' not in df.columns:
        print("Error: 'Exited' column not found in data.")
        return
        
    y = df['Exited']
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    print("Training Random Forest Classifier...")
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)
    
    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    print(f"Model Accuracy: {accuracy:.4f}")
    
    # Save the model
    joblib.dump(model, 'churn_model.joblib')
    # Save the features expected
    joblib.dump(list(X.columns), 'model_features.joblib')
    print("Model saved to churn_model.joblib")

    # If HF token is available, push to hub
    hf_token = os.getenv("HF_TOKEN")
    if hf_token:
        try:
            print("Uploading to Hugging Face...")
            api = HfApi(token=hf_token)
            # Create a repo name based on the current user or just standard
            user_info = api.whoami()
            username = user_info['name']
            repo_id = f"{username}/fintech-churn-model"
            
            api.create_repo(repo_id=repo_id, exist_ok=True)
            api.upload_file(
                path_or_fileobj="churn_model.joblib",
                path_in_repo="churn_model.joblib",
                repo_id=repo_id
            )
            api.upload_file(
                path_or_fileobj="model_features.joblib",
                path_in_repo="model_features.joblib",
                repo_id=repo_id
            )
            print(f"Successfully uploaded model to Hugging Face: {repo_id}")
        except Exception as e:
            print(f"Failed to upload to HF: {e}")
    else:
        print("No HF_TOKEN found, skipping upload.")

if __name__ == "__main__":
    train_and_save_model()
