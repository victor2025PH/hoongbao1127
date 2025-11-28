import { useState } from 'react'
import { useQuery, useMutation } from '@tanstack/react-query'
import { Table, Button, Modal, Form, Select, Input, message, Space, Tag } from 'antd'
import { DownloadOutlined, FileAddOutlined } from '@ant-design/icons'
import { reportApi } from '../utils/api'
import type { ColumnsType } from 'antd/es/table'

export default function ReportManagement() {
  const [generateModalVisible, setGenerateModalVisible] = useState(false)
  const [form] = Form.useForm()

  const { data, isLoading, refetch } = useQuery({
    queryKey: ['reports'],
    queryFn: () => reportApi.list().then(res => res.data),
  })

  const generateMutation = useMutation({
    mutationFn: (data: any) => reportApi.generate(data),
    onSuccess: () => {
      message.success('報表生成任務已創建')
      setGenerateModalVisible(false)
      form.resetFields()
      refetch()
    },
    onError: (error: any) => {
      message.error(error.response?.data?.detail || '生成失敗')
    },
  })

  const downloadReport = async (reportId: number, filename: string) => {
    try {
      const response = await reportApi.download(reportId)
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', filename)
      document.body.appendChild(link)
      link.click()
      link.remove()
      message.success('下載成功')
    } catch (error: any) {
      message.error('下載失敗')
    }
  }

  const columns: ColumnsType<any> = [
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
    },
    {
      title: '報表名稱',
      dataIndex: 'name',
      key: 'name',
    },
    {
      title: '類型',
      dataIndex: 'report_type',
      key: 'report_type',
    },
    {
      title: '格式',
      dataIndex: 'file_format',
      key: 'file_format',
      render: (format) => format.toUpperCase(),
    },
    {
      title: '狀態',
      dataIndex: 'status',
      key: 'status',
      render: (status) => {
        const colorMap: Record<string, string> = {
          completed: 'green',
          generating: 'blue',
          failed: 'red',
          pending: 'orange',
        }
        const textMap: Record<string, string> = {
          completed: '已完成',
          generating: '生成中',
          failed: '失敗',
          pending: '待處理',
        }
        return <Tag color={colorMap[status]}>{textMap[status] || status}</Tag>
      },
    },
    {
      title: '生成時間',
      dataIndex: 'generated_at',
      key: 'generated_at',
      render: (time) => time ? new Date(time).toLocaleString('zh-TW') : '-',
    },
    {
      title: '操作',
      key: 'action',
      render: (_, record) => (
        <Space>
          {record.status === 'completed' && record.download_url && (
            <Button
              type="link"
              icon={<DownloadOutlined />}
              onClick={() => downloadReport(record.id, `${record.name}.${record.file_format}`)}
            >
              下載
            </Button>
          )}
        </Space>
      ),
    },
  ]

  return (
    <div>
      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between' }}>
        <h1>報表管理</h1>
        <Button
          type="primary"
          icon={<FileAddOutlined />}
          onClick={() => setGenerateModalVisible(true)}
        >
          生成報表
        </Button>
      </div>

      <Table
        columns={columns}
        dataSource={data?.data?.reports || []}
        loading={isLoading}
        rowKey="id"
        pagination={{
          pageSize: data?.data?.limit || 20,
        }}
      />

      {/* 生成報表模態框 */}
      <Modal
        title="生成報表"
        open={generateModalVisible}
        onCancel={() => {
          setGenerateModalVisible(false)
          form.resetFields()
        }}
        onOk={() => form.submit()}
        confirmLoading={generateMutation.isPending}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={(values) => {
            generateMutation.mutate({
              report_type: values.report_type,
              name: values.name || `${values.report_type}_${new Date().toISOString().split('T')[0]}`,
              format: values.format,
            })
          }}
        >
          <Form.Item
            name="report_type"
            label="報表類型"
            rules={[{ required: true }]}
            initialValue="user"
          >
            <Select>
              <Select.Option value="user">用戶報表</Select.Option>
              <Select.Option value="transaction">交易報表</Select.Option>
              <Select.Option value="red_packet">紅包報表</Select.Option>
              <Select.Option value="group">群組報表</Select.Option>
            </Select>
          </Form.Item>
          <Form.Item
            name="name"
            label="報表名稱"
          >
            <Input placeholder="留空使用默認名稱" />
          </Form.Item>
          <Form.Item
            name="format"
            label="導出格式"
            rules={[{ required: true }]}
            initialValue="xlsx"
          >
            <Select>
              <Select.Option value="xlsx">Excel (.xlsx)</Select.Option>
              <Select.Option value="csv">CSV</Select.Option>
              <Select.Option value="json">JSON</Select.Option>
              <Select.Option value="pdf">PDF</Select.Option>
            </Select>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

