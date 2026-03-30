import { createBrowserRouter, Navigate } from 'react-router-dom'
import AppLayout from './AppLayout'
import HomePage from '../pages/HomePage'
import AuthPage from '../pages/AuthPage'
import AboutPage from '../pages/AboutPage'
import ChatPage from '../pages/ChatPage'
import AdminUsersPage from '../pages/AdminUsersPage'
import SettingsPage from '../pages/SettingsPage'

export const router = createBrowserRouter([
  {
    element: <AppLayout />,
    children: [
      { path: '/', element: <HomePage /> },
      { path: '/login', element: <AuthPage /> },
      { path: '/cadastro', element: <Navigate to="/login" replace /> },
      { path: '/sobre', element: <AboutPage /> },
      { path: '/chat', element: <ChatPage /> },
      { path: '/admin', element: <AdminUsersPage /> },
      { path: '/configuracoes', element: <SettingsPage /> },
    ],
  },
])
