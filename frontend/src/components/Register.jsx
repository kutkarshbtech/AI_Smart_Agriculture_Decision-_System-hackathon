// Register Component for new user registration
import React, { useState } from 'react';
import axios from 'axios';
import { Phone, User, Building2, MapPin, Loader, AlertCircle, CheckCircle } from 'lucide-react';

const Register = () => {
  // Form state
  const [formData, setFormData] = useState({
    userType: '',
    name: '',
    mobileNumber: '',
    businessName: '',
    city: '',
    state: '',
    pincode: '',
    vehicleTypes: [],
    operatingStates: []
  });
  
  // UI state
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);

  const validateMobile = (mobile) => {
    const cleaned = mobile.replace(/[^0-9+]/g, '');
    return /^\+?[1-9]\d{9,14}$/.test(cleaned);
  };

  const validatePincode = (pincode) => {
    return /^\d{6}$/.test(pincode);
  };

  const handleInputChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    setError('');
  };

  const handleArrayToggle = (field, value) => {
    setFormData(prev => ({
      ...prev,
      [field]: prev[field].includes(value)
        ? prev[field].filter(v => v !== value)
        : [...prev[field], value]
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    
    // Validation
    if (!formData.userType) {
      setError('Please select user type');
      return;
    }
    
    if (!formData.name || formData.name.length < 2) {
      setError('Please enter your full name');
      return;
    }
    
    if (!formData.mobileNumber) {
      setError('Please enter mobile number');
      return;
    }
    
    if (!validateMobile(formData.mobileNumber)) {
      setError('Invalid mobile number format. Use +919876543210');
      return;
    }
    
    if (formData.pincode && !validatePincode(formData.pincode)) {
      setError('Invalid pincode format (must be 6 digits)');
      return;
    }
    
    setLoading(true);
    
    try {
      const payload = {
        mobile_number: formData.mobileNumber,
        user_type: formData.userType,
        name: formData.name,
        ...(formData.businessName && { business_name: formData.businessName }),
        ...(formData.city && { city: formData.city }),
        ...(formData.state && { state: formData.state }),
        ...(formData.pincode && { pincode: formData.pincode }),
        ...(formData.vehicleTypes.length > 0 && { vehicle_types: formData.vehicleTypes }),
        ...(formData.operatingStates.length > 0 && { operating_states: formData.operatingStates })
      };
      
      const response = await axios.post('/api/auth/register', payload);
      
      if (response.data.success) {
        setSuccess(true);
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Registration failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  if (success) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-green-50 to-orange-50 p-4">
        <div className="bg-white rounded-2xl shadow-xl p-8 w-full max-w-md text-center">
          <div className="text-6xl mb-4">🎉</div>
          <h2 className="text-2xl font-bold text-gray-800 mb-4">Registration Successful!</h2>
          <p className="text-gray-600 mb-6">
            Your account has been created successfully. Please proceed to login.
          </p>
          <a
            href="/login"
            className="inline-block bg-green-600 hover:bg-green-700 text-white font-semibold px-8 py-3 rounded-lg transition-colors"
          >
            Go to Login
          </a>
        </div>
      </div>
    );
  }

  const vehicleOptions = [
    'Two Wheeler', 'Auto Rickshaw', 'Pickup Van', 
    'Mini Truck', '6-Wheeler', '10-Wheeler', 'Refrigerated Truck'
  ];

  const stateOptions = [
    'Delhi', 'Uttar Pradesh', 'Punjab', 'Haryana', 'Rajasthan',
    'Maharashtra', 'Gujarat', 'Karnataka', 'Tamil Nadu', 'West Bengal'
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 to-orange-50 p-4 py-12">
      <div className="max-w-3xl mx-auto">
        <div className="bg-white rounded-2xl shadow-xl p-8">
          {/* Header */}
          <div className="text-center mb-8">
            <div className="text-5xl mb-4">🌾</div>
            <h1 className="text-3xl font-bold text-gray-800 mb-2">SwadeshAI Registration</h1>
            <p className="text-gray-600">Create your account to get started</p>
          </div>

          {/* Error Alert */}
          {error && (
            <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg flex items-start gap-3">
              <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
              <p className="text-sm text-red-700">{error}</p>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-6">
            {/* User Type Selection */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-3">
                I am a <span className="text-red-500">*</span>
              </label>
              <div className="grid grid-cols-3 gap-3">
                {[
                  { value: 'buyer', label: '🛒 Buyer', desc: 'Wholesaler/Retailer' },
                  { value: 'seller', label: '🌾 Seller', desc: 'Farmer/Supplier' },
                  { value: 'logistic', label: '🚚 Logistic', desc: 'Transport Provider' }
                ].map((type) => (
                  <button
                    key={type.value}
                    type="button"
                    onClick={() => handleInputChange('userType', type.value)}
                    className={`p-4 rounded-lg border-2 text-sm font-medium transition-all ${
                      formData.userType === type.value
                        ? 'border-green-500 bg-green-50 text-green-700'
                        : 'border-gray-200 hover:border-gray-300 text-gray-700'
                    }`}
                  >
                    <div className="text-2xl mb-1">{type.label.split(' ')[0]}</div>
                    <div className="font-semibold">{type.label.split(' ')[1]}</div>
                    <div className="text-xs text-gray-600 mt-1">{type.desc}</div>
                  </button>
                ))}
              </div>
            </div>

            {/* Basic Information */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-2">
                  Full Name <span className="text-red-500">*</span>
                </label>
                <div className="relative">
                  <User className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                  <input
                    id="name"
                    type="text"
                    value={formData.name}
                    onChange={(e) => handleInputChange('name', e.target.value)}
                    placeholder="Rajesh Kumar"
                    className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                  />
                </div>
              </div>

              <div>
                <label htmlFor="mobile" className="block text-sm font-medium text-gray-700 mb-2">
                  Mobile Number <span className="text-red-500">*</span>
                </label>
                <div className="relative">
                  <Phone className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                  <input
                    id="mobile"
                    type="tel"
                    value={formData.mobileNumber}
                    onChange={(e) => handleInputChange('mobileNumber', e.target.value)}
                    placeholder="+919876543210"
                    className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                  />
                </div>
              </div>
            </div>

            {/* Business Name (Optional) */}
            <div>
              <label htmlFor="businessName" className="block text-sm font-medium text-gray-700 mb-2">
                Business Name {formData.userType && (
                  <span className="text-gray-500 text-xs">(Optional for {formData.userType}s)</span>
                )}
              </label>
              <div className="relative">
                <Building2 className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                <input
                  id="businessName"
                  type="text"
                  value={formData.businessName}
                  onChange={(e) => handleInputChange('businessName', e.target.value)}
                  placeholder="Company Name"
                  className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                />
              </div>
            </div>

            {/* Location */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label htmlFor="city" className="block text-sm font-medium text-gray-700 mb-2">
                  City
                </label>
                <input
                  id="city"
                  type="text"
                  value={formData.city}
                  onChange={(e) => handleInputChange('city', e.target.value)}
                  placeholder="Delhi"
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                />
              </div>

              <div>
                <label htmlFor="state" className="block text-sm font-medium text-gray-700 mb-2">
                  State
                </label>
                <input
                  id="state"
                  type="text"
                  value={formData.state}
                  onChange={(e) => handleInputChange('state', e.target.value)}
                  placeholder="Delhi"
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                />
              </div>

              <div>
                <label htmlFor="pincode" className="block text-sm font-medium text-gray-700 mb-2">
                  Pincode
                </label>
                <input
                  id="pincode"
                  type="text"
                  value={formData.pincode}
                  onChange={(e) => handleInputChange('pincode', e.target.value.replace(/\D/g, '').slice(0, 6))}
                  placeholder="110001"
                  maxLength={6}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                />
              </div>
            </div>

            {/* Logistics-specific fields */}
            {formData.userType === 'logistic' && (
              <>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-3">
                    Vehicle Types Available
                  </label>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
                    {vehicleOptions.map((vehicle) => (
                      <button
                        key={vehicle}
                        type="button"
                        onClick={() => handleArrayToggle('vehicleTypes', vehicle)}
                        className={`px-3 py-2 rounded-lg border text-sm font-medium transition-all ${
                          formData.vehicleTypes.includes(vehicle)
                            ? 'border-green-500 bg-green-50 text-green-700'
                            : 'border-gray-200 hover:border-gray-300 text-gray-700'
                        }`}
                      >
                        {vehicle}
                      </button>
                    ))}
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-3">
                    Operating States
                  </label>
                  <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
                    {stateOptions.map((state) => (
                      <button
                        key={state}
                        type="button"
                        onClick={() => handleArrayToggle('operatingStates', state)}
                        className={`px-3 py-2 rounded-lg border text-sm font-medium transition-all ${
                          formData.operatingStates.includes(state)
                            ? 'border-green-500 bg-green-50 text-green-700'
                            : 'border-gray-200 hover:border-gray-300 text-gray-700'
                        }`}
                      >
                        {state}
                      </button>
                    ))}
                  </div>
                </div>
              </>
            )}

            {/* Submit Button */}
            <button
              type="submit"
              disabled={loading}
              className="w-full bg-green-600 hover:bg-green-700 text-white font-semibold py-3 rounded-lg flex items-center justify-center gap-2 transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed"
            >
              {loading ? (
                <>
                  <Loader className="w-5 h-5 animate-spin" />
                  Registering...
                </>
              ) : (
                <>
                  <CheckCircle className="w-5 h-5" />
                  Register
                </>
              )}
            </button>
          </form>

          {/* Footer */}
          <div className="mt-6 text-center">
            <p className="text-sm text-gray-600">
              Already have an account?{' '}
              <a href="/login" className="text-green-600 hover:text-green-700 font-semibold">
                Login here
              </a>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Register;
