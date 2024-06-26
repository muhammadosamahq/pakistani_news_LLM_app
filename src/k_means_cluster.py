import re
import nltk
from nltk.corpus import stopwords
import pandas as pd
from sklearn.datasets import fetch_20newsgroups
from sklearn.feature_extraction.text import TfidfVectorizer
from sentence_transformers import SentenceTransformer
from sklearn.metrics import adjusted_rand_score, normalized_mutual_info_score, fowlkes_mallows_score
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
import matplotlib.pyplot as plt
from datetime import datetime
import seaborn as sns
#import torch
import numpy as np
import time
import json
import os
from typing import Tuple, List, Any, Dict, Union


def preprocess_text(text: str) -> str:
    # Ensure text is a string
    if not isinstance(text, str):
        return ""
    # remove links
    text: str = re.sub(r"http\S+", "", text)
    # remove special chars and numbers
    text: str = re.sub("[^A-Za-z]+", " ", text)

    # remove stopwords
    tokens: str = nltk.word_tokenize(text)
    tokens: List[str] = [w for w in tokens if not w.lower() in stopwords.words("english")]
    text: str = " ".join(tokens)
    text: str = text.lower().strip()

    return text

def get_next_file_number(directory: str) -> int:
    # Get a list of all files in the directory
    files: List[str] = os.listdir(directory)
    
    # Filter out non-JSON files and strip the .json extension
    json_files: List[str] = [f for f in files if f.endswith('.json')]
    json_numbers: List[int] = [int(f.replace('.json', '')) for f in json_files if f.replace('.json', '').isdigit()]
    
    # If there are no JSON files, start from 0
    if not json_numbers:
        return 0
    
    # Otherwise, return the next number after the highest current number
    return max(json_numbers) + 1

def fetch_and_merge_json_files(directory: str) -> List[Dict[str, Union[str, int, List[str]]]]:
    # List all files in the directory
    files: List[str] = os.listdir(directory)

    # Initialize an empty list to hold the merged JSON objects
    merged_data: List[Dict[str, Union[str, int, List[str]]]] = []

    # Iterate through each file in the directory
    for file in files:
        if file.endswith('.json'):
            # Construct the full file path
            file_path: str = os.path.join(directory, file)
            
            # Open and read the JSON file
            with open(file_path, 'r') as f:
                data: Dict[str, Union[str, int, List[str]]] = json.load(f)
                
                # If the data is a list, extend the merged_data list
                if isinstance(data, list):
                    merged_data.extend(data)
                else:
                    # If the data is a single object, append it to the merged_data list
                    merged_data.append(data)

    return merged_data

def tfidvectorizer_embeddings(df: pd.DataFrame) -> None:
    vectorizer: TfidfVectorizer = TfidfVectorizer(sublinear_tf=True, min_df=5, max_df=0.95)
    X: np.ndarray = vectorizer.fit_transform(df['text_cleaned']).toarray()

def sentance_transformers_embeddings(df: pd.DataFrame) -> np.ndarray:
    model: SentenceTransformer = SentenceTransformer('all-MiniLM-L6-v2')
    st: float = time.time()

    # Assuming `model` is initialized somewhere in your code
    df['encode_transforemers'] = df['text_cleaned'].apply(lambda text: model.encode(text, convert_to_numpy=True).flatten())

    et: float = time.time()

    print("Elapsed time: {:.2f} seconds".format(et - st))

    X_transformers: np.ndarray = np.vstack(df['encode_transforemers'])
    return X_transformers

# def fetch_today_file(directory):
#     # Get today's date in YYYY-MM-DD format
#     today_date = datetime.now().strftime("%Y-%m-%d")

#     # Construct the expected filename pattern
#     expected_filename = f"all_business_articles_{today_date}.json"

#     # List all files in the directory
#     files = os.listdir(directory)

#     # Find the file that matches today's date
#     for file in files:
#         if file == expected_filename:
#             return os.path.join(directory, file)

#     return None  # Return None if today's file is not found





def eval_cluster(embedding, target):
    kmeans = KMeans(n_clusters=3, random_state=42)
    y_pred = kmeans.fit_predict(embedding)
    
    # Evaluate the performance using ARI, NMI, and FMI
    ari = adjusted_rand_score(target, y_pred)
    nmi = normalized_mutual_info_score(target, y_pred)
    fmi = fowlkes_mallows_score(target, y_pred)

    # Print Metrics scores
    print("Adjusted Rand Index (ARI): {:.3f}".format(ari))
    print("Normalized Mutual Information (NMI): {:.3f}".format(nmi))
    print("Fowlkes-Mallows Index (FMI): {:.3f}".format(fmi))
    
    return y_pred

def dimension_reduction(df: pd.DataFrame, embedding: np.ndarray, method: str) -> None:

    pca = PCA(n_components=2, random_state=42)

    pca_vecs: np.ndarray = pca.fit_transform(embedding)

    # save our two dimensions into x0 and x1
    x0: np.ndarray = pca_vecs[:, 0]
    x1: np.ndarray = pca_vecs[:, 1]
    
    df[f'x0_{method}'] = x0 
    df[f'x1_{method}'] = x1

def plot_pca(df, x0_name, x1_name, cluster_name, method):

    plt.figure(figsize=(12, 7))

    plt.title(f"TF-IDF + KMeans 20newsgroup clustering with {method}", fontdict={"fontsize": 18})
    plt.xlabel("X0", fontdict={"fontsize": 16})
    plt.ylabel("X1", fontdict={"fontsize": 16})

    sns.scatterplot(data=df, x=x0_name, y=x1_name, hue=cluster_name, palette="viridis")
    plt.show()


# def save_cluster_to_json(df, cluster_value, category):
#     columns_to_keep = ['title', 'authors', 'source', 'publish_date', 'url', 'text_cleaned']
#     rename_columns = {'text_cleaned': 'text'}

#     today_date = datetime.now().strftime("%Y-%m-%d")
#     df_cluster = df[df['cluster_transformers'] == cluster_value]
#     df_cluster = df_cluster[columns_to_keep].rename(columns=rename_columns)

#     json_data = df_cluster.to_json(orient='records', indent=4)

#     directory_path = f'.././data/{today_date}/{category}/clusters'
#     filename = f'{directory_path}/{cluster_value}.json'
    
#     if not os.path.exists(directory_path):
#         os.makedirs(directory_path, exist_ok=True)

#     with open(filename, 'w') as file:
#         file.write(json_data)
    
#     print(f"Data saved to {filename}")

def get_clustered_dataframe(all_articles_json_list: list[Dict[str, Union[str, int, List[str]]]]) -> pd.DataFrame:

    df: pd.DataFrame = pd.DataFrame.from_records(all_articles_json_list)
    #df = pd.read_json(today_file_path)
    df['text_cleaned'] = df['text'].apply(lambda text: preprocess_text(text))
    df = df[df['text_cleaned'] != '']
    X_transformers: np.ndarray = sentance_transformers_embeddings(df)
    kmeans: KMeans = KMeans(n_clusters=3, random_state=42)
    clusters: np.ndarray = kmeans.fit_predict(X_transformers)
    clusters_result_name: str = 'cluster_transformers'
    df[clusters_result_name] = clusters
    dimension_reduction(df, X_transformers, 'transformers')
    #method = "transformers"
    #plot_pca(df, f'x0_{method}', f'x1_{method}', cluster_name=clusters_result_name, method=method)
    
    return df

def get_clusters_list(df: pd.DataFrame, category: str, today_date: datetime) -> List[List[Dict[str, str]]]:
    columns_to_keep: List[str] = ['id', 'datetime','title', 'authors', 'publish_date', 'url', 'text_cleaned']
    rename_columns: Dict[str, str] = {'text_cleaned': 'text'}
    
    clusters_list: List = []
    for cluster in [0, 1, 2]:
        df_cluster = df[df['cluster_transformers'] == cluster]
        df_cluster = df_cluster[columns_to_keep].rename(columns=rename_columns)

        json_data: str = df_cluster.to_json(orient='records', indent=4)
        json_objects_list: List[Dict[str: str]] = json.loads(json_data)
        
        if len(json_objects_list) <= 15:
            directory_path: str = f'.././data/{today_date}/{category}/clusters'
            if not os.path.exists(directory_path):
                os.makedirs(directory_path)
            file_no: int = get_next_file_number(directory_path)
            filename: str = f'{directory_path}/{file_no}.json'

            if not os.path.exists(directory_path):
                os.makedirs(directory_path, exist_ok=True)

            with open(filename, 'w') as file:
                file.write(json_data)
            
            print(f"Data saved to {filename}")

        else:
            clusters_list.append(json_objects_list)
    
    return clusters_list

def process_clusters(category: str, today_date: datetime) -> None:
    all_articles_json_list: list[Dict[str, Union[str, int, List[str]]]] = fetch_and_merge_json_files(f".././data/{today_date}/{category}/articles")
    df: pd.DataFrame = get_clustered_dataframe(all_articles_json_list)
    limit_exceeded_clusters: List[List[Dict[str: str]]] = get_clusters_list(df, category, today_date)
    
    while limit_exceeded_clusters:
        new_clusters: List = []
        for cluster_json in limit_exceeded_clusters:
            df: pd.DataFrame = get_clustered_dataframe(cluster_json)
            new_clusters.extend(get_clusters_list(df, category, today_date))
        limit_exceeded_clusters = new_clusters


def main() -> None:
    today_date: datetime = datetime.now().strftime("%Y-%m-%d")
    #today_file_path = fetch_today_file(f".././data/{today_date}/business/articles")
    categories: List[str] = ["business", "pakistan"]
    for category in categories:
        process_clusters(category, today_date)

if __name__ == "__main__":
    columns_to_keep: List[str] = ['title', 'authors', 'source', 'publish_date', 'url', 'text_cleaned']
    rename_columns: Dict[str, str] = {'text_cleaned': 'text'}

    model: SentenceTransformer = SentenceTransformer('all-MiniLM-L6-v2')
    nltk.download('punkt')
    nltk.download('stopwords')

    main()
            #save_cluster_to_json(df, cluster, category)

     #Elbow method
    # sse = []
    # k_rng = range(1,10)
    # for k in k_rng:
    #     kmeans = KMeans(n_clusters=k, random_state=42)
    #     kmeans.fit(df[['x0_transformers','x1_transformers']])
    #     sse.append(kmeans.inertia_)

    # plt.xlabel('K')
    # plt.ylabel('Sum of squared error')
    # plt.plot(k_rng,sse)
    