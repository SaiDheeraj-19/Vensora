import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import LoginView from './pages/LoginView';
import ChangePasswordView from './pages/ChangePasswordView';
import DashboardLayout from './layouts/DashboardLayout';
import LiveCallsView from './pages/LiveCallsView';
import KnowledgeBaseView from './pages/KnowledgeBaseView';
import UsersView from './pages/UsersView';
import CallHistoryView from './pages/CallHistoryView';
import ContactsView from './pages/ContactsView';
import './index.css';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginView />} />
        <Route path="/change-password" element={<ChangePasswordView />} />
        
        <Route path="/" element={<DashboardLayout />}>
          <Route index element={<Navigate to="/live-calls" replace />} />
          <Route path="live-calls" element={<LiveCallsView />} />
          <Route path="knowledge-base" element={<KnowledgeBaseView />} />
          <Route path="users" element={<UsersView />} />
          <Route path="history" element={<CallHistoryView />} />
          <Route path="contacts" element={<ContactsView />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
