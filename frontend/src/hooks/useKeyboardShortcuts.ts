// Custom hook for managing keyboard shortcuts
// Provides centralized keyboard shortcut handling for the game

import { useEffect } from "react";

export interface KeyboardShortcut {
  key: string;
  ctrl?: boolean;
  alt?: boolean;
  shift?: boolean;
  meta?: boolean;
  description: string;
  action: () => void;
  preventDefault?: boolean;
}

interface UseKeyboardShortcutsOptions {
  shortcuts: KeyboardShortcut[];
  enabled?: boolean;
}

export function useKeyboardShortcuts({
  shortcuts,
  enabled = true,
}: UseKeyboardShortcutsOptions) {
  useEffect(() => {
    if (!enabled) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      for (const shortcut of shortcuts) {
        const keyMatches = e.key.toLowerCase() === shortcut.key.toLowerCase();
        const ctrlMatches = shortcut.ctrl === undefined || shortcut.ctrl === e.ctrlKey;
        const altMatches = shortcut.alt === undefined || shortcut.alt === e.altKey;
        const shiftMatches = shortcut.shift === undefined || shortcut.shift === e.shiftKey;
        const metaMatches = shortcut.meta === undefined || shortcut.meta === e.metaKey;

        if (keyMatches && ctrlMatches && altMatches && shiftMatches && metaMatches) {
          if (shortcut.preventDefault !== false) {
            e.preventDefault();
          }
          shortcut.action();
          break;
        }
      }
    };

    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [shortcuts, enabled]);
}
