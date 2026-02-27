import { useState, useEffect, useCallback } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import { submissionsApi, getErrorMessage } from "../services/api";
import type { SubmissionDetail, RiskLevel } from "../types";
import {
  Shield, LogOut, ChevronLeft, Loader2, AlertCircle,
  CheckCircle2, XCircle, FileText, Code2
} from "lucide-react";
import { useAuth } from "../context/AuthContext";

// Helpers
// Generates a color-coded, bordered badge based on the risk level
function RiskBadge({ level }: { level: RiskLevel }) {
  const styles = {
    LOW:    "bg-green-100 text-green-700 border-green-200",
    MEDIUM: "bg-yellow-100 text-yellow-700 border-yellow-200",
    HIGH:   "bg-red-100 text-red-700 border-red-200",
  };
  return (
    <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-semibold border ${styles[level]}`}>
      {level} RISK
    </span>
  );
}

// Renders an animated, color-coded progress bar for individual algorithm scores
function ScoreBar({ label, value }: { label: string; value: number | null }) {
  // If the backend didn't use this algorithm (e.g., AST on a text file), don't render it
  if (value === null) return null;
  
  const pct = Math.round(value * 100);
  // Red for high similarity, yellow for medium, green for low/safe
  const color = pct >= 50 ? "bg-red-500" : pct >= 30 ? "bg-yellow-500" : "bg-green-500";

  return (
    <div>
      <div className="flex justify-between items-center mb-1.5">
        <span className="text-sm font-medium text-slate-600">{label}</span>
        <span className="text-sm font-bold text-slate-800">{pct}%</span>
      </div>
      <div className="w-full bg-slate-100 rounded-full h-2">
        <div
          className={`h-2 rounded-full transition-all duration-700 ${color}`}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}

// Formats the ISO timestamp into a clean, human-readable date with time
function formatDate(dateStr: string) {
  return new Date(dateStr).toLocaleString("en-US", {
    month: "short", day: "numeric", year: "numeric",
    hour: "2-digit", minute: "2-digit",
  });
}

// Component

export default function Report() {
  // Hooks & State
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { logout, user } = useAuth();

  const [submission, setSubmission] = useState<SubmissionDetail | null>(null);
  const [isLoading, setIsLoading]   = useState(true);
  const [error, setError]           = useState<string | null>(null);
  const [polling, setPolling]       = useState(false);

  // Network Calls
  // useCallback memoizes this function so it doesn't trigger unnecessary re-renders in the useEffects below
  const fetchReport = useCallback(async () => {
    if (!id) return;
    try {
      const data = await submissionsApi.getReport(Number(id));
      setSubmission(data);

      // If Celery is still processing, keep the polling flag active
      if (data.status === "pending" || data.status === "processing") {
        setPolling(true);
      } else {
        setPolling(false);
      }
    } catch (err) {
      setError(getErrorMessage(err));
      setPolling(false); // Stop polling if the server throws an error (like a 404)
    } finally {
      setIsLoading(false);
    }
  }, [id]);

  // 1. Initial fetch when the component first mounts
  useEffect(() => {
    fetchReport();
  }, [fetchReport]);

  // 2. Polling loop: Ping the server every 3 seconds ONLY if the polling flag is true
  useEffect(() => {
    if (!polling) return;
    const interval = setInterval(fetchReport, 3000);
    
    // Cleanup function runs when the component unmounts or polling stops
    return () => clearInterval(interval);
  }, [polling, fetchReport]);

  // Render
  return (
    <div className="min-h-screen bg-slate-100">

      {/* Navbar */}
      <nav className="bg-white border-b border-slate-200 px-6 py-4">
        <div className="max-w-6xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-indigo-600 rounded-lg flex items-center justify-center">
              <Shield className="w-4 h-4 text-white" />
            </div>
            <span className="font-bold text-slate-800">Plagiarism Detector</span>
          </div>
          <div className="flex items-center gap-4">
            <span className="text-sm text-slate-500">{user?.full_name}</span>
            <button
              onClick={logout}
              className="flex items-center gap-1.5 text-sm text-slate-500 hover:text-red-600 transition-colors"
            >
              <LogOut className="w-4 h-4" />
              Logout
            </button>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="max-w-4xl mx-auto px-6 py-8">

        {/* Back Navigation */}
        <Link
          to="/dashboard"
          className="inline-flex items-center text-sm font-medium text-slate-500 hover:text-indigo-600 transition-colors mb-6"
        >
          <ChevronLeft className="w-4 h-4 mr-1" />
          Back to Dashboard
        </Link>

        {/* Routing for States */}
        {isLoading ? (
          
          /* Loading State */
          <div className="flex items-center justify-center py-20">
            <Loader2 className="w-8 h-8 text-indigo-600 animate-spin" />
          </div>

        ) : error ? (
          
          /* Error State */
          <div className="bg-red-50 border border-red-200 text-red-700 rounded-xl p-6 text-center">
            <AlertCircle className="w-6 h-6 mx-auto mb-2" />
            <p className="font-medium">{error}</p>
          </div>

        ) : submission ? (
          
          /* Content State */
          <div className="space-y-6">

            {/* Header Card */}
            <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm">
              <div className="flex items-start justify-between flex-wrap gap-4">
                <div>
                  <h1 className="text-2xl font-bold text-slate-800 mb-1">
                    Scan Report #{submission.id}
                  </h1>
                  <div className="flex items-center gap-2 text-sm text-slate-500">
                    {submission.mode === "text"
                      ? <FileText className="w-4 h-4" />
                      : <Code2 className="w-4 h-4" />
                    }
                    <span className="capitalize">{submission.mode} comparison</span>
                    <span>•</span>
                    <span>{formatDate(submission.created_at)}</span>
                  </div>
                </div>

                {/* Status Indicator */}
                <div className="flex items-center gap-2">
                  {submission.status === "completed" && (
                    <CheckCircle2 className="w-5 h-5 text-green-500" />
                  )}
                  {submission.status === "failed" && (
                    <XCircle className="w-5 h-5 text-red-500" />
                  )}
                  {(submission.status === "pending" || submission.status === "processing") && (
                    <Loader2 className="w-5 h-5 text-blue-500 animate-spin" />
                  )}
                  <span className="text-sm font-medium text-slate-600 capitalize">
                    {submission.status}
                  </span>
                </div>
              </div>

              {/* File Names Grid */}
              <div className="mt-4 grid grid-cols-2 gap-4">
                <div className="bg-slate-50 rounded-xl p-4 border border-slate-100">
                  <p className="text-xs text-slate-400 mb-1 font-semibold uppercase tracking-wider">File 1</p>
                  <p className="text-sm font-medium text-slate-700 truncate" title={submission.file1_name}>
                    {submission.file1_name}
                  </p>
                </div>
                <div className="bg-slate-50 rounded-xl p-4 border border-slate-100">
                  <p className="text-xs text-slate-400 mb-1 font-semibold uppercase tracking-wider">File 2</p>
                  <p className="text-sm font-medium text-slate-700 truncate" title={submission.file2_name}>
                    {submission.file2_name}
                  </p>
                </div>
              </div>
            </div>

            {/* Processing State Banner */}
            {(submission.status === "pending" || submission.status === "processing") && (
              <div className="bg-blue-50 border border-blue-200 rounded-2xl p-8 text-center shadow-sm">
                <Loader2 className="w-10 h-10 text-blue-500 animate-spin mx-auto mb-4" />
                <h3 className="font-semibold text-blue-800 mb-1 text-lg">Analysis in Progress</h3>
                <p className="text-sm text-blue-600">
                  Your files are being analyzed by our Celery workers. This page will update automatically.
                </p>
              </div>
            )}

            {/* Failed State Banner */}
            {submission.status === "failed" && (
              <div className="bg-red-50 border border-red-200 rounded-2xl p-8 text-center shadow-sm">
                <XCircle className="w-10 h-10 text-red-500 mx-auto mb-4" />
                <h3 className="font-semibold text-red-800 mb-1 text-lg">Analysis Failed</h3>
                <p className="text-sm text-red-600">
                  {submission.error_message || "An unexpected error occurred during analysis."}
                </p>
              </div>
            )}

            {/* Completed Report Results */}
            {submission.status === "completed" && submission.report && (
              <>
                {/* Score Overview */}
                <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm">
                  <div className="flex items-center justify-between mb-6">
                    <h2 className="text-lg font-bold text-slate-800">Similarity Score</h2>
                    <RiskBadge level={submission.report.risk_level} />
                  </div>

                  {/* Big Score Display */}
                  <div className="text-center py-6">
                    <div className={`text-6xl font-black mb-2 ${
                      submission.report.final_similarity >= 0.5
                        ? "text-red-600"
                        : submission.report.final_similarity >= 0.3
                        ? "text-yellow-600"
                        : "text-green-600"
                    }`}>
                      {(submission.report.final_similarity * 100).toFixed(1)}%
                    </div>
                    <p className="text-slate-500 text-sm font-medium uppercase tracking-wider">Overall Similarity</p>
                  </div>
                </div>

                {/* Algorithm Breakdown Grid */}
                <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm">
                  <h2 className="text-lg font-bold text-slate-800 mb-6">
                    Algorithm Breakdown
                  </h2>
                  <div className="space-y-5">
                    <ScoreBar label="Cosine Similarity (TF-IDF)"  value={submission.report.scores.cosine} />
                    <ScoreBar label="Jaccard Similarity"          value={submission.report.scores.jaccard} />
                    <ScoreBar label="Longest Common Subsequence"  value={submission.report.scores.lcs} />
                    <ScoreBar label="Winnowing (Code Fingerprint)" value={submission.report.scores.winnowing} />
                    <ScoreBar label="AST Structural Similarity"   value={submission.report.scores.ast} />
                  </div>
                </div>

                {/* Meta Info Grid */}
                <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm">
                  <h2 className="text-lg font-bold text-slate-800 mb-4">Details</h2>
                  <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
                    <div>
                      <p className="text-xs text-slate-400 mb-1 font-semibold uppercase tracking-wider">Language</p>
                      <p className="text-sm font-medium text-slate-700 capitalize">
                        {submission.report.language || "—"}
                      </p>
                    </div>
                    <div>
                      <p className="text-xs text-slate-400 mb-1 font-semibold uppercase tracking-wider">Processing Time</p>
                      <p className="text-sm font-medium text-slate-700">
                        {submission.report.processing_time_ms
                          ? `${submission.report.processing_time_ms}ms`
                          : "—"}
                      </p>
                    </div>
                    <div>
                      <p className="text-xs text-slate-400 mb-1 font-semibold uppercase tracking-wider">Algorithm Version</p>
                      <p className="text-sm font-medium text-slate-700">
                        {submission.report.algorithm_version || "—"}
                      </p>
                    </div>
                    <div>
                      <p className="text-xs text-slate-400 mb-1 font-semibold uppercase tracking-wider">Completed At</p>
                      <p className="text-sm font-medium text-slate-700">
                        {submission.completed_at ? formatDate(submission.completed_at) : "—"}
                      </p>
                    </div>
                  </div>
                </div>

                {/* Actions */}
                <div className="flex justify-end gap-3 mt-4">
                  <button
                    onClick={() => navigate("/upload")}
                    className="bg-indigo-600 hover:bg-indigo-700 text-white font-semibold px-6 py-2.5 rounded-xl transition-colors text-sm shadow-sm"
                  >
                    New Scan
                  </button>
                </div>
              </>
            )}
          </div>
        ) : null}
      </main>
    </div>
  );
}



// ___________________NEW CODE BELOW______________________________



// import { useState, useEffect, useCallback } from "react";
// import { useParams, useNavigate, Link } from "react-router-dom";
// import { submissionsApi, getErrorMessage } from "../services/api";
// import type { SubmissionDetail, RiskLevel } from "../types";
// import {
//   Shield, LogOut, ChevronLeft, Loader2, AlertCircle,
//   CheckCircle2, XCircle, FileText, Code2, Activity
// } from "lucide-react";
// import { useAuth } from "../context/AuthContext";

// // ── Helpers ──
// function RiskBadge({ level }: { level: RiskLevel }) {
//   const styles = {
//     LOW:    "bg-green-100 text-green-700 border-green-200",
//     MEDIUM: "bg-yellow-100 text-yellow-700 border-yellow-200",
//     HIGH:   "bg-red-100 text-red-700 border-red-200",
//   };
//   return (
//     <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-semibold border ${styles[level]}`}>
//       {level} RISK
//     </span>
//   );
// }

// function ScoreBar({ label, value }: { label: string; value: number | null }) {
//   if (value === null) return null;
//   const pct = Math.round(value * 100);
//   const color = pct >= 50 ? "bg-red-500" : pct >= 30 ? "bg-yellow-500" : "bg-green-500";

//   return (
//     <div>
//       <div className="flex justify-between items-center mb-1.5">
//         <span className="text-sm font-medium text-slate-600">{label}</span>
//         <span className="text-sm font-bold text-slate-800">{pct}%</span>
//       </div>
//       <div className="w-full bg-slate-100 rounded-full h-2">
//         <div
//           className={`h-2 rounded-full transition-all duration-700 ${color}`}
//           style={{ width: `${pct}%` }}
//         />
//       </div>
//     </div>
//   );
// }

// function formatDate(dateStr: string) {
//   return new Date(dateStr).toLocaleString("en-US", {
//     month: "short", day: "numeric", year: "numeric",
//     hour: "2-digit", minute: "2-digit",
//   });
// }

// // ── Component ──
// export default function Report() {
//   const { id } = useParams<{ id: string }>();
//   const navigate = useNavigate();
//   const { logout, user } = useAuth();

//   const [submission, setSubmission] = useState<SubmissionDetail | null>(null);
//   const [isLoading, setIsLoading]   = useState(true);
//   const [error, setError]           = useState<string | null>(null);
//   const [polling, setPolling]       = useState(false);

//   // Simulated Progress State for the "Diagnostics" feel
//   const [progress, setProgress] = useState(0);
//   const [loadingText, setLoadingText] = useState("Initializing analysis...");

//   // ── Network Calls ──
//   const fetchReport = useCallback(async () => {
//     if (!id) return;
//     try {
//       const data = await submissionsApi.getReport(Number(id));
//       setSubmission(data);

//       if (data.status === "pending" || data.status === "processing") {
//         setPolling(true);
//       } else {
//         setPolling(false);
//         setProgress(100); // Instantly fill the bar when done!
//       }
//     } catch (err) {
//       setError(getErrorMessage(err));
//       setPolling(false);
//     } finally {
//       setIsLoading(false);
//     }
//   }, [id]);

//   // 1. Initial Fetch
//   useEffect(() => {
//     fetchReport();
//   }, [fetchReport]);

//   // 2. Polling loop (Backend Ping)
//   useEffect(() => {
//     if (!polling) return;
//     const interval = setInterval(fetchReport, 3000);
//     return () => clearInterval(interval);
//   }, [polling, fetchReport]);

//   // 3. Fake Progress & Text Cycling (Diagnostics UI)
//   useEffect(() => {
//     if (!polling) return;

//     const texts = [
//       "Queueing files for processing...",
//       "Parsing Abstract Syntax Trees...",
//       "Running NLP similarity algorithms...",
//       "Generating cryptographic fingerprints...",
//       "Finalizing scan results..."
//     ];
//     let textIndex = 0;

//     // Cycle text every 2.5 seconds
//     const textInterval = setInterval(() => {
//       textIndex = (textIndex + 1) % texts.length;
//       setLoadingText(texts[textIndex]);
//     }, 2500);

//     // Bump progress bar randomly every 800ms
//     const progressInterval = setInterval(() => {
//       setProgress((prev) => {
//         if (prev >= 95) return prev; // Hold at 95% until Celery is actually done
//         const increment = Math.max(1, Math.floor(Math.random() * 10));
//         return Math.min(prev + increment, 95);
//       });
//     }, 800);

//     return () => {
//       clearInterval(textInterval);
//       clearInterval(progressInterval);
//     };
//   }, [polling]);

//   // ── Render ──
//   return (
//     <div className="min-h-screen bg-slate-100">

//       {/* Navbar */}
//       <nav className="bg-white border-b border-slate-200 px-6 py-4">
//         <div className="max-w-6xl mx-auto flex items-center justify-between">
//           <div className="flex items-center gap-2">
//             <div className="w-8 h-8 bg-indigo-600 rounded-lg flex items-center justify-center">
//               <Shield className="w-4 h-4 text-white" />
//             </div>
//             <span className="font-bold text-slate-800">Plagiarism Detector</span>
//           </div>
//           <div className="flex items-center gap-4">
//             <span className="text-sm text-slate-500">{user?.full_name}</span>
//             <button
//               onClick={logout}
//               className="flex items-center gap-1.5 text-sm text-slate-500 hover:text-red-600 transition-colors"
//             >
//               <LogOut className="w-4 h-4" />
//               Logout
//             </button>
//           </div>
//         </div>
//       </nav>

//       {/* Main Content */}
//       <main className="max-w-4xl mx-auto px-6 py-8">
//         <Link
//           to="/dashboard"
//           className="inline-flex items-center text-sm font-medium text-slate-500 hover:text-indigo-600 transition-colors mb-6"
//         >
//           <ChevronLeft className="w-4 h-4 mr-1" />
//           Back to Dashboard
//         </Link>

//         {isLoading ? (
//           <div className="flex items-center justify-center py-20">
//             <Loader2 className="w-8 h-8 text-indigo-600 animate-spin" />
//           </div>
//         ) : error ? (
//           <div className="bg-red-50 border border-red-200 text-red-700 rounded-xl p-6 text-center">
//             <AlertCircle className="w-6 h-6 mx-auto mb-2" />
//             <p className="font-medium">{error}</p>
//           </div>
//         ) : submission ? (
//           <div className="space-y-6">

//             {/* Header Card (Now safely has file names!) */}
//             <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm">
//               <div className="flex items-start justify-between flex-wrap gap-4">
//                 <div>
//                   <h1 className="text-2xl font-bold text-slate-800 mb-1">
//                     Scan Report #{submission.id}
//                   </h1>
//                   <div className="flex items-center gap-2 text-sm text-slate-500">
//                     {submission.mode === "text"
//                       ? <FileText className="w-4 h-4" />
//                       : <Code2 className="w-4 h-4" />
//                     }
//                     <span className="capitalize">{submission.mode} comparison</span>
//                     <span>•</span>
//                     <span>{formatDate(submission.created_at)}</span>
//                   </div>
//                 </div>

//                 <div className="flex items-center gap-2">
//                   {submission.status === "completed" && <CheckCircle2 className="w-5 h-5 text-green-500" />}
//                   {submission.status === "failed" && <XCircle className="w-5 h-5 text-red-500" />}
//                   {(submission.status === "pending" || submission.status === "processing") && (
//                     <Loader2 className="w-5 h-5 text-green-500 animate-spin" />
//                   )}
//                   <span className="text-sm font-medium text-slate-600 capitalize">
//                     {submission.status}
//                   </span>
//                 </div>
//               </div>

//               <div className="mt-4 grid grid-cols-2 gap-4">
//                 <div className="bg-slate-50 rounded-xl p-4 border border-slate-100">
//                   <p className="text-xs text-slate-400 mb-1 font-semibold uppercase tracking-wider">File 1</p>
//                   <p className="text-sm font-medium text-slate-700 truncate" title={submission.file1_name}>
//                     {submission.file1_name}
//                   </p>
//                 </div>
//                 <div className="bg-slate-50 rounded-xl p-4 border border-slate-100">
//                   <p className="text-xs text-slate-400 mb-1 font-semibold uppercase tracking-wider">File 2</p>
//                   <p className="text-sm font-medium text-slate-700 truncate" title={submission.file2_name}>
//                     {submission.file2_name}
//                   </p>
//                 </div>
//               </div>
//             </div>

//             {/* ── THE NEW DIAGNOSTICS PROGRESS BAR ── */}
//             {(submission.status === "pending" || submission.status === "processing") && (
//               <div className="bg-white border border-green-200 rounded-2xl p-8 shadow-sm">
//                 <div className="max-w-xl mx-auto">
//                   <div className="flex items-center gap-4 mb-6">
//                     <div className="w-12 h-12 bg-green-50 rounded-xl flex items-center justify-center shrink-0">
//                       <Activity className="w-6 h-6 text-green-600 animate-pulse" />
//                     </div>
//                     <div>
//                       <h3 className="text-lg font-bold text-slate-800">Diagnostics Running</h3>
//                       <p className="text-sm text-slate-500 transition-all duration-300">
//                         {loadingText}
//                       </p>
//                     </div>
//                     <div className="ml-auto text-2xl font-black text-green-600">
//                       {progress}%
//                     </div>
//                   </div>

//                   {/* Progress Bar */}
//                   <div className="w-full bg-slate-100 rounded-full h-3 overflow-hidden border border-slate-200 shadow-inner">
//                     <div
//                       className="h-full bg-green-500 rounded-full transition-all duration-500 ease-out relative"
//                       style={{ width: `${progress}%` }}
//                     >
//                       <div className="absolute inset-0 bg-white/20 animate-pulse"></div>
//                     </div>
//                   </div>
//                   <p className="text-xs text-center text-slate-400 mt-4 uppercase tracking-widest font-semibold">
//                     Please wait while Celery workers analyze your files
//                   </p>
//                 </div>
//               </div>
//             )}

//             {/* Failed State Banner */}
//             {submission.status === "failed" && (
//               <div className="bg-red-50 border border-red-200 rounded-2xl p-8 text-center shadow-sm">
//                 <XCircle className="w-10 h-10 text-red-500 mx-auto mb-4" />
//                 <h3 className="font-semibold text-red-800 mb-1 text-lg">Analysis Failed</h3>
//                 <p className="text-sm text-red-600">
//                   {submission.error_message || "An unexpected error occurred during analysis."}
//                 </p>
//               </div>
//             )}

//             {/* Completed Report Results */}
//             {submission.status === "completed" && submission.report && (
//               <div className="animate-in fade-in slide-in-from-bottom-4 duration-700">
//                 {/* Score Overview */}
//                 <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm mb-6">
//                   <div className="flex items-center justify-between mb-6">
//                     <h2 className="text-lg font-bold text-slate-800">Similarity Score</h2>
//                     <RiskBadge level={submission.report.risk_level} />
//                   </div>

//                   <div className="text-center py-6">
//                     <div className={`text-6xl font-black mb-2 ${
//                       submission.report.final_similarity >= 0.5
//                         ? "text-red-600"
//                         : submission.report.final_similarity >= 0.3
//                         ? "text-yellow-600"
//                         : "text-green-600"
//                     }`}>
//                       {(submission.report.final_similarity * 100).toFixed(1)}%
//                     </div>
//                     <p className="text-slate-500 text-sm font-medium uppercase tracking-wider">Overall Similarity</p>
//                   </div>
//                 </div>

//                 {/* Algorithm Breakdown Grid */}
//                 <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm mb-6">
//                   <h2 className="text-lg font-bold text-slate-800 mb-6">
//                     Algorithm Breakdown
//                   </h2>
//                   <div className="space-y-5">
//                     <ScoreBar label="Cosine Similarity (TF-IDF)"  value={submission.report.scores.cosine} />
//                     <ScoreBar label="Jaccard Similarity"          value={submission.report.scores.jaccard} />
//                     <ScoreBar label="Longest Common Subsequence"  value={submission.report.scores.lcs} />
//                     <ScoreBar label="Winnowing (Code Fingerprint)" value={submission.report.scores.winnowing} />
//                     <ScoreBar label="AST Structural Similarity"   value={submission.report.scores.ast} />
//                   </div>
//                 </div>

//                 {/* Meta Info Grid */}
//                 <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm mb-6">
//                   <h2 className="text-lg font-bold text-slate-800 mb-4">Details</h2>
//                   <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
//                     <div>
//                       <p className="text-xs text-slate-400 mb-1 font-semibold uppercase tracking-wider">Language</p>
//                       <p className="text-sm font-medium text-slate-700 capitalize">
//                         {submission.report.language || "—"}
//                       </p>
//                     </div>
//                     <div>
//                       <p className="text-xs text-slate-400 mb-1 font-semibold uppercase tracking-wider">Processing Time</p>
//                       <p className="text-sm font-medium text-slate-700">
//                         {submission.report.processing_time_ms
//                           ? `${submission.report.processing_time_ms}ms`
//                           : "—"}
//                       </p>
//                     </div>
//                     <div>
//                       <p className="text-xs text-slate-400 mb-1 font-semibold uppercase tracking-wider">Algorithm Version</p>
//                       <p className="text-sm font-medium text-slate-700">
//                         {submission.report.algorithm_version || "—"}
//                       </p>
//                     </div>
//                     <div>
//                       <p className="text-xs text-slate-400 mb-1 font-semibold uppercase tracking-wider">Completed At</p>
//                       <p className="text-sm font-medium text-slate-700">
//                         {submission.completed_at ? formatDate(submission.completed_at) : "—"}
//                       </p>
//                     </div>
//                   </div>
//                 </div>

//                 {/* Actions */}
//                 <div className="flex justify-end gap-3 mt-4">
//                   <button
//                     onClick={() => navigate("/upload")}
//                     className="bg-indigo-600 hover:bg-indigo-700 text-white font-semibold px-6 py-2.5 rounded-xl transition-colors text-sm shadow-sm"
//                   >
//                     New Scan
//                   </button>
//                 </div>
//               </div>
//             )}
//           </div>
//         ) : null}
//       </main>
//     </div>
//   );
// }