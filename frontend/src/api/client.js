const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000/api";

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: options.body instanceof FormData ? {} : { "Content-Type": "application/json" },
    ...options,
  });

  if (!response.ok) {
    let message = `Request failed with ${response.status}`;
    try {
      const payload = await response.json();
      message = payload.detail || message;
    } catch {
      message = response.statusText || message;
    }
    throw new Error(message);
  }

  if (response.status === 204) return null;
  const contentType = response.headers.get("content-type") || "";
  if (!contentType.includes("application/json")) return response;
  return response.json();
}

export const api = {
  baseUrl: API_BASE_URL,
  getDashboard: () => request("/dashboard"),
  getDatasets: () => request("/datasets"),
  getDataset: (id) => request(`/datasets/${id}`),
  uploadDataset: (file) => {
    const formData = new FormData();
    formData.append("file", file);
    return request("/datasets/upload", { method: "POST", body: formData });
  },
  deleteDataset: (id) => request(`/datasets/${id}`, { method: "DELETE" }),
  getPreview: (id, rows = 100, offset = 0) => request(`/datasets/${id}/preview?rows=${rows}&offset=${offset}`),
  getQuality: (id) => request(`/datasets/${id}/quality`),
  cleanDataset: (id, payload) =>
    request(`/datasets/${id}/clean`, { method: "POST", body: JSON.stringify(payload) }),
  detectOutliers: (id, payload) =>
    request(`/datasets/${id}/outliers`, { method: "POST", body: JSON.stringify(payload) }),
  getEda: (id) => request(`/datasets/${id}/eda`),
  getVisualizations: (id) => request(`/datasets/${id}/visualizations`),
  createVisualization: (id, payload) =>
    request(`/datasets/${id}/visualizations`, { method: "POST", body: JSON.stringify(payload) }),
  transformDataset: (id, payload) =>
    request(`/datasets/${id}/transform`, { method: "POST", body: JSON.stringify(payload) }),
  getInsights: (id) => request(`/datasets/${id}/insights`),
  reportUrl: (id, format = "pdf", type = "full") =>
    `${API_BASE_URL}/datasets/${id}/reports?format=${format}&type=${type}`,
  cleanedCsvUrl: (id) => `${API_BASE_URL}/datasets/${id}/reports/cleaned-csv`,
};
