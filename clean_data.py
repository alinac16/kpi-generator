import pandas as pd
import re
import io

# Helper function to clean column names for programmatic access
def clean_column_name(col_name):
    """
    Cleans a column name by converting to lowercase, replacing non-alphanumeric
    characters with underscores, and stripping leading/trailing underscores.
    """
    cleaned = re.sub(r'\W+', '_', col_name).strip('_').lower()
    return cleaned

# Comprehensive regex for common currency symbols and 3-letter ISO codes
CURRENCY_PATTERN = re.compile(
    r'(?P<currency>'
    r'thb|yen|cad|usd|eur|gbp|jpy|cny|inr|rub|krw|pln|try|idr|sgd|myr|php|vnd|ils|mxn|chf|aud|nzd|zar|'
    r'\$|€|£|¥|₹|₽|฿|₩|zł|₺|rp|s\$|rm|₱|₫|₪|kr|a\$|c\$|nz\$)',
    re.IGNORECASE
)

def extract_currency_and_amount(value):
    """
    Extracts currency code/symbol from a string value and returns the cleaned numeric string
    along with the extracted currency.
    Returns a pandas Series (cleaned_numeric_string, currency_code_found).
    
    Example: "THB 100.50" -> ("THB", 100) (if converting to int)
    Example: "N/A" -> (None, None)
    Example: "Some text" -> (None, None) (if no currency or valid number)
    """
    if pd.isna(value):
        return pd.Series([None, None])
    s_value = str(value).strip()

    currency_found = None
    numeric_part = s_value

    # Try to find currency pattern
    match = CURRENCY_PATTERN.search(s_value)
    if match:
        currency_found = match.group('currency').upper()
        # Replace the matched currency symbol/code from the string
        numeric_part = s_value.replace(match.group(0), '', 1).strip() # Use count=1 to replace only first occurrence

    # Remove any remaining non-numeric characters (except dot and leading minus)
    # This also handles commas for thousands separators (e.g. '1,000.00')
    cleaned_numeric_str = re.sub(r'[^\d.-]+', '', numeric_part)

    # Handle multiple decimal points (e.g., if "1.2.3" or "1,000.50" was parsed incorrectly)
    # Keep only the first decimal point
    if cleaned_numeric_str.count('.') > 1:
        parts = cleaned_numeric_str.split('.')
        cleaned_numeric_str = parts[0] + '.' + ''.join(parts[1:])
        
    # Ensure leading minus sign is correctly placed and only one exists
    if cleaned_numeric_str.count('-') > 1:
        cleaned_numeric_str = '-' + cleaned_numeric_str.replace('-', '')


    # Attempt to convert to int. Use float as intermediate for decimals, then int truncates.
    # If cleaned_numeric_str is empty or still invalid, float() will raise ValueError, resulting in None.
    number = None
    if cleaned_numeric_str: # Only try conversion if there's a string to convert
        try:
            number = int(float(cleaned_numeric_str))
        except ValueError:
            number = None # Keep as None if it's not a valid number

    return pd.Series([currency_found, number])


# --- Conceptual roles for columns (used to identify numeric cols for cleaning) ---
CONCEPTUAL_COLUMN_ROLES = {
    "Order ID": ["order_id", "invoice_id", "transaction_id"],
    "Product Name": ["product_name", "item_name", "product"],
    "Quantity": ["quantity", "units", "items_sold", "item_count"],
    "Price": ["price", "item_price", "unit_price"],
    "Sales Amount": ["sales", "revenue", "amount", "total", "subtotal", "order_total", "line_total"],
    "Customer ID": ["customer_id", "user_id", "buyer_id"],
    "Order Date": ["order_date", "date", "transaction_date", "timestamp", "created_at"],
    "Category": ["product_category", "category", "item_category"],
    "Brand": ["brand", "product_brand"],
    "Shipping Cost": ["shipping_cost", "delivery_fee"],
    "Discount Amount": ["discount_amount", "coupon_discount"],
    "Payment Method": ["payment_method", "payment_type"],
    "Country": ["country", "billing_country", "shipping_country"],
    "City": ["city", "billing_city", "shipping_city"],
    "Website Visits": ["website_visits", "sessions", "traffic", "page_views"]
}

# Simplified mapping for identifying columns that should be treated as numeric in cleaning
NUMERIC_CONCEPTUAL_ROLES_FOR_CLEANING = {
    "Sales Amount": CONCEPTUAL_COLUMN_ROLES["Sales Amount"],
    "Quantity": CONCEPTUAL_COLUMN_ROLES["Quantity"],
    "Price": CONCEPTUAL_COLUMN_ROLES["Price"],
    "Shipping Cost": CONCEPTUAL_COLUMN_ROLES["Shipping Cost"],
    "Discount Amount": CONCEPTUAL_COLUMN_ROLES["Discount Amount"],
    "Website Visits": CONCEPTUAL_COLUMN_ROLES["Website Visits"]
}


def perform_data_cleaning(df_original):
    """
    Performs comprehensive data cleaning and standardization on the DataFrame.
    Includes enhanced currency extraction and numeric conversion, creating new
    '[original_column_name]_currency' columns for extracted currencies.

    Args:
        df_original (pd.DataFrame): The raw DataFrame to be cleaned.

    Returns:
        pd.DataFrame: The cleaned and standardized DataFrame.
    """
    df = df_original.copy()

    # 1. Clean column names to make them programmatic
    df.columns = [clean_column_name(col) for col in df.columns]

    # Identify potential monetary/numeric columns based on the conceptual roles.
    potential_numeric_cols = set()
    for role_aliases in NUMERIC_CONCEPTUAL_ROLES_FOR_CLEANING.values():
        for alias in role_aliases:
            for col in df.columns:
                if alias in col:
                    potential_numeric_cols.add(col)
                    print("Final numeric columns to process for currency:", potential_numeric_cols)

    
    # 2. Apply currency extraction and numeric conversion to identified potential monetary columns
    # Create a list to track new currency columns to ensure they are moved to the end
    new_currency_columns = [] 
    for col in potential_numeric_cols:
        # Only process if the column is of object (string) type or mixed type initially
        # This prevents errors on columns that are already purely numeric (int/float)
        if df[col].dtype == 'object' or pd.api.types.is_string_dtype(df[col]):
            
            # Apply the extraction function, which returns a Series for each row
            currency_and_numeric_parts = df[col].apply(extract_currency_and_amount)
            
            extracted_currencies_for_col = currency_and_numeric_parts.iloc[:, 0]
            numeric_values_for_col = currency_and_numeric_parts.iloc[:, 1]

            # Create a new column for currency for this specific monetary column
            currency_col_name = f"{col}_currency"
            df[currency_col_name] = extracted_currencies_for_col
            new_currency_columns.append(currency_col_name) # Add to list for later reordering
            
            # Update the original column with cleaned numeric values
            df[col] = numeric_values_for_col


    # 3. Ensure all relevant columns are numeric (Int64 for integers, float64 otherwise)
    # This step is crucial after the string manipulation
    for col in df.columns:
        if col in potential_numeric_cols: # Only process columns that were identified as potential numeric
            try:
                # Attempt to convert to nullable integer type
                df[col] = pd.to_numeric(df[col], errors='coerce').astype('Int64')
            except Exception: # Fallback for very large numbers or other issues
                df[col] = pd.to_numeric(df[col], errors='coerce')


    # 4. Date/Time Standardization
    possible_date_cols = ['order_date', 'date', 'transaction_date', 'timestamp', 'created_at']
    for col_name in possible_date_cols:
        if col_name in df.columns:
            original_series = df[col_name].copy()
            df[col_name] = pd.to_datetime(df[col_name], errors='coerce')
            if df[col_name].isnull().all() and not original_series.isnull().all():
                df[col_name] = original_series
            else:
                df[col_name] = df[col_name].dt.strftime('%Y-%m-%d %H:%M:%S').fillna('')


    # 5. General string cleaning (whitespace & case) for remaining object/string columns
    for col in df.select_dtypes(include=['object', 'string']).columns:
        df[col] = df[col].astype(str).str.strip().str.lower()


    # 6. Handle Missing Values (basic strategy)
    for col in df.columns:
        # Fill numeric NaNs with 0 for columns that are part of KPI calculations
        # Ensure we check for actual numeric dtype AFTER conversion attempts
        if pd.api.types.is_numeric_dtype(df[col]) and col in potential_numeric_cols:
            df[col] = df[col].fillna(0)
        # For the newly created currency columns, fill NaN with 'N/A' if it's still missing after extraction
        if col in new_currency_columns:
            df[col] = df[col].fillna('N/A')

    # Ensure newly created currency columns are at the end of the DataFrame
    # Preserve original column order as much as possible, just move new ones
    original_cols_ordered = [col for col in df.columns if col not in new_currency_columns]
    df = df[original_cols_ordered + new_currency_columns]

    return df

if __name__ == "__main__":
    import os

    # Load the data
    csv_path = "short_tiktok.csv"  # Make sure it's in the same folder
    df_raw = pd.read_csv(csv_path)

    # Clean the data
    df_cleaned = perform_data_cleaning(df_raw)

    # Save the cleaned output to a new CSV
    output_path = "cleaned_tiktok.csv"
    df_cleaned.to_csv(output_path, index=False)

    print(f"Cleaned data saved to: {os.path.abspath(output_path)}")

    # Optionally preview some results
    print(df_cleaned.head())
    print("Columns:", df_cleaned.columns.tolist())
