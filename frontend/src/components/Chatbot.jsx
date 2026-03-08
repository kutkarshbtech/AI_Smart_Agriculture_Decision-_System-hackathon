import { useState, useRef, useEffect } from 'react'
import axios from 'axios'
import { MessageCircle, Send, Mic, MicOff, Volume2, VolumeX, Globe, Sparkles } from 'lucide-react'

const LANGUAGES = [
  { code: 'hi', label: 'हिन्दी (Hindi)' },
  { code: 'en', label: 'English' },
  { code: 'bn', label: 'বাংলা (Bengali)' },
  { code: 'ta', label: 'தமிழ் (Tamil)' },
  { code: 'te', label: 'తెలుగు (Telugu)' },
  { code: 'mr', label: 'मराठी (Marathi)' },
  { code: 'kn', label: 'ಕನ್ನಡ (Kannada)' },
]

const SUGGESTED_PROMPTS = [
  '🌾 What is the best price for my tomatoes today?',
  '🧊 How should I store onions to reduce spoilage?',
  '🌦️ Will rain affect potato prices this week?',
  '🚚 What is the cheapest way to transport 500kg mangoes?',
  '📈 When should I sell my produce for maximum profit?',
  '🥕 How to check freshness of carrots?',
]

export default function Chatbot({ produceData }) {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [language, setLanguage] = useState('hi')
  const [loading, setLoading] = useState(false)
  const [isRecording, setIsRecording] = useState(false)
  const [playingAudio, setPlayingAudio] = useState(null)
  const messagesEndRef = useRef(null)
  const mediaRecorderRef = useRef(null)
  const audioChunksRef = useRef([])
  const currentAudioRef = useRef(null)

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // Load welcome message on mount
  useEffect(() => {
    loadWelcome()
  }, [])

  const loadWelcome = async () => {
    try {
      const response = await axios.get('/api/v1/chatbot/welcome', { params: { language } })
      if (response.data?.reply) {
        setMessages([{
          role: 'assistant',
          content: response.data.reply,
          sources: response.data.sources || [],
          suggested_actions: response.data.suggested_actions || [],
          timestamp: new Date(),
        }])
      }
    } catch {
      setMessages([{
        role: 'assistant',
        content: 'नमस्ते! 🙏 I am your SwadeshAI farming assistant. Ask me anything about pricing, storage, weather impact, or logistics for your produce.',
        sources: [],
        suggested_actions: [],
        timestamp: new Date(),
      }])
    }
  }

  const sendMessage = async (text) => {
    if (!text.trim()) return

    const userMsg = { role: 'user', content: text.trim(), timestamp: new Date() }
    setMessages((prev) => [...prev, userMsg])
    setInput('')
    setLoading(true)

    try {
      const response = await axios.post('/api/v1/chatbot/message', {
        message: text.trim(),
        language,
        context: {
          crop_name: produceData.cropName,
          quantity_kg: produceData.quantity,
          location: produceData.location,
        },
      })

      const data = response.data
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: data.reply || 'Sorry, I could not process that.',
          sources: data.sources || [],
          suggested_actions: data.suggested_actions || [],
          timestamp: new Date(),
        },
      ])
    } catch (error) {
      console.error('Chatbot error:', error)
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: 'Sorry, something went wrong. Please try again.',
          sources: [],
          suggested_actions: [],
          timestamp: new Date(),
        },
      ])
    } finally {
      setLoading(false)
    }
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage(input)
    }
  }

  // Voice recording
  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      const mediaRecorder = new MediaRecorder(stream, { mimeType: 'audio/webm' })
      mediaRecorderRef.current = mediaRecorder
      audioChunksRef.current = []

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) audioChunksRef.current.push(event.data)
      }

      mediaRecorder.onstop = async () => {
        stream.getTracks().forEach((t) => t.stop())
        const blob = new Blob(audioChunksRef.current, { type: 'audio/webm' })
        await sendVoice(blob)
      }

      mediaRecorder.start()
      setIsRecording(true)
    } catch (err) {
      console.error('Microphone access denied:', err)
      alert('Microphone access is required for voice input.')
    }
  }

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop()
      setIsRecording(false)
    }
  }

  const sendVoice = async (blob) => {
    setLoading(true)
    const userMsg = { role: 'user', content: '🎤 Voice message...', timestamp: new Date() }
    setMessages((prev) => [...prev, userMsg])

    try {
      const formData = new FormData()
      formData.append('audio', blob, 'recording.webm')
      formData.append('language', language)

      const response = await axios.post('/api/v1/chatbot/voice', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })

      const data = response.data

      // Update user message with transcript
      setMessages((prev) => {
        const updated = [...prev]
        const lastUser = updated.findLastIndex((m) => m.role === 'user')
        if (lastUser >= 0) {
          updated[lastUser] = {
            ...updated[lastUser],
            content: data.transcript || '🎤 Voice message',
            confidence: data.transcript_confidence,
          }
        }
        return [
          ...updated,
          {
            role: 'assistant',
            content: data.reply || 'Sorry, I could not process that.',
            sources: data.sources || [],
            suggested_actions: data.suggested_actions || [],
            timestamp: new Date(),
          },
        ]
      })
    } catch (error) {
      console.error('Voice chat error:', error)
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: 'Sorry, I could not process the voice message. Please try typing your question.',
          sources: [],
          suggested_actions: [],
          timestamp: new Date(),
        },
      ])
    } finally {
      setLoading(false)
    }
  }

  // Stop any currently playing audio
  const stopAudio = () => {
    if (currentAudioRef.current) {
      currentAudioRef.current.pause()
      currentAudioRef.current.currentTime = 0
      currentAudioRef.current = null
    }
    // Also stop Web Speech API if active
    if (window.speechSynthesis) {
      window.speechSynthesis.cancel()
    }
    setPlayingAudio(null)
  }

  // Cleanup audio on unmount
  useEffect(() => {
    return () => stopAudio()
  }, [])

  // TTS - Listen to response
  const speakText = async (text, msgIdx) => {
    // If same message is playing, stop it
    if (playingAudio === msgIdx) {
      stopAudio()
      return
    }

    // Stop any previously playing audio first
    stopAudio()

    try {
      setPlayingAudio(msgIdx)
      const response = await axios.post(
        '/api/v1/tts/synthesize',
        { text, language },
        { responseType: 'blob' }
      )
      const audioUrl = URL.createObjectURL(response.data)
      const audio = new Audio(audioUrl)
      currentAudioRef.current = audio
      audio.onended = () => {
        currentAudioRef.current = null
        setPlayingAudio(null)
      }
      audio.onerror = () => {
        currentAudioRef.current = null
        setPlayingAudio(null)
      }
      audio.play()
    } catch {
      currentAudioRef.current = null
      setPlayingAudio(null)
    }
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            <MessageCircle className="w-8 h-8 text-indigo-600" />
            <div>
              <h2 className="text-2xl font-bold text-gray-800">AI Farming Assistant</h2>
              <p className="text-gray-600 text-sm">Multilingual chatbot for pricing, storage & logistics advice</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {playingAudio !== null && (
              <button
                onClick={stopAudio}
                className="flex items-center gap-1.5 px-3 py-1.5 bg-red-100 text-red-700 rounded-lg text-sm font-medium hover:bg-red-200 transition-colors animate-pulse"
              >
                <VolumeX className="w-4 h-4" />
                Stop Audio
              </button>
            )}
            <Globe className="w-4 h-4 text-gray-500" />
            <select
              className="input-field w-auto text-sm py-1"
              value={language}
              onChange={(e) => setLanguage(e.target.value)}
            >
              {LANGUAGES.map((l) => (
                <option key={l.code} value={l.code}>{l.label}</option>
              ))}
            </select>
          </div>
        </div>

        {/* Context Banner */}
        <div className="bg-indigo-50 border border-indigo-200 rounded-lg p-3 text-sm text-indigo-800">
          <Sparkles className="w-4 h-4 inline mr-1" />
          Context: <strong>{produceData.cropName}</strong> • {produceData.quantity} kg • {produceData.location}
        </div>
      </div>

      {/* Chat Messages */}
      <div className="card p-0 overflow-hidden">
        <div className="h-[450px] overflow-y-auto p-4 space-y-4 bg-gray-50">
          {messages.length === 0 && !loading && (
            <div className="text-center py-8">
              <MessageCircle className="w-12 h-12 text-gray-300 mx-auto mb-3" />
              <p className="text-gray-500 mb-4">Start a conversation with your AI farming assistant</p>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-2 max-w-lg mx-auto">
                {SUGGESTED_PROMPTS.slice(0, 4).map((prompt, idx) => (
                  <button
                    key={idx}
                    onClick={() => sendMessage(prompt)}
                    className="text-left text-sm p-3 bg-white border border-gray-200 rounded-lg hover:border-indigo-400 hover:bg-indigo-50 transition-colors"
                  >
                    {prompt}
                  </button>
                ))}
              </div>
            </div>
          )}

          {messages.map((msg, idx) => (
            <div
              key={idx}
              className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-[80%] rounded-xl px-4 py-3 ${
                  msg.role === 'user'
                    ? 'bg-indigo-600 text-white rounded-br-sm'
                    : 'bg-white border border-gray-200 text-gray-800 rounded-bl-sm shadow-sm'
                }`}
              >
                <p className="whitespace-pre-wrap text-sm">{msg.content}</p>

                {msg.confidence !== undefined && (
                  <p className="text-xs mt-1 opacity-70">
                    Transcription confidence: {(msg.confidence * 100).toFixed(0)}%
                  </p>
                )}

                {msg.role === 'assistant' && (
                  <div className="mt-2 flex items-center gap-2">
                    <button
                      onClick={() => speakText(msg.content, idx)}
                      className={`text-xs flex items-center gap-1 px-2 py-1 rounded ${
                        playingAudio === idx
                          ? 'bg-red-100 text-red-700 hover:bg-red-200'
                          : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                      }`}
                    >
                      {playingAudio === idx ? (
                        <><VolumeX className="w-3 h-3" /> Stop</>
                      ) : (
                        <><Volume2 className="w-3 h-3" /> Listen</>
                      )}
                    </button>
                    {msg.sources?.length > 0 && (
                      <span className="text-xs text-gray-400">
                        Sources: {msg.sources.join(', ')}
                      </span>
                    )}
                  </div>
                )}

                {/* Suggested Actions */}
                {msg.suggested_actions?.length > 0 && (
                  <div className="mt-2 flex flex-wrap gap-1">
                    {msg.suggested_actions.map((action, i) => {
                      const label = typeof action === 'string' ? action : action.label || action.action || ''
                      return (
                        <button
                          key={i}
                          onClick={() => sendMessage(label)}
                          className="text-xs bg-indigo-50 text-indigo-700 border border-indigo-200 px-2 py-1 rounded-full hover:bg-indigo-100"
                        >
                          {label}
                        </button>
                      )
                    })}
                  </div>
                )}

                <p className="text-xs mt-1 opacity-50">
                  {msg.timestamp?.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </p>
              </div>
            </div>
          ))}

          {loading && (
            <div className="flex justify-start">
              <div className="bg-white border border-gray-200 rounded-xl px-4 py-3 shadow-sm">
                <div className="flex items-center gap-2">
                  <div className="flex gap-1">
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                  </div>
                  <span className="text-sm text-gray-500">Thinking...</span>
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        <div className="border-t border-gray-200 p-4 bg-white">
          <div className="flex items-center gap-2">
            {/* Voice Button */}
            <button
              onClick={isRecording ? stopRecording : startRecording}
              disabled={loading}
              className={`p-3 rounded-full transition-colors ${
                isRecording
                  ? 'bg-red-500 text-white animate-pulse'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
              title={isRecording ? 'Stop recording' : 'Start voice input'}
            >
              {isRecording ? <MicOff className="w-5 h-5" /> : <Mic className="w-5 h-5" />}
            </button>

            {/* Text Input */}
            <input
              type="text"
              className="input-field flex-1"
              placeholder={isRecording ? 'Recording... Click mic to stop' : 'Type your question here...'}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              disabled={loading || isRecording}
            />

            {/* Send Button */}
            <button
              onClick={() => sendMessage(input)}
              disabled={!input.trim() || loading}
              className="btn-primary p-3 rounded-full"
            >
              <Send className="w-5 h-5" />
            </button>
          </div>

          {/* Quick Prompts */}
          {messages.length > 0 && (
            <div className="flex flex-wrap gap-2 mt-3">
              {SUGGESTED_PROMPTS.slice(0, 3).map((prompt, idx) => (
                <button
                  key={idx}
                  onClick={() => sendMessage(prompt)}
                  disabled={loading}
                  className="text-xs bg-gray-100 text-gray-600 px-3 py-1.5 rounded-full hover:bg-indigo-50 hover:text-indigo-700 transition-colors"
                >
                  {prompt}
                </button>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
