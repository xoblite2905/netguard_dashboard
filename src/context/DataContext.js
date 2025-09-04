// src/context/DataContext.js (FINAL CORRECTED VERSION)

import React, { createContext, useContext, useState, useEffect, useMemo } from 'react';
import { useWebSocket } from '../hooks/useWebSocket';
import { API_BASE_URL } from '../api/config';

const DataContext = createContext(null);
const MAX_PACKETS_IN_LIST = 100;
const POLLING_INTERVAL = 15000;

export const useData = () => {
    return useContext(DataContext);
};

export const DataProvider = ({ children }) => {
    const { lastJsonMessage, isConnected } = useWebSocket();
    const [packets, setPackets] = useState([]);
    const [hosts, setHosts] = useState([]);
    const [alerts, setAlerts] = useState([]);
    const [threatOrigins, setThreatOrigins] = useState([]);
    const [connections, setConnections] = useState([]);
    const [protocolDistribution, setProtocolDistribution] = useState([]);
    const [securityPosture, setSecurityPosture] = useState({ health_score: 100 });

    const fetchAndSet = async (endpoint, setter, name) => {
        try {
            const res = await fetch(`${API_BASE_URL}${endpoint}`);
            if (!res.ok) throw new Error(`${name} fetch failed with status: ${res.status}`);
            const data = await res.json();
            setter(data);
            console.log(`[Frontend DEBUG] Fetched ${name}:`, data);
        } catch (error) {
            console.warn(`Could not load data for ${name}. This is recoverable. Error: ${error.message}`);
        }
    };

    useEffect(() => {
        const pollData = () => {
            // --- ROUTING FIX: Using the CORRECT API paths defined in main.py ---
            fetchAndSet("/api/hosts/", setHosts, "Hosts");
            fetchAndSet("/api/security/alerts", setAlerts, "Alerts");
            fetchAndSet("/api/threat-intel/origins", setThreatOrigins, "Threats");
            fetchAndSet("/api/zeek/connections", setConnections, "Connections");
            fetchAndSet("/api/zeek/protocol-distribution", setProtocolDistribution, "Zeek Protocol Distribution");
            
            // --- These routes have the '/v1/cockpit' prefix ---
            fetchAndSet("/api/v1/cockpit/security-posture", setSecurityPosture, "Security Posture");
        }

        pollData(); // Initial fetch
        const interval = setInterval(pollData, POLLING_INTERVAL);
        return () => clearInterval(interval);
    }, []);

    // Other useEffects remain the same...
    useEffect(() => { fetchAndSet("/api/packets?limit=50", setPackets, "Packets"); }, []);
    useEffect(() => {
        if (lastJsonMessage && lastJsonMessage.type === 'packet_data') {
            const newPacket = lastJsonMessage.data;
            setPackets(p => [newPacket, ...p].slice(0, MAX_PACKETS_IN_LIST));
        }
    }, [lastJsonMessage]);

    // Derived data memos remain the same...
    const derivedVulnerabilities = useMemo(() => hosts.flatMap(host => host.vulnerabilities || []), [hosts]);
    const protocolTrafficTimeline = useMemo(() => {
        if (!connections || connections.length === 0) return [];
        const BUCKET_INTERVAL_MS = 15 * 1000;
        const validConnections = connections.filter(conn => conn && typeof conn.ts === 'string' && conn.ts.length > 0);
        const buckets = validConnections.reduce((acc, conn) => {
            const timestamp = new Date(conn.ts).getTime(); if (isNaN(timestamp)) return acc;
            const bucketStart = Math.floor(timestamp / BUCKET_INTERVAL_MS) * BUCKET_INTERVAL_MS;
            if (!acc[bucketStart]) acc[bucketStart] = { time: bucketStart };
            const protocol = (conn.proto || 'unknown').toUpperCase();
            const totalBytes = (conn.orig_bytes || 0) + (conn.resp_bytes || 0);
            acc[bucketStart][protocol] = (acc[bucketStart][protocol] || 0) + totalBytes;
            return acc;
        }, {});
        const allBuckets = Object.values(buckets).filter(bucket => !isNaN(bucket.time));
        return allBuckets.sort((a, b) => a.time - b.time);
    }, [connections]);
    
    const value = {
        packets, hosts, vulnerabilities: derivedVulnerabilities, alerts,
        threatOrigins, protocolTrafficTimeline, isConnected, protocolDistribution,
        securityPosture // Expose posture to the app
    };

    return <DataContext.Provider value={value}>{children}</DataContext.Provider>;
};