import requests
import json
import os
import csv
from dotenv import load_dotenv

# --- Helper Functions for API Calls ---
def call_gemini_api(prompt: str, response_schema: dict) -> dict:
    """
    Generic function to call the Gemini API with a given prompt and response schema.
    """
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        print("Error: GEMINI_API_KEY not found in environment variables or .env file.")
        print("Please ensure you have a .env file in the same directory with GEMINI_API_KEY=\"YOUR_API_KEY\".")
        print("You can get a key from Google AI Studio: https://aistudio.google.com/app/apikey")
        return {}

    api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"

    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [{"text": prompt}]
            }
        ],
        "generationConfig": {
            "responseMimeType": "application/json",
            "responseSchema": response_schema
        }
    }

    headers = {
        "Content-Type": "application/json"
    }

    print(f"Sending request to Gemini API...")
    try:
        response = requests.post(api_url, headers=headers, data=json.dumps(payload))
        response.raise_for_status()
        result = response.json()

        if result.get("candidates") and result["candidates"][0].get("content") and \
           result["candidates"][0]["content"].get("parts") and \
           result["candidates"][0]["content"]["parts"][0].get("text"):
            
            json_string = result["candidates"][0]["content"]["parts"][0]["text"]
            
            parsed_response = json.loads(json_string)
            return parsed_response
        else:
            print("Error: Unexpected response structure from Gemini API.")
            print(f"Raw API response: {json.dumps(result, indent=2)}")
            return {}

    except requests.exceptions.HTTPError as err:
        print(f"HTTP error occurred: {err}")
        print(f"Response body: {response.text}")
        return {}
    except requests.exceptions.ConnectionError as err:
        print(f"Error connecting to the API: {err}")
        return {}
    except requests.exceptions.Timeout as err:
        print(f"Request timed out: {err}")
        return {}
    except requests.exceptions.RequestException as err:
        print(f"An unexpected error occurred: {err}")
        return {}
    except json.JSONDecodeError as err:
        print(f"Error decoding JSON response: {err}")
        print(f"Raw response: {response.text}")
        return {}

def get_kpis_and_visualizations(csv_header_columns: list[str]) -> list[dict]:
    """
    Connects to the Gemini API to get KPI suggestions and their associated
    visualization recommendations in a single call.
    """
    prompt = (
        f"Given the following e-commerce CSV column headers, act as a professional data analyst "
        f"for an e-commerce company. Suggest relevant Key Performance Indicators (KPIs) and, "
        f"for each KPI, suggest a highly effective and appropriate data visualization.\n"
        f"Include KPIs that involve analysis over time (e.g., trends, growth rates) and "
        f"grouping by categories (e.g., by product category, customer segment, sales channel).\n\n"
        f"For EACH KPI, provide the following details in a JSON array:\n"
        f"1.  **kpiName**: A concise name for the KPI.\n"
        f"2.  **description**: A brief description of what the KPI represents.\n"
        f"3.  **columnsUsed**: A list of CSV header columns required for its calculation.\n"
        f"4.  **howToInterpret**: Guidance on interpreting the KPI's value (e.g., higher is better, trends, comparisons).\n"
        f"5.  **significance**: Why this KPI is important for e-commerce analysis.\n"
        f"6.  **visualization**: An object containing details for its recommended visual:\n"
        f"    a.  **visualType**: The type of chart (e.g., 'Line Chart', 'Bar Chart', 'Pie Chart', 'Table', 'Heatmap', 'Value').\n" # Added 'Value' for direct KPI display
        f"    b.  **chartTitle**: A concise, descriptive title for the chart.\n"
        f"    c.  **dataRequirements**: Specify necessary client-side (JavaScript) aggregations or transformations. Describe the specific columns/data points from the CSV header needed and how to prepare them for the chosen visual type. For example: 'Sum of Quantity per ProductCategory, prepare as an array of labels and an array of values', 'Daily Total Revenue: parse OrderDate, sum (Price * Quantity) per day, sort by date', 'Count of unique CustomerIDs grouped by SourceChannel'. Also, consider efficient data structures for potentially large datasets.\n"
        f"    d.  **x_axisLabel**: (If applicable) Label for the X-axis.\n"
        f"    e.  **y_axisLabel**: (If applicable) Label for the Y-axis.\n"
        f"    f.  **interpretationGuidance**: How to interpret the visual insights.\n"
        f"    g.  **htmlConsiderations**: Brief notes on how this visual could be implemented for a front-end HTML dashboard. Focus on ensuring the visual is fully responsive and adapts gracefully to various screen sizes (mobile, tablet, desktop). Suggest using responsive CSS frameworks (like Tailwind CSS utility classes for `width`, `height`, `flexbox`/`grid`), setting chart options for responsiveness (`responsive: true` in Chart.js, Plotly.js), and potentially dynamic resizing of canvas elements via JavaScript `resize` events. Mention suitable JavaScript charting libraries (e.g., Chart.js, Plotly.js, D3.js) and consider a modular dashboard layout (e.g., CSS Grid or Flexbox) for arrangement.\n\n"
        f"Prioritize visualizations that effectively showcase trends over time, comparisons across categories, "
        f"distribution, and relationships. Ensure suggestions are insightful for e-commerce performance.\n\n"
        f"CSV Headers: {', '.join(csv_header_columns)}"
    )

    unified_response_schema = {
        "type": "ARRAY",
        "items": {
            "type": "OBJECT",
            "properties": {
                "kpiName": {"type": "STRING"},
                "description": {"type": "STRING"},
                "columnsUsed": {
                    "type": "ARRAY",
                    "items": {"type": "STRING"}
                },
                "howToInterpret": {"type": "STRING"},
                "significance": {"type": "STRING"},
                "visualization": {
                    "type": "OBJECT",
                    "properties": {
                        "visualType": {"type": "STRING"},
                        "chartTitle": {"type": "STRING"},
                        "dataRequirements": {"type": "STRING"},
                        "x_axisLabel": {"type": "STRING"},
                        "y_axisLabel": {"type": "STRING"},
                        "interpretationGuidance": {"type": "STRING"},
                        "htmlConsiderations": {"type": "STRING"}
                    },
                    "propertyOrdering": [
                        "visualType", "chartTitle", "dataRequirements",
                        "x_axisLabel", "y_axisLabel", "interpretationGuidance", "htmlConsiderations"
                    ]
                }
            },
            "propertyOrdering": [
                "kpiName", "description", "columnsUsed", "howToInterpret", "significance", "visualization"
            ]
        }
    }
    
    print("\n--- Getting KPI and Visualization suggestions from AI ---")
    return call_gemini_api(prompt, unified_response_schema)


# --- HTML Generation Logic ---
def generate_html_dashboard(kpi_visual_suggestions: list[dict], mock_data_js: str, output_file: str = "ecommerce_dashboard.html"):
    """
    Generates an HTML dashboard file with dynamic charts based on AI suggestions.

    Args:
        kpi_visual_suggestions: A list of dictionaries, each containing KPI and visualization details.
        mock_data_js: A JavaScript string representing the mock e-commerce data.
        output_file: The name of the HTML file to generate.
    """
    
    dashboard_content_html = []
    dashboard_chart_js_logic = []
    
    # Add a main title for the dashboard
    dashboard_content_html.append(
        '<h1 class="col-span-full text-4xl font-bold text-center text-gray-800 mb-6">E-commerce Performance Dashboard</h1>'
    )

    # Generate HTML and JS for each suggested KPI/Visual
    for i, item in enumerate(kpi_visual_suggestions):
        kpi_name = item.get('kpiName', f'KPI {i+1}')
        description = item.get('description', '')
        visual_type = item.get('visualization', {}).get('visualType', 'Value')
        chart_title = item.get('visualization', {}).get('chartTitle', kpi_name)
        data_requirements = item.get('visualization', {}).get('dataRequirements', '')
        x_axis_label = item.get('visualization', {}).get('x_axisLabel', '')
        y_axis_label = item.get('visualization', {}).get('y_axisLabel', '')
        interpretation_guidance = item.get('visualization', {}).get('interpretationGuidance', '')

        # Sanitize ID for HTML elements
        element_id = kpi_name.replace(" ", "-").replace("/", "-").replace("(", "").replace(")", "").lower()

        if visual_type == 'Value':
            # Create a simple card for a single KPI value
            dashboard_content_html.append(f"""
            <div class="kpi-card chart-card">
                <h2 class="text-xl font-semibold text-gray-700 mb-2">{chart_title}</h2>
                <div id="{element_id}-value" class="kpi-value">Loading...</div>
                <p class="text-sm text-gray-500 text-center">{description}</p>
                <p class="text-xs text-gray-400 mt-2">Interpretation: {interpretation_guidance}</p>
            </div>
            """)
            # Add JS logic to calculate and display this value
            dashboard_chart_js_logic.append(f"""
            // KPI: {kpi_name}
            (() => {{
                let value = 0;
                // Basic parsing for "Sum of X", "Count of X", "Average of X" etc.
                if ("{data_requirements}".includes("Sum of") && "{data_requirements}".includes("per")) {{
                    // Complex aggregation (e.g., "Sum of Price * Quantity per day")
                    // This is a placeholder for complex logic. A real app would need a sophisticated data processor.
                    // For now, we'll try to find a direct sum or count if implied.
                    const match = "{data_requirements}".match(/Sum of (\w+)/i);
                    if (match && mockEcommerceData[0][match[1]]) {{
                        value = mockEcommerceData.reduce((sum, item) => sum + (item[match[1]] || 0), 0);
                    }} else if ("{data_requirements}".includes("Total Revenue")) {{
                        value = mockEcommerceData.reduce((sum, item) => {{
                            if (item.OrderStatus === 'Completed') return sum + (item.Price * item.Quantity);
                            return sum;
                        }}, 0);
                    }}
                }} else if ("{data_requirements}".includes("Sum of")) {{
                    const match = "{data_requirements}".match(/Sum of (\w+)/i);
                    if (match && mockEcommerceData[0][match[1]]) {{
                        value = mockEcommerceData.reduce((sum, item) => sum + (parseFloat(item[match[1]]) || 0), 0);
                    }}
                }} else if ("{data_requirements}".includes("Count of unique")) {{
                    const match = "{data_requirements}".match(/Count of unique (\w+)/i);
                    if (match && mockEcommerceData[0][match[1]]) {{
                        value = new Set(mockEcommerceData.map(item => item[match[1]])).size;
                    }}
                }} else if ("{data_requirements}".includes("Total Orders")) {{
                    value = new Set(mockEcommerceData.filter(item => item.OrderStatus === 'Completed').map(item => item.OrderID)).size;
                }} else {{
                    // Fallback for simple values, e.g. a column name
                    const col = "{data_requirements}".split(' ')[0];
                    if (mockEcommerceData.length > 0 && mockEcommerceData[0][col] !== undefined) {{
                       value = (parseFloat(mockEcommerceData[0][col]) || 0);
                    }} else {{
                       value = 0;
                    }}
                }}
                document.getElementById('{element_id}-value').innerText = {{"{kpi_name}".includes("Revenue") or "{kpi_name}".includes("Sales") ? `'$' + value.toFixed(2)` : `value.toLocaleString()`}};
            }})();
            """)
        else:
            # Create a canvas for chart
            dashboard_content_html.append(f"""
            <div class="chart-card {'col-span-full' if visual_type == 'Line Chart' else ''}">
                <h2 class="text-xl font-semibold text-gray-700 mb-4">{chart_title}</h2>
                <canvas id="{element_id}-chart"></canvas>
            </div>
            """)
            # Add JS logic to create the chart
            dashboard_chart_js_logic.append(f"""
            // Chart: {kpi_name} ({visual_type})
            (() => {{
                const ctx = document.getElementById('{element_id}-chart').getContext('2d');
                let labels = [];
                let data = [];
                let backgroundColor = [];
                let borderColor = [];
                
                // --- Data Preparation Logic based on AI's dataRequirements ---
                // This section attempts to interpret common data requirements and transform mock data.
                // For complex requirements, this might need manual refinement.
                const req = `{data_requirements}`;
                const visualType = `{visual_type}`;
                
                if (req.includes("Daily Total Revenue")) {{
                    const dailySales = {{}};
                    mockEcommerceData.forEach(item => {{
                        if (item.OrderStatus === 'Completed') {{
                            const date = item.OrderDate;
                            const sales = item.Price * item.Quantity;
                            dailySales[date] = (dailySales[date] || 0) + sales;
                        }}
                    }});
                    labels = Object.keys(dailySales).sort();
                    data = labels.map(date => dailySales[date]);
                    backgroundColor = 'rgba(79, 70, 229, 0.2)'; // Light fill for line
                    borderColor = '#4f46e5'; // Dark line
                }} else if (req.includes("Sum of") && req.includes("per ProductCategory")) {{
                    const aggregatedData = {{}};
                    mockEcommerceData.forEach(item => {{
                        if (item.OrderStatus === 'Completed') {{
                            const category = item.ProductCategory;
                            const sales = item.Price * item.Quantity;
                            aggregatedData[category] = (aggregatedData[category] || 0) + sales;
                        }}
                    }});
                    labels = Object.keys(aggregatedData);
                    data = Object.values(aggregatedData);
                    // Generate a consistent set of colors for categories
                    const colors = ['#6366f1', '#a855f7', '#ec4899', '#f97316', '#eab308', '#06b6d4', '#10b981', '#ef4444', '#8b5cf6', '#d946b6'];
                    backgroundColor = labels.map((_,idx) => colors[idx % colors.length]);
                    borderColor = labels.map((_,idx) => colors[idx % colors.length].replace('0.2', '1')); // Make borders slightly darker
                }} else if (req.includes("Count of unique CustomerIDs grouped by SourceChannel")) {{
                    const aggregatedData = {{}};
                    mockEcommerceData.forEach(item => {{
                        const channel = item.SourceChannel || 'Direct'; // Default if not present
                        aggregatedData[channel] = (aggregatedData[channel] || 0) + 1;
                    }});
                    labels = Object.keys(aggregatedData);
                    data = Object.values(aggregatedData);
                    const colors = ['#3b82f6', '#10b981', '#ef4444', '#f59e0b', '#6b7280'];
                    backgroundColor = labels.map((_,idx) => colors[idx % colors.length]);
                    borderColor = '#ffffff'; // White border for pie
                }} else if (req.includes("Payment Method Distribution") || req.includes("PaymentMethod breakdown")) {{
                    const aggregatedData = {{}};
                    mockEcommerceData.forEach(item => {{
                        if (item.OrderStatus === 'Completed') {{
                            const method = item.PaymentMethod;
                            aggregatedData[method] = (aggregatedData[method] || 0) + 1;
                        }}
                    }});
                    labels = Object.keys(aggregatedData);
                    data = Object.values(aggregatedData);
                    const colors = ['#3b82f6', '#10b981', '#ef4444', '#f59e0b'];
                    backgroundColor = labels.map((_,idx) => colors[idx % colors.length]);
                    borderColor = '#ffffff';
                }}
                
                let chartType = 'bar'; // Default
                if (visualType.includes('Line')) chartType = 'line';
                else if (visualType.includes('Pie')) chartType = 'pie';
                else if (visualType.includes('Doughnut')) chartType = 'doughnut';
                else if (visualType.includes('Bar')) chartType = 'bar';

                const plugins = [];
                let legendDisplay = true;
                if (visualType === 'Pie' || visualType === 'Doughnut' || visualType === 'Value') {
                    plugins.push(ChartDataLabels);
                    legendDisplay = true; // Pies often need legends
                }

                new Chart(ctx, {{
                    type: chartType,
                    data: {{
                        labels: labels,
                        datasets: [{{
                            label: `{chart_title}`,
                            data: data,
                            backgroundColor: backgroundColor,
                            borderColor: borderColor,
                            borderWidth: visualType === 'Pie' || visualType === 'Doughnut' ? 2 : 1,
                            fill: chartType === 'line' ? true : false,
                            tension: chartType === 'line' ? 0.3 : 0
                        }}]
                    }},
                    options: {{
                        responsive: true,
                        maintainAspectRatio: false, // Important for responsive resizing in grid
                        plugins: {{
                            title: {{
                                display: true,
                                text: `{chart_title}`
                            }},
                            legend: {{
                                display: legendDisplay,
                                position: chartType === 'pie' || chartType === 'doughnut' ? 'bottom' : 'top'
                            }},
                            datalabels: {{ // Configuration for ChartDataLabels plugin
                                display: visualType === 'Pie' || visualType === 'Doughnut' || visualType === 'Bar', // Only for specific types
                                color: visualType === 'Pie' || visualType === 'Doughnut' ? '#fff' : '#4a4a4a',
                                font: {{
                                    weight: 'bold'
                                }},
                                formatter: (value, context) => {{
                                    if (visualType === 'Pie' || visualType === 'Doughnut') {{
                                        let sum = 0;
                                        let dataArr = context.chart.data.datasets[0].data;
                                        dataArr.map(data => {{ sum += data; }});
                                        let percentage = (value * 100 / sum).toFixed(1) + "%";
                                        return percentage;
                                    }} else if (visualType === 'Bar') {{
                                        return value.toLocaleString();
                                    }}
                                    return ''; // No datalabels for other chart types by default
                                }}
                            }}
                        }},
                        scales: {{
                            x: {{
                                display: chartType !== 'pie' && chartType !== 'doughnut',
                                title: {{
                                    display: Boolean(`{x_axis_label}`),
                                    text: `{x_axis_label}`
                                }},
                                grid: {{
                                    display: false
                                }}
                            }},
                            y: {{
                                display: chartType !== 'pie' && chartType !== 'doughnut',
                                title: {{
                                    display: Boolean(`{y_axis_label}`),
                                    text: `{y_axis_label}`
                                }},
                                beginAtZero: true
                            }}
                        }}
                    }},
                    plugins: plugins // Register plugins with the chart instance
                }});
            }})();
            """)

    full_html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dynamic E-commerce KPI Dashboard</title>
    <!-- Tailwind CSS CDN -->
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body {{
            font-family: 'Inter', sans-serif;
            background-color: #f3f4f6; /* Light gray background */
            display: flex;
            justify-content: center;
            align-items: flex-start;
            min-height: 100vh;
            padding: 20px;
        }}
        .dashboard-container {{
            background-color: #ffffff;
            border-radius: 1rem; /* Rounded corners */
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
            padding: 2.5rem; /* More padding */
            width: 100%;
            max-width: 1200px;
            display: grid;
            gap: 2rem; /* Gap between grid items */
            grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); /* Responsive grid */
            /* Ensure values occupy one column, charts expand */
        }}
        .kpi-card {{
            /* Specific styling for KPI value cards */
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            min-height: 150px; /* Ensure consistent height for value cards */
        }}
        .chart-card {{
            background-color: #f9fafb;
            border-radius: 0.75rem; /* Slightly less rounded for inner cards */
            padding: 1.5rem;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
            display: flex;
            flex-direction: column;
            align-items: center;
            /* For chart cards, allow them to expand to fill space, but maintain aspect ratio */
            min-height: 300px; /* Minimum height for charts */
        }}
        canvas {{
            max-width: 100%; /* Ensure canvas scales */
            height: 250px; /* Fixed height for charts for consistency, can be adjusted or dynamic */
            flex-grow: 1; /* Allow canvas to grow */
        }}
        .kpi-value {{
            font-size: 2.5rem; /* Larger font for KPI values */
            font-weight: 700; /* Bold */
            color: #1f2937; /* Darker text */
            margin-bottom: 1rem;
        }}
        /* Responsive adjustments for charts to take full width on smaller screens, and half on larger */
        @media (min-width: 768px) {{
            .chart-card:not(.col-span-full) {{
                grid-column: span 1; /* Default to 1 column */
            }}
            .chart-card.col-span-full {{
                grid-column: span 2; /* Full width for specific charts on medium screens */
            }}
        }}
        @media (min-width: 1024px) {{
            .chart-card.col-span-full {{
                grid-column: span 3; /* Full width for specific charts on large screens (if grid-template-columns is 3) */
            }}
        }}
    </style>
    <!-- Chart.js CDN -->
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <!-- Chart.js DataLabels Plugin (Optional, for showing values on bars/segments) -->
    <script src="https://cdn.jsdelivr.net/npm/chartjs-plugin-datalabels@2.0.0"></script>
</head>
<body>
    <div class="dashboard-container">
        <!-- Dashboard content will be dynamically inserted here by Python -->
        {"".join(dashboard_content_html)}
    </div>

    <script>
        // Register the Chart.js DataLabels plugin globally (optional, for specific charts)
        Chart.register(ChartDataLabels);

        // --- MOCK E-COMMERCE DATA ---
        // In a real application, you would load your actual CSV data here (e.g., via fetch from a server).
        // This mock data is used to make the generated HTML immediately runnable.
        {mock_data_js}

        // --- AI-SUGGESTED KPIS AND VISUALIZATIONS ---
        // This data is generated by the Python script based on your CSV header.
        const suggestedKpiVisuals = {json.dumps(kpi_visual_suggestions, indent=2)};

        // --- Dynamic Chart Rendering Logic ---
        window.onload = function() {{
            suggestedKpiVisuals.forEach(item => {{
                const kpiName = item.kpiName;
                const visual = item.visualization || {{}};
                const visualType = visual.visualType;
                const chartTitle = visual.chartTitle;
                const dataRequirements = visual.dataRequirements;
                const xAxisLabel = visual.x_axisLabel;
                const yAxisLabel = visual.y_axisLabel;
                const elementId = kpiName.replace(/ /g, '-').replace(/[^a-zA-Z0-9-]/g, '').toLowerCase(); // Sanitize ID

                // For simple KPI value display (e.g., Total Revenue, Total Orders)
                if (visualType === 'Value') {{
                    const kpiValueElement = document.getElementById(`${{elementId}}-value`);
                    if (kpiValueElement) {{
                        // Attempt to parse simple data requirements for KPI value
                        let value = 0;
                        if (dataRequirements.includes("Total Revenue") || dataRequirements.includes("Sum of Price * Quantity")) {{
                            value = mockEcommerceData.reduce((sum, d) => {{
                                if (d.OrderStatus === 'Completed') return sum + (parseFloat(d.Price) * parseFloat(d.Quantity));
                                return sum;
                            }}, 0);
                            kpiValueElement.innerText = `$${{value.toFixed(2)}}`;
                        }} else if (dataRequirements.includes("Total Orders") || dataRequirements.includes("Count of unique OrderIDs")) {{
                            const uniqueOrders = new Set(mockEcommerceData.filter(d => d.OrderStatus === 'Completed').map(d => d.OrderID));
                            value = uniqueOrders.size;
                            kpiValueElement.innerText = value.toLocaleString();
                        }} else if (dataRequirements.includes("Count of unique CustomerIDs")) {{
                            const uniqueCustomers = new Set(mockEcommerceData.map(d => d.CustomerID));
                            value = uniqueCustomers.size;
                            kpiValueElement.innerText = value.toLocaleString();
                        }}
                        // Add more specific value calculations based on common KPI types
                        else if (dataRequirements.includes("Average Order Value")) {
                            const totalRevenue = mockEcommerceData.reduce((sum, d) => {
                                if (d.OrderStatus === 'Completed') return sum + (parseFloat(d.Price) * parseFloat(d.Quantity));
                                return sum;
                            }, 0);
                            const uniqueOrders = new Set(mockEcommerceData.filter(d => d.OrderStatus === 'Completed').map(d => d.OrderID));
                            value = uniqueOrders.size > 0 ? totalRevenue / uniqueOrders.size : 0;
                            kpiValueElement.innerText = `$${{value.toFixed(2)}}`;
                        } else {{
                            // Fallback for simple values, e.g. a column name
                            const col = "{data_requirements}".split(' ')[0];
                            if (mockEcommerceData.length > 0 && mockEcommerceData[0][col] !== undefined) {{
                               value = (parseFloat(mockEcommerceData[0][col]) || 0);
                            }} else {{
                               value = 0;
                            }}
                        }}
                    }}
                    return; // Skip chart rendering for 'Value' type
                }}

                // --- Chart Rendering Logic ---
                const ctx = document.getElementById(`${{elementId}}-chart`);
                if (!ctx) return; // Skip if canvas element not found

                const canvasParent = ctx.parentElement;
                if(canvasParent) {{
                    canvasParent.style.height = 'auto'; // Allow card to define height
                    canvasParent.style.minHeight = '300px'; // Set a minimum height for charts
                }}

                let labels = [];
                let chartData = [];
                let chartBackgroundColor = [];
                let chartBorderColor = [];
                
                // Helper to generate consistent colors
                const baseColors = [
                    '#6366f1', '#a855f7', '#ec4899', '#f97316', '#eab308', // Tailwind palette
                    '#06b6d4', '#10b981', '#ef4444', '#8b5cf6', '#d946b6'
                ];
                function generateColors(count) {{
                    const colors = [];
                    for(let i=0; i<count; i++) {{
                        colors.push(baseColors[i % baseColors.length]);
                    }}
                    return colors;
                }}

                // --- Data Transformation based on dataRequirements ---
                // This section attempts to interpret the 'dataRequirements' string and processes mockEcommerceData
                // This will need to be robust for various AI suggestions.
                if (dataRequirements.includes("Daily Total Revenue")) {{
                    const dailySales = {{}};
                    mockEcommerceData.forEach(d => {{
                        if (d.OrderStatus === 'Completed') {{
                            const date = d.OrderDate;
                            const sales = parseFloat(d.Price) * parseFloat(d.Quantity);
                            dailySales[date] = (dailySales[date] || 0) + sales;
                        }}
                    }});
                    labels = Object.keys(dailySales).sort();
                    chartData = labels.map(date => dailySales[date]);
                    chartBackgroundColor = 'rgba(79, 70, 229, 0.2)'; // Light fill for line
                    chartBorderColor = '#4f46e5'; // Dark line
                }} else if (dataRequirements.includes("Sum of") && dataRequirements.includes("per ProductCategory")) {{
                    const salesByCategory = {{}};
                    mockEcommerceData.forEach(d => {{
                        if (d.OrderStatus === 'Completed') {{
                            const category = d.ProductCategory;
                            const sales = parseFloat(d.Price) * parseFloat(d.Quantity);
                            salesByCategory[category] = (salesByCategory[category] || 0) + sales;
                        }}
                    }});
                    labels = Object.keys(salesByCategory);
                    chartData = Object.values(salesByCategory);
                    chartBackgroundColor = generateColors(labels.length);
                    chartBorderColor = generateColors(labels.length).map(c => c.replace('0.2', '1')); // Make borders slightly darker
                }} else if (dataRequirements.includes("Count of unique OrderIDs grouped by PaymentMethod")) {{
                    const ordersByPayment = {};
                    mockEcommerceData.forEach(d => {{
                        if (d.OrderStatus === 'Completed') {{
                            const method = d.PaymentMethod;
                            ordersByPayment[method] = (ordersByPayment[method] || 0) + 1;
                        }}
                    }});
                    labels = Object.keys(ordersByPayment);
                    chartData = Object.values(ordersByPayment);
                    const colors = ['#3b82f6', '#10b981', '#ef4444', '#f59e0b'];
                    chartBackgroundColor = labels.map((_,idx) => colors[idx % colors.length]);
                    chartBorderColor = '#ffffff'; // White border for pie
                }}
                // Add more data parsing logic here for other dataRequirements...
                // Example for 'Review Score Distribution':
                else if (dataRequirements.includes("Distribution of ReviewScore")) {
                    const reviewCounts = {1:0, 2:0, 3:0, 4:0, 5:0};
                    mockEcommerceData.forEach(d => {
                        const score = parseInt(d.ReviewScore);
                        if (!isNaN(score) && score >=1 && score <=5) {
                            reviewCounts[score]++;
                        }
                    });
                    labels = Object.keys(reviewCounts);
                    chartData = Object.values(reviewCounts);
                    chartBackgroundColor = generateColors(labels.length); // Use colors for bars
                    chartBorderColor = generateColors(labels.length);
                } else if (dataRequirements.includes("Total Quantity Sold per ProductSKU")) {
                    const quantityBySku = {};
                    mockEcommerceData.forEach(d => {
                        if (d.OrderStatus === 'Completed') {
                            const sku = d.ProductSKU;
                            quantityBySku[sku] = (quantityBySku[sku] || 0) + parseInt(d.Quantity);
                        }
                    });
                    labels = Object.keys(quantityBySku);
                    chartData = Object.values(quantityBySku);
                    chartBackgroundColor = generateColors(labels.length);
                    chartBorderColor = generateColors(labels.length);
                }
                
                let chartConfig = {{
                    type: 'bar', // Default
                    data: {{
                        labels: labels,
                        datasets: [{{
                            label: chartTitle,
                            data: chartData,
                            backgroundColor: chartBackgroundColor,
                            borderColor: chartBorderColor,
                            borderWidth: 1
                        }}]
                    }},
                    options: {{
                        responsive: true,
                        maintainAspectRatio: false, // Allows chart to fill container width while respecting height
                        plugins: {{
                            title: {{
                                display: true,
                                text: chartTitle
                            }},
                            legend: {{
                                display: visualType !== 'Pie' && visualType !== 'Doughnut' && visualType !== 'Value',
                            }},
                            datalabels: {{
                                display: false // Only enable for specific charts like pie/doughnut/bar if useful
                            }}
                        }},
                        scales: {{
                            x: {{
                                display: visualType !== 'Pie' && visualType !== 'Doughnut',
                                title: {{
                                    display: Boolean(`{x_axis_label}`),
                                    text: xAxisLabel
                                }},
                                grid: {{ display: false }}
                            }},
                            y: {{
                                display: visualType !== 'Pie' && visualType !== 'Doughnut',
                                title: {{
                                    display: Boolean(`{y_axis_label}`),
                                    text: yAxisLabel
                                }},
                                beginAtZero: true
                            }}
                        }}
                    }},
                    plugins: plugins // Register plugins with the chart instance
                }};

                // Adjust chart type and specific options
                if (visualType.includes('Line')) {{
                    chartConfig.type = 'line';
                    chartConfig.data.datasets[0].fill = true;
                    chartConfig.data.datasets[0].tension = 0.3;
                }} else if (visualType.includes('Pie')) {{
                    chartConfig.type = 'pie';
                    chartConfig.options.plugins.datalabels.display = true;
                    chartConfig.options.plugins.datalabels.color = '#fff';
                    chartConfig.options.plugins.legend.position = 'bottom';
                    chartConfig.data.datasets[0].borderWidth = 2;
                }} else if (visualType.includes('Doughnut')) {{
                    chartConfig.type = 'doughnut';
                    chartConfig.options.plugins.datalabels.display = true;
                    chartConfig.options.plugins.datalabels.color = '#fff';
                    chartConfig.options.plugins.legend.position = 'bottom';
                    chartConfig.data.datasets[0].borderWidth = 2;
                }} else if (visualType.includes('Bar')) {{
                    chartConfig.type = 'bar';
                    chartConfig.options.plugins.datalabels.display = true;
                    chartConfig.options.plugins.datalabels.color = '#4a4a4a';
                    chartConfig.options.plugins.datalabels.formatter = (value) => value.toLocaleString();
                }}

                new Chart(ctx, chartConfig);
            }});
        }};
    </script>
</body>
</html>
    """
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(full_html_content)
    print(f"\nGenerated dashboard HTML file: '{output_file}'")
    print(f"Open '{output_file}' in your web browser to see the visuals.")


# --- Main Execution ---
if __name__ == "__main__":
    # --- CSV FILE CONFIGURATION ---
    # IMPORTANT: Set the path to your local CSV file here.
    # If the CSV is in the same directory as this script, just use the filename.
    csv_file_path = "ecommerce_data.csv" 

    # --- MOCK DATA FOR HTML DASHBOARD ---
    # This mock data is embedded directly into the generated HTML.
    # In a real application, you would load your actual CSV data here in Python,
    # process it, and then serialize it to JSON to embed in the HTML or serve via an API.
    mock_ecommerce_data_js = """
        const mockEcommerceData = [
            { OrderID: '1001', CustomerID: 'C001', ProductSKU: 'P001', Quantity: 2, Price: 25.50, OrderDate: '2023-01-01', ShippingCost: 5.00, PaymentMethod: 'Credit Card', ProductCategory: 'Electronics', OrderStatus: 'Completed', RefundAmount: 0, ReviewScore: 5, SourceChannel: 'Organic Search' },
            { OrderID: '1002', CustomerID: 'C002', ProductSKU: 'P002', Quantity: 1, Price: 120.00, OrderDate: '2023-01-01', ShippingCost: 7.50, PaymentMethod: 'PayPal', ProductCategory: 'Home Goods', OrderStatus: 'Completed', RefundAmount: 0, ReviewScore: 4, SourceChannel: 'Paid Ads' },
            { OrderID: '1003', CustomerID: 'C001', ProductSKU: 'P003', Quantity: 3, Price: 10.00, OrderDate: '2023-01-02', ShippingCost: 4.00, PaymentMethod: 'Credit Card', ProductCategory: 'Apparel', OrderStatus: 'Completed', RefundAmount: 0, ReviewScore: 3, SourceChannel: 'Organic Search' },
            { OrderID: '1004', CustomerID: 'C003', ProductSKU: 'P001', Quantity: 1, Price: 25.50, OrderDate: '2023-01-02', ShippingCost: 5.00, PaymentMethod: 'Debit Card', ProductCategory: 'Electronics', OrderStatus: 'Completed', RefundAmount: 0, ReviewScore: 5, SourceChannel: 'Social Media' },
            { OrderID: '1005', CustomerID: 'C004', ProductSKU: 'P004', Quantity: 1, Price: 200.00, OrderDate: '2023-01-03', ShippingCost: 10.00, PaymentMethod: 'Credit Card', ProductCategory: 'Electronics', OrderStatus: 'Completed', RefundAmount: 0, ReviewScore: 0, SourceChannel: 'Email Marketing' },
            { OrderID: '1006', CustomerID: 'C005', ProductSKU: 'P005', Quantity: 5, Price: 5.00, OrderDate: '2023-01-03', ShippingCost: 3.00, PaymentMethod: 'PayPal', ProductCategory: 'Books', OrderStatus: 'Completed', RefundAmount: 0, ReviewScore: 4, SourceChannel: 'Organic Search' },
            { OrderID: '1007', CustomerID: 'C001', ProductSKU: 'P002', Quantity: 1, Price: 120.00, OrderDate: '2023-01-04', ShippingCost: 7.50, PaymentMethod: 'Credit Card', ProductCategory: 'Home Goods', OrderStatus: 'Completed', RefundAmount: 0, ReviewScore: 5, SourceChannel: 'Paid Ads' },
            { OrderID: '1008', CustomerID: 'C006', ProductSKU: 'P006', Quantity: 1, Price: 75.00, OrderDate: '2023-01-04', ShippingCost: 6.00, PaymentMethod: 'Debit Card', ProductCategory: 'Apparel', OrderStatus: 'Completed', RefundAmount: 0, ReviewScore: 4, SourceChannel: 'Social Media' },
            { OrderID: '1009', CustomerID: 'C007', ProductSKU: 'P001', Quantity: 2, Price: 25.50, OrderDate: '2023-01-05', ShippingCost: 5.00, PaymentMethod: 'Credit Card', ProductCategory: 'Electronics', OrderStatus: 'Completed', RefundAmount: 0, ReviewScore: 3, SourceChannel: 'Email Marketing' },
            { OrderID: '1010', CustomerID: 'C008', ProductSKU: 'P007', Quantity: 1, Price: 30.00, OrderDate: '2023-01-05', ShippingCost: 4.50, PaymentMethod: 'PayPal', ProductCategory: 'Apparel', OrderStatus: 'Completed', RefundAmount: 0, ReviewScore: 5, SourceChannel: 'Organic Search' },
            { OrderID: '1011', CustomerID: 'C009', ProductSKU: 'P008', Quantity: 1, Price: 50.00, OrderDate: '2023-01-06', ShippingCost: 5.00, PaymentMethod: 'Credit Card', ProductCategory: 'Books', OrderStatus: 'Completed', RefundAmount: 0, ReviewScore: 4, SourceChannel: 'Paid Ads' },
            { OrderID: '1012', CustomerID: 'C010', ProductSKU: 'P009', Quantity: 2, Price: 15.00, OrderDate: '2023-01-06', ShippingCost: 4.00, PaymentMethod: 'Debit Card', ProductCategory: 'Apparel', OrderStatus: 'Completed', RefundAmount: 0, ReviewScore: 5, SourceChannel: 'Social Media' },
            { OrderID: '1013', CustomerID: 'C001', ProductSKU: 'P010', Quantity: 1, Price: 99.99, OrderDate: '2023-01-07', ShippingCost: 8.00, PaymentMethod: 'Credit Card', ProductCategory: 'Home Goods', OrderStatus: 'Completed', RefundAmount: 0, ReviewScore: 5, SourceChannel: 'Organic Search' },
            { OrderID: '1014', CustomerID: 'C002', ProductSKU: 'P011', Quantity: 1, Price: 150.00, OrderDate: '2023-01-07', ShippingCost: 10.00, PaymentMethod: 'PayPal', ProductCategory: 'Electronics', OrderStatus: 'Pending', RefundAmount: 0, ReviewScore: 0, SourceChannel: 'Email Marketing' },
            { OrderID: '1015', CustomerID: 'C003', ProductSKU: 'P012', Quantity: 4, Price: 8.00, OrderDate: '2023-01-08', ShippingCost: 3.50, PaymentMethod: 'Credit Card', ProductCategory: 'Apparel', OrderStatus: 'Completed', RefundAmount: 0, ReviewScore: 4, SourceChannel: 'Paid Ads' },
        ];
    """

    csv_header_columns = []
    try:
        with open(csv_file_path, 'r', newline='', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            csv_header_columns = next(reader)
        print(f"Successfully read header from '{csv_file_path}': {csv_header_columns}")

    except FileNotFoundError:
        print(f"Error: The file '{csv_file_path}' was not found.")
        print("Please ensure the CSV file is in the same directory as the script, or provide the full path.")
    except Exception as e:
        print(f"An error occurred while reading the CSV file: {e}")

    if csv_header_columns:
        unified_suggestions = get_kpis_and_visualizations(csv_header_columns)

        if unified_suggestions:
            print("\nGenerating HTML Dashboard with Suggested KPIs and Visualizations...")
            generate_html_dashboard(unified_suggestions, mock_ecommerce_data_js)
            print("\nDashboard generated successfully!")
        else:
            print("No KPIs or visualization suggestions were returned. HTML dashboard not generated.")
    else:
        print("Cannot proceed with analysis as no CSV header was loaded.")

