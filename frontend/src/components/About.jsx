import { Award, Target, Zap, Shield, TrendingUp, Users } from 'lucide-react'

export default function About() {
  return (
    <div className="space-y-6">
      <div className="card">
        <h2 className="text-3xl font-bold text-gray-800 mb-4">About SwadeshAI</h2>
        <p className="text-lg text-gray-600 mb-6">
          AI-powered Farm-to-Market Intelligence Platform reducing India's ₹92,651 crore annual post-harvest losses
        </p>

        {/* Problem Statement */}
        <div className="bg-red-50 border-l-4 border-red-500 p-6 rounded-lg mb-6">
          <h3 className="text-xl font-bold text-red-800 mb-3">The Problem</h3>
          <p className="text-gray-700 mb-3">
            India loses <strong>₹92,651 crores annually</strong> due to post-harvest losses. Small farmers struggle with:
          </p>
          <ul className="list-disc list-inside space-y-2 text-gray-700">
            <li>Lack of quality assessment tools leading to price exploitation</li>
            <li>No visibility into real-time mandi prices</li>
            <li>Difficulty finding verified buyers willing to purchase their produce</li>
            <li>Inefficient logistics planning causing spoilage during transport</li>
            <li>Information asymmetry favoring middlemen over farmers</li>
          </ul>
        </div>

        {/* Solution */}
        <div className="bg-green-50 border-l-4 border-green-500 p-6 rounded-lg mb-6">
          <h3 className="text-xl font-bold text-green-800 mb-3">Our Solution</h3>
          <p className="text-gray-700 mb-4">
            SwadeshAI is a comprehensive platform empowering farmers with AI-driven insights:
          </p>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="bg-white p-4 rounded-lg shadow">
              <div className="flex items-center space-x-3 mb-2">
                <Zap className="w-6 h-6 text-yellow-600" />
                <h4 className="font-semibold text-gray-800">AI Quality Assessment</h4>
              </div>
              <p className="text-sm text-gray-600">
                Computer vision models analyze produce images for freshness grading (5 levels), damage detection,
                and spoilage prediction with 97.7% accuracy.
              </p>
            </div>
            <div className="bg-white p-4 rounded-lg shadow">
              <div className="flex items-center space-x-3 mb-2">
                <TrendingUp className="w-6 h-6 text-blue-600" />
                <h4 className="font-semibold text-gray-800">Smart Pricing</h4>
              </div>
              <p className="text-sm text-gray-600">
                Real-time mandi price integration with quality-based pricing recommendations.
                Protects farmers from selling below MSP.
              </p>
            </div>
            <div className="bg-white p-4 rounded-lg shadow">
              <div className="flex items-center space-x-3 mb-2">
                <Users className="w-6 h-6 text-purple-600" />
                <h4 className="font-semibold text-gray-800">Buyer Matching</h4>
              </div>
              <p className="text-sm text-gray-600">
                Geospatial matching connects farmers with verified buyers. Multi-factor scoring considers
                proximity, rating, capacity, and payment speed.
              </p>
            </div>
            <div className="bg-white p-4 rounded-lg shadow">
              <div className="flex items-center space-x-3 mb-2">
                <Shield className="w-6 h-6 text-green-600" />
                <h4 className="font-semibold text-gray-800">Logistics Intelligence</h4>
              </div>
              <p className="text-sm text-gray-600">
                AI recommends optimal vehicle type, estimates cost/time, and suggests logistics providers
                based on distance, perishability, and quantity.
              </p>
            </div>
          </div>
        </div>

        {/* Tech Stack */}
        <div className="mb-6">
          <h3 className="text-xl font-bold text-gray-800 mb-4">Technology Stack</h3>
          <div className="bg-gradient-to-r from-blue-50 to-purple-50 p-6 rounded-lg">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <h4 className="font-semibold text-gray-800 mb-2">AWS AI Services</h4>
                <ul className="space-y-1 text-sm text-gray-700">
                  <li>• Amazon Bedrock (Claude 3.5) for enhanced insights</li>
                  <li>• Amazon SageMaker for ML model deployment</li>
                  <li>• Amazon Rekognition for image analysis</li>
                  <li>• AWS Lambda for serverless computing</li>
                  <li>• Amazon Location Service for geospatial</li>
                </ul>
              </div>
              <div>
                <h4 className="font-semibold text-gray-800 mb-2">ML & Backend</h4>
                <ul className="space-y-1 text-sm text-gray-700">
                  <li>• PyTorch & MobileNetV2 for freshness detection</li>
                  <li>• XGBoost for spoilage prediction</li>
                  <li>• FastAPI for REST APIs</li>
                  <li>• PostgreSQL for data persistence</li>
                  <li>• Docker for containerization</li>
                </ul>
              </div>
            </div>
          </div>
        </div>

        {/* Impact */}
        <div className="bg-blue-50 border-l-4 border-blue-500 p-6 rounded-lg mb-6">
          <h3 className="text-xl font-bold text-blue-800 mb-3 flex items-center">
            <Target className="w-6 h-6 mr-2" />
            Expected Impact
          </h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center">
              <p className="text-3xl font-bold text-blue-700">30%</p>
              <p className="text-sm text-gray-700">Reduction in post-harvest losses</p>
            </div>
            <div className="text-center">
              <p className="text-3xl font-bold text-blue-700">15-20%</p>
              <p className="text-sm text-gray-700">Increase in farmer income</p>
            </div>
            <div className="text-center">
              <p className="text-3xl font-bold text-blue-700">50%</p>
              <p className="text-sm text-gray-700">Time saved in finding buyers</p>
            </div>
            <div className="text-center">
              <p className="text-3xl font-bold text-blue-700">100K+</p>
              <p className="text-sm text-gray-700">Farmers targeted in Phase 1</p>
            </div>
          </div>
        </div>

        {/* Awards */}
        <div className="bg-gradient-to-r from-yellow-50 to-orange-50 p-6 rounded-lg">
          <h3 className="text-xl font-bold text-gray-800 mb-3 flex items-center">
            <Award className="w-6 h-6 mr-2 text-yellow-600" />
            AWS AI for Bharat Hackathon 2026
          </h3>
          <p className="text-gray-700">
            SwadeshAI is developed as part of the <strong>AWS AI for Bharat Hackathon</strong>, focusing on
            using AI to solve critical problems in Indian agriculture and empower smallholder farmers
            across the nation.
          </p>
        </div>
      </div>

      {/* Team & Contact */}
      <div className="card">
        <h3 className="text-xl font-bold text-gray-800 mb-4">Get In Touch</h3>
        <p className="text-gray-600 mb-4">
          We're building SwadeshAI to transform Indian agriculture. Interested in partnering, investing,
          or deploying this solution in your region?
        </p>
        <div className="flex flex-wrap gap-3">
          <a href="mailto:utkarsharma2026@gmail.com" className="btn-primary inline-flex items-center">
            📧 Contact Us
          </a>
          <a href="https://github.com/kutkarshbtech/AI_Smart_Agriculture_Decision-_System-hackathon" target="_blank" rel="noopener noreferrer" className="btn-secondary inline-flex items-center">
            📄 Presentation Slide Deck
          </a>
          <a href="https://github.com/kutkarshbtech/AI_Smart_Agriculture_Decision-_System-hackathon" target="_blank" rel="noopener noreferrer" className="btn-secondary inline-flex items-center">
            💼 View on GitHub
          </a>
        </div>
      </div>
    </div>
  )
}
