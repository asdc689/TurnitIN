// ── Auth Types ────────────────────────────────────────────────────────────────

export interface User {
  id: number;
  email: string;
  full_name: string;
  plan: "free" | "pro";
  auth_provider: "local" | "google";
  is_verified: boolean;
  created_at: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user: User;
}

export interface MessageResponse {
  message: string;
}

// ── Submission Types ──────────────────────────────────────────────────────────

export type SubmissionMode = "text" | "code";
export type SubmissionStatus = "pending" | "processing" | "completed" | "failed";
export type RiskLevel = "LOW" | "MEDIUM" | "HIGH";

export interface Scores {
  jaccard:   number | null;
  cosine:    number | null;
  lcs:       number | null;
  winnowing: number | null;
  ast:       number | null;
}

export interface Report {
  id:                 number;
  language:           string | null;
  scores:             Scores;
  final_similarity:   number;
  risk_level:         RiskLevel;
  processing_time_ms: number | null;
  algorithm_version:  string | null;
  created_at:         string;
}

export interface SubmissionListItem {
  id:               number;
  mode:             SubmissionMode;
  file1_name:       string;
  file2_name:       string;
  status:           SubmissionStatus;
  created_at:       string;
  final_similarity: number | null;
  risk_level:       RiskLevel | null;
}

export interface SubmissionDetail {
  id:                number;
  mode:              SubmissionMode;
  file1_name:        string;
  file2_name:        string;
  language_override: string | null;
  status:            SubmissionStatus;
  error_message:     string | null;
  created_at:        string;
  completed_at:      string | null;
  report:            Report | null;
}

export interface UploadResponse {
  submission_id: number;
  status:        SubmissionStatus;
  message:       string;
}

export interface HistoryResponse {
  total:       number;
  page:        number;
  page_size:   number;
  submissions: SubmissionListItem[];
}

// ── API Error ─────────────────────────────────────────────────────────────────

export interface ApiError {
  detail: string;
}