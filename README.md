# Instagram Network Visualization

This project creates a visualization of your Instagram network, showing your followers and following relationships in an interactive graph.

## Setup

1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

2. Create a `.env` file in the root directory with your Instagram credentials:
```
INSTAGRAM_USERNAME=your_username
INSTAGRAM_PASSWORD=your_password
```

3. Install Node.js dependencies:
```bash
npm install
```

## Usage

1. First, run the scraper to collect your Instagram network data:
```bash
python scraper/instagram_scraper.py
```
This will create CSV files in the `data` directory containing your network information.

2. Start the web application:
```bash
npm run dev
```

3. Open your browser and navigate to `http://localhost:5173` to view the visualization.

## Features

- Interactive network graph visualization using D3.js
- Drag and zoom functionality
- Color-coded relationships (red for followers, green for following)
- Hover over nodes to see usernames

## Technical Details

- Frontend: React + TypeScript + Vite
- Styling: Tailwind CSS
- Visualization: D3.js
- Data Collection: Python + Selenium

## Notes

- The scraper uses Selenium to collect data from Instagram. This might break if Instagram changes their website structure.
- Make sure to keep your login credentials secure and never commit the `.env` file to version control.
- The visualization is currently limited to direct followers and following relationships.