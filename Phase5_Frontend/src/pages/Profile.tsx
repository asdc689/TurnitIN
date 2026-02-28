import { useState, type FormEvent } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { profileApi, getErrorMessage } from "../services/api";
import UserMenu from "../components/UserMenu";
import {
  Shield, ChevronLeft, User, Lock,
  AlertCircle, CheckCircle2
} from "lucide-react";

export default function Profile() {
  const { user, setUser, logout } = useAuth();

  const [fullName, setFullName]             = useState(user?.full_name || "");
  const [profileError, setProfileError]     = useState<string | null>(null);
  const [profileSuccess, setProfileSuccess] = useState<string | null>(null);
  const [isUpdating, setIsUpdating]         = useState(false);

  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword]         = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [passwordError, setPasswordError]     = useState<string | null>(null);
  const [passwordSuccess, setPasswordSuccess] = useState<string | null>(null);
  const [isChanging, setIsChanging]           = useState(false);

  const handleProfileUpdate = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setProfileError(null);
    setProfileSuccess(null);
    setIsUpdating(true);
    try {
      const updatedUser = await profileApi.update(fullName);
      setUser(updatedUser);
      setProfileSuccess("Profile updated successfully.");
    } catch (err) {
      setProfileError(getErrorMessage(err));
    } finally {
      setIsUpdating(false);
    }
  };

  const handlePasswordChange = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setPasswordError(null);
    setPasswordSuccess(null);
    if (newPassword !== confirmPassword) { setPasswordError("New passwords do not match."); return; }
    if (newPassword.length < 8) { setPasswordError("Password must be at least 8 characters."); return; }
    setIsChanging(true);
    try {
      const data = await profileApi.changePassword(currentPassword, newPassword);
      setPasswordSuccess(data.message);
      setCurrentPassword(""); setNewPassword(""); setConfirmPassword("");
    } catch (err) {
      setPasswordError(getErrorMessage(err));
    } finally {
      setIsChanging(false);
    }
  };

  const inputClass = "w-full px-4 py-2.5 border border-slate-200 dark:border-slate-600 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent bg-white dark:bg-slate-700 text-slate-800 dark:text-slate-200";

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
      <main className="max-w-2xl mx-auto px-6 py-8">

        <Link
          to="/dashboard"
          className="inline-flex items-center text-sm font-medium text-slate-500 dark:text-slate-400 hover:text-indigo-600 dark:hover:text-indigo-400 transition-colors mb-6"
        >
          <ChevronLeft className="w-4 h-4 mr-1" />
          Back to Dashboard
        </Link>

        <h1 className="text-2xl font-bold text-slate-800 dark:text-slate-100 mb-6">Profile & Settings</h1>

        {/* ── Profile Card ── */}
        <div className="bg-white dark:bg-slate-800 rounded-2xl border border-slate-200 dark:border-slate-700 p-6 mb-6 shadow-sm">
          <div className="flex items-center gap-3 mb-6">
            <div className="w-10 h-10 bg-indigo-100 dark:bg-indigo-900/40 rounded-xl flex items-center justify-center">
              <User className="w-5 h-5 text-indigo-600 dark:text-indigo-400" />
            </div>
            <div>
              <h2 className="font-semibold text-slate-800 dark:text-slate-100">Personal Information</h2>
              <p className="text-xs text-slate-400 dark:text-slate-500">{user?.email}</p>
            </div>
          </div>

          {profileError && (
            <div className="flex items-center gap-2 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-red-700 dark:text-red-400 rounded-lg p-3 mb-4 text-sm">
              <AlertCircle className="w-4 h-4 shrink-0" />
              {profileError}
            </div>
          )}
          {profileSuccess && (
            <div className="flex items-center gap-2 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 text-green-700 dark:text-green-400 rounded-lg p-3 mb-4 text-sm">
              <CheckCircle2 className="w-4 h-4 shrink-0" />
              {profileSuccess}
            </div>
          )}

          <form onSubmit={handleProfileUpdate} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1.5">Full Name</label>
              <input
                type="text"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                required
                minLength={2}
                className={inputClass}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1.5">Email Address</label>
              <input
                type="email"
                value={user?.email || ""}
                disabled
                className="w-full px-4 py-2.5 border border-slate-200 dark:border-slate-600 rounded-lg text-sm bg-slate-50 dark:bg-slate-700/50 text-slate-400 dark:text-slate-500 cursor-not-allowed"
              />
              <p className="text-xs text-slate-400 dark:text-slate-500 mt-1">Email cannot be changed.</p>
            </div>
            <div className="flex justify-end">
              <button
                type="submit"
                disabled={isUpdating}
                className="bg-indigo-600 hover:bg-indigo-700 disabled:bg-indigo-400 text-white font-semibold px-6 py-2.5 rounded-lg transition-colors text-sm"
              >
                {isUpdating ? "Saving..." : "Save Changes"}
              </button>
            </div>
          </form>
        </div>

        {/* ── Password Card ── */}
        {user?.auth_provider === "local" && (
          <div className="bg-white dark:bg-slate-800 rounded-2xl border border-slate-200 dark:border-slate-700 p-6 shadow-sm">
            <div className="flex items-center gap-3 mb-6">
              <div className="w-10 h-10 bg-indigo-100 dark:bg-indigo-900/40 rounded-xl flex items-center justify-center">
                <Lock className="w-5 h-5 text-indigo-600 dark:text-indigo-400" />
              </div>
              <div>
                <h2 className="font-semibold text-slate-800 dark:text-slate-100">Change Password</h2>
                <p className="text-xs text-slate-400 dark:text-slate-500">Update your account password</p>
              </div>
            </div>

            {passwordError && (
              <div className="flex items-center gap-2 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-red-700 dark:text-red-400 rounded-lg p-3 mb-4 text-sm">
                <AlertCircle className="w-4 h-4 shrink-0" />
                {passwordError}
              </div>
            )}
            {passwordSuccess && (
              <div className="flex items-center gap-2 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 text-green-700 dark:text-green-400 rounded-lg p-3 mb-4 text-sm">
                <CheckCircle2 className="w-4 h-4 shrink-0" />
                {passwordSuccess}
              </div>
            )}

            <form onSubmit={handlePasswordChange} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1.5">Current Password</label>
                <input type="password" value={currentPassword} onChange={(e) => setCurrentPassword(e.target.value)} required placeholder="••••••••" className={inputClass} />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1.5">New Password</label>
                <input type="password" value={newPassword} onChange={(e) => setNewPassword(e.target.value)} required minLength={8} placeholder="••••••••" className={inputClass} />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1.5">Confirm New Password</label>
                <input type="password" value={confirmPassword} onChange={(e) => setConfirmPassword(e.target.value)} required minLength={8} placeholder="••••••••" className={inputClass} />
              </div>
              <div className="flex justify-end">
                <button
                  type="submit"
                  disabled={isChanging}
                  className="bg-indigo-600 hover:bg-indigo-700 disabled:bg-indigo-400 text-white font-semibold px-6 py-2.5 rounded-lg transition-colors text-sm"
                >
                  {isChanging ? "Changing..." : "Change Password"}
                </button>
              </div>
            </form>
          </div>
        )}

        {/* ── Account Info ── */}
        <div className="bg-white dark:bg-slate-800 rounded-2xl border border-slate-200 dark:border-slate-700 p-6 mt-6 shadow-sm">
          <h2 className="font-semibold text-slate-800 dark:text-slate-100 mb-4">Account Details</h2>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <p className="text-xs text-slate-400 dark:text-slate-500 mb-1 font-semibold uppercase tracking-wider">Plan</p>
              <p className="text-sm font-medium text-slate-700 dark:text-slate-300 capitalize">{user?.plan}</p>
            </div>
            <div>
              <p className="text-xs text-slate-400 dark:text-slate-500 mb-1 font-semibold uppercase tracking-wider">Member Since</p>
              <p className="text-sm font-medium text-slate-700 dark:text-slate-300">
                {user?.created_at
                  ? new Date(user.created_at).toLocaleDateString("en-US", { month: "long", day: "numeric", year: "numeric" })
                  : "—"}
              </p>
            </div>
            <div>
              <p className="text-xs text-slate-400 dark:text-slate-500 mb-1 font-semibold uppercase tracking-wider">Email Status</p>
              <p className={`text-sm font-medium ${user?.is_verified ? "text-green-600 dark:text-green-400" : "text-yellow-600 dark:text-yellow-400"}`}>
                {user?.is_verified ? "Verified" : "Not Verified"}
              </p>
            </div>
            <div>
              <p className="text-xs text-slate-400 dark:text-slate-500 mb-1 font-semibold uppercase tracking-wider">Login Method</p>
              <p className="text-sm font-medium text-slate-700 dark:text-slate-300 capitalize">{user?.auth_provider}</p>
            </div>
          </div>
        </div>

      </main>
    </div>
  );
}