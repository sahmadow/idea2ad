import { render, screen } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import App from './App'

// Mock react-router-dom
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return {
    ...actual,
    BrowserRouter: ({ children }) => children,
  }
})

// Mock the API module
vi.mock('./api')

describe('App', () => {
  it('renders landing page by default', () => {
    render(<App />)
    // Landing page should have LaunchAd branding
    expect(screen.getAllByText(/launchad/i).length).toBeGreaterThan(0)
  })

  it('renders hero section', () => {
    render(<App />)
    expect(screen.getByText(/launch your first ad/i)).toBeInTheDocument()
  })

  it('renders CTA button', () => {
    render(<App />)
    expect(screen.getByText(/get started free/i)).toBeInTheDocument()
  })
})
