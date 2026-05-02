import React, { useState, useRef, useEffect } from 'react';
import { Send, Upload, X, Bot, User, Cloud, Settings, MessageSquare, Trash2, Download, AlertCircle, CheckCircle, Mic, MicOff } from 'lucide-react';

const AtlasChatApp = () => {
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isConnected, setIsConnected] = useState(false);
  const [threadId, setThreadId] = useState(null);
  const [showSettings, setShowSettings] = useState(false);
  const [apiUrl, setApiUrl] = useState('http://127.0.0.1:8000');
  const [connectionError, setConnectionError] = useState('');
  
  // Voice recording states
  const [isRecording, setIsRecording] = useState(false);
  const [isTranscribing, setIsTranscribing] = useState(false);
  const [recordingTime, setRecordingTime] = useState(0);
  const [mediaRecorder, setMediaRecorder] = useState(null);
  
  const messagesEndRef = useRef(null);
  const fileInputRef = useRef(null);
  const chatContainerRef = useRef(null);
  const textareaRef = useRef(null);
  const recordingIntervalRef = useRef(null);
  const audioChunksRef = useRef([]);

  // Check API health on mount and when API URL changes
  useEffect(() => {
    checkApiHealth();
  }, [apiUrl]);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = textareaRef.current.scrollHeight + 'px';
    }
  }, [inputMessage]);

  // Recording timer effect
  useEffect(() => {
    if (isRecording) {
      recordingIntervalRef.current = setInterval(() => {
        setRecordingTime(prev => prev + 1);
      }, 1000);
    } else {
      if (recordingIntervalRef.current) {
        clearInterval(recordingIntervalRef.current);
      }
      setRecordingTime(0);
    }

    return () => {
      if (recordingIntervalRef.current) {
        clearInterval(recordingIntervalRef.current);
      }
    };
  }, [isRecording]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const checkApiHealth = async () => {
    try {
      setConnectionError('');
      const response = await fetch(`${apiUrl}/health`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });
      
      if (response.ok) {
        setIsConnected(true);
        // Load conversation history
        loadConversationHistory();
      } else {
        setIsConnected(false);
        setConnectionError(`API returned status: ${response.status}`);
      }
    } catch (error) {
      setIsConnected(false);
      setConnectionError(error.message || 'Failed to connect to API');
      console.error('API health check failed:', error);
    }
  };

  const loadConversationHistory = async () => {
    if (!threadId) return;
    try {
      const response = await fetch(`${apiUrl}/conversation/${threadId}`);
      if (response.ok) {
        const data = await response.json();
        setMessages(data.messages || []);
      }
    } catch (error) {
      console.error('Failed to load conversation history:', error);
    }
  };

  const handleFileSelect = (event) => {
    const files = Array.from(event.target.files);
    setSelectedFiles(prev => [...prev, ...files]);
    // Reset file input
    event.target.value = '';
  };

  const removeFile = (index) => {
    setSelectedFiles(prev => prev.filter((_, i) => i !== index));
  };

  // Voice recording functions
  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream, {
        mimeType: 'audio/webm;codecs=opus'
      });
      
      audioChunksRef.current = [];
      
      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };
      
      recorder.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        await transcribeAudio(audioBlob);
        
        // Stop all tracks to release microphone
        stream.getTracks().forEach(track => track.stop());
      };
      
      setMediaRecorder(recorder);
      recorder.start();
      setIsRecording(true);
    } catch (error) {
      console.error('Error accessing microphone:', error);
      alert('Could not access microphone. Please check permissions.');
    }
  };

  const stopRecording = () => {
    if (mediaRecorder && mediaRecorder.state === 'recording') {
      mediaRecorder.stop();
      setIsRecording(false);
    }
  };

  const transcribeAudio = async (audioBlob) => {
    setIsTranscribing(true);
    try {
      const formData = new FormData();
      formData.append('audio', audioBlob, 'recording.webm');
      
      const response = await fetch(`${apiUrl}/transcribe/`, {
        method: 'POST',
        body: formData,
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Transcription failed');
      }
      
      const data = await response.json();
      if (data.transcript) {
        setInputMessage(prev => prev + (prev ? ' ' : '') + data.transcript);
      }
    } catch (error) {
      console.error('Transcription error:', error);
      alert(`Transcription failed: ${error.message}`);
    } finally {
      setIsTranscribing(false);
    }
  };

  const formatRecordingTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const sendMessage = async (defaultPrompt) => {
    if (!inputMessage.trim() && selectedFiles.length === 0 && !defaultPrompt?.trim()) return;
    if (!isConnected) {
      alert('API is not connected. Please check your connection.');
      return;
    }

    const userMessage = {
      role: 'user',
      content: inputMessage.trim()
    };
    
    if(inputMessage.trim() && !defaultPrompt) {
      setMessages(prev => [...prev, userMessage]);
      setInputMessage('');
    }
    setIsLoading(true);

    try {
      const formData = new FormData();
      formData.append('message', userMessage.content);
      if (threadId) {
        formData.append('thread_id', threadId);
      }
      if(defaultPrompt) {
        formData.append('message', defaultPrompt?.trim());
      }
      
      selectedFiles.forEach(file => {
        formData.append('files', file);
      });
      
      const response = await fetch(`${apiUrl}/generate`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      const agentMessage = {
        role: 'agent',
        content: data.content,
        tool_calls: data.tool_calls,
        file_urls: data.file_urls
      };

      setMessages(prev => [...prev, agentMessage]);
      setThreadId(data.thread_id);
      
    } catch (error) {
      console.error('Error sending message:', error);
      const errorMessage = {
        role: 'agent',
        content: `Sorry, I encountered an error while processing your request: ${error.message}. Please try again.`
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setSelectedFiles([]);
      setIsLoading(false);
    }
  };

  const clearConversation = async () => {
    if (!threadId) return;
    if (!window.confirm('Are you sure you want to clear the conversation?')) return;
    
    try {
      const response = await fetch(`${apiUrl}/conversation/${threadId}`, {
        method: 'DELETE',
      });
      
      if (response.ok) {
        setMessages([]);
        setThreadId(null);
      }
    } catch (error) {
      console.error('Failed to clear conversation:', error);
    }
  };
  
  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      if (!isLoading) {  // Only send if not already loading
        sendMessage();
      }
    }
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const formatTime = () => {
    return new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  return (
    <div className="min-h-screen relative overflow-hidden">
      {/* Background with blur */}
      <div className="absolute inset-0 bg-cover bg-center bg-no-repeat" style={{ 
        backgroundImage: 'url(/ibmimg.jpeg)',
        filter: 'blur(8px)',
        transform: 'scale(1.02)',
        width: '100%',
        height: '100%',
        backgroundPosition: 'center center',
        backgroundSize: 'contain',
        backgroundRepeat: 'no-repeat'
      }}></div>
      {/* Dark overlay */}
      <div className="absolute inset-0 bg-black/40"></div>
      {/* Content */}
      <div className="relative z-10 flex flex-col h-screen">
        {/* Header */}
        <header className="bg-white/10 backdrop-blur-md border-b border-white/20 p-4">
          <div className="max-w-6xl mx-auto flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="p-2 bg-gradient-to-r from-blue-500 to-purple-600 rounded-xl shadow-lg">
                <Cloud className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-white">IBM CloudMate</h1>
                <p className="text-sm text-white/90">Your Intelligent Cloud Infrastructure Agent</p>
              </div>
            </div>
            
            <div className="flex items-center space-x-3">
              <div className={`flex items-center space-x-2 px-4 py-2 rounded-full transition-all duration-300 ${
                isConnected ? 'bg-green-500/20 text-green-300 border border-green-500/30' : 'bg-red-500/20 text-red-300 border border-red-500/30'
              }`}>
                {isConnected ? (
                  <CheckCircle className="w-4 h-4" />
                ) : (
                  <AlertCircle className="w-4 h-4" />
                )}
                <span className="text-sm font-medium">{isConnected ? 'Connected' : 'Disconnected'}</span>
              </div>
              
              <button
                onClick={() => setShowSettings(!showSettings)}
                className="p-2 text-gray-300 hover:text-white hover:bg-white/10 rounded-lg transition-all duration-200"
                title="Settings"
              >
                <Settings className="w-5 h-5" />
              </button>
              
              <button
                onClick={clearConversation}
                className="p-2 text-gray-300 hover:text-white hover:bg-white/10 rounded-lg transition-all duration-200"
                title="Clear conversation"
              >
                <Trash2 className="w-5 h-5" />
              </button>
            </div>
          </div>

          {/* Settings Panel */}
          {showSettings && (
            <div className="mt-4 p-6 bg-white/5 backdrop-blur-md rounded-xl border border-white/10 animate-fade-in">
              <div className="max-w-6xl mx-auto">
                <h3 className="text-white font-semibold mb-4 flex items-center space-x-2">
                  <Settings className="w-5 h-5" />
                  <span>API Configuration</span>
                </h3>
                <div className="flex items-center space-x-4">
                  <label className="text-gray-300 text-sm font-medium min-w-fit">API URL:</label>
                  <input
                    type="text"
                    value={apiUrl}
                    onChange={(e) => setApiUrl(e.target.value)}
                    className="flex-1 max-w-md px-4 py-2 bg-white/10 border border-white/20 rounded-lg text-white placeholder-gray-400 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="http://localhost:8000"
                  />
                  <button
                    onClick={checkApiHealth}
                    className="px-6 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg text-sm transition-colors font-medium"
                  >
                    Test Connection
                  </button>
                </div>
                {connectionError && (
                  <div className="mt-3 p-3 bg-red-500/10 border border-red-500/20 rounded-lg">
                    <p className="text-red-300 text-sm">{connectionError}</p>
                  </div>
                )}
              </div>
            </div>
          )}
        </header>

        {/* Chat Messages */}
        <div 
          ref={chatContainerRef}
          className="flex-1 overflow-y-auto p-4 space-y-4"
        >
          <div className="max-w-6xl mx-auto">
            {messages.length === 0 ? (
              <div className="text-center py-16">
                <div className="p-6 bg-gradient-to-r from-blue-500 to-purple-600 rounded-full w-20 h-20 mx-auto mb-6 flex items-center justify-center shadow-2xl">
                  <Bot className="w-10 h-10 text-white" />
                </div>
                <h2 className="text-3xl font-bold text-white mb-4">Welcome to IBM CloudMate</h2>
                <p className="text-gray-300 max-w-2xl mx-auto text-lg leading-relaxed mb-8">
                  I'm your intelligent cloud infrastructure agent. While I can interact with all IBM Cloud services, 
                  I currently have implemented support for Cloud Object Storage (COS) and Cloudant databases. 
                  More services will be added soon!
                </p>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6 max-w-4xl mx-auto">
                  <div className="p-6 bg-white/5 backdrop-blur-md rounded-xl border border-white/10 hover:bg-white/10 transition-all duration-300 cursor-pointer" onClick={() =>  sendMessage('What can you do with Cloud Object Storage?')}>
                    <Cloud className="w-8 h-8 text-blue-400 mb-3" />
                    <h3 className="text-white font-semibold mb-2">Cloud Object Storage</h3>
                    <p className="text-gray-300 text-sm">Currently implemented: Create buckets, upload files, manage versions</p>
                  </div>
                  <div className="p-6 bg-white/5 backdrop-blur-md rounded-xl border border-white/10 hover:bg-white/10 transition-all duration-300 cursor-pointer" onClick={() =>  sendMessage('What can you do with Cloudant?')}>
                    <MessageSquare className="w-8 h-8 text-purple-400 mb-3" />
                    <h3 className="text-white font-semibold mb-2">Cloudant Database</h3>
                    <p className="text-gray-300 text-sm">Currently implemented: CRUD operations, queries, configurations</p>
                  </div>
                </div>
              </div>
            ) : (
              messages.map((message, index) => (
                <div
                  key={index}
                  className={`flex items-start space-x-4 ${
                    message.role === 'user' ? 'flex-row-reverse space-x-reverse' : ''
                  } animate-fade-in`}
                >
                  <div className={`p-3 rounded-xl shadow-lg ${
                    message.role === 'user' 
                      ? 'bg-gradient-to-r from-blue-500 to-purple-600' 
                      : 'bg-white/10 backdrop-blur-md border border-white/20'
                  }`}>
                    {message.role === 'user' ? (
                      <User className="w-5 h-5 text-white" />
                    ) : (
                      <Bot className="w-5 h-5 text-white" />
                    )}
                  </div>
                  
                  <div className={`flex-1 max-w-4xl ${
                    message.role === 'user' ? 'text-right' : ''
                  }`}>
                    <div className={`inline-block p-4 rounded-2xl shadow-lg ${
                      message.role === 'user'
                        ? 'bg-gradient-to-r from-blue-500 to-purple-600 text-white'
                        : 'bg-white/10 backdrop-blur-md border border-white/20 text-white'
                    }`}>
                      <div className="whitespace-pre-wrap leading-relaxed">
                        {message.content.startsWith('{') || message.content.startsWith('[') ? (
                          <div className="bg-gray-900/50 rounded-lg p-4 border border-gray-700">
                            <pre className="text-sm text-gray-300 overflow-x-auto">
                              {JSON.stringify(JSON.parse(message.content), null, 2)}
                            </pre>
                          </div>
                        ) : (
                          message.content
                        )}
                      </div>
                      
                      {/* Tool calls display */}
                      {message.tool_calls && message.tool_calls.length > 0 && (
                        <div className="mt-4 pt-4 border-t border-white/20">
                          <p className="text-sm text-gray-300 mb-2 font-medium">🔧 Tools used:</p>
                          <div className="flex flex-wrap gap-2">
                            {message.tool_calls.map((tool, idx) => (
                              <div key={idx} className="text-xs bg-white/10 rounded-full px-3 py-1 border border-white/20">
                                <span className="font-medium">{tool.name}</span>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                      
                      {/* File URLs display */}
                      {message.file_urls && Object.keys(message.file_urls).length > 0 && (
                        <div className="mt-4 pt-4 border-t border-white/20">
                          <p className="text-sm text-gray-300 mb-2 font-medium">📁 Files:</p>
                          <div className="flex flex-wrap gap-2">
                            {Object.entries(message.file_urls).map(([filename, url]) => (
                              <a
                                key={filename}
                                href={`${apiUrl}${url}`}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="inline-flex items-center space-x-2 text-xs bg-white/10 rounded-full px-3 py-1 hover:bg-white/20 transition-colors border border-white/20"
                              >
                                <Download className="w-3 h-3" />
                                <span>{filename}</span>
                              </a>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                    
                    <div className={`text-xs text-gray-400 mt-2 ${
                      message.role === 'user' ? 'text-right' : ''
                    }`}>
                      {formatTime()}
                    </div>
                  </div>
                </div>
              ))
            )}
            
            {isLoading && (
              <div className="flex items-start space-x-4 animate-fade-in">
                <div className="p-3 rounded-xl bg-white/10 backdrop-blur-md border border-white/20 shadow-lg">
                  <Bot className="w-5 h-5 text-white" />
                </div>
                <div className="flex-1 max-w-4xl">
                  <div className="inline-block p-4 rounded-2xl bg-white/10 backdrop-blur-md border border-white/20 shadow-lg">
                    <div className="flex space-x-2">
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{animationDelay: '0.1s'}}></div>
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{animationDelay: '0.2s'}}></div>
                    </div>
                  </div>
                </div>
              </div>
            )}
            
            <div ref={messagesEndRef} />
          </div>
        </div>

        {/* Input Area */}
        <div className="p-6 bg-white/10 backdrop-blur-md border-t border-white/20">
          <div className="max-w-6xl mx-auto">
            {/* Selected Files */}
            {selectedFiles.length > 0 && (
              <div className="mb-4 flex flex-wrap gap-3">
                {selectedFiles.map((file, index) => (
                  <div
                    key={index}
                    className="flex items-center space-x-3 bg-white/10 backdrop-blur-md rounded-xl px-4 py-3 border border-white/20 shadow-lg"
                  >
                    <div className="flex-1 min-w-0">
                      <p className="text-sm text-white truncate font-medium">
                        {file.name}
                      </p>
                      <p className="text-xs text-gray-300">
                        {formatFileSize(file.size)}
                      </p>
                    </div>
                    <button
                      onClick={() => removeFile(index)}
                      className="text-gray-400 hover:text-white transition-colors p-1 hover:bg-white/10 rounded"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  </div>
                ))}
              </div>
            )}

            {/* Recording indicator */}
            {(isRecording || isTranscribing) && (
              <div className="mb-4 flex items-center justify-center">
                <div className="flex items-center space-x-3 bg-red-500/20 backdrop-blur-md rounded-xl px-6 py-3 border border-red-500/30 shadow-lg">
                  {isRecording && (
                    <>
                      <div className="w-3 h-3 bg-red-500 rounded-full animate-pulse"></div>
                      <span className="text-red-300 font-medium">Recording: {formatRecordingTime(recordingTime)}</span>
                    </>
                  )}
                  {isTranscribing && (
                    <>
                      <div className="flex space-x-1">
                        <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce"></div>
                        <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{animationDelay: '0.1s'}}></div>
                        <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{animationDelay: '0.2s'}}></div>
                      </div>
                      <span className="text-blue-300 font-medium">Transcribing...</span>
                    </>
                  )}
                </div>
              </div>
            )}

            {/* Input Form */}
            <div className="flex items-end space-x-4">
              <div className="flex-1 relative">
                <textarea
                  ref={textareaRef}
                  value={inputMessage}
                  onChange={(e) => setInputMessage(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder="Ask IBM CloudMate about cloud infrastructure..."
                  className="w-full px-6 py-4 bg-white/10 backdrop-blur-md border border-white/20 rounded-2xl text-white placeholder-gray-400 resize-none focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200 shadow-lg disabled:opacity-50 disabled:cursor-not-allowed"
                  rows={1}
                  style={{ minHeight: '56px', maxHeight: '120px' }}
                  disabled={isLoading || isRecording}
                />
              </div>
              
              <input
                ref={fileInputRef}
                type="file"
                multiple
                onChange={handleFileSelect}
                className="hidden"
                disabled={isLoading || isRecording}
              />
              
              <button
                onClick={() => fileInputRef.current?.click()}
                className="p-4 text-gray-300 hover:text-white hover:bg-white/10 rounded-2xl transition-all duration-200 border border-white/20 backdrop-blur-md shadow-lg disabled:opacity-50 disabled:cursor-not-allowed"
                title="Upload files"
                disabled={isLoading || isRecording}
              >
                <Upload className="w-5 h-5" />
              </button>
              
              {/* Voice Recording Button */}
              <button
                onClick={isRecording ? stopRecording : startRecording}
                className={`p-4 rounded-2xl transition-all duration-200 border backdrop-blur-md shadow-lg disabled:opacity-50 disabled:cursor-not-allowed transform hover:scale-105 active:scale-95 ${
                  isRecording 
                    ? 'bg-red-500 hover:bg-red-600 text-white border-red-500' 
                    : 'text-gray-300 hover:text-white hover:bg-white/10 border-white/20'
                }`}
                title={isRecording ? 'Stop recording' : 'Start voice recording'}
                disabled={isLoading || isTranscribing}
              >
                {isRecording ? <MicOff className="w-5 h-5" /> : <Mic className="w-5 h-5" />}
              </button>
              
              <button
                onClick={() => sendMessage()}
                disabled={(!inputMessage.trim() && selectedFiles.length === 0) || isLoading || isRecording}
                className="p-4 bg-gradient-to-r from-blue-500 to-purple-600 text-white rounded-2xl hover:from-blue-600 hover:to-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 transform hover:scale-105 active:scale-95 shadow-lg"
                title="Send message"
              >
                <Send className="w-5 h-5" />
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AtlasChatApp;