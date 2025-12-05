import React, { useState, useEffect } from 'react'
import { getTaskStatus, claimTaskPacket } from '../utils/api'
import './TasksPage.css'

interface TaskStatus {
  task_type: string
  task_name: string
  task_description: string
  completed: boolean
  can_claim: boolean
  progress: {
    current: number
    target: number
    completed: boolean
  }
  reward_amount: number
  reward_currency: string
  red_packet_id?: string
  completed_at?: string
  claimed_at?: string
}

const TasksPage: React.FC = () => {
  const [tasks, setTasks] = useState<TaskStatus[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadTasks()
  }, [])

  const loadTasks = async () => {
    try {
      setLoading(true)
      const data = await getTaskStatus()
      setTasks(data)
      setError(null)
    } catch (err: any) {
      console.error('Failed to load tasks:', err)
      setError(err.message || '加載任務失敗')
    } finally {
      setLoading(false)
    }
  }

  const handleClaim = async (taskType: string) => {
    try {
      const result = await claimTaskPacket(taskType)
      alert(result.message || '領取成功！')
      // 重新加載任務列表
      await loadTasks()
    } catch (err: any) {
      console.error('Failed to claim task:', err)
      alert(err.message || '領取失敗')
    }
  }

  const getTaskIcon = (taskType: string) => {
    const icons: Record<string, string> = {
      checkin: '📅',
      claim_packet: '🎁',
      send_packet: '💰',
      share_app: '📤',
      invite_friend: '👥',
      invite_5: '⭐',
      invite_10: '🌟',
      claim_10: '🏆',
      send_10: '💎',
      checkin_7: '🔥',
    }
    return icons[taskType] || '✅'
  }

  const getTaskCategory = (taskType: string) => {
    if (taskType.startsWith('invite_') || taskType === 'invite_friend') {
      return 'achievement'
    }
    return 'daily'
  }

  const dailyTasks = tasks.filter(t => getTaskCategory(t.task_type) === 'daily')
  const achievementTasks = tasks.filter(t => getTaskCategory(t.task_type) === 'achievement')

  if (loading) {
    return (
      <div className="tasks-page">
        <div className="loading">加載中...</div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="tasks-page">
        <div className="error">{error}</div>
        <button onClick={loadTasks} className="retry-btn">重試</button>
      </div>
    )
  }

  return (
    <div className="tasks-page">
      <div className="tasks-header">
        <h1>🎯 任務中心</h1>
        <p>完成任務領取紅包獎勵</p>
      </div>

      {/* 每日任務 */}
      <div className="tasks-section">
        <h2>📅 每日任務</h2>
        <div className="tasks-grid">
          {dailyTasks.map((task) => (
            <div key={task.task_type} className={`task-card ${task.completed ? 'completed' : ''}`}>
              <div className="task-icon">{getTaskIcon(task.task_type)}</div>
              <div className="task-info">
                <h3>{task.task_name}</h3>
                <p>{task.task_description}</p>
                <div className="task-progress">
                  <div className="progress-bar">
                    <div
                      className="progress-fill"
                      style={{
                        width: `${Math.min((task.progress.current / task.progress.target) * 100, 100)}%`,
                      }}
                    />
                  </div>
                  <span className="progress-text">
                    {task.progress.current} / {task.progress.target}
                  </span>
                </div>
                <div className="task-reward">
                  獎勵: {task.reward_amount} {task.reward_currency.toUpperCase()}
                </div>
              </div>
              <div className="task-action">
                {task.can_claim ? (
                  <button
                    className="claim-btn"
                    onClick={() => handleClaim(task.task_type)}
                  >
                    領取
                  </button>
                ) : task.completed ? (
                  <span className="claimed-badge">已領取</span>
                ) : (
                  <button className="disabled-btn" disabled>
                    進行中
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* 成就任務 */}
      <div className="tasks-section">
        <h2>🏆 成就任務</h2>
        <div className="tasks-grid">
          {achievementTasks.map((task) => (
            <div key={task.task_type} className={`task-card achievement ${task.completed ? 'completed' : ''}`}>
              <div className="task-icon">{getTaskIcon(task.task_type)}</div>
              <div className="task-info">
                <h3>{task.task_name}</h3>
                <p>{task.task_description}</p>
                <div className="task-progress">
                  <div className="progress-bar">
                    <div
                      className="progress-fill"
                      style={{
                        width: `${Math.min((task.progress.current / task.progress.target) * 100, 100)}%`,
                      }}
                    />
                  </div>
                  <span className="progress-text">
                    {task.progress.current} / {task.progress.target}
                  </span>
                </div>
                <div className="task-reward">
                  獎勵: {task.reward_amount} {task.reward_currency.toUpperCase()}
                </div>
              </div>
              <div className="task-action">
                {task.can_claim ? (
                  <button
                    className="claim-btn"
                    onClick={() => handleClaim(task.task_type)}
                  >
                    領取
                  </button>
                ) : task.completed ? (
                  <span className="claimed-badge">已領取</span>
                ) : (
                  <button className="disabled-btn" disabled>
                    進行中
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>

      {tasks.length === 0 && (
        <div className="empty-state">
          <p>暫無可用任務</p>
        </div>
      )}
    </div>
  )
}

export default TasksPage

