import os
import ast

import openai
import pandas as pd
import numpy as np
import streamlit as st
from dotenv import load_dotenv
from openai.embeddings_utils import cosine_similarity, get_embedding

load_dotenv()


if os.getenv("OPENAI_API_KEY") is not None:
    openai.api_key = os.getenv("OPENAI_API_KEY")
else:
    st.error("OPENAI_API_KEY environment variable not found")
    st.stop()


DATA_URL = "data/course_w_embeddings.csv"
EMBEDDING_MODEL = "text-embedding-ada-002"


@st.cache_data
def materialize_data():
    df = pd.read_csv(DATA_URL)
    # df['embedding'] = df.embedding.apply(ast.literal_eval)
    df.embedding = df.embedding.apply(eval).apply(np.array)  # this was faster

    return df


@st.cache_data
def magic(df, query, n=7):
    embedding = get_embedding(query, engine=EMBEDDING_MODEL)
    df["similarities"] = df.embedding.apply(lambda x: cosine_similarity(x, embedding))
    res = df.sort_values("similarities", ascending=False).head(n)
    return res


def display_card(result):
    card_style = """
    <style>
        .card {
            background-color: #1E2019;
            border: 1px solid #ddd;
            border-radius: 10px;
            box-shadow: 1px 1px 4px rgba(0, 0, 0, 0.1);
            padding: 20px;
            margin-bottom: 15px;
            transition: box-shadow 0.3s ease-in-out;
        }
        .card:hover {
            box-shadow: 1px 1px 8px rgba(0, 0, 0, 0.3);
        }
        .card-title {
            font-size: 20px;
            color: #fff;
        }
        .card-link {
            text-decoration: none;
            color: inherit;
        }
        .card-link:hover {
            text-decoration: underline;
        }
        .card-meta {
            font-size: 14px;
            color: #ccc;
            margin-bottom: 0px;
        }
    </style>
    """

    course_title = f"{result['course_code']}: {result['course_title']}"
    course_info = f"{result['course_info']}"
    credits = (
        f"{result['credit_number']}" if pd.notnull(result["credit_number"]) else ""
    )
    semester = f"{result['semester']}" if pd.notnull(result["semester"]) else "-"

    prerequisites = f"{result['prereq']}" if pd.notnull(result["prereq"]) else "-"

    card_content = f"""
    <div class="card">
        <h2 class="card-title">{course_title}</h2>
        <p class="card-meta">Credits: {credits} | Offered in {semester}</p>
        <p class="card-meta">Prerequisites: {prerequisites}</p>
        <p style="margin-top: 10px" >{course_info}</p>
    </div>
    """

    st.markdown(card_style, unsafe_allow_html=True)
    st.markdown(card_content, unsafe_allow_html=True)


if __name__ == "__main__":
    st.set_page_config(
        page_title="CySearch",
        page_icon="🔍",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    st.markdown(
        "<h1 style='text-align: center;'>CySearch 🔎</h1>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<p style='text-align: center; margin-top: -10px; color: #ccc;'>Find the right class for you using AI</p>",
        unsafe_allow_html=True,
    )

    df = materialize_data()

    query = st.text_input(
        "Start searching 👇",
        placeholder="your query here",
        key="search_input",
    )

    # provide some sample queries to choose from, when user clicks on one, it will be copied to the search input
    sample_queries = [
        "machine learning but for engineering students",
        "statistics classes that are practical and less theory",
        "CS classes that teaches algorithms",
    ]

    # or try query below
    st.write("Or try one of these queries:")

    # display sample queries as buttons, when clicked, copy the query to the search input
    col1, col2, col3 = st.columns(3)
    for i, sample_query in enumerate(sample_queries):
        if i % 3 == 0:
            col = col1
        elif i % 3 == 1:
            col = col2
        else:
            col = col3

        if col.button(sample_query):
            query = sample_query

    if query:
        res = magic(df, query)

        if res.empty:
            st.markdown("No results found.")
        else:
            for _, result in res.iterrows():
                display_card(result)
