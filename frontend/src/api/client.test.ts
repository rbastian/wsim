import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { api, ApiError } from './client'

describe('API Client', () => {
  const mockFetch = vi.fn()
  const originalFetch = global.fetch

  beforeEach(() => {
    global.fetch = mockFetch
  })

  afterEach(() => {
    global.fetch = originalFetch
    mockFetch.mockReset()
  })

  describe('fetchJson helper', () => {
    it('should make successful GET request', async () => {
      const mockData = { status: 'ok' }
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockData,
      })

      const result = await api.health()

      expect(mockFetch).toHaveBeenCalledWith(
        'http://localhost:8000/health',
        expect.objectContaining({
          headers: expect.objectContaining({
            'Content-Type': 'application/json',
          }),
        })
      )
      expect(result).toEqual(mockData)
    })

    it('should handle HTTP error responses', async () => {
      mockFetch.mockResolvedValue({
        ok: false,
        status: 404,
        statusText: 'Not Found',
        json: async () => ({ detail: 'Game not found' }),
      })

      await expect(api.getGame('invalid-id')).rejects.toThrow(ApiError)

      mockFetch.mockResolvedValue({
        ok: false,
        status: 404,
        statusText: 'Not Found',
        json: async () => ({ detail: 'Game not found' }),
      })

      const error = await api.getGame('invalid-id').catch(e => e)
      expect(error.message).toBe('Game not found')
    })

    it('should use statusText when detail is missing', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 500,
        statusText: 'Internal Server Error',
        json: async () => ({}),
      })

      await expect(api.health()).rejects.toThrow('Internal Server Error')
    })

    it('should handle network errors', async () => {
      mockFetch.mockRejectedValue(new Error('Network failure'))

      await expect(api.health()).rejects.toThrow(ApiError)

      mockFetch.mockRejectedValue(new Error('Network failure'))

      const error = await api.health().catch(e => e)
      expect(error.message).toBe('Network error: Network failure')
    })

    it('should handle malformed JSON in error response', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 400,
        statusText: 'Bad Request',
        json: async () => { throw new Error('Invalid JSON') },
      })

      await expect(api.health()).rejects.toThrow('Bad Request')
    })
  })

  describe('health endpoint', () => {
    it('should call health endpoint correctly', async () => {
      const mockData = { status: 'healthy' }
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockData,
      })

      const result = await api.health()

      expect(mockFetch).toHaveBeenCalledWith(
        'http://localhost:8000/health',
        expect.any(Object)
      )
      expect(result).toEqual(mockData)
    })
  })

  describe('scenario endpoints', () => {
    it('should list scenarios', async () => {
      const mockScenarios = [
        { id: 'test1', name: 'Test Scenario 1', description: 'A test scenario' },
        { id: 'test2', name: 'Test Scenario 2', description: 'Another test' },
      ]
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockScenarios,
      })

      const result = await api.listScenarios()

      expect(mockFetch).toHaveBeenCalledWith(
        'http://localhost:8000/games/scenarios',
        expect.any(Object)
      )
      expect(result).toEqual(mockScenarios)
    })
  })

  describe('game management endpoints', () => {
    it('should create game with POST request', async () => {
      const request = { scenario_id: 'test-scenario' }
      const mockResponse = {
        game_id: 'game-123',
        state: { id: 'game-123', turn: 1 },
      }
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      })

      const result = await api.createGame(request)

      expect(mockFetch).toHaveBeenCalledWith(
        'http://localhost:8000/games',
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify(request),
          headers: expect.objectContaining({
            'Content-Type': 'application/json',
          }),
        })
      )
      expect(result).toEqual(mockResponse)
    })

    it('should get game by ID', async () => {
      const gameId = 'game-123'
      const mockGame = { id: gameId, turn: 5 }
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockGame,
      })

      const result = await api.getGame(gameId)

      expect(mockFetch).toHaveBeenCalledWith(
        `http://localhost:8000/games/${gameId}`,
        expect.any(Object)
      )
      expect(result).toEqual(mockGame)
    })
  })

  describe('orders and ready gate endpoints', () => {
    it('should submit orders', async () => {
      const gameId = 'game-123'
      const turn = 1
      const request = {
        side: 'P1' as const,
        orders: [{ ship_id: 'ship-1', movement_string: '3L' }],
      }
      const mockResponse = {
        success: true,
        state: { id: gameId },
      }
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      })

      const result = await api.submitOrders(gameId, turn, request)

      expect(mockFetch).toHaveBeenCalledWith(
        `http://localhost:8000/games/${gameId}/turns/${turn}/orders`,
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify(request),
        })
      )
      expect(result).toEqual(mockResponse)
    })

    it('should mark player ready', async () => {
      const gameId = 'game-123'
      const turn = 1
      const request = { side: 'P1' as const }
      const mockResponse = {
        success: true,
        ready_players: ['P1'],
      }
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      })

      const result = await api.markReady(gameId, turn, request)

      expect(mockFetch).toHaveBeenCalledWith(
        `http://localhost:8000/games/${gameId}/turns/${turn}/ready`,
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify(request),
        })
      )
      expect(result).toEqual(mockResponse)
    })
  })

  describe('phase resolution endpoints', () => {
    it('should resolve movement phase', async () => {
      const gameId = 'game-123'
      const turn = 1
      const mockResponse = {
        success: true,
        events: [],
        state: { id: gameId },
      }
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      })

      const result = await api.resolveMovement(gameId, turn)

      expect(mockFetch).toHaveBeenCalledWith(
        `http://localhost:8000/games/${gameId}/turns/${turn}/resolve/movement`,
        expect.objectContaining({ method: 'POST' })
      )
      expect(result).toEqual(mockResponse)
    })

    it('should resolve combat phase', async () => {
      const gameId = 'game-123'
      const turn = 1
      const mockResponse = {
        success: true,
        events: [],
        state: { id: gameId },
      }
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      })

      const result = await api.resolveCombat(gameId, turn)

      expect(mockFetch).toHaveBeenCalledWith(
        `http://localhost:8000/games/${gameId}/turns/${turn}/resolve/combat`,
        expect.objectContaining({ method: 'POST' })
      )
      expect(result).toEqual(mockResponse)
    })

    it('should resolve reload phase', async () => {
      const gameId = 'game-123'
      const turn = 1
      const mockResponse = {
        success: true,
        events: [],
        state: { id: gameId },
      }
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      })

      const result = await api.resolveReload(gameId, turn)

      expect(mockFetch).toHaveBeenCalledWith(
        `http://localhost:8000/games/${gameId}/turns/${turn}/resolve/reload`,
        expect.objectContaining({ method: 'POST' })
      )
      expect(result).toEqual(mockResponse)
    })

    it('should advance turn', async () => {
      const gameId = 'game-123'
      const turn = 1
      const mockResponse = {
        success: true,
        new_turn: 2,
        state: { id: gameId },
      }
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      })

      const result = await api.advanceTurn(gameId, turn)

      expect(mockFetch).toHaveBeenCalledWith(
        `http://localhost:8000/games/${gameId}/turns/${turn}/advance`,
        expect.objectContaining({ method: 'POST' })
      )
      expect(result).toEqual(mockResponse)
    })
  })

  describe('combat endpoints', () => {
    it('should fire broadside', async () => {
      const gameId = 'game-123'
      const turn = 1
      const request = {
        ship_id: 'ship-1',
        broadside: 'L' as const,
        target_ship_id: 'ship-2',
        aim: 'hull' as const,
      }
      const mockResponse = {
        success: true,
        hits: 3,
        damage: [],
      }
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      })

      const result = await api.fireBroadside(gameId, turn, request)

      expect(mockFetch).toHaveBeenCalledWith(
        `http://localhost:8000/games/${gameId}/turns/${turn}/combat/fire`,
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify(request),
        })
      )
      expect(result).toEqual(mockResponse)
    })

    it('should get broadside arc', async () => {
      const gameId = 'game-123'
      const shipId = 'ship-1'
      const broadside = 'L'
      const mockResponse = {
        arc_hexes: [[1, 2]],
        targets: [],
      }
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      })

      const result = await api.getBroadsideArc(gameId, shipId, broadside)

      expect(mockFetch).toHaveBeenCalledWith(
        `http://localhost:8000/games/${gameId}/ships/${shipId}/broadside/${broadside}/arc`,
        expect.any(Object)
      )
      expect(result).toEqual(mockResponse)
    })
  })

  describe('ApiError', () => {
    it('should create ApiError with all properties', () => {
      const error = new ApiError('Test error', 404, { detail: 'Not found' })

      expect(error.name).toBe('ApiError')
      expect(error.message).toBe('Test error')
      expect(error.status).toBe(404)
      expect(error.data).toEqual({ detail: 'Not found' })
    })

    it('should create ApiError without optional properties', () => {
      const error = new ApiError('Test error')

      expect(error.name).toBe('ApiError')
      expect(error.message).toBe('Test error')
      expect(error.status).toBeUndefined()
      expect(error.data).toBeUndefined()
    })
  })
})
