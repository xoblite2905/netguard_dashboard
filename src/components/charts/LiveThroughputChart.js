// src/components/charts/LiveThroughputChart.js

import React, { useState, useEffect } from 'react';
import { ResponsiveContainer, AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip } from 'recharts';
import { useTheme } from '../../context/ThemeContext';
// --- STEP 1: Import the new config file we created ---
import { API_BASE_URL } from '../../api/config';

const CustomTooltip = ({ active, payload, label, colors }) => {
    if (active && payload && payload.length) {
        const ingressMbps = (payload[0].value * 8 / 1000000).toFixed(2);
        const egressMbps = (payload[1].value * 8 / 1000000).toFixed(2);
        return (
            <div className="p-3 bg-light-card/80 dark:bg-dark-card/80 backdrop-blur-sm border border-light-border dark:border-dark-border rounded-lg shadow-lg">
                <p className="label font-semibold text-sm text-light-text dark:text-dark-text">{`${label}`}</p>
                <p className="intro" style={{ color: colors.in }}>{`Ingress : ${ingressMbps} Mbps`}</p>
                <p className="intro" style={{ color: colors.out }}>{`Egress : ${egressMbps} Mbps`}</p>
            </div>
        );
    }
    return null;
};

const LiveThroughputChart = () => {
    const { theme, chartColors } = useTheme();
    const [liveData, setLiveData] = useState([]);
    const [inColor, outColor] = chartColors.liveThroughput;

    useEffect(() => {
        const fetchData = async () => {
            try {
                // --- STEP 2: THIS IS THE CRITICAL CHANGE ---
                // We use the full URL from the config file. This guarantees it points to the correct IP.
                const response = await fetch(`${API_BASE_URL}/api/v1/cockpit/bandwidth`);

                if (!response.ok) { throw new Error(`Network response was not ok: ${response.statusText}`); }
                const data = await response.json();
                const formattedData = data.map(point => ({
                    time: new Date(point.time * 1000).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }),
                    'in': point.in, 'out': point.out,
                }));
                setLiveData(formattedData);
            } catch (error) {
                console.error("Failed to fetch throughput data:", error);
            }
        };
        fetchData();
        const intervalId = setInterval(fetchData, 3000);
        return () => clearInterval(intervalId);
    }, []);

    const formatYAxis = (tickItem) => { return (tickItem * 8 / 1000000).toFixed(1); };

    return (
        <div className="h-full w-full flex flex-col">
            <h3 className="text-lg font-semibold text-light-text dark:text-dark-text mb-1">Live Network Throughput</h3>
            <div className="w-full flex-grow pt-4">
                <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={liveData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                        <defs>
                            <linearGradient id={`colorIn-${theme}`} x1="0" y1="0" x2="0" y2="1"><stop offset="5%" stopColor={inColor} stopOpacity={0.8}/><stop offset="95%" stopColor={inColor} stopOpacity={0}/></linearGradient>
                            <linearGradient id={`colorOut-${theme}`} x1="0" y1="0" x2="0" y2="1"><stop offset="5%" stopColor={outColor} stopOpacity={0.8}/><stop offset="95%" stopColor={outColor} stopOpacity={0}/></linearGradient>
                        </defs>
                        <XAxis dataKey="time" stroke={chartColors.textColor} tick={{ fontSize: 12 }} axisLine={false} tickLine={false} />
                        <YAxis stroke={chartColors.textColor} tick={{ fontSize: 12 }} axisLine={false} tickLine={false} unit=" Mbps" tickFormatter={formatYAxis} />
                        <CartesianGrid strokeDasharray="1 5" stroke={chartColors.gridColor} />
                        <Tooltip content={<CustomTooltip colors={{ in: inColor, out: outColor }} />} />
                        <Area type="monotone" dataKey="in" stroke={inColor} strokeWidth={2} fillOpacity={1} fill={`url(#colorIn-${theme})`} />
                        <Area type="monotone" dataKey="out" stroke={outColor} strokeWidth={2} fillOpacity={1} fill={`url(#colorOut-${theme})`} />
                    </AreaChart>
                </ResponsiveContainer>
            </div>
        </div>
    );
};
export default LiveThroughputChart;