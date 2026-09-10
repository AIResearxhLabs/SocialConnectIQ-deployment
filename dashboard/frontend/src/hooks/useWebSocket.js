/**
 * useWebSocket — connects to /ws/live and returns the latest live payload.
 *
 * Automatically reconnects with exponential back-off on disconnect.
 */

import { useEffect, useRef, useState } from 'react';

const WS_URL = import.meta.env.VITE_WS_URL ||
    `${window.location.protocol === 'https:' ? 'wss' : 'ws'}://${window.location.host}/ws/live`;

const MAX_RECONNECT_DELAY_MS = 30000;

/**
 * @returns {{ liveData: object|null, wsStatus: 'connecting'|'open'|'closed'|'error' }}
 */
export function useWebSocket() {
    const [liveData, setLiveData] = useState(null);
    const [wsStatus, setWsStatus] = useState('connecting');
    const wsRef = useRef(null);
    const retryDelay = useRef(1000);
    const mountedRef = useRef(true);

    useEffect(() => {
        mountedRef.current = true;
        connectWs();
        return () => {
            mountedRef.current = false;
            if (wsRef.current) wsRef.current.close();
        };
    }, []);

    function connectWs() {
        if (!mountedRef.current) return;
        setWsStatus('connecting');
        const ws = new WebSocket(WS_URL);
        wsRef.current = ws;

        ws.onopen = () => {
            if (!mountedRef.current) return;
            setWsStatus('open');
            retryDelay.current = 1000;
        };

        ws.onmessage = (event) => {
            if (!mountedRef.current) return;
            try {
                const data = JSON.parse(event.data);
                setLiveData(data);
            } catch {
                /* ignore malformed messages */
            }
        };

        ws.onclose = () => {
            if (!mountedRef.current) return;
            setWsStatus('closed');
            const delay = Math.min(retryDelay.current, MAX_RECONNECT_DELAY_MS);
            retryDelay.current = delay * 2;
            setTimeout(connectWs, delay);
        };

        ws.onerror = () => {
            if (!mountedRef.current) return;
            setWsStatus('error');
        };
    }

    return { liveData, wsStatus };
}
