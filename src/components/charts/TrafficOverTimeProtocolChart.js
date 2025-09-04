// src/components/charts/TrafficOverTimeProtocolChart.js

import React from 'react';
import Chart from 'react-apexcharts';
import { useTheme } from '../../context/ThemeContext';
import { useData } from '../../context/DataContext';

const TrafficOverTimeProtocolChart = () => {
    const { isDarkMode, chartColors } = useTheme();
    
    // --- THIS IS THE FIX ---
    // We are now using the live 'protocolDistribution' data from your DataContext.
    const { protocolDistribution } = useData();

    // This logic processes the live data to fit the chart's expected format.
    const totalCount = protocolDistribution.reduce((acc, item) => acc + item.count, 0);
    const series = totalCount > 0 ? protocolDistribution.map(item => Math.round((item.count / totalCount) * 100)) : [];
    const labels = protocolDistribution.map(item => item.protocol.toUpperCase());

    const options = {
        chart: { type: 'radialBar' },
        plotOptions: {
            radialBar: {
                offsetY: -15,
                hollow: { margin: 5, size: '60%', background: 'transparent' },
                track: { background: isDarkMode ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.1)' },
                dataLabels: {
                    name: { show: false },
                    value: { show: false },
                },
            },
        },
        labels: labels,
        colors: chartColors.protocolDistribution,
        legend: {
            show: true,
            position: 'bottom',
            fontFamily: 'inherit',
            fontSize: '12px',
            labels: { colors: chartColors.textColor },
            markers: { width: 8, height: 8, radius: 4 },
            itemMargin: { horizontal: 8, vertical: 2 },
        },
        stroke: { lineCap: 'round' },
        tooltip: {
            enabled: true,
            theme: isDarkMode ? 'dark' : 'light',
            y: { formatter: (val) => `${val}% of traffic` }
        }
    };

    return (
        <div className="h-full flex flex-col justify-start">
            <h3 className="text-md font-semibold text-center text-gray-800 dark:text-gray-200 mb-2">
                Traffic by Protocol
            </h3>
            {/* This part shows a "waiting" message until the data arrives from the API */}
            {series.length > 0 ? (
                <div className="flex-grow">
                     <Chart options={options} series={series} type="radialBar" height="100%" />
                </div>
            ) : (
                <div className="flex-grow flex items-center justify-center">
                    <p className="text-gray-500 text-sm">Waiting for protocol data...</p>
                </div>
            )}
        </div>
    );
};

export default TrafficOverTimeProtocolChart;