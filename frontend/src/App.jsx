import { BrowserRouter, Routes, Route } from "react-router-dom";
import LandingPage from "./features/home/LandingPage";
import Login from "./features/auth/Login";
import Register from "./features/auth/Register";
import VerifyEmail from "./features/auth/VerifyEmail";
import StudentComplaintDashboard from "./features/complaints/StudentComplaintDashboard";
import CreateComplaintPage from "./features/complaints/CreateComplaintPage";
import MyComplaintsPage from "./features/complaints/MyComplaintsPage";
import ComplaintDetailPage from "./features/complaints/ComplaintDetailPage";
import FacultyDashboard from "./features/complaints/FacultyDashboard";

// A placeholder for the Admin Dashboard.
// You can create a real one at frontend/src/features/admin/AdminDashboard.jsx
function AdminDashboard() {
  return (
    <div style={{ padding: "2rem" }}>
      <h1>Admin Dashboard</h1>
      <p>This is a placeholder for the admin dashboard.</p>
    </div>
  );
}

function App() {
  return (
    <Routes>
      {/* Public Routes */}
      <Route path="/" element={<LandingPage />} />
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />
      <Route path="/verify-email" element={<VerifyEmail />} />

      {/* Student Routes */}
      <Route path="/dashboard" element={<StudentComplaintDashboard />} />
      <Route path="/create-complaint" element={<CreateComplaintPage />} />
      <Route path="/my-complaints" element={<MyComplaintsPage />} />
      <Route path="/my-complaints/:id" element={<ComplaintDetailPage />} />

      {/* Faculty Route */}
      <Route path="/faculty/dashboard" element={<FacultyDashboard />} />

      {/* Admin Route */}
      <Route path="/admin/dashboard" element={<AdminDashboard />} />

      {/* You can add a "Not Found" route here */}
      <Route
        path="*"
        element={<h1>404 - Page Not Found</h1>}
      />
    </Routes>
  );
}

export default App;