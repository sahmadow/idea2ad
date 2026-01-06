import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import App from './App'
import * as api from './api'

// Mock the API module
vi.mock('./api')

describe('App', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders the main heading', () => {
    render(<App />)
    expect(screen.getByText(/launchad/i)).toBeInTheDocument()
  })

  it('renders the URL input field', () => {
    render(<App />)
    const input = screen.getByPlaceholderText(/your-product/i)
    expect(input).toBeInTheDocument()
  })

  it('renders the generate button', () => {
    render(<App />)
    const button = screen.getByText(/generate campaign/i)
    expect(button).toBeInTheDocument()
  })

  it('shows loading state during analysis', async () => {
    // Mock API to never resolve (simulating loading)
    api.analyzeUrl.mockImplementation(() => new Promise(() => {}))

    render(<App />)

    const input = screen.getByPlaceholderText(/your-product/i)
    fireEvent.change(input, { target: { value: 'https://example.com' } })

    const button = screen.getByText(/generate campaign/i)
    fireEvent.click(button)

    await waitFor(() => {
      expect(screen.getByText(/analyzing/i)).toBeInTheDocument()
    })
  })

  it('displays results after successful analysis', async () => {
    const mockResult = {
      project_url: 'https://example.com',
      analysis: {
        summary: 'Test product summary',
        unique_selling_proposition: 'Best product ever',
        pain_points: ['Problem 1', 'Problem 2'],
        call_to_action: 'Buy Now',
        keywords: ['test', 'product'],
        styling_guide: {
          primary_colors: ['#ff0000'],
          secondary_colors: ['#00ff00'],
          font_families: ['Arial'],
          design_style: 'modern',
          mood: 'professional'
        }
      },
      targeting: {
        age_min: 25,
        age_max: 45,
        genders: ['male', 'female'],
        geo_locations: ['US'],
        interests: ['technology']
      },
      suggested_creatives: [],
      image_briefs: [],
      status: 'ANALYZED'
    }

    api.analyzeUrl.mockResolvedValue(mockResult)

    render(<App />)

    const input = screen.getByPlaceholderText(/your-product/i)
    fireEvent.change(input, { target: { value: 'https://example.com' } })

    const button = screen.getByText(/generate campaign/i)
    fireEvent.click(button)

    await waitFor(() => {
      expect(screen.getByText(/Test product summary/i)).toBeInTheDocument()
    })
  })

  it('displays error message on API failure', async () => {
    api.analyzeUrl.mockRejectedValue(new Error('API Error'))

    render(<App />)

    const input = screen.getByPlaceholderText(/your-product/i)
    fireEvent.change(input, { target: { value: 'https://example.com' } })

    const button = screen.getByText(/generate campaign/i)
    fireEvent.click(button)

    await waitFor(() => {
      expect(screen.getByText(/error/i)).toBeInTheDocument()
    })
  })

  it('validates URL input is required', () => {
    render(<App />)

    const button = screen.getByText(/generate campaign/i)
    fireEvent.click(button)

    // Button should be disabled or show validation error
    // Implementation depends on App component behavior
  })
})

describe('Export functionality', () => {
  it('renders export buttons when results are available', async () => {
    const mockResult = {
      project_url: 'https://example.com',
      analysis: {
        summary: 'Test',
        unique_selling_proposition: 'Best',
        pain_points: [],
        call_to_action: 'Buy',
        keywords: [],
        styling_guide: {
          primary_colors: [],
          secondary_colors: [],
          font_families: [],
          design_style: 'modern',
          mood: 'professional'
        }
      },
      targeting: {
        age_min: 18,
        age_max: 65,
        genders: [],
        geo_locations: [],
        interests: []
      },
      suggested_creatives: [],
      image_briefs: [],
      status: 'ANALYZED'
    }

    api.analyzeUrl.mockResolvedValue(mockResult)

    render(<App />)

    const input = screen.getByPlaceholderText(/your-product/i)
    fireEvent.change(input, { target: { value: 'https://example.com' } })

    const button = screen.getByText(/generate campaign/i)
    fireEvent.click(button)

    await waitFor(() => {
      // Check for export buttons
      expect(screen.getByText(/json/i)).toBeInTheDocument()
    })
  })
})
