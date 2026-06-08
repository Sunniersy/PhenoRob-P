<script setup>
import { ref, onMounted, watch, computed } from "vue";

const props = defineProps({
  title: { type: String, required: true },
  subtitle: { type: String, default: "" },
  data: { type: Array, default: () => [] },
  labels: { type: Array, default: () => [] },
  type: { type: String, default: "bar" }, // bar, line, pie, doughnut
  colors: { type: Array, default: () => ["var(--brand)", "var(--info)", "var(--success)", "var(--warning)", "var(--danger)"] },
  height: { type: Number, default: 200 },
  loading: { type: Boolean, default: false }
});

const canvasRef = ref(null);

// 计算图表数据
const chartData = computed(() => {
  if (!props.data.length) return null;

  if (props.type === "pie" || props.type === "doughnut") {
    return {
      labels: props.labels,
      datasets: [{
        data: props.data,
        backgroundColor: props.colors,
        borderWidth: 0
      }]
    };
  }

  return {
    labels: props.labels,
    datasets: [{
      data: props.data,
      backgroundColor: props.colors[0],
      borderColor: props.colors[0],
      borderWidth: 2,
      fill: props.type === "line"
    }]
  };
});

// 绘制简单图表
function drawChart() {
  if (!canvasRef.value || !chartData.value) return;

  const canvas = canvasRef.value;
  const ctx = canvas.getContext("2d");
  const { width, height } = canvas;
  const { data, labels } = chartData.value.datasets[0];
  const maxValue = Math.max(...data);
  const padding = 40;
  const chartWidth = width - padding * 2;
  const chartHeight = height - padding * 2;

  // 清空画布
  ctx.clearRect(0, 0, width, height);

  // 绘制背景
  ctx.fillStyle = "transparent";
  ctx.fillRect(0, 0, width, height);

  if (props.type === "bar") {
    // 绘制柱状图
    const barWidth = chartWidth / data.length * 0.8;
    const barGap = chartWidth / data.length * 0.2;

    data.forEach((value, index) => {
      const x = padding + (index * (barWidth + barGap)) + barGap / 2;
      const barHeight = (value / maxValue) * chartHeight;
      const y = height - padding - barHeight;

      // 绘制柱子
      ctx.fillStyle = props.colors[index % props.colors.length];
      ctx.fillRect(x, y, barWidth, barHeight);

      // 绘制标签
      ctx.fillStyle = "var(--text-secondary)";
      ctx.font = "12px Inter";
      ctx.textAlign = "center";
      ctx.fillText(labels[index] || "", x + barWidth / 2, height - 10);

      // 绘制数值
      ctx.fillStyle = "var(--text-primary)";
      ctx.font = "bold 12px Inter";
      ctx.fillText(value.toString(), x + barWidth / 2, y - 5);
    });
  } else if (props.type === "line") {
    // 绘制折线图
    ctx.beginPath();
    ctx.strokeStyle = props.colors[0];
    ctx.lineWidth = 2;

    data.forEach((value, index) => {
      const x = padding + (index * chartWidth / (data.length - 1));
      const y = height - padding - (value / maxValue) * chartHeight;

      if (index === 0) {
        ctx.moveTo(x, y);
      } else {
        ctx.lineTo(x, y);
      }

      // 绘制点
      ctx.fillStyle = props.colors[0];
      ctx.beginPath();
      ctx.arc(x, y, 4, 0, Math.PI * 2);
      ctx.fill();

      // 绘制标签
      ctx.fillStyle = "var(--text-secondary)";
      ctx.font = "12px Inter";
      ctx.textAlign = "center";
      ctx.fillText(labels[index] || "", x, height - 10);

      // 绘制数值
      ctx.fillStyle = "var(--text-primary)";
      ctx.font = "bold 12px Inter";
      ctx.fillText(value.toString(), x, y - 10);
    });

    ctx.stroke();
  } else if (props.type === "pie" || props.type === "doughnut") {
    // 绘制饼图/环形图
    const total = data.reduce((sum, val) => sum + val, 0);
    let startAngle = -Math.PI / 2;
    const centerX = width / 2;
    const centerY = height / 2;
    const radius = Math.min(chartWidth, chartHeight) / 2;
    const innerRadius = props.type === "doughnut" ? radius * 0.6 : 0;

    data.forEach((value, index) => {
      const sliceAngle = (value / total) * Math.PI * 2;
      const endAngle = startAngle + sliceAngle;

      // 绘制扇形
      ctx.beginPath();
      ctx.moveTo(centerX, centerY);
      ctx.arc(centerX, centerY, radius, startAngle, endAngle);
      ctx.closePath();
      ctx.fillStyle = props.colors[index % props.colors.length];
      ctx.fill();

      // 绘制内圆 (环形图)
      if (innerRadius > 0) {
        ctx.beginPath();
        ctx.arc(centerX, centerY, innerRadius, 0, Math.PI * 2);
        ctx.fillStyle = "var(--bg-surface-solid)";
        ctx.fill();
      }

      // 绘制标签
      const labelAngle = startAngle + sliceAngle / 2;
      const labelX = centerX + Math.cos(labelAngle) * (radius * 0.7);
      const labelY = centerY + Math.sin(labelAngle) * (radius * 0.7);

      ctx.fillStyle = "#ffffff";
      ctx.font = "bold 12px Inter";
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      ctx.fillText(labels[index] || "", labelX, labelY);

      startAngle = endAngle;
    });
  }
}

onMounted(() => {
  drawChart();
});

watch(() => props.data, () => {
  drawChart();
}, { deep: true });

watch(() => props.type, () => {
  drawChart();
});
</script>

<template>
  <div class="chart-card glass-card">
    <div class="section-head">
      <div>
        <div class="eyebrow">Chart</div>
        <h3>{{ title }}</h3>
        <p v-if="subtitle" class="page-subtitle">{{ subtitle }}</p>
      </div>
    </div>

    <!-- 加载状态 -->
    <div v-if="loading" class="chart-loading">
      <div class="chart-loading-spinner"></div>
    </div>

    <!-- 图表 -->
    <canvas
      v-else
      ref="canvasRef"
      :width="400"
      :height="height"
      class="chart-canvas"
    ></canvas>
  </div>
</template>

<style scoped>
.chart-card {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.chart-canvas {
  width: 100%;
  height: auto;
  max-height: v-bind(height + "px");
}

.chart-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  height: v-bind(height + "px");
}

.chart-loading-spinner {
  width: 32px;
  height: 32px;
  border: 3px solid var(--border-soft);
  border-top-color: var(--brand);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
</style>
