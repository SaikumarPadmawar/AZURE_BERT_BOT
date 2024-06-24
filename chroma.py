# chroma.py
import pandas as pd
import json
from sentence_transformers import SentenceTransformer
from chromadb import PersistentClient

# Read CSV file into DataFrame
df = pd.read_csv('dataset.csv', encoding='latin1')

# Process Metadata to extract device
df['device'] = df['Metadata'].apply(lambda x: x.split('|')[1].split(':')[1])

# Process Prompts to extract QnaIds
df['suggestions'] = df['Prompts'].apply(lambda x: [item['QnaId'] for item in json.loads(x)])

# Initialize BERT model for embeddings
model = SentenceTransformer('bert-large-nli-mean-tokens')  # Using a more advanced BERT model

# Generate BERT embeddings for questions
question_embeddings = model.encode(df['Question'].astype(str))

# Add embeddings to DataFrame
df['question_embedding'] = question_embeddings.tolist()

# Initialize persistent ChromaDB client
chroma_client = PersistentClient(path="db")

# Create a collection
collection = chroma_client.get_or_create_collection(name="chroma_qna_1", metadata={"hnsw:space": "cosine"})

# Insert documents into the collection
for i, row in enumerate(df.itertuples(), start=1):
    document = row.Question
    embeddings = row.question_embedding
    qnaids_str = '|'.join(map(str, row.suggestions))  # Convert list of QnaIds to a string

    collection.add(
        documents=[document],
        embeddings=[embeddings],
        metadatas=[{
            "device": row.device,
            "answer": row.Answer,
            "QnaIds": qnaids_str,
            "QnaId": row.QnaId  
        }],
        ids=[str(i)]
    )

# Print the number of documents in the collection
print("Collection Count:", collection.count())

# Print a peek of documents in the collection
print("Collection Peek:", collection.peek())

# Function to query the collection
def query_collection(question):
    # Generate the embedding for the input question
    question_embedding = model.encode([question])

    # Query the collection for the closest match
    results = collection.query(
        query_embeddings=question_embedding,
        n_results=1  # Get the closest match
    )

    # Extract the answer and suggestions from the closest match
    if results['documents']:
        closest_match = results['documents'][0][0]
        metadata = results['metadatas'][0][0]
        answer = metadata['answer']
        qnaids_str = metadata['QnaIds']
        suggestions = []

        if qnaids_str:
            qnaids = qnaids_str.split('|')
            encountered_qnaids = set()  # Set to store encountered QnaIds
            for qnaid in qnaids:
                if qnaid not in encountered_qnaids:
                    aligned_question = df.loc[df['QnaId'] == int(qnaid), 'Question'].values[0]
                    suggestions.append(aligned_question)
                    encountered_qnaids.add(qnaid)

        return answer, suggestions[:3]  # Return the answer and top 3 unique aligned questions

    return None, None
