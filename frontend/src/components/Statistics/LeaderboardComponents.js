import React from 'react';

// Seller titles based on ranking
const SELLER_TITLES = [
  { rank: 1, title: "The Protocol Overlord 🦁", color: "#fbbf24" },
  { rank: 2, title: "The Protocol Billionaire 🏦", color: "#c0c0c0" },
  { rank: 3, title: "The Silver Searcher 🥈", color: "#cd7f32" },
  { rank: 4, title: "The Search Tycoon 🎩", color: "#8b5cf6" },
  { rank: 5, title: "Protocol Prodigy 🌟", color: "#3b82f6" },
];

// Sales badges
const getSalesBadge = (sales) => {
  if (sales >= 500) return { badge: "👑", label: "Legend" };
  if (sales >= 200) return { badge: "💎", label: "Diamond" };
  if (sales >= 100) return { badge: "🏆", label: "Champion" };
  if (sales >= 50) return { badge: "⭐", label: "Star" };
  if (sales >= 20) return { badge: "🔥", label: "Hot" };
  return { badge: "📈", label: "Rising" };
};

// Revenue badges
const getRevenueBadge = (revenue) => {
  if (revenue >= 1000) return { badge: "💰", label: "Mogul" };
  if (revenue >= 500) return { badge: "💵", label: "Wealthy" };
  if (revenue >= 200) return { badge: "💲", label: "Earner" };
  if (revenue >= 100) return { badge: "🤑", label: "Profiting" };
  return { badge: "📊", label: "Growing" };
};

/**
 * TopSellersLeaderboard - Leaderboard with tabs for sales and revenue
 */
export const TopSellersLeaderboard = ({ leaderboard, activeTab, setActiveTab, onShowOnMap }) => {
  const currentData = activeTab === 'sales' ? leaderboard.sales : leaderboard.revenue;

  return (
    <div className="card" style={{ marginBottom: 25 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
        <h3 style={{ color: '#f472b6', margin: 0 }}>🏆 Top Sellers</h3>
        <div style={{ display: 'flex', gap: 10 }}>
          <button
            className={`btn ${activeTab === 'sales' ? 'btn-primary' : 'btn-secondary'}`}
            onClick={() => setActiveTab('sales')}
            style={{ padding: '6px 12px', fontSize: '0.8rem' }}
          >
            By Sales
          </button>
          <button
            className={`btn ${activeTab === 'revenue' ? 'btn-primary' : 'btn-secondary'}`}
            onClick={() => setActiveTab('revenue')}
            style={{ padding: '6px 12px', fontSize: '0.8rem' }}
          >
            By Revenue
          </button>
          <button
            className="btn btn-secondary"
            onClick={() => onShowOnMap('top_sellers', currentData)}
            style={{ padding: '6px 12px', fontSize: '0.8rem' }}
          >
            📍 Map
          </button>
        </div>
      </div>

      {currentData?.length === 0 ? (
        <p style={{ color: '#a1a1aa', textAlign: 'center', padding: 20 }}>
          No sellers yet. Be the first to sell a protocol! 🚀
        </p>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
          {currentData?.slice(0, 10).map((seller, idx) => (
            <SellerCard key={seller.user_id || idx} seller={seller} rank={idx + 1} type={activeTab} />
          ))}
        </div>
      )}
    </div>
  );
};

/**
 * SellerCard - Individual seller in the leaderboard
 */
const SellerCard = ({ seller, rank, type }) => {
  const title = SELLER_TITLES.find(t => t.rank === rank);
  const badge = type === 'sales' 
    ? getSalesBadge(seller.total_sales || seller.sales_count || 0)
    : getRevenueBadge(seller.total_revenue || 0);

  const value = type === 'sales' 
    ? `${(seller.total_sales || seller.sales_count || 0).toLocaleString()} sales`
    : `$${(seller.total_revenue || 0).toFixed(2)}`;

  return (
    <div style={{
      display: 'flex',
      alignItems: 'center',
      padding: '15px 20px',
      background: rank <= 3 
        ? `linear-gradient(135deg, rgba(${rank === 1 ? '251,191,36' : rank === 2 ? '192,192,192' : '205,127,50'},0.2) 0%, rgba(30,20,50,0.8) 100%)`
        : 'rgba(30, 20, 50, 0.5)',
      borderRadius: 12,
      border: rank <= 3 ? `1px solid ${title?.color}50` : '1px solid rgba(124, 58, 237, 0.2)'
    }}>
      {/* Rank */}
      <div style={{
        width: 40,
        height: 40,
        borderRadius: '50%',
        background: rank <= 3 ? title?.color : 'rgba(124, 58, 237, 0.3)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        fontWeight: 'bold',
        fontSize: rank <= 3 ? '1.2rem' : '1rem',
        color: rank <= 3 ? '#1e1b4b' : '#a78bfa',
        marginRight: 15
      }}>
        {rank <= 3 ? ['🥇', '🥈', '🥉'][rank - 1] : rank}
      </div>

      {/* User Info */}
      <div style={{ flex: 1 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
          <span style={{ 
            color: title?.color || '#e2e8f0', 
            fontWeight: 600,
            fontSize: rank <= 3 ? '1.1rem' : '1rem'
          }}>
            {seller.username || 'Anonymous Seller'}
          </span>
          <span style={{ 
            background: 'rgba(124, 58, 237, 0.3)', 
            padding: '2px 8px', 
            borderRadius: 10, 
            fontSize: '0.7rem',
            color: '#a78bfa'
          }}>
            {badge.badge} {badge.label}
          </span>
        </div>
        {title && (
          <div style={{ color: title.color, fontSize: '0.8rem', fontStyle: 'italic' }}>
            {title.title}
          </div>
        )}
      </div>

      {/* Value */}
      <div style={{ 
        textAlign: 'right',
        color: type === 'revenue' ? '#10b981' : '#f472b6',
        fontWeight: 'bold',
        fontSize: '1.1rem'
      }}>
        {value}
      </div>
    </div>
  );
};

/**
 * MostCopiedLeaderboard - Most copied protocols leaderboard
 */
export const MostCopiedLeaderboard = ({ data, onShowOnMap }) => {
  const { leaderboard = [], stats = {} } = data;

  return (
    <div className="card" style={{ marginBottom: 25 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
        <h3 style={{ color: '#f472b6', margin: 0 }}>📋 Most Copied Protocols</h3>
        <button
          className="btn btn-secondary"
          onClick={() => onShowOnMap('most_copied', leaderboard)}
          style={{ padding: '6px 12px', fontSize: '0.8rem' }}
        >
          📍 Map
        </button>
      </div>

      {/* Stats Summary */}
      <div style={{ 
        display: 'flex', 
        gap: 15, 
        marginBottom: 20, 
        flexWrap: 'wrap' 
      }}>
        <StatBadge label="Total Copies" value={stats.total_copies || 0} color="#8b5cf6" />
        <StatBadge label="Free Copies" value={stats.free_copies || 0} color="#10b981" />
        <StatBadge label="Paid Copies" value={stats.paid_copies || 0} color="#f59e0b" />
      </div>

      {leaderboard.length === 0 ? (
        <p style={{ color: '#a1a1aa', textAlign: 'center', padding: 20 }}>
          No protocols copied yet. Create one and share it! 📤
        </p>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
          {leaderboard.slice(0, 10).map((item, idx) => (
            <CopiedProtocolCard key={item.protocol_id || idx} item={item} rank={idx + 1} />
          ))}
        </div>
      )}
    </div>
  );
};

const StatBadge = ({ label, value, color }) => (
  <div style={{
    background: `${color}20`,
    border: `1px solid ${color}50`,
    borderRadius: 20,
    padding: '8px 15px',
    display: 'flex',
    alignItems: 'center',
    gap: 8
  }}>
    <span style={{ color, fontWeight: 'bold' }}>{value.toLocaleString()}</span>
    <span style={{ color: '#a1a1aa', fontSize: '0.85rem' }}>{label}</span>
  </div>
);

const CopiedProtocolCard = ({ item, rank }) => (
  <div style={{
    display: 'flex',
    alignItems: 'center',
    padding: '12px 15px',
    background: 'rgba(30, 20, 50, 0.5)',
    borderRadius: 10,
    border: '1px solid rgba(124, 58, 237, 0.2)'
  }}>
    <div style={{
      width: 30,
      height: 30,
      borderRadius: '50%',
      background: rank <= 3 ? 'rgba(251, 191, 36, 0.3)' : 'rgba(124, 58, 237, 0.2)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      fontSize: '0.9rem',
      marginRight: 12,
      color: rank <= 3 ? '#fbbf24' : '#a78bfa'
    }}>
      {rank}
    </div>
    <div style={{ flex: 1 }}>
      <div style={{ color: '#e2e8f0', fontWeight: 500 }}>{item.name || 'Unnamed Protocol'}</div>
      <div style={{ color: '#71717a', fontSize: '0.8rem' }}>by {item.creator || 'Anonymous'}</div>
    </div>
    <div style={{ 
      background: 'rgba(16, 185, 129, 0.2)', 
      padding: '4px 10px', 
      borderRadius: 15,
      color: '#10b981',
      fontSize: '0.85rem',
      fontWeight: 600
    }}>
      📋 {item.copy_count || 0} copies
    </div>
  </div>
);

export default TopSellersLeaderboard;
