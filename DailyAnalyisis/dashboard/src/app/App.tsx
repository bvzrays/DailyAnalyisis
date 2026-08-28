import React, { useEffect, useState } from "react";
import { Alert, Button, Card, ConfigProvider, Input, Space, Spin, Tabs, Typography, message, theme } from "antd";
import {
  DashboardOutlined,
  ApartmentOutlined,
  ExperimentOutlined,
  FolderOpenOutlined,
  FileTextOutlined,
  SettingOutlined,
} from "@ant-design/icons";
import { subscribeSSE } from "../shared/api/bridge";
import { useTheme } from "../shared/lib/useTheme";
import { HeaderBar } from "../widgets/header-bar/HeaderBar";
import { TraceDrawer } from "../widgets/trace-drawer/TraceDrawer";
import { TriggerTaskModal } from "../features/trigger-task/ui/TriggerTaskModal";
import { useTriggerTask } from "../features/trigger-task/model/useTriggerTask";
import { OverviewPage } from "../pages/overview/ui/OverviewPage";
import { useOverviewViewModel } from "../pages/overview/model/useOverviewViewModel";
import { TracesPage } from "../pages/traces/ui/TracesPage";
import { useTracesViewModel } from "../pages/traces/model/useTracesViewModel";
import { ContextInsightPage } from "../pages/context-insight/ui/ContextInsightPage";
import { useContextInsightViewModel } from "../pages/context-insight/model/useContextInsightViewModel";
import { ReportsPage } from "../pages/reports/ui/ReportsPage";
import { useReportsViewModel } from "../pages/reports/model/useReportsViewModel";
import { LogsPage } from "../pages/logs/ui/LogsPage";
import { useLogsViewModel } from "../pages/logs/model/useLogsViewModel";
import { ConfigPage } from "../pages/config/ui/ConfigPage";
import { useConfigViewModel } from "../pages/config/model/useConfigViewModel";

import { invalidateTraceCache } from "../entities/trace/api/traceApi";
import { invalidateGroupsCache } from "../entities/group/api/groupApi";
import { ActiveTask } from "../entities/task/model/types";
import {
  fetchWebUIAuthStatus,
  loginWebUI,
  setupWebUIPassword,
} from "../entities/config/api/configApi";

const TASK_PROGRESS_EVENTS = new Set(["task_started", "task_progress"]);
const TASK_TERMINAL_EVENTS = new Set([
  "task_finished",
  "task_canceled",
  "task_timed_out",
]);

const DashboardApp: React.FC = () => {
  const { isDark } = useTheme();
  const [activeTab, setActiveTab] = useState("overview");
  const [selectedTraceId, setSelectedTraceId] = useState<string | null>(null);

  // ViewModels
  const overviewVM = useOverviewViewModel();
  const tracesVM = useTracesViewModel();
  const contextInsightVM = useContextInsightViewModel();
  const reportsVM = useReportsViewModel();
  const logsVM = useLogsViewModel(activeTab === "logs");
  const configVM = useConfigViewModel(() => {
    handleRefreshAll();
  });

  const handleRefreshAll = () => {
    // 显式清理前端冷数据缓存，确保强制刷新时数据 100% 同步
    invalidateTraceCache();
    invalidateGroupsCache();
    overviewVM.refresh();
    tracesVM.refresh();
    contextInsightVM.refresh();
    reportsVM.refresh();
    logsVM.refresh();
  };

  const triggerVM = useTriggerTask(tracesVM.groups, () => {
    invalidateGroupsCache();
    overviewVM.refresh();
    tracesVM.refresh();
  });

  // 当 activeTab 切换时，自动将选中的 Tab 元素平滑居中滚动至可视区域中央（防止移动端右侧 Tab 溢出不可见）
  useEffect(() => {
    const timer = setTimeout(() => {
      const activeTabEl = document.querySelector<HTMLElement>(
        `.ant-tabs-tab-active, [data-node-key="${activeTab}"]`
      );
      if (activeTabEl && typeof activeTabEl.scrollIntoView === "function") {
        activeTabEl.scrollIntoView({
          behavior: "smooth",
          inline: "center",
          block: "nearest",
        });
      }
    }, 60);
    return () => clearTimeout(timer);
  }, [activeTab]);

  // SSE 实时事件订阅：接收到后端任务状态变更时精准失效相关缓存
  useEffect(() => {
    const unsubscribe = subscribeSSE({
      onMessage: (eventPayload: unknown) => {
        if (!eventPayload || typeof eventPayload !== "object") return;
        const realtimeEvent = eventPayload as {
          event?: string;
          data?: Partial<ActiveTask> & { task_id?: string };
        };
        const eventName = realtimeEvent.event || "";
        if (!TASK_PROGRESS_EVENTS.has(eventName) && !TASK_TERMINAL_EVENTS.has(eventName)) {
          return;
        }

        const taskId = realtimeEvent.data?.task_id;
        if (taskId) invalidateTraceCache(taskId);

        if (TASK_PROGRESS_EVENTS.has(eventName)) {
          overviewVM.upsertActiveTask(realtimeEvent.data as ActiveTask);
          return;
        }

        if (taskId) overviewVM.removeActiveTask(taskId);
        invalidateGroupsCache();
        overviewVM.refresh(true);
        tracesVM.refresh(true);
        contextInsightVM.refresh(true);
        reportsVM.refresh(true);
      },
    });

    return () => {
      if (unsubscribe) unsubscribe();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleViewTrace = (traceId: string) => {
    setSelectedTraceId(traceId);
  };

  const tabItems = [
    {
      key: "overview",
      label: (
        <span>
          <DashboardOutlined /> 运行总览
        </span>
      ),
      children: (
        <OverviewPage
          viewModel={overviewVM}
          onOpenTrigger={triggerVM.handleOpen}
          onViewTrace={handleViewTrace}
        />
      ),
    },
    {
      key: "traces",
      label: (
        <span>
          <ApartmentOutlined /> 分析记录
        </span>
      ),
      children: (
        <TracesPage
          viewModel={tracesVM}
          onViewTrace={handleViewTrace}
        />
      ),
    },
    {
      key: "context",
      label: (
        <span>
          <ExperimentOutlined /> 统计与消耗
        </span>
      ),
      children: (
        <ContextInsightPage
          viewModel={contextInsightVM}
          onViewTrace={handleViewTrace}
        />
      ),
    },
    {
      key: "reports",
      label: (
        <span>
          <FolderOpenOutlined /> 历史报告
        </span>
      ),
      children: (
        <ReportsPage viewModel={reportsVM} onViewTrace={handleViewTrace} />
      ),
    },
    {
      key: "logs",
      label: (
        <span>
          <FileTextOutlined /> 运行日志
        </span>
      ),
      children: (
        <LogsPage viewModel={logsVM} onViewTrace={handleViewTrace} />
      ),
    },
    {
      key: "config",
      label: (
        <span>
          <SettingOutlined /> 配置中心
        </span>
      ),
      children: <ConfigPage viewModel={configVM} />,
    },
  ];

  return (
    <ConfigProvider
      theme={{
        algorithm: isDark ? theme.darkAlgorithm : theme.defaultAlgorithm,
        token: {
          colorPrimary: "#1677ff",
          borderRadius: 4,
          fontFamily:
            "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', sans-serif",
          fontFamilyCode:
            "'JetBrains Mono', 'Fira Code', ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', monospace",
        },
      }}
    >
      <div
        style={{
          minHeight: "100vh",
          background: isDark ? "#000000" : "#f5f5f5",
          padding: 12,
          color: isDark ? "#ffffff" : "#000000",
          fontFamily:
            "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', sans-serif",
        }}
      >
        {/* 顶部 HeaderBar 微件 */}
        <HeaderBar
          isDark={isDark}
          onRefresh={handleRefreshAll}
          onOpenTrigger={triggerVM.handleOpen}
          loading={overviewVM.loading}
        />

        {/* 核心 Tab 导航与页面路由 */}
        <Tabs
          activeKey={activeTab}
          onChange={(key) => {
            setActiveTab(key);
            if (key === "overview") overviewVM.refresh();
            else if (key === "traces") tracesVM.refresh();
            else if (key === "context") contextInsightVM.refresh();
            else if (key === "reports") reportsVM.refresh();
            else if (key === "logs") logsVM.refresh();
          }}
          items={tabItems}
          type="card"
          size="small"
        />

        {/* 触发任务模态框 (Feature) */}
        <TriggerTaskModal
          open={triggerVM.open}
          groupId={triggerVM.groupId}
          groupName={triggerVM.groupName}
          platform={triggerVM.platform}
          submitting={triggerVM.submitting}
          connectedPlatforms={triggerVM.connectedPlatforms}
          loadingPlatforms={triggerVM.loadingPlatforms}
          onGroupIdChange={triggerVM.setGroupId}
          onGroupNameChange={triggerVM.setGroupName}
          onPlatformChange={triggerVM.setPlatform}
          onClose={triggerVM.handleClose}
          onSubmit={triggerVM.handleSubmit}
        />

        {/* 链路追溯抽屉 (Widget) */}
        <TraceDrawer
          traceId={selectedTraceId}
          open={!!selectedTraceId}
          onClose={() => setSelectedTraceId(null)}
        />
      </div>
    </ConfigProvider>
  );
};

interface WebUIAuthPageProps {
  configured: boolean;
  onAuthenticated: () => void;
}

const WebUIAuthPage: React.FC<WebUIAuthPageProps> = ({
  configured,
  onAuthenticated,
}) => {
  const [password, setPassword] = useState("");
  const [confirmation, setConfirmation] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async () => {
    setSubmitting(true);
    try {
      if (configured) {
        await loginWebUI(password);
        message.success("WebUI 登录成功");
      } else {
        await setupWebUIPassword(password, confirmation);
        message.success("WebUI 密码设置成功");
      }
      onAuthenticated();
    } catch (error) {
      message.error(error instanceof Error ? error.message : "认证请求失败");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div
      style={{
        minHeight: "100vh",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: 20,
        background: "#f5f7fb",
      }}
    >
      <Card style={{ width: "100%", maxWidth: 420 }}>
        <Space direction="vertical" size="middle" style={{ width: "100%" }}>
          <div>
            <Typography.Title level={3} style={{ margin: 0 }}>
              DailyAnalyisis WebUI
            </Typography.Title>
            <Typography.Paragraph type="secondary" style={{ margin: "8px 0 0" }}>
              {configured
                ? "请输入 WebUI 密码后继续。"
                : "这是第一次进入 WebUI，请先设置一个访问密码。"}
            </Typography.Paragraph>
          </div>
          {!configured && (
            <Alert
              type="warning"
              showIcon
              message="公网访问安全提示"
              description="密码只保存为不可逆摘要。请使用至少 8 个字符，并建议通过 HTTPS 暴露 WebUI。"
            />
          )}
          <Input.Password
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            onPressEnter={() => {
              if (configured) void handleSubmit();
            }}
            placeholder={configured ? "WebUI 访问密码" : "设置 WebUI 访问密码"}
            autoFocus
          />
          {!configured && (
            <Input.Password
              value={confirmation}
              onChange={(event) => setConfirmation(event.target.value)}
              onPressEnter={() => void handleSubmit()}
              placeholder="再次输入密码"
            />
          )}
          <Button
            type="primary"
            block
            loading={submitting}
            onClick={() => void handleSubmit()}
          >
            {configured ? "登录 WebUI" : "设置密码并进入"}
          </Button>
        </Space>
      </Card>
    </div>
  );
};

export const App: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [authStatus, setAuthStatus] = useState<{
    configured: boolean;
    authenticated: boolean;
  } | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchWebUIAuthStatus()
      .then((status) => setAuthStatus(status))
      .catch((reason: unknown) => {
        setError(reason instanceof Error ? reason.message : "无法连接 WebUI 认证服务");
      })
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div style={{ minHeight: "100vh", display: "grid", placeItems: "center" }}>
        <Spin tip="正在检查 WebUI 安全状态" />
      </div>
    );
  }

  if (error || !authStatus) {
    return (
      <div style={{ maxWidth: 520, margin: "15vh auto", padding: 20 }}>
        <Alert
          type="error"
          showIcon
          message="WebUI 无法启动"
          description={error || "认证服务没有返回有效状态，请检查 GsCore 与插件是否已重载。"}
        />
      </div>
    );
  }

  if (!authStatus.authenticated) {
    return (
      <WebUIAuthPage
        configured={authStatus.configured}
        onAuthenticated={() =>
          setAuthStatus({ ...authStatus, configured: true, authenticated: true })
        }
      />
    );
  }

  return <DashboardApp />;
};
