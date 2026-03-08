import { useState, useEffect, useRef } from 'react'
import axios from 'axios'
import { Volume2, VolumeX, Square } from 'lucide-react'

/**
 * SpeakButton – reads text aloud.
 *
 * English: uses Amazon Polly (Kajal neural voice) via /api/v1/tts/synthesize
 * Hindi:   uses browser Web Speech API (hi-IN)
 *
 * Props:
 *   text       – string to speak (plain English)
 *   textHindi  – optional Hindi translation to speak instead when Hindi is selected
 *   label      – button label (default "Read Aloud")
 *   className  – additional CSS classes
 *   size       – "sm" | "md" (default "sm")
 */
export default function SpeakButton({ text, textHindi, label = 'Read Aloud', className = '', size = 'sm' }) {
  const [speaking, setSpeaking] = useState(false)
  const [lang, setLang] = useState('en')
  const audioRef = useRef(null)
  const utteranceRef = useRef(null)

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      window.speechSynthesis?.cancel()
      if (audioRef.current) {
        audioRef.current.pause()
        audioRef.current = null
      }
    }
  }, [])

  const stop = () => {
    window.speechSynthesis?.cancel()
    if (audioRef.current) {
      audioRef.current.pause()
      audioRef.current.currentTime = 0
      audioRef.current = null
    }
    setSpeaking(false)
  }

  const speak = async () => {
    if (speaking) {
      stop()
      return
    }

    const speechText = lang === 'hi' && textHindi ? textHindi : text
    if (!speechText) return

    // ── English → Amazon Polly (Kajal neural voice) ──
    if (lang === 'en') {
      setSpeaking(true)
      try {
        const response = await axios.post(
          '/api/v1/tts/synthesize',
          { text: speechText, language: 'en' },
          { responseType: 'blob' },
        )
        const url = URL.createObjectURL(response.data)
        const audio = new Audio(url)
        audioRef.current = audio
        audio.onended = () => {
          setSpeaking(false)
          URL.revokeObjectURL(url)
          audioRef.current = null
        }
        audio.onerror = () => {
          setSpeaking(false)
          URL.revokeObjectURL(url)
          audioRef.current = null
        }
        audio.play()
      } catch (err) {
        console.warn('Polly TTS failed, falling back to Web Speech API:', err)
        // Fallback to browser TTS if Polly fails
        speakWithBrowser(speechText, 'en-IN')
      }
      return
    }

    // ── Hindi → Web Speech API ──
    speakWithBrowser(speechText, 'hi-IN')
  }

  const speakWithBrowser = (speechText, langCode) => {
    if (!window.speechSynthesis) {
      alert('Text-to-speech is not supported in this browser.')
      return
    }

    const utterance = new SpeechSynthesisUtterance(speechText)
    utterance.lang = langCode
    utterance.rate = 0.9
    utterance.pitch = 1.0

    const voices = window.speechSynthesis.getVoices()
    const targetLang = langCode.split('-')[0]
    const preferred = voices.find(v => v.lang.startsWith(targetLang) && v.lang.includes('IN'))
      || voices.find(v => v.lang.startsWith(targetLang))
    if (preferred) utterance.voice = preferred

    utterance.onend = () => setSpeaking(false)
    utterance.onerror = () => setSpeaking(false)

    utteranceRef.current = utterance
    setSpeaking(true)
    window.speechSynthesis.speak(utterance)
  }

  const sizeClasses = size === 'sm'
    ? 'px-3 py-1.5 text-xs gap-1.5'
    : 'px-4 py-2 text-sm gap-2'

  const iconSize = size === 'sm' ? 'w-3.5 h-3.5' : 'w-4 h-4'

  return (
    <div className={`inline-flex items-center gap-2 ${className}`}>
      {/* Language toggle */}
      <div className="inline-flex rounded-md border border-gray-300 overflow-hidden text-xs">
        <button
          onClick={() => setLang('en')}
          className={`px-2 py-1 transition-colors ${lang === 'en' ? 'bg-primary-600 text-white' : 'bg-white text-gray-600 hover:bg-gray-50'}`}
        >
          EN
        </button>
        <button
          onClick={() => setLang('hi')}
          className={`px-2 py-1 transition-colors ${lang === 'hi' ? 'bg-primary-600 text-white' : 'bg-white text-gray-600 hover:bg-gray-50'}`}
        >
          हिं
        </button>
      </div>

      {/* Speak / Stop button */}
      <button
        onClick={speak}
        disabled={!text}
        className={`inline-flex items-center ${sizeClasses} rounded-lg font-medium transition-all
          ${speaking
            ? 'bg-red-100 text-red-700 hover:bg-red-200 border border-red-300'
            : 'bg-orange-100 text-orange-700 hover:bg-orange-200 border border-orange-300'}
          disabled:opacity-40 disabled:cursor-not-allowed`}
        title={speaking ? 'Stop' : label}
      >
        {speaking ? (
          <>
            <Square className={iconSize} />
            Stop
          </>
        ) : (
          <>
            <Volume2 className={iconSize} />
            {label}
          </>
        )}
      </button>
    </div>
  )
}
