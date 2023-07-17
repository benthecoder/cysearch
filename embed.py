import ast
import os

import openai
import pandas as pd
import tiktoken
from dotenv import load_dotenv
from openai.embeddings_utils import get_embedding

load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")


if __name__ == "__main__":
    df = pd.read_csv("data/courses.csv")

    # embedding model parameters
    embedding_model = "text-embedding-ada-002"
    embedding_encoding = "cl100k_base"  # this the encoding for text-embedding-ada-002
    max_tokens = 8000  # the maximum for text-embedding-ada-002 is 8191

    encoding = tiktoken.get_encoding(embedding_encoding)
    df["n_tokens"] = df.combined.apply(lambda x: len(encoding.encode(x)))
    df["embedding"] = df.combined.apply(
        lambda x: get_embedding(x, engine=embedding_model)
    )
    df["embedding"] = df["embedding"].apply(ast.literal_eval)
    df.to_csv("data/course_w_embeddings.csv", index=False)
