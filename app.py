import os
import pandas as pd
from dotenv import load_dotenv
import google.generativeai as genai
import json

def analyze_ecommerce_data_with_ai():
    """
    Analyzes e-commerce CSV files using a Google Gemini AI agent to identify KPIs
    and provide actionable insights based on a detailed prompt and specified platform.
    It automatically switches to cross-platform analysis if multiple CSVs are detected.
    It expects CSV files in an 'ecommerce_data' directory and GOOGLE_API_KEY
    in a .env file. Outputs KPI analysis by embedding it directly into 'kpi_report.html'.
    """
    # 1. Load environment variables from .env file
    load_dotenv()
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

    if not GOOGLE_API_KEY:
        print("Error: 'GOOGLE_API_KEY' not found in your .env file.")
        print("Please create a .env file in the same directory as this script and add: GOOGLE_API_KEY='YOUR_API_KEY_HERE'")
        print("Exiting...")
        return

    # Configure the Google Generative AI with the loaded API key
    genai.configure(api_key=GOOGLE_API_KEY)
    # Using 'gemini-1.5-flash' as it's generally available and efficient for this task.
    model = genai.GenerativeModel('gemini-1.5-flash')

    # --- USER CONFIGURATION: Default platform for single-CSV analysis ---
    # This will be used IF ONLY ONE CSV IS PROVIDED.
    # Options: 'TikTok Shop', 'Shopee', 'Lazada', 'Amazon', 'General'
    default_selected_platform = 'General' # <--- CHANGE THIS VALUE for single-file analysis
    # -------------------------------------------------------------------

    # Define the list of available platforms for the dropdown and AI context.
    AVAILABLE_PLATFORMS = ['General', 'TikTok Shop', 'Shopee', 'Lazada', 'Amazon', 'Cross-Platform'] # Added 'Cross-Platform' for context

    # 2. Define the directory where CSV files are expected
    data_directory = "ecommerce_data"
    if not os.path.exists(data_directory):
        os.makedirs(data_directory)
        print(f"Created directory '{data_directory}'.")
        print(f"Please place all your e-commerce CSV files inside '{data_directory}' and re-run the script.")
        print("Exiting...")
        return

    # 3. Load and inspect CSV data from the specified directory
    all_dataframes = {}
    csv_files = [f for f in os.listdir(data_directory) if f.endswith('.csv')]

    if not csv_files:
        print(f"No CSV files found in '{data_directory}'.")
        print(f"Please place your e-commerce CSV files there and re-run the script.")
        print("Exiting...")
        return

    print(f"Found {len(csv_files)} CSV file(s) in '{data_directory}'. Loading data...")
    for file_name in csv_files:
        file_path = os.path.join(data_directory, file_name)
        try:
            df = pd.read_csv(file_path)
            all_dataframes[file_name] = df
            print(f"Successfully loaded '{file_name}' with {len(df.columns)} columns and {len(df)} rows.")
        except pd.errors.EmptyDataError:
            print(f"Warning: '{file_name}' is empty. Skipping.")
            continue
        except Exception as e:
            print(f"Error loading '{file_name}': {e}. Skipping this file.")
            continue

    if not all_dataframes:
        print("No CSV files could be loaded successfully or all were empty. Exiting.")
        return

    # Determine the actual analysis context based on number of CSVs
    if len(csv_files) > 1:
        analysis_context_platform = 'Cross-Platform'
        print("\nMultiple CSV files detected. Analysis will be performed in 'Cross-Platform' mode.")
    else:
        # Use the default_selected_platform if only one CSV is present
        analysis_context_platform = default_selected_platform
        if analysis_context_platform not in AVAILABLE_PLATFORMS: # Ensure it's a valid specific platform
            print(f"Warning: '{analysis_context_platform}' is not a recognized platform for single-file analysis. Defaulting to 'General'.")
            analysis_context_platform = 'General'
        print(f"\nSingle CSV file detected. Analysis will be performed for '{analysis_context_platform}' platform.")


    # 4. Construct a detailed prompt for the AI model
    prompt_parts = []
    prompt_parts.append("You are an expert e-commerce data analyst AI agent. Your role is to analyze CSV data and provide actionable business insights through compelling data storytelling. The analysis should consider both individual platform performance and cross-platform trends if multiple datasets are provided.\n")
    prompt_parts.append("The headers within the CSV files might be in English or Thai, and you must interpret them correctly.\n\n")

    prompt_parts.append("ANALYSIS PROCESS:\n")
    prompt_parts.append("1. Parse CSV column headers to identify data types and business context.\n")
    prompt_parts.append("2. Suggest relevant analyses based on detected patterns and potential KPIs.\n")
    prompt_parts.append("3. For each identified KPI, provide narrative-driven insights with specific recommendations.\n\n")

    prompt_parts.append("COLUMN PATTERN RECOGNITION (for context, you should infer from actual data too):\n")
    prompt_parts.append("- Revenue/Financial: price, cost, revenue, sales, amount, total, fee, commission\n")
    prompt_parts.append("- Products: product, item, sku, name, title, brand, category, type\n")
    prompt_parts.append("- Quantities: quantity, units, sold, count, volume, stock\n")
    prompt_parts.append("- Temporal: date, time, created, updated, timestamp, day, month, year\n")
    prompt_parts.append("- Customer: customer, user, buyer, client, email, phone\n")
    prompt_parts.append("- Performance: views, clicks, conversion, rating, review, engagement\n")
    prompt_parts.append("- Geography: country, city, region, location, address, shipping\n")
    prompt_parts.append("- Risk: return, refund, cancel, dispute, complaint, issue\n\n")

    # Add platform-specific intelligence based on the detected analysis context
    prompt_parts.append("PLATFORM-SPECIFIC INTELLIGENCE:\n")
    if analysis_context_platform == 'TikTok Shop':
        prompt_parts.append("- Focus on content performance, viral metrics, influencer data relevant to TikTok Shop.\n")
    elif analysis_context_platform == 'Shopee':
        prompt_parts.append("- Emphasize seller ratings, shipping costs, promotional impact specific to Shopee.\n")
    elif analysis_context_platform == 'Lazada':
        prompt_parts.append("- Highlight competitive pricing, brand performance, logistics strategies relevant to Lazada.\n")
    elif analysis_context_platform == 'Amazon':
        prompt_parts.append("- Analyze reviews, rankings, advertising effectiveness, and FBA considerations for Amazon.\n")
    elif analysis_context_platform == 'Cross-Platform':
        prompt_parts.append("- **Crucially, perform a cross-platform analysis.** Focus on KPIs that compare performance across different channels. Identify common strengths, weaknesses, and opportunities across the entire e-commerce ecosystem. Look for discrepancies, leading platforms, and areas for consolidated strategy. Suggest aggregated metrics where appropriate.\n")
    else: # 'General' or unrecognized (should be handled by pre-check now)
        prompt_parts.append("- Adapt to any e-commerce platform based on column patterns, providing general but actionable insights.\n")
    prompt_parts.append("\n")

    prompt_parts.append("STORYTELLING STRUCTURE FOR EACH KPI INSIGHT:\n")
    prompt_parts.append("1.  **Hook**: Lead with the most compelling finding.\n")
    prompt_parts.append("2.  **Context**: Explain what the data represents for this KPI. Format this as a single string, using Markdown for formatting (e.g., **important text**).\n")
    prompt_parts.append("3.  **Key Findings**: Provide 3-5 bullet points. These bullet points MUST include specific, illustrative numerical findings or trends derived from the provided sample data or based on common e-commerce data patterns (e.g., 'AOV increased by 15% last month', 'Top 3 products account for 40% of sales', 'Conversion rate is X%'). Act as if you have seen the full dataset. Format this as a single string, using Markdown for formatting (e.g., * list item).\n")
    prompt_parts.append("4.  **Business Impact**: Why this KPI's performance matters for revenue/growth. Format this as a single string, using Markdown for formatting.\n")
    prompt_parts.append("5.  **Actionable Recommendations**: Specific next steps with priorities. Format this as a single string, using Markdown for formatting.\n\n")

    prompt_parts.append("INSIGHT CATEGORIES:\n")
    prompt_parts.append("- Quick Wins: High impact, low effort (e.g., trend identification, top performers).\n")
    prompt_parts.append("- Standard Analysis: Medium complexity (e.g., segmentation, seasonality).\n")
    prompt_parts.append("- Advanced Insights: High complexity (e.g., predictive patterns, optimization).\n\n")

    prompt_parts.append("COMMUNICATION STYLE:\n")
    prompt_parts.append("- Use clear, business-friendly language.\n")
    prompt_parts.append("- Include specific numbers and percentages (real or illustrative, based on data context).\n")
    prompt_parts.append("- Provide context (industry benchmarks when possible, based on general knowledge).\n")
    prompt_parts.append("- Focus on actionable insights over raw statistics.\n")
    prompt_parts.append("- Use emojis strategically for visual appeal.\n")
    prompt_parts.append("- Structure with headers and bullet points for scanability.\n\n")

    prompt_parts.append("RECOMMENDATIONS FORMAT:\n")
    prompt_parts.append("- Prioritize by impact and ease of implementation.\n")
    prompt_parts.append("- Include specific next steps.\n")
    prompt_parts.append("- Suggest monitoring frequencies.\n")
    prompt_parts.append("- Mention tools/methods for execution (general, not specific software).\n")
    prompt_parts.append("- Consider resource requirements (e.g., 'requires marketing budget', 'needs development').\n\n")

    prompt_parts.append("VISUAL GUIDANCE (Suggest appropriate chart types):\n")
    prompt_parts.append("- Suggest appropriate chart types for each insight (e.g., bar chart, line graph, pie chart).\n")
    prompt_parts.append("- Recommend simple, clear visualizations.\n")
    prompt_parts.append("- Focus on charts that support the narrative.\n")
    prompt_parts.append("- Avoid overwhelming with too many visuals.\n\n")

    prompt_parts.append("AVOID:\n")
    prompt_parts.append("- Generic insights that apply to any business.\n")
    prompt_parts.append("- Technical jargon without explanation.\n")
    prompt_parts.append("- Analysis without clear business implications.\n")
    prompt_parts.append("- Recommendations without specific actions.\n")
    prompt_parts.append("- Overcomplicating simple patterns.\n\n")

    prompt_parts.append("Your final output MUST be a JSON object with a single top-level key `kpis` which contains an array of KPI objects. Each KPI object MUST include the following details in both English and Thai:\n")
    prompt_parts.append("1.  `name_en`: English KPI Name\n")
    prompt_parts.append("2.  `name_th`: Thai KPI Name\n")
    prompt_parts.append("3.  `description_en`: English Description. MUST be a single string formatted with Markdown for any structure (e.g., **bold**, * bullet points).\n")
    prompt_parts.append("4.  `description_th`: Thai Description. MUST be a single string formatted with Markdown for any structure.\n")
    prompt_parts.append("5.  `columns_used`: List of column names used (exact match from CSV headers). If a KPI is cross-platform, you can list relevant columns from multiple files.\n")
    prompt_parts.append("6.  `why_it_matters_en`: English Importance. MUST be a single string formatted with Markdown for any structure.\n")
    prompt_parts.append("7.  `why_it_matters_th`: Thai Importance. MUST be a single string formatted with Markdown for any structure.\n")
    prompt_parts.append("8.  `significance_and_advice_en`: English Significance and Advice. MUST be a single string formatted with Markdown for any structure. It should incorporate illustrative numerical findings/trends based on the 'Storytelling Structure', 'Recommendations Format', and 'Visual Guidance' sections.\n")
    prompt_parts.append("9.  `significance_and_advice_th`: Thai Significance and Advice. MUST be a single string formatted with Markdown for any structure. It should incorporate illustrative numerical findings/trends based on the 'Storytelling Structure', 'Recommendations Format', and 'Visual Guidance' sections.\n\n")
    prompt_parts.append("Do NOT include any introductory/concluding text or other formatting outside the raw JSON object. Ensure the JSON is well-formed.\n\n")

    prompt_parts.append("Here are the headers and a few sample rows (first 2 rows) from your CSV files for context:\n\n")

    for file_name, df in all_dataframes.items():
        prompt_parts.append(f"--- Data from '{file_name}' ---\n")
        prompt_parts.append("Headers: " + ", ".join(df.columns.tolist()) + "\n")
        if not df.empty:
            prompt_parts.append("Sample Rows:\n")
            prompt_parts.append(df.head(2).to_markdown(index=False) + "\n\n")
        else:
            prompt_parts.append("No sample rows (dataframe is empty or has only headers).\n\n")

    full_prompt = "".join(prompt_parts)

    # 5. Call the AI model and process the response
    print(f"\nAnalyzing data with '{analysis_context_platform}' context using AI model. This may take a moment, please be patient...")
    try:
        response = model.generate_content(full_prompt)
        raw_ai_response = response.text

        json_start = raw_ai_response.find('{')
        json_end = raw_ai_response.rfind('}') + 1

        if json_start != -1 and json_end != -1 and json_end > json_start:
            json_string = raw_ai_response[json_start:json_end]
            kpi_results = json.loads(json_string)
        else:
            raise ValueError("Could not find a valid JSON object within the AI response. Raw response was:\n" + raw_ai_response)

        # 6. Embed KPI results and platform options into the HTML template
        html_template_path = "index.html" # Use the provided HTML as a template
        output_html_path = "kpi_report.html" # Output to a new file

        if not os.path.exists(html_template_path):
            print(f"Error: HTML template '{html_template_path}' not found.")
            print("Please ensure 'index.html' is in the same directory as this script.")
            return

        with open(html_template_path, 'r', encoding='utf-8') as f:
            html_content = f.read()

        # Convert kpi_results (Python dict) to a JavaScript-friendly JSON string
        kpi_data_js_string = json.dumps(kpi_results, ensure_ascii=False, indent=4)

        # Generate options for the platform dropdown, including 'Cross-Platform'
        platform_options_html = ""
        for platform in AVAILABLE_PLATFORMS:
            # The dropdown will now display the actual analysis context
            selected_attr = 'selected' if platform == analysis_context_platform else ''
            platform_options_html += f'<option value="{platform}" {selected_attr}>{platform}</option>\n'

        # Inject KPI data and platform options into the HTML
        js_injection_code = f"""
        <script>
            // Injected KPI data from Python script
            window.kpiData = {kpi_data_js_string};
            // Injected analysis context platform (actual platform used for analysis)
            window.selectedPlatform = "{analysis_context_platform}";
            // Injected available platforms for the dropdown
            window.availablePlatforms = {json.dumps(AVAILABLE_PLATFORMS)};
            // The rest of the original script logic follows below this comment.
            // DO NOT REMOVE THE COMMENT ABOVE THIS LINE.
        """
        html_content = html_content.replace('<script>', js_injection_code, 1)

        # Replace the placeholder dropdown with dynamically generated options
        html_content = html_content.replace(
            '<select id="data-source">\n                <option value="General">General E-commerce</option>\n                <option value="TikTok Shop">TikTok Shop</option>\n                <option value="Shopee">Shopee</option>\n                <option value="Lazada">Lazada</option>\n                <option value="Amazon">Amazon</option>\n            </select>',
            f'<select id="data-source">\n{platform_options_html}            </select>'
        )


        with open(output_html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

        print(f"KPI analysis report successfully generated at '{output_html_path}'.")
        print(f"Open '{output_html_path}' in your web browser to view the results. (You no longer need to run a local server or worry about fetch errors!)")
        print(f"Remember to adjust the CSVs in '{data_directory}' to control single-platform vs. cross-platform analysis.")

    except genai.types.BlockedPromptException as e:
        print(f"Error: The prompt was blocked by the safety system. This usually happens if the content violates safety guidelines. Details: {e}")
        print("Please review your CSV data and the prompt content.")
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON from AI response: {e}")
        print("This often means the AI did not return a perfectly valid JSON. Review the raw AI response for clues:")
        print(raw_ai_response)
    except Exception as e:
        print(f"An unexpected error occurred during AI model interaction or HTML generation: {e}")
        print("Possible causes: network issues, incorrect API key, or issues with HTML template.")

if __name__ == "__main__":
    analyze_ecommerce_data_with_ai()
