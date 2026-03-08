# SwadeshAI Frontend

Modern React-based frontend for the SwadeshAI Farm-to-Market Intelligence Platform.

## Features

- **Quality Assessment** - Upload produce images for AI-powered freshness analysis
- **Mandi Prices** - Real-time market prices from mandis across India
- **Buyer Matching** - Geospatial matching with verified buyers
- **Logistics Intelligence** - Smart vehicle and route recommendations
- **Responsive Design** - Works seamlessly on desktop, tablet, and mobile

## Tech Stack

- **React 18** - Modern React with hooks
- **Vite** - Fast build tool and dev server
- **React Router** - Client-side routing
- **Tailwind CSS** - Utility-first CSS framework
- **Recharts** - Data visualization
- **Lucide React** - Beautiful icon library
- **Axios** - HTTP client for API calls

## Getting Started

### Prerequisites

- Node.js 18+ and npm/yarn
- Backend API running on `http://localhost:8000`

### Installation

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

The app will be available at `http://localhost:3000`

### Build for Production

```bash
npm run build
npm run preview
```

## Project Structure

```
frontend/
├── src/
│   ├── components/
│   │   ├── QualityAssessment.jsx  # Image upload & AI analysis
│   │   ├── MandiPrices.jsx        # Live mandi price display
│   │   ├── BuyerMatching.jsx      # Geospatial buyer search
│   │   ├── ProduceForm.jsx        # Sidebar form for produce details
│   │   └── About.jsx              # About page
│   ├── App.jsx                    # Main app component with routing
│   ├── main.jsx                   # React entry point
│   └── index.css                  # Global styles with Tailwind
├── index.html                     # HTML template
├── vite.config.js                 # Vite configuration
├── tailwind.config.js             # Tailwind CSS configuration
└── package.json                   # Dependencies and scripts
```

## Configuration

### API Proxy

The Vite dev server is configured to proxy API requests to the backend:

```javascript
// vite.config.js
proxy: {
  '/api': {
    target: 'http://localhost:8000',
    changeOrigin: true,
  }
}
```

### Customization

- **Colors**: Edit `tailwind.config.js` to customize the color palette
- **API Endpoint**: Update the proxy target in `vite.config.js`
- **City List**: Modify the `indianCities` object in `ProduceForm.jsx`

## Features in Detail

### Quality Assessment Tab
- Drag-and-drop image upload
- Real-time AI analysis with loading states
- Comprehensive results display:
  - Freshness grade (Excellent → Critical)
  - Damage assessment
  - Price recommendations
  - Shelf life prediction
- Visual indicators with color-coded badges

### Mandi Prices Tab
- Fetch live prices from government data API
- State-based filtering
- Interactive bar charts comparing prices
- Detailed price cards with min/max/modal prices
- Summary metrics (avg price, lowest, highest, states covered)

### Buyer Matching Tab
- Geospatial search within configurable radius
- Advanced filters (buyer type, rating, sort order)
- Comprehensive buyer cards showing:
  - Match score breakdown (6 factors)
  - Contact information
  - Active demand alerts
  - Logistics recommendations
  - Business details
- One-click contact buttons

### Responsive Sidebar
- Sticky sidebar with produce details form
- Crop selection dropdown
- Quantity input
- City/location picker with 30+ Indian cities
- Custom coordinate entry option
- Search distance slider
- State filter for mandi prices

## API Integration

The frontend expects the following API endpoints:

- `POST /api/quality/assess` - Quality assessment
- `GET /api/mandi/prices?crop={crop}&state={state}` - Mandi prices
- `POST /api/buyers/match` - Buyer matching
- `POST /api/logistics/recommend` - Logistics recommendations

## Deployment

### Docker

```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
RUN npm run build
EXPOSE 3000
CMD ["npm", "run", "preview"]
```

### Vercel/Netlify

This project is ready for deployment on Vercel or Netlify. Just connect your Git repository!

### Environment Variables

Create `.env` file for environment-specific configuration:

```env
VITE_API_BASE_URL=http://localhost:8000
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

Part of the SwadeshAI project for AWS AI for Bharat Hackathon 2026.

## Support

For questions or issues, please open a GitHub issue or contact the team.
