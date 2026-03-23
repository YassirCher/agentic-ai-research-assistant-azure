import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Sidebar from './components/Sidebar';
import ChatWindow from './components/ChatWindow';
import HomeView from './components/HomeView';

function App() {
  const [theme, setTheme] = useState(localStorage.getItem('theme') || 'dark');
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  const [chatRefreshToken, setChatRefreshToken] = useState(0);

  const handleUploadSuccess = () => {
    setChatRefreshToken((prev) => prev + 1);
  };

  return (
    <Router>
      <div className="app-container" data-theme={theme}>
        <Sidebar 
          theme={theme} 
          setTheme={setTheme} 
          isCollapsed={isSidebarCollapsed} 
          setIsCollapsed={setIsSidebarCollapsed} 
          refreshSignal={chatRefreshToken}
        />
        
        <main className="main-content">
          <Routes>
            <Route path="/" element={<HomeView onUploadSuccess={handleUploadSuccess} />} />
            <Route path="/c/:chatId" element={<ChatWindow />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;
