import os
import pandas as pd
from datetime import datetime, timedelta
from mcp.server.fastmcp import FastMCP
from mcp.types import TextContent


# Get absolute path to the CSV in the same folder as this script
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_FILE = os.path.join(BASE_DIR, "transactions.csv")



# Load and save helpers
def load_transactions():
    try:
        return pd.read_csv(CSV_FILE, parse_dates=["Date"])
    except FileNotFoundError:
        return pd.DataFrame(columns=["Date", "Category", "Amount"])

def save_transactions(df):
    df.to_csv(CSV_FILE, index=False)

# Initialize MCP server
mcp = FastMCP("Finance MCP", instructions="Query and update your personal finance CSV.")


# -----------------------------------------------------
# Tool 1: Get recent expenses (last 7 days)
# -----------------------------------------------------
@mcp.tool()
def get_recent_expenses():
    """Fetch expenses from the last 7 days."""
    df = load_transactions()
    if df.empty:
        return TextContent(type="text", text="No expense records found.")

    today = datetime.today()
    seven_days_ago = today - timedelta(days=7)
    recent = df[df["Date"] >= seven_days_ago]

    if recent.empty:
        return TextContent(type="text", text="No expenses in the last 7 days.")

    output = "\n".join([
        f"{row.Date.strftime('%Y-%m-%d')}: {row.Category} - ₹{row.Amount}"
        for _, row in recent.iterrows()
    ])
    return TextContent(type="text", text=output)


# -----------------------------------------------------
# Tool 2: Get monthly summary
# -----------------------------------------------------
@mcp.tool()
def get_monthly_summary(month: str):
    """
    Get total expenses for a given month.
    Month format: YYYY-MM (e.g., 2025-08)
    """
    df = load_transactions()
    if df.empty:
        return TextContent(type="text", text="No expense records found.")

    df["MonthStr"] = df["Date"].dt.strftime("%Y-%m")
    total = df[df["MonthStr"] == month]["Amount"].sum()
    return TextContent(type="text", text=f"Total expenses for {month}: ₹{total}")

# -----------------------------------------------------
# Tool 3: Add a new expense
# -----------------------------------------------------
@mcp.tool()
def add_expense(category: str, amount: float, description: str = ""):
    """Add a new expense record."""
    df = load_transactions()
    today_str = datetime.today().strftime("%Y-%m-%d %H:%M:%S")  # Standardized format

    new_row = pd.DataFrame([{
        "Date": today_str,
        "Description": description,
        "Category": category,
        "Amount": amount * (-1)
    }])

    df = pd.concat([df, new_row], ignore_index=True)
    save_transactions(df)

    return TextContent(type="text", text=f"Added: {category} - ₹{amount}")

# -----------------------------------------------------
# Tool 4: Get total spent by category in a month/year
# -----------------------------------------------------
@mcp.tool()
def get_total_spent(category: str, month: int, year: int) -> dict:
    """
    Get total spent for a category in a given month and year.
    """
    df = load_transactions()
    if df.empty:
        return {"error": "No expense records found."}

    filtered = df[
        (df["Category"].str.lower() == category.lower()) &
        (df["Date"].dt.month == month) &
        (df["Date"].dt.year == year)
    ]
    total = filtered["Amount"].sum()
    return {
        "category": category,
        "month": month,
        "year": year,
        "total_spent": total
    }

# -----------------------------------------------------
# Tool 5: List all categories
# -----------------------------------------------------
@mcp.tool()
def list_categories() -> list:
    """List all unique spending categories."""
    df = load_transactions()
    if df.empty:
        return []
    return sorted(df["Category"].unique().tolist())

# -----------------------------------------------------