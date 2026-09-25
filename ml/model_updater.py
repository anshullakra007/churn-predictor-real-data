import pandas as pd
from sqlalchemy import create_engine
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
import joblib
import os
from dotenv import load_dotenv

def get_latest_data():
    load_dotenv()
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        raise ValueError("DATABASE_URL not found")
        
    engine = create_engine(db_url)
    # Pulling the latest 30 days of data
    # Assuming there's a timestamp column 'created_at'. If not, we just pull all data for this prototype.
    try:
        query = "SELECT * FROM customers WHERE created_at >= NOW() - INTERVAL '30 days'"
        df = pd.read_sql(query, engine)
    except:
        # Fallback if created_at doesn't exist in the current schema
        query = "SELECT * FROM customers"
        df = pd.read_sql(query, engine)
        
    # Clean data
    df = df.drop_duplicates()
    for col in df.columns:
        if df[col].dtype == 'object':
            df[col] = df[col].fillna(df[col].mode()[0])
        else:
            df[col] = df[col].fillna(df[col].median())
    return df

def update_model():
    print("Fetching latest data for model retraining...")
    df = get_latest_data()
    
    if len(df) < 100:
        print("Not enough data to retrain model.")
        return

    df = pd.get_dummies(df, columns=['Geography', 'Gender'], drop_first=True)
    
    cols_to_drop = ['RowNumber', 'CustomerId', 'Surname', 'Exited', 'created_at']
    X = df.drop([c for c in cols_to_drop if c in df.columns], axis=1)
    
    if 'Exited' not in df.columns:
        print("No Exited column found.")
        return
        
    y = df['Exited']
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    print("Training new Random Forest model...")
    new_model = RandomForestClassifier(n_estimators=100, random_state=42)
    new_model.fit(X_train, y_train)
    new_pred = new_model.predict(X_test)
    new_accuracy = accuracy_score(y_test, new_pred)
    
    model_path = 'churn_model.joblib'
    if os.path.exists(model_path):
        old_model = joblib.load(model_path)
        # We need to make sure the features match
        try:
            expected_features = joblib.load('model_features.joblib')
            # Realign X_test to match expected_features for old model
            X_test_old = X_test.copy()
            for col in expected_features:
                if col not in X_test_old.columns:
                    X_test_old[col] = 0
            X_test_old = X_test_old[expected_features]
            
            old_pred = old_model.predict(X_test_old)
            old_accuracy = accuracy_score(y_test, old_pred)
        except:
            old_accuracy = 0
    else:
        old_accuracy = 0
        
    print(f"Old Model Accuracy: {old_accuracy:.4f}")
    print(f"New Model Accuracy: {new_accuracy:.4f}")
    
    if new_accuracy >= old_accuracy + 0.02:
        print("New model is significantly better (+2%). Overwriting existing model...")
        joblib.dump(new_model, model_path)
        joblib.dump(list(X.columns), 'model_features.joblib')
        
        # Trigger Streamlit cache clear by touching the main app file
        app_path = '../app.py'
        if os.path.exists(app_path):
            os.utime(app_path, None)
            print("Triggered Streamlit app reload/cache clear.")
    else:
        print("New model did not meet the +2% improvement threshold. Discarding.")

if __name__ == "__main__":
    update_model()
