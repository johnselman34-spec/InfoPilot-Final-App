/**
 * Personal Report Achievement Badges
 * Gamification badges earned through creating Personal Reports
 */
import React from 'react';

// Personal Report Achievement Definitions
export const PERSONAL_REPORT_BADGES = [
  {
    id: 'first_story',
    name: 'First Story',
    description: 'Created your first Personal Report',
    icon: '📝',
    requirement: 1,
    xp: 50,
    rarity: 'common'
  },
  {
    id: 'storyteller',
    name: 'Storyteller',
    description: 'Created 5 Personal Reports',
    icon: '📖',
    requirement: 5,
    xp: 100,
    rarity: 'uncommon'
  },
  {
    id: 'travel_blogger',
    name: 'Travel Blogger',
    description: 'Created 5 reports with different locations',
    icon: '✈️',
    requirement: 5,
    xp: 150,
    rarity: 'uncommon',
    type: 'locations'
  },
  {
    id: 'prolific_author',
    name: 'Prolific Author',
    description: 'Created 25 Personal Reports',
    icon: '✍️',
    requirement: 25,
    xp: 300,
    rarity: 'rare'
  },
  {
    id: 'photo_journalist',
    name: 'Photo Journalist',
    description: 'Added images to 10 reports',
    icon: '📸',
    requirement: 10,
    xp: 200,
    rarity: 'rare',
    type: 'images'
  },
  {
    id: 'topic_expert',
    name: 'Topic Expert',
    description: 'Created 10 reports in the same topic',
    icon: '🎯',
    requirement: 10,
    xp: 250,
    rarity: 'rare',
    type: 'same_topic'
  },
  {
    id: 'world_traveler',
    name: 'World Traveler',
    description: 'Reports from 10 different locations',
    icon: '🌍',
    requirement: 10,
    xp: 400,
    rarity: 'epic',
    type: 'locations'
  },
  {
    id: 'master_chronicler',
    name: 'Master Chronicler',
    description: 'Created 50 Personal Reports',
    icon: '📚',
    requirement: 50,
    xp: 500,
    rarity: 'epic'
  },
  {
    id: 'legendary_scribe',
    name: 'Legendary Scribe',
    description: 'Created 100 Personal Reports',
    icon: '🏆',
    requirement: 100,
    xp: 1000,
    rarity: 'legendary'
  },
  {
    id: 'early_bird',
    name: 'Early Bird',
    description: 'Created a report before 6 AM',
    icon: '🌅',
    requirement: 1,
    xp: 75,
    rarity: 'uncommon',
    type: 'time_early'
  },
  {
    id: 'night_owl',
    name: 'Night Owl',
    description: 'Created a report after midnight',
    icon: '🦉',
    requirement: 1,
    xp: 75,
    rarity: 'uncommon',
    type: 'time_late'
  },
  {
    id: 'wordsmith',
    name: 'Wordsmith',
    description: 'Wrote a report with 1000+ words',
    icon: '📜',
    requirement: 1,
    xp: 150,
    rarity: 'rare',
    type: 'long_content'
  }
];

// Rarity colors
const RARITY_COLORS = {
  common: { bg: 'rgba(156, 163, 175, 0.2)', border: '#9ca3af', text: '#9ca3af' },
  uncommon: { bg: 'rgba(34, 197, 94, 0.2)', border: '#22c55e', text: '#22c55e' },
  rare: { bg: 'rgba(59, 130, 246, 0.2)', border: '#3b82f6', text: '#3b82f6' },
  epic: { bg: 'rgba(168, 85, 247, 0.2)', border: '#a855f7', text: '#a855f7' },
  legendary: { bg: 'rgba(245, 158, 11, 0.2)', border: '#f59e0b', text: '#f59e0b' }
};

// Badge Card Component
export const PersonalReportBadgeCard = ({ badge, earned = false, progress = 0 }) => {
  const colors = RARITY_COLORS[badge.rarity];
  
  return (
    <div style={{
      background: earned ? colors.bg : 'rgba(30, 20, 50, 0.5)',
      border: `2px solid ${earned ? colors.border : 'rgba(255,255,255,0.1)'}`,
      borderRadius: 12,
      padding: 15,
      textAlign: 'center',
      opacity: earned ? 1 : 0.6,
      transition: 'all 0.3s',
      position: 'relative'
    }} data-testid={`badge-${badge.id}`}>
      {/* Earned indicator */}
      {earned && (
        <div style={{
          position: 'absolute',
          top: -8,
          right: -8,
          background: '#10b981',
          borderRadius: '50%',
          width: 24,
          height: 24,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontSize: '0.8rem',
          boxShadow: '0 2px 8px rgba(16, 185, 129, 0.4)'
        }}>
          ✓
        </div>
      )}
      
      {/* Icon */}
      <div style={{ 
        fontSize: '2.5rem', 
        marginBottom: 8,
        filter: earned ? 'none' : 'grayscale(100%)'
      }}>
        {badge.icon}
      </div>
      
      {/* Name */}
      <div style={{ 
        color: earned ? colors.text : '#71717a', 
        fontWeight: 700, 
        fontSize: '0.9rem',
        marginBottom: 5
      }}>
        {badge.name}
      </div>
      
      {/* Description */}
      <div style={{ color: '#a1a1aa', fontSize: '0.75rem', marginBottom: 8 }}>
        {badge.description}
      </div>
      
      {/* Progress bar (if not earned) */}
      {!earned && badge.requirement > 1 && (
        <div style={{
          background: 'rgba(255,255,255,0.1)',
          borderRadius: 10,
          height: 6,
          overflow: 'hidden',
          marginBottom: 8
        }}>
          <div style={{
            background: colors.border,
            height: '100%',
            width: `${Math.min((progress / badge.requirement) * 100, 100)}%`,
            transition: 'width 0.3s'
          }} />
        </div>
      )}
      
      {/* XP reward */}
      <div style={{
        background: earned ? 'rgba(16, 185, 129, 0.2)' : 'rgba(0,0,0,0.2)',
        padding: '4px 10px',
        borderRadius: 10,
        display: 'inline-block',
        fontSize: '0.7rem',
        color: earned ? '#10b981' : '#71717a'
      }}>
        +{badge.xp} XP
      </div>
      
      {/* Rarity tag */}
      <div style={{
        position: 'absolute',
        bottom: 5,
        left: 5,
        fontSize: '0.6rem',
        color: colors.text,
        textTransform: 'uppercase',
        fontWeight: 600
      }}>
        {badge.rarity}
      </div>
    </div>
  );
};

// Full Badge Gallery Component
const PersonalReportBadges = ({ userStats = {}, earnedBadges = [] }) => {
  const earnedIds = new Set(earnedBadges.map(b => b.id || b));
  
  // Calculate progress for each badge
  const getBadgeProgress = (badge) => {
    switch (badge.type) {
      case 'locations':
        return userStats.unique_locations || 0;
      case 'images':
        return userStats.reports_with_images || 0;
      case 'same_topic':
        return userStats.max_topic_count || 0;
      case 'long_content':
        return userStats.has_long_report ? 1 : 0;
      case 'time_early':
        return userStats.has_early_report ? 1 : 0;
      case 'time_late':
        return userStats.has_late_report ? 1 : 0;
      default:
        return userStats.total_reports || 0;
    }
  };
  
  const totalXP = PERSONAL_REPORT_BADGES
    .filter(b => earnedIds.has(b.id))
    .reduce((sum, b) => sum + b.xp, 0);
  
  const earnedCount = PERSONAL_REPORT_BADGES.filter(b => earnedIds.has(b.id)).length;
  
  return (
    <div style={{
      background: 'linear-gradient(135deg, rgba(124, 58, 237, 0.1), rgba(236, 72, 153, 0.1))',
      borderRadius: 16,
      padding: 20,
      border: '1px solid rgba(124, 58, 237, 0.3)'
    }} data-testid="personal-report-badges">
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
        <h3 style={{ color: '#f472b6', margin: 0, display: 'flex', alignItems: 'center', gap: 10 }}>
          📝 Report Writing Badges
        </h3>
        <div style={{ display: 'flex', gap: 15 }}>
          <div style={{
            background: 'rgba(16, 185, 129, 0.2)',
            padding: '5px 12px',
            borderRadius: 10,
            color: '#10b981',
            fontSize: '0.8rem',
            fontWeight: 600
          }}>
            {earnedCount}/{PERSONAL_REPORT_BADGES.length} Earned
          </div>
          <div style={{
            background: 'rgba(245, 158, 11, 0.2)',
            padding: '5px 12px',
            borderRadius: 10,
            color: '#f59e0b',
            fontSize: '0.8rem',
            fontWeight: 600
          }}>
            {totalXP} XP
          </div>
        </div>
      </div>
      
      {/* Badge Grid */}
      <div style={{ 
        display: 'grid', 
        gridTemplateColumns: 'repeat(auto-fill, minmax(140px, 1fr))', 
        gap: 15 
      }}>
        {PERSONAL_REPORT_BADGES.map(badge => (
          <PersonalReportBadgeCard
            key={badge.id}
            badge={badge}
            earned={earnedIds.has(badge.id)}
            progress={getBadgeProgress(badge)}
          />
        ))}
      </div>
      
      {/* Tips */}
      <div style={{
        marginTop: 20,
        padding: 15,
        background: 'rgba(0,0,0,0.2)',
        borderRadius: 10,
        fontSize: '0.8rem',
        color: '#a1a1aa'
      }}>
        <strong style={{ color: '#f472b6' }}>💡 Tips:</strong> Create Personal Reports (Organic) about topics you&apos;re passionate about! 
        Add locations, images, and detailed content to earn more badges. The more you write, the more XP you earn!
      </div>
    </div>
  );
};

export default PersonalReportBadges;
