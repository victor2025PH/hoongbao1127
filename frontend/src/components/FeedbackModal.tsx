import { useState } from 'react'
import { X, Send, Image as ImageIcon, AlertCircle } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import { useTranslation } from '../providers/I18nProvider'
import { useMutation } from '@tanstack/react-query'
import { submitFeedback, getFeedbackTypes } from '../utils/api'
import { showAlert } from '../utils/telegram'

interface FeedbackModalProps {
  isOpen: boolean
  onClose: () => void
}

export default function FeedbackModal({ isOpen, onClose }: FeedbackModalProps) {
  const { t } = useTranslation()
  const [type, setType] = useState<'bug' | 'feature' | 'suggestion' | 'other'>('bug')
  const [title, setTitle] = useState('')
  const [content, setContent] = useState('')
  const [contact, setContact] = useState('')
  const [screenshotUrl, setScreenshotUrl] = useState('')

  const feedbackMutation = useMutation({
    mutationFn: submitFeedback,
    onSuccess: () => {
      showAlert(t('feedback_submitted') || '反馈已提交，感谢您的反馈！')
      onClose()
      // 重置表单
      setType('bug')
      setTitle('')
      setContent('')
      setContact('')
      setScreenshotUrl('')
    },
    onError: (error: Error) => {
      showAlert(error.message || '提交失败，请重试')
    },
  })

  const handleSubmit = () => {
    if (!title.trim() || !content.trim()) {
      showAlert(t('please_fill_all_fields') || '请填写所有必填字段')
      return
    }

    feedbackMutation.mutate({
      type,
      title: title.trim(),
      content: content.trim(),
      contact: contact.trim() || undefined,
      screenshot_url: screenshotUrl.trim() || undefined,
    })
  }

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4"
          onClick={onClose}
        >
          <motion.div
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0.9, opacity: 0 }}
            onClick={(e) => e.stopPropagation()}
            className="bg-[#1C1C1E] rounded-3xl p-6 w-full max-w-md max-h-[90vh] overflow-y-auto"
          >
            {/* 头部 */}
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-xl font-bold text-white">
                {t('submit_feedback') || '提交反馈'}
              </h2>
              <button
                onClick={onClose}
                className="p-2 hover:bg-white/10 rounded-full transition-colors"
              >
                <X size={20} className="text-gray-400" />
              </button>
            </div>

            {/* 反馈类型 */}
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-300 mb-2">
                {t('feedback_type') || '反馈类型'}
              </label>
              <div className="grid grid-cols-2 gap-2">
                {(['bug', 'feature', 'suggestion', 'other'] as const).map((feedbackType) => (
                  <button
                    key={feedbackType}
                    onClick={() => setType(feedbackType)}
                    className={`py-2 px-4 rounded-xl text-sm font-medium transition-colors ${
                      type === feedbackType
                        ? 'bg-purple-500 text-white'
                        : 'bg-white/5 text-gray-400 hover:bg-white/10'
                    }`}
                  >
                    {feedbackType === 'bug' && (t('bug_report') || 'Bug 报告')}
                    {feedbackType === 'feature' && (t('feature_request') || '功能建议')}
                    {feedbackType === 'suggestion' && (t('suggestion') || '改进建议')}
                    {feedbackType === 'other' && (t('other') || '其他')}
                  </button>
                ))}
              </div>
            </div>

            {/* 标题 */}
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-300 mb-2">
                {t('title') || '标题'} <span className="text-red-400">*</span>
              </label>
              <input
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder={t('enter_title') || '请输入标题'}
                className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white placeholder-gray-500 focus:outline-none focus:border-purple-500/50"
                maxLength={200}
              />
            </div>

            {/* 内容 */}
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-300 mb-2">
                {t('content') || '内容'} <span className="text-red-400">*</span>
              </label>
              <textarea
                value={content}
                onChange={(e) => setContent(e.target.value)}
                placeholder={t('enter_feedback_content') || '请详细描述您的问题或建议'}
                className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white placeholder-gray-500 focus:outline-none focus:border-purple-500/50 resize-none"
                rows={5}
                maxLength={2000}
              />
              <div className="text-xs text-gray-500 mt-1 text-right">
                {content.length}/2000
              </div>
            </div>

            {/* 联系方式 */}
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-300 mb-2">
                {t('contact') || '联系方式'} ({t('optional') || '可选'})
              </label>
              <input
                type="text"
                value={contact}
                onChange={(e) => setContact(e.target.value)}
                placeholder={t('enter_contact') || 'Telegram 用户名或邮箱'}
                className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white placeholder-gray-500 focus:outline-none focus:border-purple-500/50"
                maxLength={100}
              />
            </div>

            {/* 提交按钮 */}
            <button
              onClick={handleSubmit}
              disabled={feedbackMutation.isPending || !title.trim() || !content.trim()}
              className="w-full bg-gradient-to-r from-purple-500 to-pink-500 text-white py-3 rounded-xl font-medium flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {feedbackMutation.isPending ? (
                <>
                  <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  {t('submitting') || '提交中...'}
                </>
              ) : (
                <>
                  <Send size={18} />
                  {t('submit') || '提交'}
                </>
              )}
            </button>

            {/* 提示信息 */}
            <div className="mt-4 p-3 bg-blue-500/10 border border-blue-500/20 rounded-xl flex items-start gap-2">
              <AlertCircle size={16} className="text-blue-400 mt-0.5 flex-shrink-0" />
              <p className="text-xs text-blue-300">
                {t('feedback_tip') || '您的反馈对我们非常重要，我们会认真处理每一条反馈。'}
              </p>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}

