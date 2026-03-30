import { useState, useEffect } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import { submissionsApi, getErrorMessage } from "../services/api";
import type { SubmissionDetail, RiskLevel, FileContents, MatchedBlock } from "../types";
import { useAuth } from "../context/AuthContext";
import UserMenu from "../components/UserMenu";
import {
  Shield, ChevronLeft, Loader2, AlertCircle,
  CheckCircle2, XCircle, FileText, Code2, ChevronDown, ChevronUp, Printer
} from "lucide-react";

// ── Helpers ───────────────────────────────────────────────────────────────────

function RiskBadge({ level }: { level: RiskLevel }) {
  const styles = {
    LOW:    "bg-green-100 text-green-700 border-green-200 dark:bg-green-900/30 dark:text-green-400 dark:border-green-800",
    MEDIUM: "bg-yellow-100 text-yellow-700 border-yellow-200 dark:bg-yellow-900/30 dark:text-yellow-400 dark:border-yellow-800",
    HIGH:   "bg-red-100 text-red-700 border-red-200 dark:bg-red-900/30 dark:text-red-400 dark:border-red-800",
  };
  return (
    <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-semibold border ${styles[level]}`}>
      {level} RISK
    </span>
  );
}

function formatDate(dateStr: string) {
  return new Date(dateStr).toLocaleString("en-US", {
    month: "short", day: "numeric", year: "numeric",
    hour: "2-digit", minute: "2-digit",
  });
}

function handlePrint() {
  window.print();
}

// ── Side by Side Viewer ───────────────────────────────────────────────────────
const BLOCK_COLORS = [
  "bg-red-500/20 border-l-2 border-red-500",
  "bg-blue-500/20 border-l-2 border-blue-500",
  "bg-yellow-500/20 border-l-2 border-yellow-500",
  "bg-green-500/20 border-l-2 border-green-500",
  "bg-purple-500/20 border-l-2 border-purple-500",
  "bg-orange-500/20 border-l-2 border-orange-500",
  "bg-pink-500/20 border-l-2 border-pink-500",
  "bg-cyan-500/20 border-l-2 border-cyan-500",
  "bg-teal-500/20 border-l-2 border-teal-500",
  "bg-indigo-500/20 border-l-2 border-indigo-500",
];

function SideBySideViewer({
  fileContents,
  blocks,
}: {
  fileContents: FileContents;
  blocks:       MatchedBlock[];
}) {
  const [showFull, setShowFull]         = useState(false);
  const [activeBlock, setActiveBlock]   = useState<number | null>(null);

  const file1Lines = fileContents.file1.content.split("\n");
  const file2Lines = fileContents.file2.content.split("\n");

  // Build a map of line number → block index for fast lookup
  const lineToBlockA = new Map<number, number>();
  const lineToBlockB = new Map<number, number>();
  blocks.forEach((block, idx) => {
    for (let l = block.file_a_region[0]; l <= block.file_a_region[1]; l++) lineToBlockA.set(l, idx);
    for (let l = block.file_b_region[0]; l <= block.file_b_region[1]; l++) lineToBlockB.set(l, idx);
  });

  const visibleLinesA = new Set<number>();
  const visibleLinesB = new Set<number>();
  blocks.forEach(block => {
    for (let l = block.file_a_region[0]; l <= block.file_a_region[1]; l++) visibleLinesA.add(l);
    for (let l = block.file_b_region[0]; l <= block.file_b_region[1]; l++) visibleLinesB.add(l);
  });

  const renderLines = (
    lines: string[],
    lineToBlock: Map<number, number>,
    showAll: boolean
  ) => {
    return lines.map((line, idx) => {
      const lineNum    = idx + 1;
      const blockIdx   = lineToBlock.get(lineNum);
      const isHighlight = blockIdx !== undefined;
      const isActive   = activeBlock !== null ? blockIdx === activeBlock : true;

      if (!showAll && !isHighlight) return null;

      const colorClass = isHighlight && isActive
        ? BLOCK_COLORS[blockIdx! % BLOCK_COLORS.length]
        : isHighlight
        ? "bg-slate-700/30 border-l-2 border-slate-600"
        : "border-l-2 border-transparent";

      return (
        <div
          key={idx}
          className={`flex gap-3 px-3 py-0.5 font-mono text-xs leading-5 ${colorClass}`}
        >
          <span className="select-none text-slate-500 dark:text-slate-600 w-8 shrink-0 text-right">
            {lineNum}
          </span>
          <span className={`whitespace-pre ${isHighlight ? "text-slate-200" : "text-slate-400 dark:text-slate-500"}`}>
            {line || " "}
          </span>
        </div>
      );
    });
  };

  return (
    <div className="bg-white dark:bg-slate-800 rounded-2xl border border-slate-200 dark:border-slate-700 shadow-sm overflow-hidden">

      {/* Header */}
      <div className="px-6 py-4 border-b border-slate-200 dark:border-slate-700 flex items-center justify-between">
        <h2 className="text-lg font-bold text-slate-800 dark:text-slate-100">
          Side-by-Side Comparison
        </h2>
        <button
          onClick={() => setShowFull(v => !v)}
          className="flex items-center gap-1.5 text-sm font-medium text-indigo-600 dark:text-indigo-400 hover:opacity-80 transition-opacity"
        >
          {showFull ? (
            <><ChevronUp className="w-4 h-4" /> Show matched only</>
          ) : (
            <><ChevronDown className="w-4 h-4" /> Show full files</>
          )}
        </button>
      </div>

      {/* File headers */}
      <div className="grid grid-cols-2 border-b border-slate-200 dark:border-slate-700">
        <div className="px-4 py-2.5 bg-slate-50 dark:bg-slate-700/50 border-r border-slate-200 dark:border-slate-700">
          <p className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider truncate">
            {fileContents.file1.name}
          </p>
          <p className="text-xs text-slate-400 font-mono mt-0.5">
            {blocks.length} matched region{blocks.length !== 1 ? "s" : ""} flagged
          </p>
        </div>
        <div className="px-4 py-2.5 bg-slate-50 dark:bg-slate-700/50">
          <p className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider truncate">
            {fileContents.file2.name}
          </p>
          <p className="text-xs text-slate-400 font-mono mt-0.5">
            {blocks.length} matched region{blocks.length !== 1 ? "s" : ""} flagged
          </p>
        </div>
      </div>

      {/* Blocks Panel */}
      {blocks.length > 1 && (
        <div className="flex items-center gap-2 px-4 py-3 border-b border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-700/30 overflow-x-auto">
          <span className="text-xs text-slate-400 dark:text-slate-500 shrink-0">Matched blocks:</span>
          <button
            onClick={() => setActiveBlock(null)}
            className={`shrink-0 px-2.5 py-1 rounded-full text-xs font-semibold transition-colors ${
              activeBlock === null
                ? "bg-slate-700 text-white"
                : "bg-slate-200 dark:bg-slate-700 text-slate-500 hover:bg-slate-300"
            }`}
          >
            All
          </button>
          {blocks.map((block, idx) => (
            <button
              key={idx}
              onClick={() => setActiveBlock(activeBlock === idx ? null : idx)}
              className={`shrink-0 px-2.5 py-1 rounded-full text-xs font-semibold transition-colors ${
                activeBlock === idx
                  ? "text-white " + BLOCK_COLORS[idx % BLOCK_COLORS.length].split(" ")[0].replace("/20", "")
                  : "bg-slate-200 dark:bg-slate-700 text-slate-500 hover:bg-slate-300"
              }`}
            >
              Block {idx + 1} — {block.score}%
            </button>
          ))}
        </div>
      )}

      {/* Code panels */}
      <div className="grid grid-cols-2 divide-x divide-slate-200 dark:divide-slate-700">
        {/* File 1 */}
        <div className="bg-slate-900 dark:bg-slate-950 overflow-x-auto max-h-[500px] overflow-y-auto">
          <div className="py-2">
            {renderLines(file1Lines, lineToBlockA, showFull)}
          </div>
        </div>

        {/* File 2 */}
        <div className="bg-slate-900 dark:bg-slate-950 overflow-x-auto max-h-[500px] overflow-y-auto">
          <div className="py-2">
            {renderLines(file2Lines, lineToBlockB, showFull)}
          </div>
        </div>
      </div>

      {/* Footer */}
      <div className="px-6 py-3 border-t border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-700/30">
        <p className="text-xs text-slate-400 dark:text-slate-500 text-center">
          Highlighted lines indicate the most similar region detected between the two files.
        </p>
      </div>
    </div>
  );
}

// ── Component ─────────────────────────────────────────────────────────────────

export default function Report() {
  const { id }   = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { logout, user } = useAuth();

  const [submission, setSubmission]       = useState<SubmissionDetail | null>(null);
  const [fileContents, setFileContents]   = useState<FileContents | null>(null);
  const [isLoading, setIsLoading]         = useState(true);
  const [filesLoading, setFilesLoading]   = useState(false);
  const [error, setError]                 = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    const load = async () => {
      try {
        const data = await submissionsApi.getReport(Number(id));
        setSubmission(data);

        // If code mode and matched_blocks exist, fetch file contents
        if (data.mode === "code" && data.report?.matched_blocks) {
          setFilesLoading(true);
          try {
            const files = await submissionsApi.getFiles(Number(id));
            setFileContents(files);
          } catch {
            // Non-critical — viewer just won't show
          } finally {
            setFilesLoading(false);
          }
        }

      } catch (err) {
        setError(getErrorMessage(err));
      } finally {
        setIsLoading(false);
      }
    };
    load();
  }, [id]);

  return (
    <div className="min-h-screen bg-slate-100 dark:bg-slate-900">

      {/* Navbar */}
      <nav className="bg-white dark:bg-slate-800 border-b border-slate-200 dark:border-slate-700 px-6 py-4">
        <div className="max-w-6xl mx-auto flex items-center justify-between">
          <Link to="/dashboard" className="flex items-center gap-2 hover:opacity-80 transition-opacity">
            <div className="w-8 h-8 bg-indigo-600 rounded-lg flex items-center justify-center">
              <Shield className="w-4 h-4 text-white" />
            </div>
            <span className="font-bold text-slate-800 dark:text-slate-100">Plagiarism Detector</span>
          </Link>
          <UserMenu name={user?.full_name ?? ""} onLogout={logout} />
        </div>
      </nav>

      {/* Main */}
      <main className="max-w-6xl mx-auto px-6 py-8">

        <Link
          to="/dashboard"
          className="inline-flex items-center text-sm font-medium text-slate-500 dark:text-slate-400 hover:text-indigo-600 dark:hover:text-indigo-400 transition-colors mb-6"
        >
          <ChevronLeft className="w-4 h-4 mr-1" />
          Back to Dashboard
        </Link>

        {/* Loading */}
        {isLoading ? (
          <div className="flex items-center justify-center py-20">
            <Loader2 className="w-8 h-8 text-indigo-600 animate-spin" />
          </div>

        ) : error ? (
          <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-red-700 dark:text-red-400 rounded-xl p-6 text-center">
            <AlertCircle className="w-6 h-6 mx-auto mb-2" />
            <p className="font-medium">{error}</p>
            <button onClick={() => navigate("/dashboard")} className="mt-4 text-sm underline">
              Back to Dashboard
            </button>
          </div>

        ) : submission ? (
          <div className="space-y-6">

            {/* Header Card */}
            <div className="bg-white dark:bg-slate-800 rounded-2xl border border-slate-200 dark:border-slate-700 p-6 shadow-sm">
              <div className="flex items-start justify-between flex-wrap gap-4">
                <div>
                  <h1 className="text-2xl font-bold text-slate-800 dark:text-slate-100 mb-1">
                    Scan Report #{submission.id}
                  </h1>
                  <div className="flex items-center gap-2 text-sm text-slate-500 dark:text-slate-400">
                    {submission.mode === "text"
                      ? <FileText className="w-4 h-4" />
                      : <Code2 className="w-4 h-4" />
                    }
                    <span className="capitalize">{submission.mode} comparison</span>
                    <span>•</span>
                    <span>{formatDate(submission.created_at)}</span>
                  </div>
                </div>
                <CheckCircle2 className="w-5 h-5 text-green-500" />
              </div>

              {/* File Names */}
              <div className="mt-4 grid grid-cols-2 gap-4">
                <div className="bg-slate-50 dark:bg-slate-700/50 rounded-xl p-4 border border-slate-100 dark:border-slate-700">
                  <p className="text-xs text-slate-400 dark:text-slate-500 mb-1 font-semibold uppercase tracking-wider">File 1</p>
                  <p className="text-sm font-medium text-slate-700 dark:text-slate-300 truncate" title={submission.file1_name}>
                    {submission.file1_name}
                  </p>
                </div>
                <div className="bg-slate-50 dark:bg-slate-700/50 rounded-xl p-4 border border-slate-100 dark:border-slate-700">
                  <p className="text-xs text-slate-400 dark:text-slate-500 mb-1 font-semibold uppercase tracking-wider">File 2</p>
                  <p className="text-sm font-medium text-slate-700 dark:text-slate-300 truncate" title={submission.file2_name}>
                    {submission.file2_name}
                  </p>
                </div>
              </div>
            </div>

            {/* Failed */}
            {submission.status === "failed" && (
              <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-2xl p-8 text-center shadow-sm">
                <XCircle className="w-10 h-10 text-red-500 mx-auto mb-4" />
                <h3 className="font-semibold text-red-800 dark:text-red-400 mb-1 text-lg">Analysis Failed</h3>
                <p className="text-sm text-red-600 dark:text-red-500">
                  {submission.error_message || "An unexpected error occurred during analysis."}
                </p>
              </div>
            )}

            {/* Completed */}
            {submission.status === "completed" && submission.report && (
              <div id="print-report" className="space-y-6">
                {/* Score Overview */}
                <div className="bg-white dark:bg-slate-800 rounded-2xl border border-slate-200 dark:border-slate-700 p-6 shadow-sm">
                  <div className="flex items-center justify-between mb-6">
                    <h2 className="text-lg font-bold text-slate-800 dark:text-slate-100">Similarity Score</h2>
                    <RiskBadge level={submission.report.risk_level} />
                  </div>
                  <div className="text-center py-6">
                    <div className={`text-6xl font-black mb-2 ${
                      submission.report.final_similarity >= 0.5 ? "text-red-600 dark:text-red-400" :
                      submission.report.final_similarity >= 0.3 ? "text-yellow-600 dark:text-yellow-400" :
                      "text-green-600 dark:text-green-400"
                    }`}>
                      {(submission.report.final_similarity * 100).toFixed(1)}%
                    </div>
                    <p className="text-slate-500 dark:text-slate-400 text-sm font-medium uppercase tracking-wider">
                      Overall Similarity
                    </p>
                  </div>
                </div>

                {/* Side-by-Side Viewer — code mode only */}
                {submission.mode === "code" && Array.isArray(submission.report.matched_blocks) && submission.report.matched_blocks.length > 0 && (
                  filesLoading ? (
                    <div className="bg-white dark:bg-slate-800 rounded-2xl border border-slate-200 dark:border-slate-700 p-8 text-center shadow-sm">
                      <Loader2 className="w-6 h-6 text-indigo-600 animate-spin mx-auto mb-2" />
                      <p className="text-sm text-slate-500 dark:text-slate-400">Loading file contents...</p>
                    </div>
                  ) : fileContents ? (
                    <SideBySideViewer
                      fileContents = {fileContents}
                      blocks       = {submission.report.matched_blocks}
                    />
                  ) : null
                )}

                {/* Details */}
                <div className="bg-white dark:bg-slate-800 rounded-2xl border border-slate-200 dark:border-slate-700 p-6 shadow-sm">
                  <h2 className="text-lg font-bold text-slate-800 dark:text-slate-100 mb-4">Details</h2>
                  <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
                    <div>
                      <p className="text-xs text-slate-400 dark:text-slate-500 mb-1 font-semibold uppercase tracking-wider">Language</p>
                      <p className="text-sm font-medium text-slate-700 dark:text-slate-300 capitalize">
                        {submission.report.language || "—"}
                      </p>
                    </div>
                    <div>
                      <p className="text-xs text-slate-400 dark:text-slate-500 mb-1 font-semibold uppercase tracking-wider">Processing Time</p>
                      <p className="text-sm font-medium text-slate-700 dark:text-slate-300">
                        {submission.report.processing_time_ms
                          ? `${submission.report.processing_time_ms}ms`
                          : "—"}
                      </p>
                    </div>
                    <div>
                      <p className="text-xs text-slate-400 dark:text-slate-500 mb-1 font-semibold uppercase tracking-wider">Algorithm Version</p>
                      <p className="text-sm font-medium text-slate-700 dark:text-slate-300">
                        {submission.report.algorithm_version || "—"}
                      </p>
                    </div>
                    <div>
                      <p className="text-xs text-slate-400 dark:text-slate-500 mb-1 font-semibold uppercase tracking-wider">Completed At</p>
                      <p className="text-sm font-medium text-slate-700 dark:text-slate-300">
                        {submission.completed_at ? formatDate(submission.completed_at) : "—"}
                      </p>
                    </div>
                  </div>
                </div>

                {/* Actions */}
                <div className="flex justify-end gap-3 mt-4">
                  <button
                    onClick={handlePrint}
                    className="flex items-center gap-2 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-300 hover:text-indigo-600 dark:hover:text-indigo-400 font-semibold px-6 py-2.5 rounded-xl transition-colors text-sm shadow-sm"
                  >
                    <Printer className="w-4 h-4" />
                    Download PDF
                  </button>
                  <button
                    onClick={() => navigate("/upload")}
                    className="bg-indigo-600 hover:bg-indigo-700 text-white font-semibold px-6 py-2.5 rounded-xl transition-colors text-sm shadow-sm"
                  >
                    New Scan
                  </button>
                </div>
              {/* end print-report */}
              </div>
            )}
          </div>
        ) : null}
      </main>
    </div>
  );
}