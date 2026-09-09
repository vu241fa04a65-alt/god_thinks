import React, { useState, useEffect, useRef } from 'react';
import {
  MessageSquare,
  Send,
  Mic,
  MicOff,
  X,
  Bot,
  User,
  Sparkles,
  Globe,
  Loader2,
  Volume2,
  AlertTriangle,
  ChevronDown,
} from 'lucide-react';
import { ChatbotService } from '../services/api';

interface ChatMessage {
  id: string;
  sender: 'user' | 'bot';
  text: string;
  actions?: string[];
  warning?: string;
  timestamp: string;
}

const SUPPORTED_LANGUAGES = [
  { code: 'hi', label: 'हिंदी (Hindi)', speechLocale: 'hi-IN' },
  { code: 'mr', label: 'मराठी (Marathi)', speechLocale: 'mr-IN' },
  { code: 'te', label: 'తెలుగు (Telugu)', speechLocale: 'te-IN' },
  { code: 'en', label: 'English', speechLocale: 'en-US' },
];

export const Chatbot: React.FC = () => {
  const [isOpen, setIsOpen] = useState<boolean>(false);
  const [language, setLanguage] = useState<string>('hi');
  const [inputText, setInputText] = useState<string>('');
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: 'welcome',
      sender: 'bot',
      text: 'नमस्ते किसान भाई! मैं CropHealthAI कृषी सहाय्यक हूँ। फसल रोग, फवारणी किंवा सेंद्रिय उपायांबद्दल काहीही विचारा। (Ask me about crop diseases, sprays or bio-controls).',
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    },
  ]);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [isListening, setIsListening] = useState<boolean>(false);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const recognitionRef = useRef<any>(null);

  // Auto scroll to latest message
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isOpen]);

  // Setup Web Speech Recognition API
  useEffect(() => {
    const SpeechRecognition =
      (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;

    if (SpeechRecognition) {
      const recognition = new SpeechRecognition();
      recognition.continuous = false;
      recognition.interimResults = false;

      // Select locale based on current language
      const langConfig = SUPPORTED_LANGUAGES.find((l) => l.code === language);
      recognition.lang = langConfig?.speechLocale || 'en-US';

      recognition.onresult = (event: any) => {
        const transcript = event.results[0][0].transcript;
        if (transcript) {
          setInputText(transcript);
        }
        setIsListening(false);
      };

      recognition.onerror = () => {
        setIsListening(false);
      };

      recognition.onend = () => {
        setIsListening(false);
      };

      recognitionRef.current = recognition;
    }
  }, [language]);

  // Toggle voice recognition
  const toggleVoiceInput = () => {
    if (!recognitionRef.current) {
      alert('Speech Recognition is not supported by your current browser.');
      return;
    }

    if (isListening) {
      recognitionRef.current.stop();
      setIsListening(false);
    } else {
      try {
        const langConfig = SUPPORTED_LANGUAGES.find((l) => l.code === language);
        recognitionRef.current.lang = langConfig?.speechLocale || 'en-US';
        recognitionRef.current.start();
        setIsListening(true);
      } catch (e) {
        setIsListening(false);
      }
    }
  };

  // Send message to API
  const handleSendMessage = async (textToSend?: string) => {
    const query = (textToSend || inputText).trim();
    if (!query || isLoading) return;

    const userMsg: ChatMessage = {
      id: `user-${Date.now()}`,
      sender: 'user',
      text: query,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInputText('');
    setIsLoading(true);

    try {
      const response = await ChatbotService.getAdvice({
        message: query,
        language: language,
      });

      const data = response.data?.data;
      const botMsg: ChatMessage = {
        id: `bot-${Date.now()}`,
        sender: 'bot',
        text: data?.response_text || 'Unable to analyze message. Please try again.',
        actions: data?.recommended_actions || [],
        warning: data?.safety_warning,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };
      setMessages((prev) => [...prev, botMsg]);
    } catch (err) {
      const errorMsg: ChatMessage = {
        id: `bot-err-${Date.now()}`,
        sender: 'bot',
        text: 'क्षमा करें, सलाह प्राप्त करने में त्रुटि हुई। कृपया पुनः प्रयास करें।',
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="fixed bottom-6 right-6 z-50 flex flex-col items-end">
      {/* Expanded Chatbot Modal */}
      {isOpen && (
        <div className="mb-3 w-[380px] sm:w-[420px] max-w-[94vw] h-[580px] max-h-[82vh] bg-white rounded-3xl shadow-2xl border border-gray-100 flex flex-col overflow-hidden animate-in slide-in-from-bottom-5 duration-200">
          {/* Header */}
          <div className="bg-gradient-to-r from-emerald-700 to-teal-800 p-4 text-white flex items-center justify-between shadow-md">
            <div className="flex items-center gap-2.5">
              <div className="w-10 h-10 rounded-2xl bg-white/10 backdrop-blur-md flex items-center justify-center border border-white/20 text-lg">
                🌿
              </div>
              <div>
                <h3 className="font-bold text-sm tracking-tight flex items-center gap-1.5">
                  CropHealth AI Bot
                  <span className="w-2 h-2 rounded-full bg-emerald-300 animate-pulse" />
                </h3>
                <p className="text-[11px] text-emerald-100/80">Multilingual Field Agronomist</p>
              </div>
            </div>

            <div className="flex items-center gap-2">
              {/* Language Selector */}
              <div className="relative">
                <select
                  value={language}
                  onChange={(e) => setLanguage(e.target.value)}
                  className="appearance-none bg-emerald-900/60 text-white text-xs font-semibold py-1 px-2.5 pr-6 rounded-xl border border-emerald-500/40 focus:outline-none cursor-pointer"
                >
                  {SUPPORTED_LANGUAGES.map((l) => (
                    <option key={l.code} value={l.code} className="text-gray-900 bg-white">
                      {l.label}
                    </option>
                  ))}
                </select>
                <ChevronDown className="w-3 h-3 text-emerald-300 absolute right-1.5 top-2 pointer-events-none" />
              </div>

              <button
                onClick={() => setIsOpen(false)}
                className="p-1.5 text-white/80 hover:text-white hover:bg-white/10 rounded-xl transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* Quick Disease Prompt Chips */}
          <div className="px-3 py-2 bg-emerald-50/50 border-b border-emerald-100 flex gap-1.5 overflow-x-auto text-[11px] no-scrollbar">
            <button
              onClick={() => handleSendMessage('Tomato leaf brown concentric spots')}
              className="whitespace-nowrap px-2.5 py-1 bg-white hover:bg-emerald-50 border border-emerald-200 text-emerald-800 rounded-full font-medium shadow-2xs"
            >
              🍅 Tomato Early Blight
            </button>
            <button
              onClick={() => handleSendMessage('Potato leaves water soaked spots')}
              className="whitespace-nowrap px-2.5 py-1 bg-white hover:bg-emerald-50 border border-emerald-200 text-emerald-800 rounded-full font-medium shadow-2xs"
            >
              🥔 Late Blight
            </button>
            <button
              onClick={() => handleSendMessage('Grape yellow oily spots on leaves')}
              className="whitespace-nowrap px-2.5 py-1 bg-white hover:bg-emerald-50 border border-emerald-200 text-emerald-800 rounded-full font-medium shadow-2xs"
            >
              🍇 Downy Mildew
            </button>
          </div>

          {/* Messages Feed */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4 text-xs bg-slate-50/60">
            {messages.map((m) => (
              <div
                key={m.id}
                className={`flex gap-2.5 ${m.sender === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                {m.sender === 'bot' && (
                  <div className="w-7 h-7 rounded-xl bg-emerald-100 text-emerald-700 flex items-center justify-center flex-shrink-0 mt-0.5 shadow-2xs">
                    <Bot className="w-4 h-4" />
                  </div>
                )}

                <div
                  className={`max-w-[82%] rounded-2xl p-3.5 space-y-2 shadow-xs leading-relaxed ${
                    m.sender === 'user'
                      ? 'bg-emerald-600 text-white rounded-br-none'
                      : 'bg-white text-gray-800 rounded-bl-none border border-gray-100'
                  }`}
                >
                  <p className="whitespace-pre-line text-xs">{m.text}</p>

                  {/* Dynamic Action Steps */}
                  {m.actions && m.actions.length > 0 && (
                    <div className="pt-2 border-t border-gray-100 space-y-1">
                      <span className="font-bold text-[10px] uppercase tracking-wider text-emerald-700 block">
                        Recommended Actions:
                      </span>
                      {m.actions.map((act, i) => (
                        <div key={i} className="text-[11px] text-gray-700 flex items-start gap-1">
                          <span className="text-emerald-600 font-bold">•</span>
                          <span>{act}</span>
                        </div>
                      ))}
                    </div>
                  )}

                  <div
                    className={`text-[9px] text-right ${
                      m.sender === 'user' ? 'text-emerald-200' : 'text-gray-400'
                    }`}
                  >
                    {m.timestamp}
                  </div>
                </div>

                {m.sender === 'user' && (
                  <div className="w-7 h-7 rounded-xl bg-emerald-800 text-white flex items-center justify-center flex-shrink-0 mt-0.5 shadow-2xs">
                    <User className="w-4 h-4" />
                  </div>
                )}
              </div>
            ))}

            {isLoading && (
              <div className="flex gap-2 items-center text-xs text-gray-500">
                <Loader2 className="w-4 h-4 animate-spin text-emerald-600" />
                <span>कृषी सल्लागार विचार करत आहे (Generating advisory)...</span>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Chat Input Bar */}
          <div className="p-3 bg-white border-t border-gray-100">
            <form
              onSubmit={(e) => {
                e.preventDefault();
                handleSendMessage();
              }}
              className="flex items-center gap-2"
            >
              {/* Web Speech Voice Input Button */}
              <button
                type="button"
                onClick={toggleVoiceInput}
                className={`p-2.5 rounded-2xl transition-all ${
                  isListening
                    ? 'bg-red-500 text-white animate-pulse shadow-md shadow-red-200'
                    : 'bg-gray-100 hover:bg-gray-200 text-gray-600'
                }`}
                title={isListening ? 'Listening... click to stop' : 'Click to speak'}
              >
                {isListening ? <MicOff className="w-4 h-4" /> : <Mic className="w-4 h-4" />}
              </button>

              <input
                type="text"
                value={inputText}
                onChange={(e) => setInputText(e.target.value)}
                placeholder={
                  isListening
                    ? 'Listening... speak now'
                    : language === 'hi'
                    ? 'रोग या फसल के बारे में पूछें...'
                    : language === 'mr'
                    ? 'पिकावरील रोगाबद्दल विचारा...'
                    : 'Ask about crop symptoms or sprays...'
                }
                className="flex-1 px-3.5 py-2.5 bg-gray-50 border border-gray-200 rounded-2xl text-xs focus:outline-none focus:ring-2 focus:ring-emerald-500 text-gray-800"
              />

              <button
                type="submit"
                disabled={!inputText.trim() || isLoading}
                className={`p-2.5 rounded-2xl text-white font-bold transition-all shadow-sm ${
                  !inputText.trim() || isLoading
                    ? 'bg-gray-200 text-gray-400 cursor-not-allowed'
                    : 'bg-emerald-600 hover:bg-emerald-700 shadow-emerald-200'
                }`}
              >
                <Send className="w-4 h-4" />
              </button>
            </form>
          </div>
        </div>
      )}

      {/* Floating Widget Trigger Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="group relative flex items-center gap-2 px-5 py-3.5 bg-gradient-to-r from-emerald-600 to-teal-700 hover:from-emerald-500 hover:to-teal-600 text-white rounded-full shadow-2xl shadow-emerald-900/30 transition-all hover:scale-105 active:scale-95"
      >
        <span className="text-xl">🌿</span>
        <span className="text-xs font-bold tracking-wide">
          {isOpen ? 'Close Advisory' : 'Ask CropHealth AI'}
        </span>
        <span className="flex h-2.5 w-2.5 relative">
          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-300 opacity-75" />
          <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-emerald-400" />
        </span>
      </button>
    </div>
  );
};
