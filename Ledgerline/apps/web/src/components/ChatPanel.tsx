'use client';

import { useState, useEffect } from 'react';
import { Send, Bot, User, Sparkles } from 'lucide-react';
import { aiApi, ChatResponse, AiStatusResponse } from '@/lib/api';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
}

export default function ChatPanel() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      role: 'assistant',
      content: '👋 Welcome to Ledgerline AI Trading Assistant! How can I help you today?\n\n**Available features:**\n- 📊 Portfolio Analysis\n- 📈 Signal Generation\n- 🌍 Market Insights\n- 🎯 Trade Recommendations',
      timestamp: '2026-07-07T00:00:00.000000',
    },
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [aiStatus, setAiStatus] = useState<AiStatusResponse | null>(null);

  useEffect(() => {
    aiApi.status().then(res => setAiStatus(res.data)).catch(() => {});
  }, []);

  const handleSend = async () => {
    if (!input.trim() || loading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input.trim(),
      timestamp: new Date().toISOString(),
    };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    try {
      const response = await aiApi.chat({
        message: userMessage.content,
        include_context: true,
      });
      
      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: response.data.content,
        timestamp: response.data.timestamp,
      };
      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: 'Sorry, I encountered an error. Please try again later.',
        timestamp: new Date().toISOString(),
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const isMock = aiStatus?.llm_provider === 'mock';
  const providerName = aiStatus?.llm_provider ? aiStatus.llm_provider.toUpperCase() : '...';
  const modelName = aiStatus?.available_models?.[0] || '';

  return (
    <div className="bg-dark-800 rounded-xl border border-dark-700 h-full flex flex-col">
      <div className="flex items-center gap-3 px-6 py-4 border-b border-dark-700">
        <div className="w-10 h-10 rounded-full bg-gradient-to-br from-primary-500 to-secondary-500 flex items-center justify-center">
          <Bot className="w-5 h-5 text-white" />
        </div>
        <div>
          <h3 className="font-semibold text-white">AI Trading Assistant</h3>
          <p className="text-xs text-dark-600 flex items-center gap-1">
            <Sparkles className="w-3 h-3 text-primary-500" />
            {aiStatus ? (
              isMock ? `Mock Mode` : `${providerName} · ${modelName}`
            ) : 'Connecting...'}
          </p>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-6 space-y-4">
        {messages.map((message) => (
          <div key={message.id} className={`flex gap-3 ${message.role === 'user' ? 'flex-row-reverse' : ''}`}>
            <div className={`w-8 h-8 rounded-full flex-shrink-0 flex items-center justify-center ${
              message.role === 'user' 
                ? 'bg-primary-500/20 text-primary-500' 
                : 'bg-dark-700 text-dark-600'
            }`}>
              {message.role === 'user' ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
            </div>
            <div className={`max-w-[80%] ${message.role === 'user' ? 'text-right' : ''}`}>
              <div className={`inline-block px-4 py-2 rounded-2xl ${
                message.role === 'user' 
                  ? 'bg-primary-500 text-white rounded-tr-sm' 
                  : 'bg-dark-700 text-white rounded-tl-sm'
              }`}>
                <p className="text-sm whitespace-pre-wrap">{message.content}</p>
              </div>
              <p className="text-xs text-dark-600 mt-1">
                {new Date(message.timestamp).toLocaleTimeString('en-US', { hour12: false })}
              </p>
            </div>
          </div>
        ))}
        
        {loading && (
          <div className="flex gap-3">
            <div className="w-8 h-8 rounded-full bg-dark-700 text-dark-600 flex-shrink-0 flex items-center justify-center">
              <Bot className="w-4 h-4" />
            </div>
            <div className="bg-dark-700 px-4 py-2 rounded-2xl rounded-tl-sm">
              <div className="flex gap-1">
                <span className="w-2 h-2 bg-dark-600 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                <span className="w-2 h-2 bg-dark-600 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                <span className="w-2 h-2 bg-dark-600 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
              </div>
            </div>
          </div>
        )}
      </div>

      <div className="p-4 border-t border-dark-700">
        <div className="flex items-center gap-3">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Ask about your portfolio, signals, or market..."
            className="flex-1 bg-dark-700 border border-dark-600 rounded-xl px-4 py-3 text-white placeholder-dark-600 focus:outline-none focus:border-primary-500 transition-colors"
            disabled={loading}
          />
          <button
            onClick={handleSend}
            disabled={loading}
            className={`w-12 h-12 rounded-xl flex items-center justify-center transition-colors ${
              loading 
                ? 'bg-dark-700 text-dark-600 cursor-not-allowed' 
                : 'bg-primary-500 text-white hover:bg-primary-600'
            }`}
          >
            <Send className="w-5 h-5" />
          </button>
        </div>
        <div className="flex items-center gap-2 mt-2">
          <span className="text-xs text-dark-600">Quick actions:</span>
          <button 
            onClick={() => setInput('Analyze my portfolio')}
            className="text-xs px-2 py-1 bg-dark-700 rounded text-dark-600 hover:text-white hover:bg-dark-600 transition-colors"
          >
            Portfolio
          </button>
          <button 
            onClick={() => setInput('Generate RSI signal for BTC')}
            className="text-xs px-2 py-1 bg-dark-700 rounded text-dark-600 hover:text-white hover:bg-dark-600 transition-colors"
          >
            RSI Signal
          </button>
          <button 
            onClick={() => setInput('What is the market outlook?')}
            className="text-xs px-2 py-1 bg-dark-700 rounded text-dark-600 hover:text-white hover:bg-dark-600 transition-colors"
          >
            Market
          </button>
        </div>
      </div>
    </div>
  );
}
