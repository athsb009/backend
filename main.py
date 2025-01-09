from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

from typing import Optional  
import requests

app = FastAPI()


# CORS Configuration: Allow requests from the React frontend
origins = [
    "https://valueglance-5rijcsfoc-athsb009s-projects.vercel.app", 
    "http://localhost:3000",  
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"], 
    allow_headers=["*"],  
)

# API URL for fetching financial data for Apple 
API_URL = "https://financialmodelingprep.com/api/v3/income-statement/AAPL?period=annual&apikey=pCq6P0dhgukB49VuZbnmrn14ZSpbbo3f"
cached_data = None  # Cache to store the financial data fetched from the API

@app.on_event("startup")
def preload_data():
    """
    Preloads financial data when the server starts.
    This ensures data is available immediately without waiting for the first request.
    """
    global cached_data
    try:
        response = requests.get(API_URL)
        response.raise_for_status()  
        cached_data = response.json()  # Stores the fetched data in the cache
        print("Data preloaded successfully.")
    except Exception as e:
        print(f"Error preloading data: {e}")

@app.get("/fetch-data")
def fetch_data():
    """
    Endpoint to fetch fresh data from the Financial Modeling Prep API.
    Returns the fetched data as a JSON response.
    """
    global cached_data
    response = requests.get(API_URL)  # Fetches data from the API
    if response.status_code == 200:
        cached_data = response.json()  # Updates the cached data
        return {"status": "success", "data": cached_data}  # Returns the data
    return {"status": "error", "message": response.text}  # Handles API errors

@app.get("/filter-data")
def filter_data(
    start_date: Optional[str] = Query(None),  #start date filter
    end_date: Optional[str] = Query(None),    #end date filter
    min_revenue: Optional[float] = Query(None),  #minimum revenue filter
    max_revenue: Optional[float] = Query(None),  #maximum revenue filter
    min_net_income: Optional[float] = Query(None),  #minimum net income filter
    max_net_income: Optional[float] = Query(None),  #maximum net income filter
    sort_by: Optional[str] = Query("date"),  #sort field is 'date'
    order: Optional[str] = Query("asc"),     #sort order is 'ascending'
):
    """
    Endpoint to filter and sort financial data based on query parameters.
    Supports filtering by date range, revenue range, and net income range.
    Allows sorting by date, revenue, or net income in ascending/descending order.
    """
    global cached_data
    if not cached_data:
        return {"status": "error", "message": "No data available. Fetch data first."}

    # Makes a copy of the cached data to avoid modifying the original data
    filtered_data = cached_data.copy()

    # Filter by date range
    if start_date or end_date:
        filtered_data = [
            item for item in filtered_data
            if (not start_date or item["date"] >= start_date)  # Includes items after start_date
            and (not end_date or item["date"] <= end_date)    # Includes items before end_date
        ]

    # Filter by revenue range
    if min_revenue or max_revenue:
        filtered_data = [
            item for item in filtered_data
            if (not min_revenue or item["revenue"] >= min_revenue)  # Includes items with revenue >= min_revenue
            and (not max_revenue or item["revenue"] <= max_revenue)  # Includes items with revenue <= max_revenue
        ]

    # Filter by net income range
    if min_net_income or max_net_income:
        filtered_data = [
            item for item in filtered_data
            if (not min_net_income or item["netIncome"] >= min_net_income)  # Includes items with net income >= min_net_income
            and (not max_net_income or item["netIncome"] <= max_net_income)  # Includes items with net income <= max_net_income
        ]

    # Sorting Logic
    reverse = order == "desc"  # Determines if sorting should be descending
    if sort_by in filtered_data[0]:  # Checks if the sort_by field exists in the data
        filtered_data.sort(key=lambda x: x.get(sort_by, 0), reverse=reverse)  # Sorts the data
    else:
        return {"status": "error", "message": f"Invalid sort field: {sort_by}"}  # Handles invalid sort field

    # Returns the filtered and sorted data
    return {"status": "success", "data": filtered_data}
