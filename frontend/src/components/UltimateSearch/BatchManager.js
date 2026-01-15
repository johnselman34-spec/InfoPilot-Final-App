import React from 'react';

/**
 * BatchManager - Manage and delete search sessions/batches
 */
const BatchManager = ({
  batches,
  showBatchManager,
  setShowBatchManager,
  onFetchBatches,
  onDeleteBatch,
  lastBatchId
}) => {
  const handleToggle = () => {
    setShowBatchManager(!showBatchManager);
    if (!showBatchManager) {
      onFetchBatches();
    }
  };

  return (
    <div style={{ marginBottom: 20 }}>
      <button
        className="btn btn-secondary"
        onClick={handleToggle}
        style={{ padding: '8px 16px', fontSize: '0.85rem' }}
        data-testid="batch-manager-toggle"
      >
        🗑️ Manage Search Sessions ({batches.length})
      </button>
      
      {showBatchManager && (
        <div style={{ 
          marginTop: 10, 
          padding: 15, 
          background: 'rgba(30, 20, 50, 0.5)', 
          borderRadius: 12,
          border: '1px solid rgba(239, 68, 68, 0.3)'
        }}>
          <h4 style={{ color: '#f87171', marginBottom: 10 }}>Search Sessions (Batches)</h4>
          <p style={{ color: '#a1a1aa', fontSize: '0.8rem', marginBottom: 15 }}>
            Delete all results from a specific Search & Collate session:
          </p>
          {batches.length === 0 ? (
            <p style={{ color: '#71717a', fontSize: '0.9rem' }}>No search sessions found.</p>
          ) : (
            <div style={{ maxHeight: 200, overflowY: 'auto' }}>
              {batches.map(batch => (
                <BatchItem
                  key={batch.batch_id}
                  batch={batch}
                  onDelete={() => onDeleteBatch(batch.batch_id)}
                />
              ))}
            </div>
          )}
          {lastBatchId && (
            <button
              className="btn"
              onClick={() => onDeleteBatch(lastBatchId)}
              style={{ 
                marginTop: 10,
                background: 'linear-gradient(135deg, rgba(239, 68, 68, 0.3), rgba(249, 115, 22, 0.3))',
                color: '#fbbf24',
                border: '1px solid rgba(239, 68, 68, 0.5)'
              }}
              data-testid="delete-last-batch"
            >
              🗑️ Delete Last Search Session
            </button>
          )}
        </div>
      )}
    </div>
  );
};

/**
 * BatchItem - Individual batch row
 */
const BatchItem = ({ batch, onDelete }) => {
  return (
    <div 
      style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        padding: '10px 12px',
        background: 'rgba(0,0,0,0.2)',
        borderRadius: 8,
        marginBottom: 8
      }}
    >
      <div>
        <span style={{ color: '#e2e8f0', fontSize: '0.9rem' }}>
          {batch.result_count} results
        </span>
        <span style={{ color: '#71717a', fontSize: '0.8rem', marginLeft: 10 }}>
          "{batch.sample_title}..."
        </span>
        {batch.collated_at && (
          <span style={{ color: '#6b7280', fontSize: '0.75rem', marginLeft: 10 }}>
            {new Date(batch.collated_at).toLocaleDateString()}
          </span>
        )}
      </div>
      <button
        className="btn"
        onClick={onDelete}
        style={{ 
          background: 'rgba(239, 68, 68, 0.2)', 
          color: '#f87171', 
          padding: '6px 12px',
          fontSize: '0.8rem',
          border: '1px solid rgba(239, 68, 68, 0.3)'
        }}
        data-testid={`delete-batch-${batch.batch_id}`}
      >
        🗑️ Delete
      </button>
    </div>
  );
};

export { BatchManager, BatchItem };
export default BatchManager;
