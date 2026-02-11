import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { Toaster } from 'sonner'
import './index.css'
import App from './App.tsx'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
    <Toaster
      theme="dark"
      position="bottom-right"
      toastOptions={{
        style: {
          background: '#202020',
          border: '1px solid rgba(255,255,255,0.1)',
          color: '#F5F5F5',
          fontFamily: '"JetBrains Mono", monospace',
          fontSize: '13px',
        },
      }}
    />
  </StrictMode>,
)
