import { useState, useRef, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { submissionsApi, getErrorMessage } from "../services/api";
import { useAuth } from "../context/AuthContext";
import {
  Shield, LogOut, ArrowLeft, Upload, FileText,
  Code2, X, AlertCircle, Loader2, CheckCircle2
} from "lucide-react";

// File Drop Zone Component
// Extracted into its own component so each input safely manages its own 'useRef'
function FileDropZone({
  label, file, onFile, accept
}: {
  label: string;
  file: File | null;
  onFile: (f: File) => void;
  accept: string;
}) {
  const inputRef = useRef<HTMLInputElement>(null);

  return (
    <div
      onClick={() => inputRef.current?.click()}
      className="border-2 border-dashed border-slate-200 rounded-xl p-8 text-center cursor-pointer hover:border-indigo-400 hover:bg-indigo-50 transition-all"
    >
      <input
        ref={inputRef}
        type="file"
        accept={accept}
        className="hidden"
        onChange={(e) => {
          if (e.target.files?.[0]) onFile(e.target.files[0]);
        }}
      />
      {file ? (
        <div className="flex items-center justify-center gap-2">
          <CheckCircle2 className="w-5 h-5 text-green-500" />
          <span className="text-sm font-medium text-slate-700">{file.name}</span>
        </div>
      ) : (
        <>
          <Upload className="w-8 h-8 text-slate-300 mx-auto mb-3" />
          <p className="text-sm font-medium text-slate-600">{label}</p>
          <p className="text-xs text-slate-400 mt-1">Click to browse files</p>
        </>
      )}
    </div>
  );
}

// Main Upload Page Component

export default function UploadPage() {
  // Hooks
  const { logout, user } = useAuth();
  const navigate = useNavigate();

  // State
  const [mode, setMode]       = useState<"text" | "code">("text");
  const [langOverride, setLangOverride] = useState(""); // Added language override
  const [file1, setFile1]     = useState<File | null>(null);
  const [file2, setFile2]     = useState<File | null>(null);
  const [error, setError]     = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Dynamically set accepted file extensions based on the selected mode
  const accept = mode === "text"
    ? ".txt,.pdf,.docx"
    : ".py,.java,.cpp,.c,.js,.ts";

  // Handlers
  // Clear files and errors when switching modes to prevent invalid comparisons
  const handleModeChange = (newMode: "text" | "code") => {
    setMode(newMode);
    setFile1(null);
    setFile2(null);
    setError(null);
    setLangOverride(""); // Reset language when switching modes
  };

  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setError(null);

    // Safety check
    if (!file1 || !file2) {
      setError("Please select both files before submitting");
      return;
    }

    setIsSubmitting(true);

    try {
      // Send files and mode to FastAPI using FormData. 
      // Include language override ONLY if we are in code mode and a language was selected.
      const data = await submissionsApi.upload(
        file1, 
        file2, 
        mode,
        mode === "code" && langOverride ? langOverride : undefined
      );
      
      // Redirect to the newly created report page
      navigate(`/report/${data.submission_id}`);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setIsSubmitting(false);
    }
  };

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
      <main className="max-w-2xl mx-auto px-6 py-8">

        {/* Back button */}
        <button
          onClick={() => navigate("/dashboard")}
          className="flex items-center gap-1.5 text-sm text-slate-500 hover:text-slate-800 transition-colors mb-6"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to Dashboard
        </button>

        <div className="bg-white rounded-2xl border border-slate-200 p-8 shadow-sm">

          <h1 className="text-2xl font-bold text-slate-800 mb-1">New Submission</h1>
          <p className="text-slate-500 text-sm mb-8">
            Upload two files to compare for plagiarism
          </p>

          <form onSubmit={handleSubmit} className="space-y-6">

            {/* 1. Mode Selector */}
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-3">
                Comparison Mode
              </label>
              <div className="grid grid-cols-2 gap-3">
                <button
                  type="button"
                  onClick={() => handleModeChange("text")}
                  className={`flex items-center justify-center gap-2 py-3 px-4 rounded-xl border-2 font-medium text-sm transition-all ${
                    mode === "text"
                      ? "border-indigo-500 bg-indigo-50 text-indigo-700"
                      : "border-slate-200 text-slate-600 hover:border-slate-300"
                  }`}
                >
                  <FileText className="w-4 h-4" />
                  Text / Document
                </button>
                <button
                  type="button"
                  onClick={() => handleModeChange("code")}
                  className={`flex items-center justify-center gap-2 py-3 px-4 rounded-xl border-2 font-medium text-sm transition-all ${
                    mode === "code"
                      ? "border-indigo-500 bg-indigo-50 text-indigo-700"
                      : "border-slate-200 text-slate-600 hover:border-slate-300"
                  }`}
                >
                  <Code2 className="w-4 h-4" />
                  Source Code
                </button>
              </div>
            </div>

            {/* 2. Optional Language Override (Only shows in Code mode) */}
            {mode === "code" && (
              <div className="p-4 bg-slate-50 rounded-xl border border-slate-200">
                <label className="block text-sm font-medium text-slate-700 mb-1.5">
                  Programming Language (Optional)
                </label>
                <p className="text-xs text-slate-500 mb-3">
                  We automatically detect the language, but you can force a specific parser.
                </p>
                <select
                  value={langOverride}
                  onChange={(e) => setLangOverride(e.target.value)}
                  className="w-full sm:w-1/2 px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none text-sm bg-white"
                >
                  <option value="">Auto-detect</option>
                  <option value="python">Python</option>
                  <option value="cpp">C / C++</option>
                  <option value="java">Java</option>
                  <option value="javascript">JavaScript</option>
                </select>
              </div>
            )}

            {/* 3. File Upload Dropzones */}
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-3">
                Upload Files
                <span className="text-slate-400 font-normal ml-1">
                  ({mode === "text" ? ".txt, .pdf, .docx" : ".py, .java, .cpp, .c, .js, .ts"})
                </span>
              </label>
              <div className="space-y-3">
                <FileDropZone
                  label="File 1 — Click to upload"
                  file={file1}
                  onFile={setFile1}
                  accept={accept}
                />
                <FileDropZone
                  label="File 2 — Click to upload"
                  file={file2}
                  onFile={setFile2}
                  accept={accept}
                />
              </div>
            </div>

            {/* Clear Files Button */}
            {(file1 || file2) && (
              <button
                type="button"
                onClick={() => { setFile1(null); setFile2(null); }}
                className="flex items-center gap-1.5 text-sm text-slate-400 hover:text-red-500 transition-colors"
              >
                <X className="w-4 h-4" />
                Clear files
              </button>
            )}

            {/* Error Banner */}
            {error && (
              <div className="flex items-center gap-2 bg-red-50 border border-red-200 text-red-700 rounded-lg p-3 text-sm">
                <AlertCircle className="w-4 h-4 shrink-0" />
                {error}
              </div>
            )}

            {/* Submit Button */}
            <button
              type="submit"
              disabled={isSubmitting || !file1 || !file2}
              className="w-full bg-indigo-600 hover:bg-indigo-700 disabled:bg-indigo-400 disabled:cursor-not-allowed text-white font-semibold py-3 rounded-xl transition-colors flex items-center justify-center gap-2"
            >
              {isSubmitting ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Uploading...
                </>
              ) : (
                <>
                  <Upload className="w-4 h-4" />
                  Analyze Files
                </>
              )}
            </button>

          </form>
        </div>
      </main>
    </div>
  );
}