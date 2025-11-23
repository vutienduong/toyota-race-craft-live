"use client";

import { useState, useEffect, useRef, useCallback } from "react";

interface WebSocketMessage {
  type: string;
  [key: string]: any;
}

interface UseWebSocketOptions {
  onMessage?: (data: WebSocketMessage) => void;
  onError?: (error: Event) => void;
  onOpen?: () => void;
  onClose?: () => void;
  reconnect?: boolean;
  reconnectInterval?: number;
}

export function useWebSocket(url: string, options: UseWebSocketOptions = {}) {
  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null);
  const ws = useRef<WebSocket | null>(null);
  const reconnectTimeout = useRef<NodeJS.Timeout | null>(null);

  const {
    onMessage,
    onError,
    onOpen,
    onClose,
    reconnect = true,
    reconnectInterval = 3000,
  } = options;

  const connect = useCallback(() => {
    try {
      // Create WebSocket connection
      ws.current = new WebSocket(url);

      ws.current.onopen = () => {
        console.log("WebSocket connected:", url);
        setIsConnected(true);
        onOpen?.();
      };

      ws.current.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data) as WebSocketMessage;
          setLastMessage(data);
          onMessage?.(data);
        } catch (error) {
          console.error("Failed to parse WebSocket message:", error);
        }
      };

      ws.current.onerror = (error) => {
        console.error("WebSocket error:", error);
        onError?.(error);
      };

      ws.current.onclose = () => {
        console.log("WebSocket disconnected");
        setIsConnected(false);
        onClose?.();

        // Attempt reconnection
        if (reconnect) {
          reconnectTimeout.current = setTimeout(() => {
            console.log("Attempting to reconnect...");
            connect();
          }, reconnectInterval);
        }
      };
    } catch (error) {
      console.error("Failed to create WebSocket:", error);
    }
  }, [url, onMessage, onError, onOpen, onClose, reconnect, reconnectInterval]);

  const disconnect = useCallback(() => {
    if (reconnectTimeout.current) {
      clearTimeout(reconnectTimeout.current);
    }
    if (ws.current) {
      ws.current.close();
      ws.current = null;
    }
    setIsConnected(false);
  }, []);

  const sendMessage = useCallback((message: any) => {
    if (ws.current && ws.current.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify(message));
    } else {
      console.warn("WebSocket is not connected");
    }
  }, []);

  useEffect(() => {
    connect();

    return () => {
      disconnect();
    };
  }, [connect, disconnect]);

  return {
    isConnected,
    lastMessage,
    sendMessage,
    disconnect,
  };
}

interface RaceUpdate {
  type: string;
  vehicle_id: string;
  race_id: string;
  current_lap: number;
  total_laps: number;
  pace: {
    current: number;
    average: number;
    best: number;
    trend: string;
  };
  degradation: {
    rate: number;
    health: string;
    action: string;
  };
  threat: {
    level: string;
    probability: number;
    laps_until: number;
    recommendations: string[];
  };
  pit_window: {
    optimal_lap: number;
    window_start: number;
    window_end: number;
    confidence: number;
  };
}

export function useRaceWebSocket(
  vehicleId: string,
  raceId: string = "R1",
  enabled: boolean = true
) {
  const [raceData, setRaceData] = useState<RaceUpdate | null>(null);
  const [connectionStatus, setConnectionStatus] = useState<"connecting" | "connected" | "disconnected">("disconnected");

  // Construct WebSocket URL (assuming backend is on localhost:8000)
  const wsUrl = `ws://localhost:8000/ws/race/${raceId}/${vehicleId}`;

  const { isConnected, lastMessage, sendMessage } = useWebSocket(wsUrl, {
    onMessage: (data) => {
      if (data.type === "race_update") {
        setRaceData(data as RaceUpdate);
      }
    },
    onOpen: () => {
      setConnectionStatus("connected");
    },
    onClose: () => {
      setConnectionStatus("disconnected");
    },
    reconnect: enabled,
  });

  useEffect(() => {
    if (isConnected) {
      setConnectionStatus("connected");
    } else {
      setConnectionStatus("connecting");
    }
  }, [isConnected]);

  const updateLap = useCallback(
    (lap: number) => {
      sendMessage({
        type: "lap_update",
        lap,
      });
    },
    [sendMessage]
  );

  return {
    raceData,
    isConnected,
    connectionStatus,
    updateLap,
  };
}
