import joblib
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans

# Example training data
data = pd.DataFrame({
    'feature1': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
    'feature2': [10, 9, 8, 7, 6, 5, 4, 3, 2, 1],
    'feature3': [2, 4, 6, 8, 10, 12, 14, 16, 18, 20]
})

# Train the scaler
scaler = StandardScaler()
scaler.fit(data)

# Save the scaler model
joblib.dump(scaler, 'models/scaler.pkl')

# Scale the data
data_scaled = scaler.transform(data)

# Train the KMeans model
kmeans = KMeans(n_clusters=3)
kmeans.fit(data_scaled)

# Save the KMeans model
joblib.dump(kmeans, 'models/kmeans_model.pkl')

print("Models retrained and saved successfully!")
