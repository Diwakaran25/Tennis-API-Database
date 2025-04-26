import streamlit as st
import pandas as pd
import mysql.connector

# --- Database Connection ---
@st.cache_resource
def get_connection():
    mydb = mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="tennis_db"
    )
    return mydb

mydb = get_connection()

# --- Helper Function ---
def fetch_query(query):
    mycursor = mydb.cursor()
    mycursor.execute(query)
    rows = mycursor.fetchall()
    columns = [i[0] for i in mycursor.description]
    return pd.DataFrame(rows, columns=columns)

# --- Pages ---
def homepage():
    st.title("🎾 Tennis Analytics Dashboard")

    total_competitors = fetch_query("SELECT COUNT(*) as total FROM Competitors;")
    countries_count = fetch_query("SELECT COUNT(DISTINCT country) as countries FROM Competitors;")
    highest_points = fetch_query("SELECT MAX(points) as max_points FROM Competitor_Rankings;")

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Competitors", total_competitors['total'][0])
    col2.metric("Countries Represented", countries_count['countries'][0])
    col3.metric("Highest Points", highest_points['max_points'][0])

def search_filter():
    st.title("🔍 Search and Filter Competitors")

    name = st.text_input("Search Competitor by Name")
    rank_range = st.slider("Select Rank Range", 1, 500, (1, 100))
    country_list = fetch_query("SELECT DISTINCT country FROM Competitors;")['country'].tolist()
    country = st.selectbox("Select Country", ["All"] + country_list)
    points = st.slider("Minimum Points", 0, 5000, 0)

    query = f"""
    SELECT c.name, r.rank, r.points, c.country
    FROM Competitors c
    JOIN Competitor_Rankings r ON c.competitor_id = r.competitor_id
    WHERE (c.name LIKE '%{name}%')
    AND (r.rank BETWEEN {rank_range[0]} AND {rank_range[1]})
    AND (r.points >= {points})
    {f"AND c.country = '{country}'" if country != "All" else ""}
    ORDER BY r.rank ASC;
    """

    data = fetch_query(query)
    st.dataframe(data)

def competitor_details():
    st.title("👤 Competitor Details Viewer")

    competitors = fetch_query("SELECT name FROM Competitors;")['name'].tolist()
    selected = st.selectbox("Select a Competitor", competitors)

    query = f"""
    SELECT c.name, r.rank, r.movement, r.competitions_played, c.country
    FROM Competitors c
    JOIN Competitor_Rankings r ON c.competitor_id = r.competitor_id
    WHERE c.name = '{selected}';
    """

    details = fetch_query(query)
    st.table(details)

def country_analysis():
    st.title("🌎 Country-Wise Analysis")

    query = """
    SELECT c.country, COUNT(c.competitor_id) as total_competitors,
           AVG(r.points) as avg_points
    FROM Competitors c
    JOIN Competitor_Rankings r ON c.competitor_id = r.competitor_id
    GROUP BY c.country
    ORDER BY total_competitors DESC;
    """

    country_stats = fetch_query(query)
    st.dataframe(country_stats)
    st.bar_chart(country_stats.set_index('country')['total_competitors'])

def leaderboards():
    st.title("🏆 Leaderboards")

    top_n = st.slider("Top N Competitors", 1, 50, 10)

    query_rank = f"""
    SELECT c.name, r.rank, r.points
    FROM Competitors c
    JOIN Competitor_Rankings r ON c.competitor_id = r.competitor_id
    ORDER BY r.rank ASC
    LIMIT {top_n};
    """
    rank_leaderboard = fetch_query(query_rank)
    st.subheader("Top Competitors by Rank")
    st.table(rank_leaderboard)

    query_points = f"""
    SELECT c.name, r.points
    FROM Competitors c
    JOIN Competitor_Rankings r ON c.competitor_id = r.competitor_id
    ORDER BY r.points DESC
    LIMIT {top_n};
    """
    points_leaderboard = fetch_query(query_points)
    st.subheader("Top Competitors by Points")
    st.table(points_leaderboard)

# --- Sidebar Navigation ---
page = st.sidebar.selectbox("Navigate", (
    "Homepage Dashboard",
    "Search and Filter Competitors",
    "Competitor Details Viewer",
    "Country-Wise Analysis",
    "Leaderboards"
))

if page == "Homepage Dashboard":
    homepage()
elif page == "Search and Filter Competitors":
    search_filter()
elif page == "Competitor Details Viewer":
    competitor_details()
elif page == "Country-Wise Analysis":
    country_analysis()
elif page == "Leaderboards":
    leaderboards()