import React, { useState, useEffect } from 'react';
import Layout from '@theme/Layout';
import useDocusaurusContext from '@docusaurus/useDocusaurusContext';
import styles from './chat.module.css';

function ChatPage() {
  const { siteConfig } = useDocusaurusContext();
  const [messages, setMessages] = useState([
    { id: 1, text: "Hello! I'm your AI assistant for the Physical AI textbook. How can I help you today?", sender: 'ai' }
  ]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleSendMessage = async () => {
    if (!inputValue.trim()) return;

    // Add user message
    const userMessage = { id: Date.now(), text: inputValue, sender: 'user' };
    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsLoading(true);

    try {
      // Call the backend RAG API
      const response = await fetch('http://localhost:8000/api/v1/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          session_id: 'frontend-session', // In a real app, you'd manage sessions properly
          query: inputValue,
          mode: 'full_book', // Use full-book RAG mode
          book_id: 'textbook-content' // Default book ID - would be dynamic in production
        })
      });

      if (!response.ok) {
        throw new Error(`API error: ${response.status} ${response.statusText}`);
      }

      const data = await response.json();

      const aiResponse = {
        id: Date.now() + 1,
        text: data.answer || "Sorry, I couldn't generate a response.",
        sender: 'ai'
      };
      setMessages(prev => [...prev, aiResponse]);
    } catch (error) {
      console.error('Error sending message:', error);
      const errorMessage = {
        id: Date.now() + 1,
        text: "Sorry, I encountered an error processing your request. The backend might not be running or properly configured.",
        sender: 'ai'
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <Layout
      title={`AI Chat - ${siteConfig.title}`}
      description="Interactive AI chatbot for the Physical AI textbook">
      <div className={styles.chatContainer}>
        <div className={styles.chatHeader}>
          <h1>AI Textbook Assistant</h1>
          <p>Ask questions about Physical AI, Humanoid Robotics, ROS 2, and more</p>
        </div>

        <div className={styles.chatMessages}>
          {messages.map((message) => (
            <div
              key={message.id}
              className={`${styles.message} ${styles[message.sender]}`}
            >
              <div className={styles.messageText}>{message.text}</div>
            </div>
          ))}
          {isLoading && (
            <div className={`${styles.message} ${styles.ai}`}>
              <div className={styles.typingIndicator}>
                <div className={styles.dot}></div>
                <div className={styles.dot}></div>
                <div className={styles.dot}></div>
              </div>
            </div>
          )}
        </div>

        <div className={styles.chatInput}>
          <textarea
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Ask a question about the textbook content..."
            rows="3"
            disabled={isLoading}
          />
          <button
            onClick={handleSendMessage}
            disabled={isLoading || !inputValue.trim()}
            className={styles.sendButton}
          >
            {isLoading ? 'Sending...' : 'Send'}
          </button>
        </div>
      </div>
    </Layout>
  );
}

export default ChatPage;