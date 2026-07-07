'use client';

import Layout from '@/components/Layout';
import ChatPanel from '@/components/ChatPanel';

export default function ChatPage() {
  return (
    <Layout currentPage="chat">
      <div className="p-8 h-[calc(100vh-2rem)]">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold text-white">AI Chat</h1>
            <p className="text-dark-600 mt-1">Ask the AI assistant for trading insights</p>
          </div>
        </div>
        <div className="h-[calc(100%-6rem)]">
          <ChatPanel />
        </div>
      </div>
    </Layout>
  );
}
