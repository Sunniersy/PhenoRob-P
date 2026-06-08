function isObject(value) {
  return value !== null && typeof value === "object" && !Array.isArray(value);
}

function formatDateMaybe(value) {
  if (typeof value !== "string") return null;
  const looksLikeIso = /^\d{4}-\d{2}-\d{2}T/.test(value);
  if (!looksLikeIso) return null;
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return null;
  return date.toLocaleString();
}

export function shortenText(value, head = 10, tail = 6) {
  const text = String(value || "");
  if (!text) return "-";
  if (text.length <= head + tail + 3) return text;
  return `${text.slice(0, head)}...${text.slice(-tail)}`;
}

export function formatBytes(value) {
  const bytes = Number(value);
  if (!Number.isFinite(bytes) || bytes < 0) return "-";
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  if (bytes < 1024 * 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  return `${(bytes / (1024 * 1024 * 1024)).toFixed(1)} GB`;
}

export function formatValue(value) {
  if (value === null || value === undefined || value === "") return "-";
  if (typeof value === "boolean") return value ? "是" : "否";
  if (typeof value === "number") return String(value);
  if (typeof value === "string") {
    return formatDateMaybe(value) || value;
  }
  if (Array.isArray(value)) {
    if (!value.length) return "无";
    const scalarItems = value.filter((item) => !isObject(item) && !Array.isArray(item));
    if (scalarItems.length === value.length) {
      return scalarItems.map((item) => formatValue(item)).join(" / ");
    }
    return `${value.length} 条记录`;
  }
  if (isObject(value)) return `${Object.keys(value).length} 个字段`;
  return String(value);
}

export function toSummaryRows(payload, maxRows = 6) {
  if (!isObject(payload)) return [];
  return Object.entries(payload)
    .filter(([, value]) => value !== null && value !== undefined && value !== "")
    .slice(0, maxRows)
    .map(([key, value]) => ({ key, value: formatValue(value) }));
}

export function parseCommaList(input) {
  return String(input || "")
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
}
