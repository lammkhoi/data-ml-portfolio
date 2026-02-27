"""
Portfolio Analyser
==================
Utility functions for analysing investment portfolios:
  - Find tickers held in common across multiple portfolios
  - Rank tickers by how many portfolios hold them
  - Analyse product catalogues: most expensive, best-selling, most profitable

All functions use type hints and clean Pythonic patterns (built-ins, Counter,
sorted with lambda keys) — no pandas or external dependencies required.
"""

import csv
from collections import Counter
from typing import Optional


# ---------------------------------------------------------------------------
# Portfolio analysis
# ---------------------------------------------------------------------------

def common_investments(*portfolios: set[str]) -> list[str]:
    """
    Return tickers held in ALL of the provided portfolios, sorted alphabetically.

    Parameters
    ----------
    *portfolios : any number of sets of ticker strings

    Returns
    -------
    Sorted list of common tickers, or [] if none provided.

    Examples
    --------
    >>> p1 = {"AAPL", "GOOGL", "NVDA"}
    >>> p2 = {"GOOGL", "NVDA", "MSFT"}
    >>> common_investments(p1, p2)
    ['GOOGL', 'NVDA']
    """
    if not portfolios:
        return []
    common = set.intersection(*portfolios)
    return sorted(common)


def popular_investments(
    *portfolios: set[str],
    threshold: int = 2,
) -> list[tuple[str, int]]:
    """
    Return tickers held in at least `threshold` portfolios, ranked by popularity.

    Parameters
    ----------
    *portfolios : any number of sets of ticker strings
    threshold   : minimum number of portfolios a ticker must appear in

    Returns
    -------
    List of (ticker, count) tuples sorted by count descending, then ticker ascending.

    Examples
    --------
    >>> p1 = {"AAPL", "GOOGL", "NVDA"}
    >>> p2 = {"GOOGL", "NVDA", "MSFT"}
    >>> p3 = {"NVDA", "AMD"}
    >>> popular_investments(p1, p2, p3, threshold=2)
    [('NVDA', 3), ('GOOGL', 2)]
    """
    counts = Counter()
    for portfolio in portfolios:
        counts.update(portfolio)

    filtered = [(ticker, count) for ticker, count in counts.items() if count >= threshold]
    return sorted(filtered, key=lambda x: (-x[1], x[0]))


# ---------------------------------------------------------------------------
# Product catalogue analysis
# ---------------------------------------------------------------------------

def most_expensive(products: list[dict], k: int = 3) -> list[dict]:
    """Return the top-k products by price (ties broken alphabetically by name)."""
    return sorted(products, key=lambda p: (-p['price'], p['name']))[:k]


def bestsellers(products: list[dict], k: int = 3) -> list[dict]:
    """Return the top-k products by units sold (ties broken alphabetically by name)."""
    return sorted(products, key=lambda p: (-p['sales'], p['name']))[:k]


def most_profitable(products: list[dict], k: int = 3) -> list[dict]:
    """Return the top-k products by total revenue = price × sales."""
    enriched = [{**p, 'profit': p['price'] * p['sales']} for p in products]
    return sorted(enriched, key=lambda p: (-p['profit'], p['name']))[:k]


def print_tops(products: list[dict], k: int = 3) -> None:
    """
    Print the top-k most expensive, best-selling, and most profitable products.

    Parameters
    ----------
    products : list of dicts with keys 'name', 'price', 'sales'
    k        : number of entries to display per category
    """
    if k > len(products):
        print(f"[ERROR] k={k} exceeds the number of products ({len(products)}).")
        return

    print(f"\nTop {k} most expensive products:")
    for rank, p in enumerate(most_expensive(products, k), start=1):
        print(f"  {rank}. {p['name']:20s}  ${p['price']:.2f}")

    print(f"\nTop {k} best-selling products:")
    for rank, p in enumerate(bestsellers(products, k), start=1):
        print(f"  {rank}. {p['name']:20s}  {p['sales']:,} units sold")

    print(f"\nTop {k} most profitable products:")
    for rank, p in enumerate(most_profitable(products, k), start=1):
        print(f"  {rank}. {p['name']:20s}  ${p['profit']:,.2f} revenue")


def read_products(filename: str) -> list[dict]:
    """
    Read a product catalogue from a CSV file.

    Expected CSV columns: name, price, sales

    Parameters
    ----------
    filename : path to the CSV file

    Returns
    -------
    List of product dicts, or [] if the file is not found.
    """
    products = []
    try:
        with open(filename, mode='r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                products.append({
                    'name':  row['name'],
                    'price': float(row['price']),
                    'sales': int(row['sales']),
                })
    except FileNotFoundError:
        print(f"[ERROR] File not found: '{filename}'")
    return products


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # --- Portfolio analysis demo ---
    print("=" * 50)
    print("PORTFOLIO ANALYSIS")
    print("=" * 50)

    portfolio1 = {"AAPL", "GOOGL", "TSLA", "NVDA", "JPM"}
    portfolio2 = {"GOOGL", "AMZN", "MSFT", "NKE",  "NVDA"}
    portfolio3 = {"AMD",   "PFE",  "AMZN", "MSFT", "GOOGL", "NVDA"}
    portfolio4 = {"GOOGL", "AMD",  "NFLX"}

    print("\nTickers common to portfolios 1, 2, and 3:")
    print(" ", common_investments(portfolio1, portfolio2, portfolio3))

    print("\nTickers common to portfolios 3 and 4:")
    print(" ", common_investments(portfolio3, portfolio4))

    print("\nTickers held by ≥ 2 portfolios:")
    for ticker, count in popular_investments(portfolio1, portfolio2, portfolio3, portfolio4, threshold=2):
        print(f"  {ticker:8s}  held in {count} portfolios")

    print("\nTickers held by ≥ 3 portfolios:")
    for ticker, count in popular_investments(portfolio1, portfolio2, portfolio3, portfolio4, threshold=3):
        print(f"  {ticker:8s}  held in {count} portfolios")

    # --- Product catalogue demo ---
    print("\n" + "=" * 50)
    print("PRODUCT CATALOGUE ANALYSIS")
    print("=" * 50)

    clothes = [
        {'name': 'T-Shirt',  'price': 19.99, 'sales': 300},
        {'name': 'Jeans',    'price': 49.99, 'sales': 200},
        {'name': 'Sweater',  'price': 34.99, 'sales': 150},
        {'name': 'Jacket',   'price': 89.99, 'sales':  80},
        {'name': 'Dress',    'price': 59.99, 'sales': 120},
        {'name': 'Shorts',   'price': 29.99, 'sales': 180},
    ]
    print_tops(clothes, k=3)
