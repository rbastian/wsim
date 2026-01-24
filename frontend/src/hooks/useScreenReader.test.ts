import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { useScreenReader } from './useScreenReader'

describe('useScreenReader', () => {
  let liveRegion: HTMLElement

  beforeEach(() => {
    // Create a mock live region element
    liveRegion = document.createElement('div')
    liveRegion.id = 'sr-live-region'
    document.body.appendChild(liveRegion)
  })

  afterEach(() => {
    // Clean up the live region
    if (liveRegion && liveRegion.parentNode) {
      document.body.removeChild(liveRegion)
    }
    vi.clearAllTimers()
  })

  it('should announce message with polite priority by default', async () => {
    vi.useFakeTimers()
    const { result } = renderHook(() => useScreenReader())

    act(() => {
      result.current.announce('Test message')
    })

    // Initially empty after clearing
    expect(liveRegion.textContent).toBe('')
    expect(liveRegion.getAttribute('aria-live')).toBe('polite')

    // After timeout, message should appear
    act(() => {
      vi.advanceTimersByTime(100)
    })

    expect(liveRegion.textContent).toBe('Test message')

    vi.useRealTimers()
  })

  it('should announce message with assertive priority', async () => {
    vi.useFakeTimers()
    const { result } = renderHook(() => useScreenReader())

    act(() => {
      result.current.announce('Urgent message', 'assertive')
    })

    expect(liveRegion.getAttribute('aria-live')).toBe('assertive')

    act(() => {
      vi.advanceTimersByTime(100)
    })

    expect(liveRegion.textContent).toBe('Urgent message')

    vi.useRealTimers()
  })

  it('should clear region before announcing', async () => {
    vi.useFakeTimers()
    const { result } = renderHook(() => useScreenReader())

    // Set initial content
    liveRegion.textContent = 'Old message'

    act(() => {
      result.current.announce('New message')
    })

    // Should be cleared immediately
    expect(liveRegion.textContent).toBe('')

    act(() => {
      vi.advanceTimersByTime(100)
    })

    expect(liveRegion.textContent).toBe('New message')

    vi.useRealTimers()
  })

  it('should cancel previous announcement when new one is made', async () => {
    vi.useFakeTimers()
    const { result } = renderHook(() => useScreenReader())

    act(() => {
      result.current.announce('First message')
    })

    // Advance time by 50ms (less than 100ms timeout)
    act(() => {
      vi.advanceTimersByTime(50)
    })

    // First message should not be shown yet
    expect(liveRegion.textContent).toBe('')

    // Make another announcement
    act(() => {
      result.current.announce('Second message')
    })

    // Advance remaining time
    act(() => {
      vi.advanceTimersByTime(100)
    })

    // Only the second message should appear
    expect(liveRegion.textContent).toBe('Second message')

    vi.useRealTimers()
  })

  it('should handle custom live region ID', async () => {
    vi.useFakeTimers()
    const customLiveRegion = document.createElement('div')
    customLiveRegion.id = 'custom-live-region'
    document.body.appendChild(customLiveRegion)

    const { result } = renderHook(() =>
      useScreenReader({ liveRegionId: 'custom-live-region' })
    )

    act(() => {
      result.current.announce('Custom region message')
    })

    act(() => {
      vi.advanceTimersByTime(100)
    })

    expect(customLiveRegion.textContent).toBe('Custom region message')
    // Original region should be unchanged
    expect(liveRegion.textContent).toBe('')

    document.body.removeChild(customLiveRegion)
    vi.useRealTimers()
  })

  it('should warn when live region not found', () => {
    const consoleWarnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {})

    // Remove the live region
    document.body.removeChild(liveRegion)

    const { result } = renderHook(() => useScreenReader())

    act(() => {
      result.current.announce('Test message')
    })

    expect(consoleWarnSpy).toHaveBeenCalledWith(
      'Live region with id "sr-live-region" not found'
    )

    consoleWarnSpy.mockRestore()
  })

  it('should clean up timeout on unmount', async () => {
    vi.useFakeTimers()
    const { result, unmount } = renderHook(() => useScreenReader())

    act(() => {
      result.current.announce('Test message')
    })

    // Unmount before timeout completes
    unmount()

    // Advance timers
    act(() => {
      vi.advanceTimersByTime(100)
    })

    // Message should not be set because cleanup happened
    expect(liveRegion.textContent).toBe('')

    vi.useRealTimers()
  })

  it('should handle multiple announcements in sequence', async () => {
    vi.useFakeTimers()
    const { result } = renderHook(() => useScreenReader())

    // First announcement
    act(() => {
      result.current.announce('First')
    })

    act(() => {
      vi.advanceTimersByTime(100)
    })

    expect(liveRegion.textContent).toBe('First')

    // Second announcement
    act(() => {
      result.current.announce('Second')
    })

    act(() => {
      vi.advanceTimersByTime(100)
    })

    expect(liveRegion.textContent).toBe('Second')

    // Third announcement with different priority
    act(() => {
      result.current.announce('Third', 'assertive')
    })

    act(() => {
      vi.advanceTimersByTime(100)
    })

    expect(liveRegion.textContent).toBe('Third')
    expect(liveRegion.getAttribute('aria-live')).toBe('assertive')

    vi.useRealTimers()
  })

  it('should handle empty string announcements', async () => {
    vi.useFakeTimers()
    const { result } = renderHook(() => useScreenReader())

    act(() => {
      result.current.announce('')
    })

    act(() => {
      vi.advanceTimersByTime(100)
    })

    expect(liveRegion.textContent).toBe('')

    vi.useRealTimers()
  })

  it('should handle special characters in announcements', async () => {
    vi.useFakeTimers()
    const { result } = renderHook(() => useScreenReader())

    const specialMessage = 'Test <script>alert("xss")</script> & "quotes"'

    act(() => {
      result.current.announce(specialMessage)
    })

    act(() => {
      vi.advanceTimersByTime(100)
    })

    // textContent automatically escapes HTML
    expect(liveRegion.textContent).toBe(specialMessage)

    vi.useRealTimers()
  })
})
