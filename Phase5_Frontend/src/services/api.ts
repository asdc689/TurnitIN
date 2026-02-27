import axios, { AxiosError } from "axios";
import type {
  TokenResponse,
  MessageResponse,
  UploadResponse,
  SubmissionDetail,
  HistoryResponse,
} from "../types"

// ── Base Config ───────────────────────────────────────────────────────────────

// This points directly to your local FastAPI server
const API_BASE = "http://localhost:8000/api/v1";

// We create a custom Axios instance instead of using the global axios object.
// This allows us to set default headers and interceptors just for our API calls.
const api = axios.create({
  baseURL: API_BASE,
  headers: {
    "Content-Type": "application/json",
  },
});

// ── Request Interceptor — attach token ────────────────────────────────────────

// This acts like a toll booth for every OUTGOING request.
// Before the request leaves the browser, it checks if we have a saved login token.
// If we do, it automatically attaches it to the 'Authorization' header.
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("access_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// ── Response Interceptor — handle 401 ────────────────────────────────────────

// This acts like a toll booth for every INCOMING response.
// If your FastAPI backend rejects a request because the token is expired (401 Unauthorized),
// this automatically catches it, wipes the dead tokens, and kicks the user to the login page.
api.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (error.response?.status === 401) {
      // Clear everything so we don't get stuck in an endless login loop
      localStorage.removeItem("access_token");
      localStorage.removeItem("refresh_token");
      localStorage.removeItem("user");
      window.location.href = "/login";
    }
    return Promise.reject(error);
  }
);

// ── Helper ────────────────────────────────────────────────────────────────────

// FastAPI returns errors in a very specific format (under the 'detail' key).
// This helper safely digs into the error response and extracts the human-readable string,
// handling both standard errors and Pydantic validation arrays.
export const getErrorMessage = (error: unknown): string => {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail;
    if (typeof detail === "string") return detail;
    if (Array.isArray(detail)) return detail[0]?.msg || "Validation error";
  }
  return "An unexpected error occurred";
};

// ── Auth ──────────────────────────────────────────────────────────────────────

export const authApi = {
  // Standard JSON POST request for creating a new user
  register: async (email: string, full_name: string, password: string): Promise<MessageResponse> => {
    const res = await api.post("/auth/register", { email, full_name, password });
    return res.data;
  },

  login: async (email: string, password: string): Promise<TokenResponse> => {
    const res = await api.post("/auth/login", { email, password });
    const data: TokenResponse = res.data;
    localStorage.setItem("access_token", data.access_token);
    localStorage.setItem("refresh_token", data.refresh_token);
    localStorage.setItem("user", JSON.stringify(data.user));
    return data;
  },

  // Wipes the local storage and forces the browser back to the login screen
  logout: () => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    localStorage.removeItem("user");
    window.location.href = "/login";
  },

  // Fetches the current user's profile data using the attached JWT
  getMe: async () => {
    const res = await api.get("/auth/me");
    return res.data;
  },
};

// ── Submissions ───────────────────────────────────────────────────────────────

export const submissionsApi = {
  // We use FormData here instead of standard JSON because we are transmitting 
  // actual files across the network (multipart/form-data).
  upload: async (
    file1: File,
    file2: File,
    mode: "text" | "code",
    langOverride?: string
  ): Promise<UploadResponse> => {
    const formData = new FormData();
    formData.append("file1", file1);
    formData.append("file2", file2);
    formData.append("mode", mode);
    if (langOverride) formData.append("lang_override", langOverride);

    // Let Axios automatically set the correct boundary headers for the file upload
    const res = await api.post("/submissions/upload", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });
    return res.data;
  },

  // Standard GET request to check if Celery has finished processing
  getStatus: async (id: number) => {
    const res = await api.get(`/submissions/${id}/status`);
    return res.data;
  },

  // Fetches the final Jaccard/AST similarity scores
  getReport: async (id: number): Promise<SubmissionDetail> => {
    const res = await api.get(`/submissions/${id}/report`);
    return res.data;
  },

  // Fetches past submissions, defaulting to page 1 with 10 items
  getHistory: async (page = 1, pageSize = 10): Promise<HistoryResponse> => {
    const res = await api.get("/submissions/history", {
      params: { page, page_size: pageSize },
    });
    return res.data;
  },

  // Deletes a specific submission from the database
  delete: async (id: number): Promise<void> => {
    await api.delete(`/submissions/${id}`);
  },
};

export default api;

// ── Profile ───────────────────────────────────────────────────────────────────

export const profileApi = {
  update: async (fullName: string) => {
    const res = await api.put("/auth/profile", { full_name: fullName });
    const currentUser = JSON.parse(localStorage.getItem("user") || "{}");
    localStorage.setItem("user", JSON.stringify({ ...currentUser, full_name: fullName }));
    return res.data;
  },

  changePassword: async (currentPassword: string, newPassword: string) => {
    const res = await api.put("/auth/change-password", {
      current_password: currentPassword,
      new_password: newPassword,
    });
    return res.data;
  },
};