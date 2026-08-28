import React, { useEffect, useState } from "react";
import { Modal, Alert, Form, Select, Space } from "antd";
import { SyncOutlined, SkinOutlined } from "@ant-design/icons";
import { fetchReportTemplates } from "../../../entities/report/api/reportApi";
import { formatTemplateOptions, ReportTemplateItem } from "../../../entities/report/model/templates";

interface ResumeTaskModalProps {
  open: boolean;
  loading: boolean;
  onCancel: () => void;
  onConfirm: (selectedTemplate?: string) => void;
}

export const ResumeTaskModal: React.FC<ResumeTaskModalProps> = ({
  open,
  loading,
  onCancel,
  onConfirm,
}) => {
  const [templates, setTemplates] = useState<ReportTemplateItem[]>([]);
  const [loadingTemplates, setLoadingTemplates] = useState(false);
  const [selectedTemplate, setSelectedTemplate] = useState("auto");

  useEffect(() => {
    if (open) {
      setSelectedTemplate("auto");
      setLoadingTemplates(true);
      fetchReportTemplates()
        .then((list) => setTemplates(list))
        .catch(() => {})
        .finally(() => setLoadingTemplates(false));
    }
  }, [open]);

  const handleOk = () => {
    onConfirm(selectedTemplate !== "auto" ? selectedTemplate : undefined);
  };

  const templateOptions = formatTemplateOptions(templates, true);

  return (
    <Modal
      title={
        <Space>
          <SyncOutlined />
          <span>幂等断点续跑 / 重试分析</span>
        </Space>
      }
      open={open}
      onCancel={onCancel}
      onOk={handleOk}
      confirmLoading={loading}
      okText="立即续跑"
      cancelText="取消"
      destroyOnClose
      width={460}
    >
      <div style={{ marginTop: 12 }}>
        <Alert
          type="info"
          showIcon
          message="零浪费 Token 细粒度产物复用"
          description="系统已自动跳过消息拉取与清洗，并直接复用本次任务中已有非空产物的子分析（如已生成的话题/画像），仅对失败或未完成的子任务向大模型发起补充请求。"
          style={{ marginBottom: 16 }}
        />

        <Form layout="vertical">
          <Form.Item
            label={
              <Space>
                <SkinOutlined style={{ color: "#722ed1" }} />
                <span>视觉主题模板 (选填)</span>
              </Space>
            }
            extra="续跑生成报告时可切换报告排版视觉模板"
          >
            <Select
              value={selectedTemplate}
              onChange={setSelectedTemplate}
              loading={loadingTemplates}
              options={templateOptions}
            />
          </Form.Item>
        </Form>
      </div>
    </Modal>
  );
};
