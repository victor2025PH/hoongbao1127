/**
 * 推荐树可视化组件
 */
import { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Users, TrendingUp, Award, ChevronRight, ChevronDown } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { getReferralStats, getReferralTree } from '../utils/api';
import { useTranslation } from '../providers/I18nProvider';

interface ReferralTreeNode {
  user_id: number;
  username: string | null;
  referral_code: string | null;
  referrals: ReferralTreeNode[];
}

interface ReferralStats {
  tier1_count: number;
  tier2_count: number;
  total_referrals: number;
  total_reward: string;
  reward_count: number;
  tier1_reward: string;
  tier2_reward: string;
}

export default function ReferralTree() {
  const { t } = useTranslation();
  const [expandedNodes, setExpandedNodes] = useState<Set<number>>(new Set());

  // 获取推荐统计
  const { data: stats, isLoading: statsLoading } = useQuery<ReferralStats>({
    queryKey: ['referral-stats'],
    queryFn: getReferralStats,
    retry: 1,
  });

  // 获取推荐树
  const { data: tree, isLoading: treeLoading } = useQuery<ReferralTreeNode>({
    queryKey: ['referral-tree'],
    queryFn: getReferralTree,
    retry: 1,
  });

  const toggleNode = (userId: number) => {
    const newExpanded = new Set(expandedNodes);
    if (newExpanded.has(userId)) {
      newExpanded.delete(userId);
    } else {
      newExpanded.add(userId);
    }
    setExpandedNodes(newExpanded);
  };

  if (statsLoading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="text-gray-400">加载中...</div>
      </div>
    );
  }

  if (!stats) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="text-gray-400">暂无推荐数据</div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* 推荐统计卡片 */}
      <div className="grid grid-cols-2 gap-4">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-gradient-to-br from-blue-500/20 to-cyan-500/20 rounded-2xl p-4 border border-blue-500/30"
        >
          <div className="flex items-center gap-2 mb-2">
            <Users className="w-5 h-5 text-blue-400" />
            <span className="text-sm text-gray-300">Tier 1推荐</span>
          </div>
          <div className="text-2xl font-bold text-blue-400">{stats.tier1_count}</div>
          <div className="text-xs text-gray-400 mt-1">奖励: {parseFloat(stats.tier1_reward).toFixed(2)} USDT</div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="bg-gradient-to-br from-purple-500/20 to-pink-500/20 rounded-2xl p-4 border border-purple-500/30"
        >
          <div className="flex items-center gap-2 mb-2">
            <TrendingUp className="w-5 h-5 text-purple-400" />
            <span className="text-sm text-gray-300">Tier 2推荐</span>
          </div>
          <div className="text-2xl font-bold text-purple-400">{stats.tier2_count}</div>
          <div className="text-xs text-gray-400 mt-1">奖励: {parseFloat(stats.tier2_reward).toFixed(2)} USDT</div>
        </motion.div>
      </div>

      {/* 总推荐统计 */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
        className="bg-gradient-to-r from-emerald-500/20 to-green-500/20 rounded-2xl p-6 border border-emerald-500/30"
      >
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <Award className="w-6 h-6 text-emerald-400" />
            <span className="text-lg font-semibold text-white">总推荐统计</span>
          </div>
        </div>
        <div className="grid grid-cols-3 gap-4">
          <div>
            <div className="text-sm text-gray-400 mb-1">总推荐人数</div>
            <div className="text-2xl font-bold text-emerald-400">{stats.total_referrals}</div>
          </div>
          <div>
            <div className="text-sm text-gray-400 mb-1">总奖励</div>
            <div className="text-2xl font-bold text-emerald-400">{parseFloat(stats.total_reward).toFixed(2)}</div>
            <div className="text-xs text-gray-400">USDT</div>
          </div>
          <div>
            <div className="text-sm text-gray-400 mb-1">奖励次数</div>
            <div className="text-2xl font-bold text-emerald-400">{stats.reward_count}</div>
          </div>
        </div>
      </motion.div>

      {/* 推荐树 */}
      {tree && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="bg-gray-800/50 rounded-2xl p-6 border border-gray-700"
        >
          <h3 className="text-lg font-semibold text-white mb-4">推荐树</h3>
          <ReferralTreeNodeComponent
            node={tree}
            level={0}
            expandedNodes={expandedNodes}
            onToggle={toggleNode}
          />
        </motion.div>
      )}
    </div>
  );
}

interface ReferralTreeNodeProps {
  node: ReferralTreeNode;
  level: number;
  expandedNodes: Set<number>;
  onToggle: (userId: number) => void;
}

function ReferralTreeNodeComponent({ node, level, expandedNodes, onToggle }: ReferralTreeNodeProps) {
  const isExpanded = expandedNodes.has(node.user_id);
  const hasChildren = node.referrals && node.referrals.length > 0;

  return (
    <div className="ml-4">
      <div
        className={`flex items-center gap-2 p-2 rounded-lg hover:bg-gray-700/50 cursor-pointer ${
          level === 0 ? 'bg-blue-500/20 border border-blue-500/30' : ''
        }`}
        onClick={() => hasChildren && onToggle(node.user_id)}
      >
        {hasChildren && (
          <div className="w-4 h-4 flex items-center justify-center">
            {isExpanded ? (
              <ChevronDown className="w-4 h-4 text-gray-400" />
            ) : (
              <ChevronRight className="w-4 h-4 text-gray-400" />
            )}
          </div>
        )}
        {!hasChildren && <div className="w-4 h-4" />}
        <div className="flex-1">
          <div className="text-white font-medium">
            {node.username || `User ${node.user_id}`}
            {level === 0 && <span className="ml-2 text-xs text-blue-400">(我)</span>}
          </div>
          {node.referral_code && (
            <div className="text-xs text-gray-400">推荐码: {node.referral_code}</div>
          )}
        </div>
        {level > 0 && (
          <div className="text-xs text-gray-400">
            {level === 1 ? 'Tier 1' : 'Tier 2'}
          </div>
        )}
      </div>
      <AnimatePresence>
        {isExpanded && hasChildren && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="mt-2"
          >
            {node.referrals.map((child) => (
              <ReferralTreeNodeComponent
                key={child.user_id}
                node={child}
                level={level + 1}
                expandedNodes={expandedNodes}
                onToggle={onToggle}
              />
            ))}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

