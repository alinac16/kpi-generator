from flask import Flask, request, jsonify, render_template
import pandas as pd
import io
import re
import os

# Initialize the Flask application
# The 'static_folder' and 'template_folder' arguments tell Flask where to find the files.
app = Flask(__name__, template_folder='templates', static_folder='static')

# --- In-memory storage for simplicity ---
# In a real app, you'd use a more robust storage solution
DATA_STORE = {
    'original_df': None,
    'cleaned_df': None
}

# --- API Endpoints ---

@app.route('/')
def index():
    """Renders the main HTML page from the 'templates' folder."""
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    """Handles CSV file upload and stores it in memory."""
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'No file part'})
    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'error': 'No selected file'})
    if file and file.filename.endswith('.csv'):
        try:
            # Read CSV into a pandas DataFrame
            csv_data = io.StringIO(file.stream.read().decode("UTF8"))
            df = pd.read_csv(csv_data)
            
            # Store the original DataFrame
            DATA_STORE['original_df'] = df.copy()
            DATA_STORE['cleaned_df'] = df.copy() # Initialize cleaned_df

            # Return success response with a preview
            return jsonify({
                'success': True,
                'filename': file.filename,
                'rows': len(df),
                'preview': df.head().to_dict('records')
            })
        except Exception as e:
            return jsonify({'success': False, 'error': f'Error processing file: {e}'})
    return jsonify({'success': False, 'error': 'Invalid file type. Please upload a CSV.'})

@app.route('/generate_steps', methods=['POST'])
def generate_steps():
    """
    SIMULATES an AI call to break down a high-level prompt into a list of cleaning steps.
    """
    data = request.get_json()
    prompt = data.get('prompt', '').lower()
    
    if not prompt:
        return jsonify({'error': 'Prompt is empty.'})

    # --- AI Simulation Logic ---
    # In a real app, this would be a call to an LLM
    steps = []
    if 'price' in prompt or 'currency' in prompt:
        steps.append("Remove currency symbols from the 'price' column.")
        steps.append("Convert the 'price' column to a numeric type.")
    if 'category' in prompt or 'categories' in prompt:
        steps.append("Standardize values in the 'category' column (e.g., 'Men's Apparel' -> 'Menswear').")
    if 'missing' in prompt or 'fill' in prompt:
        steps.append("Fill missing values in the 'stock_quantity' column with 0.")
    if 'typo' in prompt or 'correct' in prompt:
        steps.append("Correct common typos in the 'country' column.")
    if 'duplicate' in prompt:
        steps.append("Remove duplicate rows from the dataset.")

    if not steps:
        return jsonify({'error': "Sorry, I couldn't understand that request. Try being more specific about columns like 'price' or 'category'."})

    return jsonify({'steps': steps})

@app.route('/apply_cleaning', methods=['POST'])
def apply_cleaning():
    """
    Applies the list of cleaning steps to the stored DataFrame.
    SIMULATES the execution of each step.
    """
    data = request.get_json()
    steps = data.get('steps', [])
    
    if DATA_STORE['original_df'] is None:
        return jsonify({'success': False, 'error': 'No data uploaded yet.'})

    # Start with a fresh copy of the original data
    df = DATA_STORE['original_df'].copy()
    
    # --- Step Execution Logic ---
    # In a real app, an AI agent might generate and execute pandas/python code for each step.
    for step in steps:
        step_lower = step.lower()
        try:
            if 'remove currency' in step_lower and 'price' in step_lower:
                if 'price' in df.columns:
                    df['price'] = df['price'].astype(str).str.replace(r'[$\€,]', '', regex=True)
            
            elif 'convert' in step_lower and 'price' in step_lower and 'numeric' in step_lower:
                if 'price' in df.columns:
                    df['price'] = pd.to_numeric(df['price'], errors='coerce')

            elif 'standardize' in step_lower and 'category' in step_lower:
                if 'category' in df.columns:
                    replacements = {'Men\'s Apparel': 'Menswear', 'Gents Fashion': 'Menswear', 'Women\'s Fashion': 'Womenswear', 'Ladies Wear': 'Womenswear'}
                    df['category'] = df['category'].replace(replacements)

            elif 'fill missing' in step_lower and 'stock_quantity' in step_lower:
                 if 'stock_quantity' in df.columns:
                    df['stock_quantity'].fillna(0, inplace=True)
            
            elif 'correct' in step_lower and 'country' in step_lower:
                if 'country' in df.columns:
                    typo_map = {'USA': 'United States', 'U.S.A.': 'United States', 'Can': 'Canada'}
                    df['country'] = df['country'].replace(typo_map)

            elif 'remove duplicate' in step_lower:
                df.drop_duplicates(inplace=True)

        except Exception as e:
            return jsonify({'success': False, 'error': f'Error on step "{step}": {e}'})


    DATA_STORE['cleaned_df'] = df
    return jsonify({
        'success': True,
        'message': 'Cleaning steps applied successfully!',
        'preview': df.head().to_dict('records')
    })


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
    
