// Login Component with Mobile OTP Authentication
import React, { useState } from 'react';
import axios from 'axios';
import { useAuth } from '../context/AuthContext';
import { Phone, Key, Loader, AlertCircle, CheckCircle } from 'lucide-react';

const Login = () => {
  const { login } = useAuth();
  
  // Form state
  const [userType, setUserType] = useState('');
  const [mobileNumber, setMobileNumber] = useState('');
  const [otp, setOtp] = useState('');
  
  // UI state
  const [step, setStep] = useState(1); // 1 = enter mobile, 2 = enter OTP
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [demoOtp, setDemoOtp] = useState('');

  const validateMobile = (mobile) => {
    const cleaned = mobile.replace(/[^0-9+]/g, '');
    return /^\+?[1-9]\d{9,14}$/.test(cleaned);
  };

  const handleRequestOTP = async (e) => {
    e.preventDefault();
    setError('');
    
    // Validation
    if (!userType) {
      setError('Please select user type');
      return;
    }
    
    if (!mobileNumber) {
      setError('Please enter mobile number');
      return;
    }
    
    if (!validateMobile(mobileNumber)) {
      setError('Invalid mobile number format. Use +919876543210');
      return;
    }
    
    setLoading(true);
    
    try {
      const response = await axios.post('/api/auth/login/request-otp', {
        mobile_number: mobileNumber,
        user_type: userType
      });
      
      if (response.data.success) {
        setStep(2);
        setDemoOtp(response.data.demo_otp || '');
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to send OTP. Please check your mobile number.');
    } finally {
      setLoading(false);
    }
  };

  const handleVerifyOTP = async (e) => {
    e.preventDefault();
    setError('');
    
    if (!otp || otp.length !== 6) {
      setError('Please enter 6-digit OTP');
      return;
    }
    
    setLoading(true);
    
    try {
      const response = await axios.post('/api/auth/login/verify-otp', {
        mobile_number: mobileNumber,
        user_type: userType,
        otp: otp
      });
      
      const { access_token, user_id, user_type: uType, name, mobile_number: mobile } = response.data;
      
      login(access_token, {
        id: user_id,
        user_type: uType,
        name: name,
        mobile_number: mobile
      });
      
      // Redirect will be handled by App.jsx based on auth state
    } catch (err) {
      setError(err.response?.data?.detail || 'Invalid OTP. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleBack = () => {
    setStep(1);
    setOtp('');
    setDemoOtp('');
    setError('');
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-green-50 to-orange-50 p-4">
      <div className="bg-white rounded-2xl shadow-xl p-8 w-full max-w-md">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="text-5xl mb-4">🌾</div>
          <h1 className="text-3xl font-bold text-gray-800 mb-2">SwadeshAI</h1>
          <p className="text-gray-600">Login to your account</p>
        </div>

        {/* Error Alert */}
        {error && (
          <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
            <p className="text-sm text-red-700">{error}</p>
          </div>
        )}

        {/* Step 1: Request OTP */}
        {step === 1 && (
          <form onSubmit={handleRequestOTP} className="space-y-6">
            {/* User Type Selection */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Login as
              </label>
              <div className="grid grid-cols-3 gap-3">
                {[
                  { value: 'buyer', label: '🛒 Buyer', color: 'blue' },
                  { value: 'seller', label: '🌾 Seller', color: 'green' },
                  { value: 'logistic', label: '🚚 Logistic', color: 'orange' }
                ].map((type) => (
                  <button
                    key={type.value}
                    type="button"
                    onClick={() => setUserType(type.value)}
                    className={`p-3 rounded-lg border-2 text-sm font-medium transition-all ${
                      userType === type.value
                        ? `border-${type.color}-500 bg-${type.color}-50 text-${type.color}-700`
                        : 'border-gray-200 hover:border-gray-300 text-gray-700'
                    }`}
                  >
                    {type.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Mobile Number Input */}
            <div>
              <label htmlFor="mobile" className="block text-sm font-medium text-gray-700 mb-2">
                Mobile Number
              </label>
              <div className="relative">
                <Phone className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                <input
                  id="mobile"
                  type="tel"
                  value={mobileNumber}
                  onChange={(e) => setMobileNumber(e.target.value)}
                  placeholder="+919876543210"
                  className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                />
              </div>
              <p className="mt-1 text-xs text-gray-500">Include country code (e.g., +91 for India)</p>
            </div>

            {/* Submit Button */}
            <button
              type="submit"
              disabled={loading}
              className="w-full bg-green-600 hover:bg-green-700 text-white font-semibold py-3 rounded-lg flex items-center justify-center gap-2 transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed"
            >
              {loading ? (
                <>
                  <Loader className="w-5 h-5 animate-spin" />
                  Sending OTP...
                </>
              ) : (
                <>
                  <Phone className="w-5 h-5" />
                  Send OTP
                </>
              )}
            </button>
          </form>
        )}

        {/* Step 2: Verify OTP */}
        {step === 2 && (
          <form onSubmit={handleVerifyOTP} className="space-y-6">
            {/* Success Message */}
            <div className="p-4 bg-green-50 border border-green-200 rounded-lg flex items-start gap-3">
              <CheckCircle className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
              <div>
                <p className="text-sm text-green-700">OTP sent to {mobileNumber}</p>
                {demoOtp && (
                  <p className="text-xs text-green-600 mt-1 font-mono">
                    Demo OTP: <strong>{demoOtp}</strong>
                  </p>
                )}
              </div>
            </div>

            {/* OTP Input */}
            <div>
              <label htmlFor="otp" className="block text-sm font-medium text-gray-700 mb-2">
                Enter 6-digit OTP
              </label>
              <div className="relative">
                <Key className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                <input
                  id="otp"
                  type="text"
                  value={otp}
                  onChange={(e) => setOtp(e.target.value.replace(/\D/g, '').slice(0, 6))}
                  placeholder="123456"
                  maxLength={6}
                  className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg text-center text-2xl tracking-widest font-mono focus:ring-2 focus:ring-green-500 focus:border-transparent"
                />
              </div>
            </div>

            {/* Buttons */}
            <div className="flex gap-3">
              <button
                type="button"
                onClick={handleBack}
                disabled={loading}
                className="flex-1 bg-gray-200 hover:bg-gray-300 text-gray-700 font-semibold py-3 rounded-lg transition-colors disabled:opacity-50"
              >
                Back
              </button>
              <button
                type="submit"
                disabled={loading}
                className="flex-1 bg-green-600 hover:bg-green-700 text-white font-semibold py-3 rounded-lg flex items-center justify-center gap-2 transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed"
              >
                {loading ? (
                  <>
                    <Loader className="w-5 h-5 animate-spin" />
                    Verifying...
                  </>
                ) : (
                  <>
                    <Key className="w-5 h-5" />
                    Verify & Login
                  </>
                )}
              </button>
            </div>
          </form>
        )}

        {/* Footer */}
        <div className="mt-6 text-center">
          <p className="text-sm text-gray-600">
            Don't have an account?{' '}
            <a href="/register" className="text-green-600 hover:text-green-700 font-semibold">
              Register here
            </a>
          </p>
        </div>
      </div>
    </div>
  );
};

export default Login;
