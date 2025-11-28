import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  Table,
  Button,
  Space,
  Tag,
  Modal,
  Form,
  Input,
  Select,
  message,
  Popconfirm,
  Switch,
} from 'antd'
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  EyeOutlined,
  CopyOutlined,
} from '@ant-design/icons'
import { telegramApi } from '../utils/api'
import type { ColumnsType } from 'antd/es/table'
import dayjs from 'dayjs'

const { TextArea } = Input
const { Option } = Select

export default function MessageTemplateManagement() {
  const [modalVisible, setModalVisible] = useState(false)
  const [previewModalVisible, setPreviewModalVisible] = useState(false)
  const [editingTemplate, setEditingTemplate] = useState<any>(null)
  const [form] = Form.useForm()
  const [previewForm] = Form.useForm()
  const queryClient = useQueryClient()

  const { data, isLoading } = useQuery({
    queryKey: ['message-templates'],
    queryFn: () => telegramApi.getTemplates().then(res => res.data),
  })

  const createMutation = useMutation({
    mutationFn: (data: any) => telegramApi.createTemplate(data),
    onSuccess: () => {
      message.success('模板創建成功')
      setModalVisible(false)
      form.resetFields()
      queryClient.invalidateQueries({ queryKey: ['message-templates'] })
    },
    onError: (error: any) => {
      message.error(error.response?.data?.detail || '創建失敗')
    },
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: any }) =>
      telegramApi.updateTemplate(id, data),
    onSuccess: () => {
      message.success('模板更新成功')
      setModalVisible(false)
      setEditingTemplate(null)
      form.resetFields()
      queryClient.invalidateQueries({ queryKey: ['message-templates'] })
    },
    onError: (error: any) => {
      message.error(error.response?.data?.detail || '更新失敗')
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (id: number) => telegramApi.deleteTemplate(id),
    onSuccess: () => {
      message.success('模板刪除成功')
      queryClient.invalidateQueries({ queryKey: ['message-templates'] })
    },
    onError: (error: any) => {
      message.error(error.response?.data?.detail || '刪除失敗')
    },
  })

  const renderMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: any }) =>
      telegramApi.renderTemplate(id, data),
    onSuccess: (response) => {
      const rendered = response.data.data.rendered_content
      previewForm.setFieldsValue({ preview_content: rendered })
      setPreviewModalVisible(true)
    },
    onError: (error: any) => {
      message.error(error.response?.data?.detail || '渲染失敗')
    },
  })

  const handleCreate = () => {
    setEditingTemplate(null)
    form.resetFields()
    setModalVisible(true)
  }

  const handleEdit = (template: any) => {
    setEditingTemplate(template)
    form.setFieldsValue({
      name: template.name,
      category: template.category,
      content: template.content,
      message_type: template.message_type,
      is_active: template.is_active,
    })
    setModalVisible(true)
  }

  const handleDelete = (id: number) => {
    deleteMutation.mutate(id)
  }

  const handlePreview = (template: any) => {
    previewForm.setFieldsValue({ template_id: template.id })
    setPreviewModalVisible(true)
  }

  const handleRender = () => {
    const templateId = previewForm.getFieldValue('template_id')
    const variables = previewForm.getFieldsValue()
    delete variables.template_id
    delete variables.preview_content
    
    // 提取變量值
    const varValues: any = {}
    Object.keys(variables).forEach(key => {
      if (key.startsWith('var_')) {
        varValues[key.replace('var_', '')] = variables[key]
      }
    })
    
    renderMutation.mutate({ id: templateId, data: { variables: varValues } })
  }

  const copyContent = (text: string) => {
    navigator.clipboard.writeText(text)
    message.success('內容已複製')
  }

  const columns: ColumnsType<any> = [
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
      width: 80,
    },
    {
      title: '模板名稱',
      dataIndex: 'name',
      key: 'name',
    },
    {
      title: '分類',
      dataIndex: 'category',
      key: 'category',
      render: (category) => category ? <Tag>{category}</Tag> : '-',
    },
    {
      title: '內容預覽',
      dataIndex: 'content',
      key: 'content',
      ellipsis: true,
      render: (text) => text ? text.substring(0, 50) + '...' : '-',
    },
    {
      title: '類型',
      dataIndex: 'message_type',
      key: 'message_type',
      width: 100,
    },
    {
      title: '使用次數',
      dataIndex: 'usage_count',
      key: 'usage_count',
      width: 100,
      sorter: (a, b) => (a.usage_count || 0) - (b.usage_count || 0),
    },
    {
      title: '狀態',
      dataIndex: 'is_active',
      key: 'is_active',
      width: 100,
      render: (isActive) => (
        <Tag color={isActive ? 'green' : 'red'}>
          {isActive ? '啟用' : '禁用'}
        </Tag>
      ),
    },
    {
      title: '更新時間',
      dataIndex: 'updated_at',
      key: 'updated_at',
      width: 180,
      render: (time) => time ? dayjs(time).format('YYYY-MM-DD HH:mm') : '-',
    },
    {
      title: '操作',
      key: 'action',
      width: 250,
      render: (_, record) => (
        <Space>
          <Button
            type="link"
            size="small"
            icon={<EyeOutlined />}
            onClick={() => handlePreview(record)}
          >
            預覽
          </Button>
          <Button
            type="link"
            size="small"
            icon={<EditOutlined />}
            onClick={() => handleEdit(record)}
          >
            編輯
          </Button>
          <Popconfirm
            title="確定要刪除這個模板嗎？"
            onConfirm={() => handleDelete(record.id)}
            okText="確定"
            cancelText="取消"
          >
            <Button
              type="link"
              size="small"
              danger
              icon={<DeleteOutlined />}
            >
              刪除
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ]

  return (
    <div>
      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between' }}>
        <h1>消息模板管理</h1>
        <Button type="primary" icon={<PlusOutlined />} onClick={handleCreate}>
          創建模板
        </Button>
      </div>

      <Table
        columns={columns}
        dataSource={data?.data?.templates || []}
        loading={isLoading}
        rowKey="id"
        pagination={{
          total: data?.data?.total || 0,
          pageSize: data?.data?.limit || 20,
        }}
      />

      {/* 創建/編輯模板模態框 */}
      <Modal
        title={editingTemplate ? '編輯模板' : '創建模板'}
        open={modalVisible}
        onCancel={() => {
          setModalVisible(false)
          setEditingTemplate(null)
          form.resetFields()
        }}
        onOk={() => form.submit()}
        confirmLoading={createMutation.isPending || updateMutation.isPending}
        width={800}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={(values) => {
            if (editingTemplate) {
              updateMutation.mutate({ id: editingTemplate.id, data: values })
            } else {
              createMutation.mutate(values)
            }
          }}
        >
          <Form.Item
            name="name"
            label="模板名稱"
            rules={[{ required: true, message: '請輸入模板名稱' }]}
          >
            <Input placeholder="例如：歡迎消息" />
          </Form.Item>
          <Form.Item
            name="category"
            label="分類"
          >
            <Select placeholder="選擇分類">
              <Option value="notification">通知</Option>
              <Option value="marketing">營銷</Option>
              <Option value="system">系統</Option>
              <Option value="welcome">歡迎</Option>
            </Select>
          </Form.Item>
          <Form.Item
            name="content"
            label="模板內容（支持變量，使用 {變量名} 格式）"
            rules={[{ required: true, message: '請輸入模板內容' }]}
          >
            <TextArea
              rows={8}
              placeholder="例如：歡迎 {username} 加入群組！您的 ID 是 {user_id}"
            />
          </Form.Item>
          <Form.Item
            name="message_type"
            label="消息類型"
            initialValue="text"
          >
            <Select>
              <Option value="text">文本</Option>
              <Option value="photo">圖片</Option>
              <Option value="video">視頻</Option>
            </Select>
          </Form.Item>
          {editingTemplate && (
            <Form.Item
              name="is_active"
              label="狀態"
              valuePropName="checked"
            >
              <Switch />
            </Form.Item>
          )}
        </Form>
      </Modal>

      {/* 預覽模態框 */}
      <Modal
        title="模板預覽"
        open={previewModalVisible}
        onCancel={() => {
          setPreviewModalVisible(false)
          previewForm.resetFields()
        }}
        footer={[
          <Button key="cancel" onClick={() => setPreviewModalVisible(false)}>
            關閉
          </Button>,
          <Button key="render" type="primary" onClick={handleRender} loading={renderMutation.isPending}>
            渲染
          </Button>,
        ]}
        width={800}
      >
        <Form form={previewForm} layout="vertical">
          <Form.Item name="template_id" hidden>
            <Input />
          </Form.Item>
          <Form.Item label="變量值（可選）">
            <Space direction="vertical" style={{ width: '100%' }}>
              <Input.Group compact>
                <Input
                  style={{ width: '30%' }}
                  placeholder="變量名"
                  disabled
                  value="username"
                />
                <Form.Item name="var_username" noStyle>
                  <Input style={{ width: '70%' }} placeholder="例如：張三" />
                </Form.Item>
              </Input.Group>
              <Input.Group compact>
                <Input
                  style={{ width: '30%' }}
                  placeholder="變量名"
                  disabled
                  value="user_id"
                />
                <Form.Item name="var_user_id" noStyle>
                  <Input style={{ width: '70%' }} placeholder="例如：123456789" />
                </Form.Item>
              </Input.Group>
            </Space>
          </Form.Item>
          <Form.Item label="渲染結果">
            <Form.Item name="preview_content" noStyle>
              <TextArea rows={6} readOnly />
            </Form.Item>
            <Button
              type="link"
              icon={<CopyOutlined />}
              onClick={() => {
                const content = previewForm.getFieldValue('preview_content')
                if (content) copyContent(content)
              }}
            >
              複製內容
            </Button>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

