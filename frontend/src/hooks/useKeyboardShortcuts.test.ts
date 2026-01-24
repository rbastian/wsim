import { describe, it, expect, vi } from 'vitest'
import { renderHook } from '@testing-library/react'
import { useKeyboardShortcuts, type KeyboardShortcut } from './useKeyboardShortcuts'

describe('useKeyboardShortcuts', () => {
  const createKeyboardEvent = (
    key: string,
    modifiers: {
      ctrl?: boolean
      alt?: boolean
      shift?: boolean
      meta?: boolean
    } = {}
  ): KeyboardEvent => {
    return new KeyboardEvent('keydown', {
      key,
      ctrlKey: modifiers.ctrl || false,
      altKey: modifiers.alt || false,
      shiftKey: modifiers.shift || false,
      metaKey: modifiers.meta || false,
      bubbles: true,
      cancelable: true,
    })
  }

  it('should trigger action when matching key is pressed', () => {
    const action = vi.fn()
    const shortcuts: KeyboardShortcut[] = [
      {
        key: 'a',
        description: 'Test action',
        action,
      },
    ]

    renderHook(() => useKeyboardShortcuts({ shortcuts }))

    const event = createKeyboardEvent('a')
    document.dispatchEvent(event)

    expect(action).toHaveBeenCalledTimes(1)
  })

  it('should be case insensitive', () => {
    const action = vi.fn()
    const shortcuts: KeyboardShortcut[] = [
      {
        key: 'A',
        description: 'Test action',
        action,
      },
    ]

    renderHook(() => useKeyboardShortcuts({ shortcuts }))

    // Press lowercase 'a'
    document.dispatchEvent(createKeyboardEvent('a'))
    expect(action).toHaveBeenCalledTimes(1)

    // Press uppercase 'A'
    document.dispatchEvent(createKeyboardEvent('A'))
    expect(action).toHaveBeenCalledTimes(2)
  })

  it('should match Ctrl modifier', () => {
    const action = vi.fn()
    const shortcuts: KeyboardShortcut[] = [
      {
        key: 's',
        ctrl: true,
        description: 'Save',
        action,
      },
    ]

    renderHook(() => useKeyboardShortcuts({ shortcuts }))

    // Press 's' without Ctrl - should not trigger
    document.dispatchEvent(createKeyboardEvent('s'))
    expect(action).not.toHaveBeenCalled()

    // Press 's' with Ctrl - should trigger
    document.dispatchEvent(createKeyboardEvent('s', { ctrl: true }))
    expect(action).toHaveBeenCalledTimes(1)
  })

  it('should match Alt modifier', () => {
    const action = vi.fn()
    const shortcuts: KeyboardShortcut[] = [
      {
        key: 'f',
        alt: true,
        description: 'File menu',
        action,
      },
    ]

    renderHook(() => useKeyboardShortcuts({ shortcuts }))

    document.dispatchEvent(createKeyboardEvent('f'))
    expect(action).not.toHaveBeenCalled()

    document.dispatchEvent(createKeyboardEvent('f', { alt: true }))
    expect(action).toHaveBeenCalledTimes(1)
  })

  it('should match Shift modifier', () => {
    const action = vi.fn()
    const shortcuts: KeyboardShortcut[] = [
      {
        key: 'a',
        shift: true,
        description: 'Select all',
        action,
      },
    ]

    renderHook(() => useKeyboardShortcuts({ shortcuts }))

    document.dispatchEvent(createKeyboardEvent('a'))
    expect(action).not.toHaveBeenCalled()

    document.dispatchEvent(createKeyboardEvent('a', { shift: true }))
    expect(action).toHaveBeenCalledTimes(1)
  })

  it('should match Meta modifier', () => {
    const action = vi.fn()
    const shortcuts: KeyboardShortcut[] = [
      {
        key: 'k',
        meta: true,
        description: 'Command palette',
        action,
      },
    ]

    renderHook(() => useKeyboardShortcuts({ shortcuts }))

    document.dispatchEvent(createKeyboardEvent('k'))
    expect(action).not.toHaveBeenCalled()

    document.dispatchEvent(createKeyboardEvent('k', { meta: true }))
    expect(action).toHaveBeenCalledTimes(1)
  })

  it('should match multiple modifiers', () => {
    const action = vi.fn()
    const shortcuts: KeyboardShortcut[] = [
      {
        key: 's',
        ctrl: true,
        shift: true,
        description: 'Save As',
        action,
      },
    ]

    renderHook(() => useKeyboardShortcuts({ shortcuts }))

    // Only Ctrl
    document.dispatchEvent(createKeyboardEvent('s', { ctrl: true }))
    expect(action).not.toHaveBeenCalled()

    // Only Shift
    document.dispatchEvent(createKeyboardEvent('s', { shift: true }))
    expect(action).not.toHaveBeenCalled()

    // Both Ctrl and Shift
    document.dispatchEvent(createKeyboardEvent('s', { ctrl: true, shift: true }))
    expect(action).toHaveBeenCalledTimes(1)
  })

  it('should prevent default by default', () => {
    const action = vi.fn()
    const shortcuts: KeyboardShortcut[] = [
      {
        key: 's',
        ctrl: true,
        description: 'Save',
        action,
      },
    ]

    renderHook(() => useKeyboardShortcuts({ shortcuts }))

    const event = createKeyboardEvent('s', { ctrl: true })
    const preventDefaultSpy = vi.spyOn(event, 'preventDefault')

    document.dispatchEvent(event)

    expect(action).toHaveBeenCalledTimes(1)
    expect(preventDefaultSpy).toHaveBeenCalledTimes(1)
  })

  it('should not prevent default when preventDefault is false', () => {
    const action = vi.fn()
    const shortcuts: KeyboardShortcut[] = [
      {
        key: 'a',
        description: 'Test action',
        action,
        preventDefault: false,
      },
    ]

    renderHook(() => useKeyboardShortcuts({ shortcuts }))

    const event = createKeyboardEvent('a')
    const preventDefaultSpy = vi.spyOn(event, 'preventDefault')

    document.dispatchEvent(event)

    expect(action).toHaveBeenCalledTimes(1)
    expect(preventDefaultSpy).not.toHaveBeenCalled()
  })

  it('should handle multiple shortcuts', () => {
    const action1 = vi.fn()
    const action2 = vi.fn()
    const action3 = vi.fn()
    const shortcuts: KeyboardShortcut[] = [
      {
        key: 'a',
        description: 'Action 1',
        action: action1,
      },
      {
        key: 'b',
        description: 'Action 2',
        action: action2,
      },
      {
        key: 'c',
        ctrl: true,
        description: 'Action 3',
        action: action3,
      },
    ]

    renderHook(() => useKeyboardShortcuts({ shortcuts }))

    document.dispatchEvent(createKeyboardEvent('a'))
    expect(action1).toHaveBeenCalledTimes(1)
    expect(action2).not.toHaveBeenCalled()
    expect(action3).not.toHaveBeenCalled()

    document.dispatchEvent(createKeyboardEvent('b'))
    expect(action1).toHaveBeenCalledTimes(1)
    expect(action2).toHaveBeenCalledTimes(1)
    expect(action3).not.toHaveBeenCalled()

    document.dispatchEvent(createKeyboardEvent('c', { ctrl: true }))
    expect(action1).toHaveBeenCalledTimes(1)
    expect(action2).toHaveBeenCalledTimes(1)
    expect(action3).toHaveBeenCalledTimes(1)
  })

  it('should only trigger first matching shortcut', () => {
    const action1 = vi.fn()
    const action2 = vi.fn()
    const shortcuts: KeyboardShortcut[] = [
      {
        key: 'a',
        description: 'Action 1',
        action: action1,
      },
      {
        key: 'a',
        description: 'Action 2',
        action: action2,
      },
    ]

    renderHook(() => useKeyboardShortcuts({ shortcuts }))

    document.dispatchEvent(createKeyboardEvent('a'))

    // Only the first matching shortcut should be triggered
    expect(action1).toHaveBeenCalledTimes(1)
    expect(action2).not.toHaveBeenCalled()
  })

  it('should not trigger when disabled', () => {
    const action = vi.fn()
    const shortcuts: KeyboardShortcut[] = [
      {
        key: 'a',
        description: 'Test action',
        action,
      },
    ]

    renderHook(() => useKeyboardShortcuts({ shortcuts, enabled: false }))

    document.dispatchEvent(createKeyboardEvent('a'))

    expect(action).not.toHaveBeenCalled()
  })

  it('should re-enable when enabled prop changes', () => {
    const action = vi.fn()
    const shortcuts: KeyboardShortcut[] = [
      {
        key: 'a',
        description: 'Test action',
        action,
      },
    ]

    const { rerender } = renderHook(
      ({ enabled }) => useKeyboardShortcuts({ shortcuts, enabled }),
      { initialProps: { enabled: false } }
    )

    document.dispatchEvent(createKeyboardEvent('a'))
    expect(action).not.toHaveBeenCalled()

    // Enable shortcuts
    rerender({ enabled: true })

    document.dispatchEvent(createKeyboardEvent('a'))
    expect(action).toHaveBeenCalledTimes(1)
  })

  it('should clean up event listener on unmount', () => {
    const action = vi.fn()
    const shortcuts: KeyboardShortcut[] = [
      {
        key: 'a',
        description: 'Test action',
        action,
      },
    ]

    const { unmount } = renderHook(() => useKeyboardShortcuts({ shortcuts }))

    // Should work before unmount
    document.dispatchEvent(createKeyboardEvent('a'))
    expect(action).toHaveBeenCalledTimes(1)

    // Unmount and try again
    unmount()
    document.dispatchEvent(createKeyboardEvent('a'))

    // Should not trigger after unmount
    expect(action).toHaveBeenCalledTimes(1)
  })

  it('should update when shortcuts array changes', () => {
    const action1 = vi.fn()
    const action2 = vi.fn()

    const shortcuts1: KeyboardShortcut[] = [
      {
        key: 'a',
        description: 'Action 1',
        action: action1,
      },
    ]

    const shortcuts2: KeyboardShortcut[] = [
      {
        key: 'a',
        description: 'Action 2',
        action: action2,
      },
    ]

    const { rerender } = renderHook(
      ({ shortcuts }) => useKeyboardShortcuts({ shortcuts }),
      { initialProps: { shortcuts: shortcuts1 } }
    )

    document.dispatchEvent(createKeyboardEvent('a'))
    expect(action1).toHaveBeenCalledTimes(1)
    expect(action2).not.toHaveBeenCalled()

    // Update shortcuts
    rerender({ shortcuts: shortcuts2 })

    document.dispatchEvent(createKeyboardEvent('a'))
    expect(action1).toHaveBeenCalledTimes(1)
    expect(action2).toHaveBeenCalledTimes(1)
  })

  it('should handle special keys', () => {
    const escapeAction = vi.fn()
    const enterAction = vi.fn()
    const spaceAction = vi.fn()

    const shortcuts: KeyboardShortcut[] = [
      {
        key: 'Escape',
        description: 'Close',
        action: escapeAction,
      },
      {
        key: 'Enter',
        description: 'Submit',
        action: enterAction,
      },
      {
        key: ' ',
        description: 'Space',
        action: spaceAction,
      },
    ]

    renderHook(() => useKeyboardShortcuts({ shortcuts }))

    document.dispatchEvent(createKeyboardEvent('Escape'))
    expect(escapeAction).toHaveBeenCalledTimes(1)

    document.dispatchEvent(createKeyboardEvent('Enter'))
    expect(enterAction).toHaveBeenCalledTimes(1)

    document.dispatchEvent(createKeyboardEvent(' '))
    expect(spaceAction).toHaveBeenCalledTimes(1)
  })

  it('should handle arrow keys', () => {
    const upAction = vi.fn()
    const downAction = vi.fn()
    const leftAction = vi.fn()
    const rightAction = vi.fn()

    const shortcuts: KeyboardShortcut[] = [
      { key: 'ArrowUp', description: 'Up', action: upAction },
      { key: 'ArrowDown', description: 'Down', action: downAction },
      { key: 'ArrowLeft', description: 'Left', action: leftAction },
      { key: 'ArrowRight', description: 'Right', action: rightAction },
    ]

    renderHook(() => useKeyboardShortcuts({ shortcuts }))

    document.dispatchEvent(createKeyboardEvent('ArrowUp'))
    expect(upAction).toHaveBeenCalledTimes(1)

    document.dispatchEvent(createKeyboardEvent('ArrowDown'))
    expect(downAction).toHaveBeenCalledTimes(1)

    document.dispatchEvent(createKeyboardEvent('ArrowLeft'))
    expect(leftAction).toHaveBeenCalledTimes(1)

    document.dispatchEvent(createKeyboardEvent('ArrowRight'))
    expect(rightAction).toHaveBeenCalledTimes(1)
  })

  it('should allow modifier to be undefined (matches any state)', () => {
    const action = vi.fn()
    const shortcuts: KeyboardShortcut[] = [
      {
        key: 'a',
        // No modifiers specified - should match with or without modifiers
        description: 'Test action',
        action,
      },
    ]

    renderHook(() => useKeyboardShortcuts({ shortcuts }))

    // Without modifiers
    document.dispatchEvent(createKeyboardEvent('a'))
    expect(action).toHaveBeenCalledTimes(1)

    // With Ctrl
    document.dispatchEvent(createKeyboardEvent('a', { ctrl: true }))
    expect(action).toHaveBeenCalledTimes(2)

    // With multiple modifiers
    document.dispatchEvent(createKeyboardEvent('a', { ctrl: true, shift: true }))
    expect(action).toHaveBeenCalledTimes(3)
  })
})
