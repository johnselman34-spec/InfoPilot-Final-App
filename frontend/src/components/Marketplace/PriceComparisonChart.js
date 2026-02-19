/**
 * PriceComparisonChart - Shows how a protocol's price compares to marketplace average
 * Features:
 * - Visual bar chart comparison
 * - Percentile ranking
 * - Price suggestions
 * - Category-specific comparisons
 */
import React, { useState, useEffect, useMemo } from 'react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, ReferenceLine, Cell } from 'recharts';

const PriceComparisonChart = ({ 
  currentPrice = 0, 
  categoryName = 'General',
  allPrices = [],
  showSuggestions = true 
}) => {
  // Calculate statistics
  const stats = useMemo(() => {
    const validPrices = allPrices.filter(p => p > 0);
    if (validPrices.length === 0) {
      return {
        min: 0.20,
        max: 24.97,
        avg: 5.00,
        median: 2.99,
        percentile: 50,
        distribution: []
      };
    }
    
    const sorted = [...validPrices].sort((a, b) => a - b);
    const sum = sorted.reduce((a, b) => a + b, 0);
    const avg = sum / sorted.length;
    const median = sorted.length % 2 === 0 
      ? (sorted[sorted.length/2 - 1] + sorted[sorted.length/2]) / 2
      : sorted[Math.floor(sorted.length/2)];
    
    // Calculate percentile of current price
    const belowCount = sorted.filter(p => p < currentPrice).length;
    const percentile = Math.round((belowCount / sorted.length) * 100);
    
    // Create distribution buckets
    const buckets = [
      { range: '$0.20-$1', min: 0.20, max: 1, count: 0 },
      { range: '$1-$3', min: 1, max: 3, count: 0 },
      { range: '$3-$5', min: 3, max: 5, count: 0 },
      { range: '$5-$10', min: 5, max: 10, count: 0 },
      { range: '$10-$15', min: 10, max: 15, count: 0 },
      { range: '$15-$25', min: 15, max: 25, count: 0 },
    ];
    
    sorted.forEach(price => {
      const bucket = buckets.find(b => price >= b.min && price < b.max);
      if (bucket) bucket.count++;
    });
    
    return {
      min: sorted[0],
      max: sorted[sorted.length - 1],
      avg: avg,
      median: median,
      percentile: percentile,
      distribution: buckets,
      total: sorted.length
    };
  }, [allPrices, currentPrice]);
  
  // Price positioning for current price indicator
  const getPricePosition = () => {
    if (currentPrice <= 0) return 'FREE';
    if (currentPrice < stats.avg * 0.5) return 'Budget';
    if (currentPrice < stats.avg) return 'Below Average';
    if (currentPrice < stats.avg * 1.5) return 'Average';
    if (currentPrice < stats.avg * 2) return 'Above Average';
    return 'Premium';
  };
  
  const pricePosition = getPricePosition();
  
  // Color for price position
  const getPositionColor = () => {
    switch (pricePosition) {
      case 'FREE': return '#10b981';
      case 'Budget': return '#22c55e';
      case 'Below Average': return '#84cc16';
      case 'Average': return '#eab308';
      case 'Above Average': return '#f97316';
      case 'Premium': return '#ef4444';
      default: return '#8b5cf6';
    }
  };

  return (
    <div style={{
      background: 'linear-gradient(135deg, rgba(139, 92, 246, 0.1), rgba(59, 130, 246, 0.1))',
      borderRadius: 16,
      padding: 20,
      border: '1px solid rgba(139, 92, 246, 0.3)'
    }}>
      <h3 style={{ color: '#a78bfa', margin: '0 0 15px 0', fontSize: '1.1rem' }}>
        💰 Price Comparison - {categoryName}
      </h3>
      
      {/* Current Price Display */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        marginBottom: 20,
        padding: 15,
        background: 'rgba(0,0,0,0.2)',
        borderRadius: 12
      }}>
        <div>
          <span style={{ color: '#a1a1aa', fontSize: '0.85rem' }}>Your Price</span>
          <div style={{ 
            color: '#fff', 
            fontSize: '2rem', 
            fontWeight: 700,
            display: 'flex',
            alignItems: 'baseline',
            gap: 8
          }}>
            {currentPrice > 0 ? `$${currentPrice.toFixed(2)}` : 'FREE'}
            <span style={{ 
              background: getPositionColor(),
              color: '#fff',
              padding: '4px 10px',
              borderRadius: 20,
              fontSize: '0.75rem',
              fontWeight: 600
            }}>
              {pricePosition}
            </span>
          </div>
        </div>
        
        <div style={{ textAlign: 'right' }}>
          <span style={{ color: '#a1a1aa', fontSize: '0.85rem' }}>Market Average</span>
          <div style={{ color: '#8b5cf6', fontSize: '1.5rem', fontWeight: 600 }}>
            ${stats.avg.toFixed(2)}
          </div>
        </div>
      </div>
      
      {/* Statistics Row */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(4, 1fr)',
        gap: 10,
        marginBottom: 20
      }}>
        <StatBox label="Lowest" value={`$${stats.min.toFixed(2)}`} color="#22c55e" />
        <StatBox label="Median" value={`$${stats.median.toFixed(2)}`} color="#3b82f6" />
        <StatBox label="Average" value={`$${stats.avg.toFixed(2)}`} color="#8b5cf6" />
        <StatBox label="Highest" value={`$${stats.max.toFixed(2)}`} color="#ef4444" />
      </div>
      
      {/* Distribution Chart */}
      {stats.distribution.length > 0 && (
        <div style={{ marginBottom: 20 }}>
          <h4 style={{ color: '#c4b5fd', margin: '0 0 10px 0', fontSize: '0.9rem' }}>
            📊 Price Distribution ({stats.total} protocols)
          </h4>
          <ResponsiveContainer width="100%" height={150}>
            <BarChart data={stats.distribution}>
              <XAxis 
                dataKey="range" 
                tick={{ fill: '#a1a1aa', fontSize: 11 }}
                axisLine={{ stroke: 'rgba(255,255,255,0.1)' }}
              />
              <YAxis 
                tick={{ fill: '#a1a1aa', fontSize: 11 }}
                axisLine={{ stroke: 'rgba(255,255,255,0.1)' }}
              />
              <Tooltip 
                contentStyle={{ 
                  background: '#1a1a2e', 
                  border: '1px solid rgba(139, 92, 246, 0.5)',
                  borderRadius: 8
                }}
                labelStyle={{ color: '#fff' }}
              />
              <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                {stats.distribution.map((entry, index) => (
                  <Cell 
                    key={`cell-${index}`} 
                    fill={currentPrice >= entry.min && currentPrice < entry.max 
                      ? '#ec4899' 
                      : '#8b5cf6'
                    }
                  />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}
      
      {/* Percentile Indicator */}
      <div style={{
        background: 'rgba(0,0,0,0.2)',
        borderRadius: 10,
        padding: 15,
        marginBottom: 15
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
          <span style={{ color: '#a1a1aa', fontSize: '0.85rem' }}>Your Price Percentile</span>
          <span style={{ color: '#fff', fontWeight: 600 }}>{stats.percentile}%</span>
        </div>
        <div style={{
          height: 8,
          background: 'rgba(255,255,255,0.1)',
          borderRadius: 4,
          overflow: 'hidden',
          position: 'relative'
        }}>
          <div style={{
            width: `${stats.percentile}%`,
            height: '100%',
            background: `linear-gradient(90deg, #22c55e, ${getPositionColor()})`,
            borderRadius: 4,
            transition: 'width 0.5s ease'
          }} />
          <div style={{
            position: 'absolute',
            left: `${stats.percentile}%`,
            top: -4,
            width: 16,
            height: 16,
            background: '#fff',
            borderRadius: '50%',
            border: `3px solid ${getPositionColor()}`,
            transform: 'translateX(-50%)'
          }} />
        </div>
        <p style={{ color: '#71717a', fontSize: '0.75rem', margin: '8px 0 0 0' }}>
          Your price is higher than {stats.percentile}% of protocols in this category
        </p>
      </div>
      
      {/* Price Suggestions */}
      {showSuggestions && (
        <div style={{
          background: 'rgba(16, 185, 129, 0.1)',
          borderRadius: 10,
          padding: 15,
          border: '1px solid rgba(16, 185, 129, 0.3)'
        }}>
          <h4 style={{ color: '#10b981', margin: '0 0 10px 0', fontSize: '0.9rem' }}>
            💡 Pricing Suggestions
          </h4>
          <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
            {[
              { label: 'Budget', price: 0.99, desc: 'High volume sales' },
              { label: 'Competitive', price: Math.max(0.20, stats.avg * 0.8).toFixed(2), desc: 'Below average' },
              { label: 'Standard', price: stats.avg.toFixed(2), desc: 'Market rate' },
              { label: 'Premium', price: Math.min(24.97, stats.avg * 1.5).toFixed(2), desc: 'High value' },
            ].map(suggestion => (
              <div 
                key={suggestion.label}
                style={{
                  background: 'rgba(0,0,0,0.2)',
                  padding: '8px 12px',
                  borderRadius: 8,
                  textAlign: 'center',
                  minWidth: 80
                }}
              >
                <div style={{ color: '#10b981', fontWeight: 600, fontSize: '0.9rem' }}>
                  ${suggestion.price}
                </div>
                <div style={{ color: '#a1a1aa', fontSize: '0.7rem' }}>
                  {suggestion.label}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

// Stat box component
const StatBox = ({ label, value, color }) => (
  <div style={{
    background: 'rgba(0,0,0,0.2)',
    padding: 10,
    borderRadius: 8,
    textAlign: 'center'
  }}>
    <div style={{ color, fontSize: '1.1rem', fontWeight: 600 }}>{value}</div>
    <div style={{ color: '#71717a', fontSize: '0.7rem' }}>{label}</div>
  </div>
);

export default PriceComparisonChart;
