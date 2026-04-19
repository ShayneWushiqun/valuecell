const isPrimitive = (value: unknown): value is string | number | boolean =>
  ["string", "number", "boolean"].includes(typeof value);

const prettyKey = (value: string) =>
  value
    .replace(/_/g, " ")
    .replace(/\b\w/g, (char) => char.toUpperCase());

const toInlineText = (value: unknown): string => {
  if (value == null) return "";
  if (isPrimitive(value)) return String(value);
  if (Array.isArray(value)) {
    return value.map((item) => toInlineText(item)).filter(Boolean).join("； ");
  }
  if (typeof value === "object") {
    const parts = Object.entries(value as Record<string, unknown>)
      .map(([key, item]) => {
        const rendered = toInlineText(item);
        return rendered ? `${prettyKey(key)}: ${rendered}` : "";
      })
      .filter(Boolean);
    return parts.join("； ");
  }
  return String(value);
};

const toMarkdown = (value: unknown, depth = 0): string => {
  if (value == null) return "";
  if (typeof value === "string") return value;
  if (typeof value === "number" || typeof value === "boolean") {
    return String(value);
  }
  if (Array.isArray(value)) {
    return value
      .map((item) => {
        if (isPrimitive(item)) {
          return `- ${String(item)}`;
        }
        const inline = toInlineText(item);
        return inline ? `- ${inline}` : "";
      })
      .filter(Boolean)
      .join("\n");
  }
  if (typeof value === "object") {
    return Object.entries(value as Record<string, unknown>)
      .map(([key, item]) => {
        const titlePrefix = `${"#".repeat(Math.min(depth + 3, 6))} ${prettyKey(key)}`;
        if (isPrimitive(item)) {
          return `- **${prettyKey(key)}**: ${String(item)}`;
        }
        if (Array.isArray(item)) {
          const rendered = toMarkdown(item, depth + 1);
          return rendered ? `${titlePrefix}\n${rendered}` : "";
        }
        const rendered = toMarkdown(item, depth + 1);
        return rendered ? `${titlePrefix}\n${rendered}` : "";
      })
      .filter(Boolean)
      .join("\n\n");
  }
  return String(value);
};

export const normalizeReportContent = (value: unknown): string => {
  if (typeof value === "string") return value;
  return toMarkdown(value);
};
