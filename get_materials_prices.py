import urllib.request
import json
import csv
import sys
from datetime import datetime

BASE_URL = "https://index-api.tpso.go.th"
HEADERS = {
    'Content-Type': 'application/json',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

def fetch_master_data():
    """Fetches the list of provinces and available periods."""
    url = f"{BASE_URL}/OpenApi/CmiPrice/Month/MasterData"
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req) as r:
            data = json.loads(r.read().decode('utf-8'))
        return data
    except Exception as e:
        print(f"Error fetching master data: {e}", file=sys.stderr)
        return None

def fetch_prices(year, month, province_code):
    """Fetches building material prices for a given year, month, and province code."""
    url = f"{BASE_URL}/OpenApi/CmiPrice/Month"
    payload = {
        "year": int(year),
        "month": int(month),
        "type": int(province_code)
    }
    req = urllib.request.Request(
        url, 
        data=json.dumps(payload).encode('utf-8'),
        headers=HEADERS,
        method='POST'
    )
    try:
        with urllib.request.urlopen(req) as r:
            data = json.loads(r.read().decode('utf-8'))
        return data
    except Exception as e:
        print(f"Error fetching prices for province {province_code} ({year}/{month}): {e}", file=sys.stderr)
        return None

def main():
    # Phra Nakhon Si Ayutthaya (code 14) is set as default
    default_province_code = "14"
    query_year = None
    query_month = None
    province_code = default_province_code

    # Check command line arguments: get_materials_prices.py [province_code] [year] [month]
    if len(sys.argv) >= 4:
        province_code = sys.argv[1]
        try:
            query_year = int(sys.argv[2])
            query_month = int(sys.argv[3])
        except ValueError:
            print("Error: Year and Month must be integers.", file=sys.stderr)
            print("Usage: python3 get_materials_prices.py [province_code] [year_BE] [month]", file=sys.stderr)
            sys.exit(1)
    elif len(sys.argv) == 2 and sys.argv[1] in ["-h", "--help"]:
        print("Usage: python3 get_materials_prices.py [province_code] [year_BE] [month]")
        print("Example: python3 get_materials_prices.py 14 2567 3 (for Ayutthaya, March 2567)")
        sys.exit(0)
    elif len(sys.argv) > 1:
        print("Warning: Insufficient arguments. Using auto-detect for defaults.")
        print("Usage: python3 get_materials_prices.py [province_code] [year_BE] [month]")

    print("Fetching master data from TPSO Index API...")
    master = fetch_master_data()
    if not master:
        print("Failed to load master data. Exiting.")
        sys.exit(1)
        
    provinces = master.get("types", [])
    periods = master.get("dataAvailablePeriods", [])
    
    print(f"Found {len(provinces)} provinces.")
    
    # Auto-detect latest available month and year from master data if not provided
    if query_year is None or query_month is None:
        if periods:
            p = periods[0]
            query_month = p.get('endPeriod') or p.get('endMonth') or 3
            query_year = p.get('endYear') or p.get('endMonth') or 2567
            print(f"No date specified. Auto-detected latest: {query_month}/{query_year} (BE)")
        else:
            query_year = 2567
            query_month = 3
            print("Warning: Could not parse available periods. Using default 3/2567.")
    else:
        print(f"Using specified date: {query_month}/{query_year} (BE)")
        
    province_name = next((p["name"] for p in provinces if p["code"] == province_code), "Unknown")
    
    print(f"\nFetching prices in Real-time for:")
    print(f"- Province: {province_name} (Code: {province_code})")
    print(f"- Period: {query_month}/{query_year} (BE)")
    
    prices = fetch_prices(query_year, query_month, province_code)
    if not prices:
        print("Failed to fetch price data.")
        sys.exit(1)
        
    print(f"Received {len(prices)} items.")
    
    # Save to CSV
    filename = f"material_prices_province_{province_code}_{query_year}_{query_month}.csv"
    csv_fields = [
        "id", "type", "typeName", "commodityCode", "commodityNameTH", 
        "unitName", "curMonth", "curYear", "priceCur", "priceVAT", "createdAt"
    ]
    
    try:
        with open(filename, "w", newline="", encoding="utf-8-sig") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=csv_fields)
            writer.writeheader()
            for item in prices:
                row = {k: item.get(k) for k in csv_fields}
                writer.writerow(row)
        print(f"\nSuccessfully exported data to: {filename}")
    except Exception as e:
        print(f"Error exporting to CSV: {e}", file=sys.stderr)

if __name__ == '__main__':
    main()
