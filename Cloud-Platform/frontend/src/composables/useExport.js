import { ref } from "vue";
import { useToast } from "./useToast";

export function useExport() {
  const { success: showSuccess, error: showError } = useToast();
  const exporting = ref(false);

  // 导出为JSON
  function exportAsJSON(data, filename = "export.json") {
    exporting.value = true;
    try {
      const jsonStr = JSON.stringify(data, null, 2);
      const blob = new Blob([jsonStr], { type: "application/json" });
      downloadBlob(blob, filename);
      showSuccess("导出成功", `已导出 ${filename}`);
    } catch (err) {
      showError("导出失败", err.message);
    } finally {
      exporting.value = false;
    }
  }

  // 导出为CSV
  function exportAsCSV(data, filename = "export.csv", columns = null) {
    exporting.value = true;
    try {
      if (!data.length) {
        showError("导出失败", "没有数据可导出");
        return;
      }

      // 获取列名
      const headers = columns || Object.keys(data[0]);

      // 生成CSV内容
      const csvRows = [];
      csvRows.push(headers.join(","));

      data.forEach((row) => {
        const values = headers.map((header) => {
          const value = row[header];
          // 处理包含逗号或引号的值
          if (typeof value === "string" && (value.includes(",") || value.includes('"'))) {
            return `"${value.replace(/"/g, '""')}"`;
          }
          return value ?? "";
        });
        csvRows.push(values.join(","));
      });

      const csvStr = csvRows.join("\n");
      const blob = new Blob(["﻿" + csvStr], { type: "text/csv;charset=utf-8" });
      downloadBlob(blob, filename);
      showSuccess("导出成功", `已导出 ${filename}`);
    } catch (err) {
      showError("导出失败", err.message);
    } finally {
      exporting.value = false;
    }
  }

  // 导出为Excel (简单实现，使用CSV格式)
  function exportAsExcel(data, filename = "export.xlsx", columns = null) {
    // 实际项目中可以使用 xlsx 库
    // 这里简单实现为CSV格式
    exportAsCSV(data, filename.replace(".xlsx", ".csv"), columns);
  }

  // 下载Blob
  function downloadBlob(blob, filename) {
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }

  // 导出任务报告
  function exportTaskReport(tasks) {
    const columns = [
      "id",
      "name",
      "task_type",
      "robot_code",
      "status",
      "progress",
      "created_at",
      "updated_at"
    ];

    const data = tasks.map((task) => ({
      id: task.id,
      name: task.name,
      task_type: task.task_type,
      robot_code: task.robot_code,
      status: task.status,
      progress: task.progress,
      created_at: task.created_at,
      updated_at: task.updated_at
    }));

    exportAsCSV(data, `任务报告_${new Date().toISOString().slice(0, 10)}.csv`, columns);
  }

  // 导出机器人状态
  function exportRobotStatus(robots) {
    const columns = [
      "id",
      "robot_code",
      "name",
      "status",
      "protocol",
      "last_heartbeat_at",
      "created_at"
    ];

    const data = robots.map((robot) => ({
      id: robot.id,
      robot_code: robot.robot_code,
      name: robot.name,
      status: robot.status,
      protocol: robot.protocol,
      last_heartbeat_at: robot.last_heartbeat_at,
      created_at: robot.created_at
    }));

    exportAsCSV(data, `机器人状态_${new Date().toISOString().slice(0, 10)}.csv`, columns);
  }

  // 导出资产列表
  function exportAssetList(assets) {
    const columns = [
      "id",
      "file_name",
      "asset_type",
      "size_bytes",
      "task_id",
      "robot_id",
      "created_at"
    ];

    const data = assets.map((asset) => ({
      id: asset.id,
      file_name: asset.file_name,
      asset_type: asset.asset_type,
      size_bytes: asset.size_bytes,
      task_id: asset.task_id,
      robot_id: asset.robot_id,
      created_at: asset.created_at
    }));

    exportAsCSV(data, `资产列表_${new Date().toISOString().slice(0, 10)}.csv`, columns);
  }

  // 导出分析结果
  function exportAnalysisResults(results) {
    const columns = [
      "id",
      "task_id",
      "summary",
      "status",
      "created_at"
    ];

    const data = results.map((result) => ({
      id: result.id,
      task_id: result.task_id,
      summary: result.summary,
      status: result.status,
      created_at: result.created_at
    }));

    exportAsCSV(data, `分析结果_${new Date().toISOString().slice(0, 10)}.csv`, columns);
  }

  return {
    exporting,
    exportAsJSON,
    exportAsCSV,
    exportAsExcel,
    exportTaskReport,
    exportRobotStatus,
    exportAssetList,
    exportAnalysisResults
  };
}
