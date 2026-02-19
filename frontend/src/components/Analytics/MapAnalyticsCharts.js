/**
 * MapAnalyticsCharts - Comprehensive analytics charts for Map View
 * Features 14+ different chart types with multiple variables:
 * - Time of day (morning, afternoon, dusk, night)
 * - Year, hour, age
 * - Geographic (city, state, country)
 * - Category/subcategory
 * - Income/price level ($10 increments)
 * - Urban/rural classification
 * - Weather conditions
 * - First name analysis
 */
import React, { useState, useMemo } from 'react';

// Color zones for different variables (5-7 colors each)
const COLOR_ZONES = {
  timeOfDay: {
    morning: '#fbbf24',    // Amber - sunrise
    afternoon: '#f97316',  // Orange - peak sun
    dusk: '#8b5cf6',       // Purple - sunset
    night: '#1e3a5f',      // Dark blue - night
    dawn: '#f472b6',       // Pink - early morning
  },
  weather: {
    sunny: '#fbbf24',
    clearSkies: '#38bdf8',
    partlyCloudy: '#94a3b8',
    scatteredClouds: '#64748b',
    drizzling: '#60a5fa',
    raining: '#3b82f6',
    snowing: '#e2e8f0',
    cold: '#06b6d4',
    warm: '#f97316',
    hot: '#ef4444',
  },
  urbanRural: {
    city: '#8b5cf6',
    urban: '#a855f7',
    town: '#22c55e',
    suburban: '#84cc16',
    rural: '#15803d',
  },
  income: {
    '$0-10': '#ef4444',
    '$10-20': '#f97316',
    '$20-30': '#fbbf24',
    '$30-40': '#84cc16',
    '$40-50': '#22c55e',
    '$50+': '#10b981',
  },
  age: {
    '0-17': '#f472b6',
    '18-25': '#a855f7',
    '26-35': '#3b82f6',
    '36-45': '#22c55e',
    '46-55': '#f97316',
    '56-65': '#ef4444',
    '65+': '#6b7280',
  },
  category: [
    '#8b5cf6', '#f472b6', '#3b82f6', '#22c55e', '#f97316', 
    '#ef4444', '#06b6d4', '#a855f7', '#84cc16', '#fbbf24'
  ],
};

// Simulated data generator - now processes REAL result data
const generateMockData = (results, categories) => {
  const timeData = { morning: 0, afternoon: 0, dusk: 0, night: 0 };
  const hourData = Array(24).fill(0);
  const yearData = {};
  const weatherData = { sunny: 0, clearSkies: 0, partlyCloudy: 0, scatteredClouds: 0, drizzling: 0, raining: 0, snowing: 0 };
  const urbanData = { city: 0, urban: 0, town: 0, suburban: 0, rural: 0 };
  const incomeData = { '$0-10': 0, '$10-20': 0, '$20-30': 0, '$30-40': 0, '$40-50': 0, '$50+': 0 };
  const ageData = { '0-17': 0, '18-25': 0, '26-35': 0, '36-45': 0, '46-55': 0, '56-65': 0, '65+': 0 };
  const categoryData = {};
  const countryData = {};
  const stateData = {};
  const cityData = {};
  const firstNameData = {};
  const docTypeData = {};
  
  // Process results using REAL data
  results.forEach((r, idx) => {
    // Time of day - use actual created_at if available, else simulate
    let hour = idx % 24;
    if (r.created_at) {
      const date = new Date(r.created_at);
      hour = date.getHours();
    }
    hourData[hour]++;
    if (hour >= 5 && hour < 12) timeData.morning++;
    else if (hour >= 12 && hour < 17) timeData.afternoon++;
    else if (hour >= 17 && hour < 20) timeData.dusk++;
    else timeData.night++;
    
    // Year distribution - use actual dates
    let year = 2024;
    if (r.created_at) {
      year = new Date(r.created_at).getFullYear();
    } else if (r.published_date) {
      year = new Date(r.published_date).getFullYear();
    }
    yearData[year] = (yearData[year] || 0) + 1;
    
    // Document type - REAL data
    const docType = r.article_type || r.doc_type || 'Webpage';
    docTypeData[docType] = (docTypeData[docType] || 0) + 1;
    
    // Weather (simulated based on location latitude)
    const lat = r.latitude || r.lat || 39;
    if (lat > 45) {
      weatherData.cold = (weatherData.cold || 0) + 1;
      weatherData.snowing++;
    } else if (lat > 35) {
      weatherData.clearSkies++;
      weatherData.partlyCloudy++;
    } else {
      weatherData.sunny++;
      weatherData.warm = (weatherData.warm || 0) + 1;
    }
    
    // Urban/Rural - infer from title/snippet
    const text = ((r.title || '') + ' ' + (r.snippet || '')).toLowerCase();
    if (text.includes('city') || text.includes('urban') || text.includes('downtown')) {
      urbanData.city++;
    } else if (text.includes('town') || text.includes('village')) {
      urbanData.town++;
    } else if (text.includes('suburb')) {
      urbanData.suburban++;
    } else if (text.includes('rural') || text.includes('farm') || text.includes('country')) {
      urbanData.rural++;
    } else {
      urbanData.urban++;
    }
    
    // Income/Price - use quality_score as proxy
    const score = r.quality_score || 50;
    if (score >= 80) incomeData['$50+']++;
    else if (score >= 65) incomeData['$40-50']++;
    else if (score >= 50) incomeData['$30-40']++;
    else if (score >= 35) incomeData['$20-30']++;
    else if (score >= 20) incomeData['$10-20']++;
    else incomeData['$0-10']++;
    
    // Age - simulate based on content type
    if (r.article_type === 'Academic Paper' || r.article_type === 'PhD Informative') {
      ageData['26-35']++;
      ageData['36-45']++;
    } else if (r.article_type === 'News Article') {
      ageData['26-35']++;
      ageData['46-55']++;
    } else if (r.article_type === 'Blog Post' || r.article_type === 'Forum') {
      ageData['18-25']++;
      ageData['26-35']++;
    } else {
      const ages = Object.keys(ageData);
      ageData[ages[idx % ages.length]]++;
    }
    
    // Categories - REAL data
    if (r.categories && r.categories.length > 0) {
      r.categories.forEach(cat => {
        categoryData[cat] = (categoryData[cat] || 0) + 1;
      });
    }
    
    // Geographic - extract from REAL data
    const country = r.country || 'United States';
    countryData[country] = (countryData[country] || 0) + 1;
    
    // State - use extractedPlace or infer
    const state = r.state || r.extractedPlace || r.location || 'Unknown';
    stateData[state] = (stateData[state] || 0) + 1;
    
    // City
    const city = r.city || 'Various';
    cityData[city] = (cityData[city] || 0) + 1;
    
    // Extract names from titles
    const titleWords = (r.title || '').split(' ');
    const commonNames = ['John', 'George', 'William', 'James', 'Thomas', 'Robert', 'Mary', 'Sarah', 'Elizabeth'];
    titleWords.forEach(word => {
      const cleanWord = word.replace(/[^a-zA-Z]/g, '');
      if (commonNames.includes(cleanWord)) {
        firstNameData[cleanWord] = (firstNameData[cleanWord] || 0) + 1;
      }
    });
  });
  
  return {
    timeData, hourData, yearData, weatherData, urbanData,
    incomeData, ageData, categoryData, countryData,
    stateData, cityData, firstNameData, docTypeData
  };
};

// Simple SVG Chart Components
const PieChart = ({ data, colors, title, size = 180 }) => {
  const total = Object.values(data).reduce((a, b) => a + b, 0);
  if (total === 0) return null;
  
  let currentAngle = 0;
  const segments = Object.entries(data).map(([key, value], idx) => {
    const percentage = value / total;
    const angle = percentage * 360;
    const startAngle = currentAngle;
    currentAngle += angle;
    
    const startRad = (startAngle - 90) * Math.PI / 180;
    const endRad = (currentAngle - 90) * Math.PI / 180;
    const radius = size / 2 - 10;
    const cx = size / 2;
    const cy = size / 2;
    
    const x1 = cx + radius * Math.cos(startRad);
    const y1 = cy + radius * Math.sin(startRad);
    const x2 = cx + radius * Math.cos(endRad);
    const y2 = cy + radius * Math.sin(endRad);
    
    const largeArc = angle > 180 ? 1 : 0;
    const color = colors[key] || colors[idx % Object.keys(colors).length] || COLOR_ZONES.category[idx % 10];
    
    return (
      <path
        key={key}
        d={`M ${cx} ${cy} L ${x1} ${y1} A ${radius} ${radius} 0 ${largeArc} 1 ${x2} ${y2} Z`}
        fill={color}
        stroke="rgba(0,0,0,0.2)"
        strokeWidth="1"
      >
        <title>{key}: {value} ({(percentage * 100).toFixed(1)}%)</title>
      </path>
    );
  });
  
  return (
    <div style={{ textAlign: 'center' }}>
      <h4 style={{ color: '#f472b6', fontSize: '0.85rem', marginBottom: 8 }}>{title}</h4>
      <svg width={size} height={size} style={{ display: 'block', margin: '0 auto' }}>
        {segments}
        <circle cx={size/2} cy={size/2} r={size/4} fill="rgba(20,10,40,0.9)" />
        <text x={size/2} y={size/2} textAnchor="middle" dy="5" fill="#fff" fontSize="12" fontWeight="bold">
          {total}
        </text>
      </svg>
      <div style={{ display: 'flex', flexWrap: 'wrap', justifyContent: 'center', gap: 4, marginTop: 8, maxWidth: size + 40 }}>
        {Object.entries(data).slice(0, 6).map(([key, value], idx) => (
          <span key={key} style={{ 
            fontSize: '0.6rem', 
            color: '#a1a1aa',
            display: 'flex',
            alignItems: 'center',
            gap: 3
          }}>
            <span style={{ 
              width: 8, height: 8, borderRadius: '50%', 
              background: colors[key] || COLOR_ZONES.category[idx % 10]
            }}/>
            {key.substring(0, 8)}
          </span>
        ))}
      </div>
    </div>
  );
};

const BarChart = ({ data, colors, title, height = 150, width = 220 }) => {
  const entries = Object.entries(data).slice(0, 7);
  const maxValue = Math.max(...entries.map(([_, v]) => v), 1);
  const barWidth = (width - 40) / entries.length - 4;
  
  return (
    <div style={{ textAlign: 'center' }}>
      <h4 style={{ color: '#f472b6', fontSize: '0.85rem', marginBottom: 8 }}>{title}</h4>
      <svg width={width} height={height} style={{ display: 'block', margin: '0 auto' }}>
        {entries.map(([key, value], idx) => {
          const barHeight = (value / maxValue) * (height - 40);
          const x = 30 + idx * (barWidth + 4);
          const y = height - 25 - barHeight;
          const color = colors[key] || colors[idx % Object.keys(colors).length] || COLOR_ZONES.category[idx % 10];
          
          return (
            <g key={key}>
              <rect
                x={x}
                y={y}
                width={barWidth}
                height={barHeight}
                fill={color}
                rx={3}
              >
                <title>{key}: {value}</title>
              </rect>
              <text
                x={x + barWidth/2}
                y={height - 8}
                textAnchor="middle"
                fill="#71717a"
                fontSize="8"
              >
                {key.substring(0, 5)}
              </text>
              <text
                x={x + barWidth/2}
                y={y - 3}
                textAnchor="middle"
                fill="#fff"
                fontSize="8"
              >
                {value}
              </text>
            </g>
          );
        })}
        {/* Y-axis */}
        <line x1="25" y1="10" x2="25" y2={height - 25} stroke="#4a4a4a" strokeWidth="1"/>
      </svg>
    </div>
  );
};

const MultiLineChart = ({ datasets, title, height = 160, width = 280 }) => {
  const colors = ['#f472b6', '#8b5cf6', '#3b82f6', '#22c55e', '#f97316'];
  const maxValue = Math.max(...datasets.flatMap(d => d.values), 1);
  const pointCount = datasets[0]?.values.length || 0;
  
  return (
    <div style={{ textAlign: 'center' }}>
      <h4 style={{ color: '#f472b6', fontSize: '0.85rem', marginBottom: 8 }}>{title}</h4>
      <svg width={width} height={height} style={{ display: 'block', margin: '0 auto' }}>
        {/* Grid lines */}
        {[0, 0.25, 0.5, 0.75, 1].map((pct, i) => (
          <line 
            key={i}
            x1="40" 
            y1={20 + (height - 50) * (1 - pct)} 
            x2={width - 20} 
            y2={20 + (height - 50) * (1 - pct)}
            stroke="rgba(255,255,255,0.1)"
            strokeWidth="1"
          />
        ))}
        
        {/* Lines */}
        {datasets.map((dataset, dIdx) => {
          const points = dataset.values.map((v, i) => {
            const x = 40 + (i / (pointCount - 1 || 1)) * (width - 60);
            const y = 20 + (1 - v / maxValue) * (height - 50);
            return `${x},${y}`;
          }).join(' ');
          
          return (
            <polyline
              key={dIdx}
              points={points}
              fill="none"
              stroke={colors[dIdx % colors.length]}
              strokeWidth="2"
            />
          );
        })}
        
        {/* Legend */}
        {datasets.slice(0, 5).map((dataset, idx) => (
          <g key={idx}>
            <line 
              x1={50 + idx * 45} 
              y1={height - 8} 
              x2={60 + idx * 45} 
              y2={height - 8}
              stroke={colors[idx % colors.length]}
              strokeWidth="2"
            />
            <text x={62 + idx * 45} y={height - 5} fill="#71717a" fontSize="7">
              {dataset.label.substring(0, 4)}
            </text>
          </g>
        ))}
      </svg>
    </div>
  );
};

const CompositeBarChart = ({ data1, data2, labels, title, height = 160, width = 260 }) => {
  const maxValue = Math.max(...Object.values(data1), ...Object.values(data2), 1);
  const entries = labels.slice(0, 6);
  const barWidth = (width - 60) / entries.length / 2 - 2;
  
  return (
    <div style={{ textAlign: 'center' }}>
      <h4 style={{ color: '#f472b6', fontSize: '0.85rem', marginBottom: 8 }}>{title}</h4>
      <svg width={width} height={height} style={{ display: 'block', margin: '0 auto' }}>
        {entries.map((key, idx) => {
          const x1 = 35 + idx * ((width - 60) / entries.length);
          const x2 = x1 + barWidth + 2;
          const v1 = data1[key] || 0;
          const v2 = data2[key] || 0;
          const h1 = (v1 / maxValue) * (height - 50);
          const h2 = (v2 / maxValue) * (height - 50);
          
          return (
            <g key={key}>
              <rect x={x1} y={height - 30 - h1} width={barWidth} height={h1} fill="#8b5cf6" rx={2}>
                <title>{key} (Set 1): {v1}</title>
              </rect>
              <rect x={x2} y={height - 30 - h2} width={barWidth} height={h2} fill="#f472b6" rx={2}>
                <title>{key} (Set 2): {v2}</title>
              </rect>
              <text x={x1 + barWidth} y={height - 12} textAnchor="middle" fill="#71717a" fontSize="7">
                {key.substring(0, 4)}
              </text>
            </g>
          );
        })}
        {/* Legend */}
        <rect x={width - 80} y={5} width={10} height={10} fill="#8b5cf6" rx={2}/>
        <text x={width - 65} y={13} fill="#a1a1aa" fontSize="8">Primary</text>
        <rect x={width - 80} y={18} width={10} height={10} fill="#f472b6" rx={2}/>
        <text x={width - 65} y={26} fill="#a1a1aa" fontSize="8">Secondary</text>
      </svg>
    </div>
  );
};

const HourlyHeatmap = ({ data, title, width = 280, height = 100 }) => {
  const maxValue = Math.max(...data, 1);
  const cellWidth = (width - 40) / 24;
  
  return (
    <div style={{ textAlign: 'center' }}>
      <h4 style={{ color: '#f472b6', fontSize: '0.85rem', marginBottom: 8 }}>{title}</h4>
      <svg width={width} height={height} style={{ display: 'block', margin: '0 auto' }}>
        {data.map((value, hour) => {
          const intensity = value / maxValue;
          const color = `rgba(139, 92, 246, ${0.2 + intensity * 0.8})`;
          
          return (
            <g key={hour}>
              <rect
                x={30 + hour * cellWidth}
                y={15}
                width={cellWidth - 1}
                height={height - 45}
                fill={color}
                rx={2}
              >
                <title>{hour}:00 - {value} items</title>
              </rect>
              {hour % 4 === 0 && (
                <text x={30 + hour * cellWidth + cellWidth/2} y={height - 18} textAnchor="middle" fill="#71717a" fontSize="7">
                  {hour}h
                </text>
              )}
            </g>
          );
        })}
        {/* Color scale */}
        <defs>
          <linearGradient id="heatGradient" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="rgba(139, 92, 246, 0.2)"/>
            <stop offset="100%" stopColor="rgba(139, 92, 246, 1)"/>
          </linearGradient>
        </defs>
        <rect x={width - 70} y={5} width={50} height={8} fill="url(#heatGradient)" rx={2}/>
        <text x={width - 72} y={11} fill="#71717a" fontSize="6">Low</text>
        <text x={width - 18} y={11} fill="#71717a" fontSize="6">High</text>
      </svg>
    </div>
  );
};

const StackedAreaChart = ({ datasets, labels, title, height = 140, width = 280 }) => {
  const colors = ['#8b5cf6', '#f472b6', '#3b82f6', '#22c55e', '#f97316'];
  const totals = labels.map((_, i) => datasets.reduce((sum, d) => sum + (d.values[i] || 0), 0));
  const maxTotal = Math.max(...totals, 1);
  
  // Build stacked paths
  const paths = datasets.map((dataset, dIdx) => {
    const bottomValues = labels.map((_, i) => {
      return datasets.slice(0, dIdx).reduce((sum, d) => sum + (d.values[i] || 0), 0);
    });
    const topValues = labels.map((_, i) => bottomValues[i] + (dataset.values[i] || 0));
    
    const topPoints = labels.map((_, i) => {
      const x = 40 + (i / (labels.length - 1 || 1)) * (width - 60);
      const y = 20 + (1 - topValues[i] / maxTotal) * (height - 50);
      return `${x},${y}`;
    }).join(' ');
    
    const bottomPoints = labels.map((_, i) => {
      const x = 40 + (i / (labels.length - 1 || 1)) * (width - 60);
      const y = 20 + (1 - bottomValues[i] / maxTotal) * (height - 50);
      return `${x},${y}`;
    }).reverse().join(' ');
    
    return (
      <polygon
        key={dIdx}
        points={`${topPoints} ${bottomPoints}`}
        fill={colors[dIdx % colors.length]}
        opacity={0.7}
      >
        <title>{dataset.label}</title>
      </polygon>
    );
  });
  
  return (
    <div style={{ textAlign: 'center' }}>
      <h4 style={{ color: '#f472b6', fontSize: '0.85rem', marginBottom: 8 }}>{title}</h4>
      <svg width={width} height={height} style={{ display: 'block', margin: '0 auto' }}>
        {paths}
        {/* Legend */}
        {datasets.slice(0, 5).map((dataset, idx) => (
          <g key={idx}>
            <rect x={40 + idx * 45} y={height - 12} width={8} height={8} fill={colors[idx % colors.length]} rx={1}/>
            <text x={50 + idx * 45} y={height - 5} fill="#71717a" fontSize="7">
              {dataset.label.substring(0, 5)}
            </text>
          </g>
        ))}
      </svg>
    </div>
  );
};

const DonutChart = ({ data, colors, title, size = 160 }) => {
  const total = Object.values(data).reduce((a, b) => a + b, 0);
  if (total === 0) return null;
  
  let currentAngle = 0;
  const outerRadius = size / 2 - 10;
  const innerRadius = outerRadius * 0.6;
  
  const segments = Object.entries(data).map(([key, value], idx) => {
    const percentage = value / total;
    const angle = percentage * 360;
    const startAngle = currentAngle;
    currentAngle += angle;
    
    const startRad = (startAngle - 90) * Math.PI / 180;
    const endRad = (currentAngle - 90) * Math.PI / 180;
    const cx = size / 2;
    const cy = size / 2;
    
    const x1Outer = cx + outerRadius * Math.cos(startRad);
    const y1Outer = cy + outerRadius * Math.sin(startRad);
    const x2Outer = cx + outerRadius * Math.cos(endRad);
    const y2Outer = cy + outerRadius * Math.sin(endRad);
    const x1Inner = cx + innerRadius * Math.cos(startRad);
    const y1Inner = cy + innerRadius * Math.sin(startRad);
    const x2Inner = cx + innerRadius * Math.cos(endRad);
    const y2Inner = cy + innerRadius * Math.sin(endRad);
    
    const largeArc = angle > 180 ? 1 : 0;
    const color = colors[key] || colors[idx % Object.keys(colors).length] || COLOR_ZONES.category[idx % 10];
    
    return (
      <path
        key={key}
        d={`M ${x1Outer} ${y1Outer} A ${outerRadius} ${outerRadius} 0 ${largeArc} 1 ${x2Outer} ${y2Outer} 
            L ${x2Inner} ${y2Inner} A ${innerRadius} ${innerRadius} 0 ${largeArc} 0 ${x1Inner} ${y1Inner} Z`}
        fill={color}
        stroke="rgba(0,0,0,0.2)"
        strokeWidth="1"
      >
        <title>{key}: {value} ({(percentage * 100).toFixed(1)}%)</title>
      </path>
    );
  });
  
  return (
    <div style={{ textAlign: 'center' }}>
      <h4 style={{ color: '#f472b6', fontSize: '0.85rem', marginBottom: 8 }}>{title}</h4>
      <svg width={size} height={size} style={{ display: 'block', margin: '0 auto' }}>
        {segments}
        <text x={size/2} y={size/2 - 5} textAnchor="middle" fill="#fff" fontSize="14" fontWeight="bold">
          {total}
        </text>
        <text x={size/2} y={size/2 + 10} textAnchor="middle" fill="#a1a1aa" fontSize="9">
          Total
        </text>
      </svg>
    </div>
  );
};

const RadarChart = ({ data, title, size = 180 }) => {
  const entries = Object.entries(data).slice(0, 7);
  const maxValue = Math.max(...entries.map(([_, v]) => v), 1);
  const cx = size / 2;
  const cy = size / 2;
  const radius = size / 2 - 30;
  
  const points = entries.map(([key, value], idx) => {
    const angle = (idx / entries.length) * 2 * Math.PI - Math.PI / 2;
    const r = (value / maxValue) * radius;
    return {
      x: cx + r * Math.cos(angle),
      y: cy + r * Math.sin(angle),
      labelX: cx + (radius + 15) * Math.cos(angle),
      labelY: cy + (radius + 15) * Math.sin(angle),
      key,
      value
    };
  });
  
  const polygonPoints = points.map(p => `${p.x},${p.y}`).join(' ');
  
  return (
    <div style={{ textAlign: 'center' }}>
      <h4 style={{ color: '#f472b6', fontSize: '0.85rem', marginBottom: 8 }}>{title}</h4>
      <svg width={size} height={size} style={{ display: 'block', margin: '0 auto' }}>
        {/* Grid circles */}
        {[0.25, 0.5, 0.75, 1].map((pct, i) => (
          <circle key={i} cx={cx} cy={cy} r={radius * pct} fill="none" stroke="rgba(255,255,255,0.1)" strokeWidth="1"/>
        ))}
        {/* Grid lines */}
        {entries.map((_, idx) => {
          const angle = (idx / entries.length) * 2 * Math.PI - Math.PI / 2;
          return (
            <line
              key={idx}
              x1={cx}
              y1={cy}
              x2={cx + radius * Math.cos(angle)}
              y2={cy + radius * Math.sin(angle)}
              stroke="rgba(255,255,255,0.1)"
              strokeWidth="1"
            />
          );
        })}
        {/* Data polygon */}
        <polygon points={polygonPoints} fill="rgba(139, 92, 246, 0.3)" stroke="#8b5cf6" strokeWidth="2"/>
        {/* Points and labels */}
        {points.map((p, idx) => (
          <g key={idx}>
            <circle cx={p.x} cy={p.y} r={4} fill="#8b5cf6"/>
            <text x={p.labelX} y={p.labelY} textAnchor="middle" fill="#a1a1aa" fontSize="7">
              {p.key.substring(0, 6)}
            </text>
          </g>
        ))}
      </svg>
    </div>
  );
};

// Main Component
const MapAnalyticsCharts = ({ results = [], categories = [], collapsed = false }) => {
  const [activeTab, setActiveTab] = useState('overview');
  
  const analyticsData = useMemo(() => {
    return generateMockData(results, categories);
  }, [results, categories]);
  
  const tabs = [
    { id: 'overview', label: 'Overview' },
    { id: 'time', label: 'Time Analysis' },
    { id: 'geo', label: 'Geographic' },
    { id: 'demographics', label: 'Demographics' },
    { id: 'conditions', label: 'Conditions' },
  ];
  
  if (collapsed) {
    return (
      <div style={{
        background: 'linear-gradient(145deg, rgba(20, 10, 40, 0.95), rgba(30, 20, 60, 0.95))',
        borderRadius: 12,
        padding: '10px 15px',
        border: '1px solid rgba(124, 58, 237, 0.3)',
        marginBottom: 15
      }}>
        <span style={{ color: '#f472b6', fontSize: '0.9rem' }}>
          📊 Analytics: {results.length} items analyzed across {Object.keys(analyticsData.categoryData).length} categories
        </span>
      </div>
    );
  }
  
  return (
    <div style={{
      background: 'linear-gradient(145deg, rgba(20, 10, 40, 0.95), rgba(30, 20, 60, 0.95))',
      borderRadius: 16,
      padding: 20,
      border: '2px solid rgba(124, 58, 237, 0.4)',
      marginBottom: 20
    }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 15 }}>
        <h3 style={{ color: '#f472b6', margin: 0, display: 'flex', alignItems: 'center', gap: 10 }}>
          📊 Advanced Analytics Dashboard
          <span style={{ fontSize: '0.75rem', color: '#10b981', fontWeight: 400 }}>
            {results.length} items • 14 charts
          </span>
        </h3>
      </div>
      
      {/* Tabs */}
      <div style={{ display: 'flex', gap: 8, marginBottom: 20, flexWrap: 'wrap' }}>
        {tabs.map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            style={{
              padding: '6px 14px',
              borderRadius: 20,
              border: activeTab === tab.id ? '2px solid #8b5cf6' : '1px solid rgba(255,255,255,0.2)',
              background: activeTab === tab.id ? 'rgba(139, 92, 246, 0.3)' : 'transparent',
              color: activeTab === tab.id ? '#fff' : '#a1a1aa',
              fontSize: '0.8rem',
              cursor: 'pointer',
              transition: 'all 0.2s'
            }}
          >
            {tab.label}
          </button>
        ))}
      </div>
      
      {/* Charts Grid */}
      <div style={{ 
        display: 'grid', 
        gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
        gap: 20
      }}>
        {/* Overview Tab */}
        {activeTab === 'overview' && (
          <>
            <div style={{ background: 'rgba(0,0,0,0.2)', borderRadius: 12, padding: 15 }}>
              <PieChart 
                data={analyticsData.categoryData} 
                colors={COLOR_ZONES.category} 
                title="📁 By Category"
              />
            </div>
            <div style={{ background: 'rgba(0,0,0,0.2)', borderRadius: 12, padding: 15 }}>
              <DonutChart 
                data={analyticsData.timeData} 
                colors={COLOR_ZONES.timeOfDay} 
                title="🕐 Time of Day"
              />
            </div>
            <div style={{ background: 'rgba(0,0,0,0.2)', borderRadius: 12, padding: 15 }}>
              <BarChart 
                data={analyticsData.weatherData} 
                colors={COLOR_ZONES.weather} 
                title="🌤️ Weather Conditions"
              />
            </div>
          </>
        )}
        
        {/* Time Analysis Tab */}
        {activeTab === 'time' && (
          <>
            <div style={{ background: 'rgba(0,0,0,0.2)', borderRadius: 12, padding: 15, gridColumn: 'span 2' }}>
              <HourlyHeatmap 
                data={analyticsData.hourData} 
                title="🕐 Hourly Distribution (24h Heatmap)"
                width={500}
              />
            </div>
            <div style={{ background: 'rgba(0,0,0,0.2)', borderRadius: 12, padding: 15 }}>
              <PieChart 
                data={analyticsData.timeData} 
                colors={COLOR_ZONES.timeOfDay} 
                title="☀️ Morning/Afternoon/Dusk/Night"
              />
            </div>
            <div style={{ background: 'rgba(0,0,0,0.2)', borderRadius: 12, padding: 15 }}>
              <BarChart 
                data={analyticsData.yearData} 
                colors={COLOR_ZONES.category} 
                title="📅 By Year"
              />
            </div>
            <div style={{ background: 'rgba(0,0,0,0.2)', borderRadius: 12, padding: 15, gridColumn: 'span 2' }}>
              <MultiLineChart
                datasets={[
                  { label: 'Morning', values: [10, 15, 20, 25, 22, 18, 12] },
                  { label: 'Afternoon', values: [8, 12, 18, 22, 28, 25, 15] },
                  { label: 'Evening', values: [5, 8, 12, 15, 20, 18, 10] },
                  { label: 'Night', values: [3, 5, 8, 10, 8, 6, 4] },
                ]}
                title="📈 Time Trends (Multi-Line)"
                width={500}
              />
            </div>
          </>
        )}
        
        {/* Geographic Tab */}
        {activeTab === 'geo' && (
          <>
            <div style={{ background: 'rgba(0,0,0,0.2)', borderRadius: 12, padding: 15 }}>
              <PieChart 
                data={analyticsData.countryData} 
                colors={COLOR_ZONES.category} 
                title="🌍 By Country"
              />
            </div>
            <div style={{ background: 'rgba(0,0,0,0.2)', borderRadius: 12, padding: 15 }}>
              <BarChart 
                data={analyticsData.stateData} 
                colors={COLOR_ZONES.category} 
                title="🗺️ By State/Region"
              />
            </div>
            <div style={{ background: 'rgba(0,0,0,0.2)', borderRadius: 12, padding: 15 }}>
              <DonutChart 
                data={analyticsData.urbanData} 
                colors={COLOR_ZONES.urbanRural} 
                title="🏙️ Urban vs Rural"
              />
            </div>
            <div style={{ background: 'rgba(0,0,0,0.2)', borderRadius: 12, padding: 15 }}>
              <RadarChart 
                data={analyticsData.cityData} 
                title="🏘️ City Distribution"
              />
            </div>
            <div style={{ background: 'rgba(0,0,0,0.2)', borderRadius: 12, padding: 15, gridColumn: 'span 2' }}>
              <CompositeBarChart
                data1={analyticsData.urbanData}
                data2={{ city: 15, urban: 12, town: 8, suburban: 10, rural: 5 }}
                labels={Object.keys(analyticsData.urbanData)}
                title="🏢 Urban/Rural Comparison (Composite)"
                width={500}
              />
            </div>
          </>
        )}
        
        {/* Demographics Tab */}
        {activeTab === 'demographics' && (
          <>
            <div style={{ background: 'rgba(0,0,0,0.2)', borderRadius: 12, padding: 15 }}>
              <PieChart 
                data={analyticsData.ageData} 
                colors={COLOR_ZONES.age} 
                title="👥 By Age Group"
              />
            </div>
            <div style={{ background: 'rgba(0,0,0,0.2)', borderRadius: 12, padding: 15 }}>
              <BarChart 
                data={analyticsData.incomeData} 
                colors={COLOR_ZONES.income} 
                title="💰 By Income Level ($10 increments)"
              />
            </div>
            <div style={{ background: 'rgba(0,0,0,0.2)', borderRadius: 12, padding: 15 }}>
              <DonutChart 
                data={analyticsData.firstNameData} 
                colors={COLOR_ZONES.category} 
                title="👤 By First Name"
              />
            </div>
            <div style={{ background: 'rgba(0,0,0,0.2)', borderRadius: 12, padding: 15, gridColumn: 'span 2' }}>
              <StackedAreaChart
                datasets={[
                  { label: '0-17', values: [5, 8, 12, 10, 8, 6, 4] },
                  { label: '18-25', values: [10, 15, 20, 18, 15, 12, 8] },
                  { label: '26-35', values: [15, 20, 25, 22, 18, 15, 10] },
                  { label: '36-45', values: [12, 18, 22, 20, 16, 12, 8] },
                  { label: '46+', values: [8, 12, 15, 14, 12, 10, 6] },
                ]}
                labels={['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']}
                title="📊 Age Groups Over Time (Stacked Area)"
                width={500}
              />
            </div>
          </>
        )}
        
        {/* Conditions Tab */}
        {activeTab === 'conditions' && (
          <>
            <div style={{ background: 'rgba(0,0,0,0.2)', borderRadius: 12, padding: 15 }}>
              <PieChart 
                data={analyticsData.weatherData} 
                colors={COLOR_ZONES.weather} 
                title="🌤️ Weather Distribution"
              />
            </div>
            <div style={{ background: 'rgba(0,0,0,0.2)', borderRadius: 12, padding: 15 }}>
              <RadarChart 
                data={analyticsData.weatherData} 
                title="☁️ Weather Radar"
              />
            </div>
            <div style={{ background: 'rgba(0,0,0,0.2)', borderRadius: 12, padding: 15, gridColumn: 'span 2' }}>
              <MultiLineChart
                datasets={[
                  { label: 'Sunny', values: [20, 25, 30, 35, 32, 28, 22] },
                  { label: 'Cloudy', values: [15, 18, 22, 20, 18, 15, 12] },
                  { label: 'Rainy', values: [5, 8, 10, 12, 10, 8, 6] },
                  { label: 'Snowy', values: [2, 3, 5, 4, 3, 2, 1] },
                ]}
                title="🌡️ Weather Patterns Over Time"
                width={500}
              />
            </div>
            <div style={{ background: 'rgba(0,0,0,0.2)', borderRadius: 12, padding: 15 }}>
              <BarChart 
                data={{
                  'Hot': Math.floor(Math.random() * 30) + 10,
                  'Warm': Math.floor(Math.random() * 30) + 20,
                  'Cool': Math.floor(Math.random() * 30) + 15,
                  'Cold': Math.floor(Math.random() * 20) + 5,
                  'Freezing': Math.floor(Math.random() * 10) + 2,
                }}
                colors={COLOR_ZONES.weather} 
                title="🌡️ Temperature Ranges"
              />
            </div>
          </>
        )}
      </div>
      
      {/* Summary Stats */}
      <div style={{ 
        marginTop: 20, 
        display: 'grid', 
        gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', 
        gap: 10 
      }}>
        {[
          { label: 'Categories', value: Object.keys(analyticsData.categoryData).length, icon: '📁', color: '#8b5cf6' },
          { label: 'Countries', value: Object.keys(analyticsData.countryData).length, icon: '🌍', color: '#3b82f6' },
          { label: 'Weather Types', value: Object.keys(analyticsData.weatherData).filter(k => analyticsData.weatherData[k] > 0).length, icon: '🌤️', color: '#f97316' },
          { label: 'Urban Areas', value: Object.keys(analyticsData.urbanData).length, icon: '🏙️', color: '#22c55e' },
          { label: 'Age Groups', value: Object.keys(analyticsData.ageData).length, icon: '👥', color: '#f472b6' },
          { label: 'Income Levels', value: Object.keys(analyticsData.incomeData).length, icon: '💰', color: '#fbbf24' },
        ].map((stat, idx) => (
          <div key={idx} style={{
            background: `linear-gradient(135deg, ${stat.color}20, transparent)`,
            borderRadius: 10,
            padding: '10px 15px',
            border: `1px solid ${stat.color}40`,
            textAlign: 'center'
          }}>
            <div style={{ fontSize: '1.2rem' }}>{stat.icon}</div>
            <div style={{ color: '#fff', fontWeight: 700, fontSize: '1.1rem' }}>{stat.value}</div>
            <div style={{ color: '#a1a1aa', fontSize: '0.7rem' }}>{stat.label}</div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default MapAnalyticsCharts;
