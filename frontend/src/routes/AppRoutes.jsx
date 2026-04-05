import { Route, Routes } from "react-router-dom";

import FacultyAssignment from "../features/admin/FacultyAssignment";
import ViewComplaints from "../features/admin/ViewComplaints";
import AdminComplaintDetail from "../features/admin/AdminComplaintDetail";
import ViewDepartments from "../features/admin/ViewDepartments";
import Login from "../features/auth/Login";
import Register from "../features/auth/Register";
import VerifyEmail from "../features/auth/VerifyEmail";
import LandingPage from "../features/home/LandingPage";
import StudentComplaintDashboard from "../features/complaints/StudentComplaintDashboard";
import CreateComplaintPage from "../features/complaints/CreateComplaintPage";
import MyComplaintsPage from "../features/complaints/MyComplaintsPage";
import ComplaintDetailPage from "../features/complaints/ComplaintDetailPage";
import FacultyDashboard from "../features/complaints/FacultyDashboard";

// A placeholder for the Admin Dashboard, keeping it consistent with App.jsx.
// You can create a real one at frontend/src/features/admin/AdminDashboard.jsx
function AdminDashboard() {
  return (
    <div style={{ padding: "2rem" }}>
      <h1>Admin Dashboard</h1>
      <p>This is a placeholder for the admin dashboard.</p>
    </div>
  );
}

function AppRoutes() {
  return (
    <Routes>
      {/* Public Routes */}
      <Route path="/" element={<LandingPage />} />
      <Route path="/register" element={<Register />} />
      <Route path="/login" element={<Login />} />
      <Route path="/verify-email" element={<VerifyEmail />} />

      {/* Admin Routes */}
      <Route path="/admin/dashboard" element={<AdminDashboard />} />
      <Route path="/admin/faculty-assignment" element={<FacultyAssignment />} />
      <Route path="/admin/complaints" element={<ViewComplaints />} />
      <Route path="/admin/complaints/:id" element={<AdminComplaintDetail />} />
      <Route path="/admin/departments" element={<ViewDepartments />} />

      {/* Student Routes */}
      <Route path="/dashboard" element={<StudentComplaintDashboard initialView="overview" />} />
      <Route path="/create-complaint" element={<CreateComplaintPage />} />
      <Route path="/my-complaints" element={<MyComplaintsPage />} />
      <Route path="/my-complaints/:id" element={<ComplaintDetailPage />} />

      {/* Faculty Route */}
      <Route path="/faculty/dashboard" element={<FacultyDashboard />} />

      {/* Not Found Route */}
      <Route path="*" element={<h1>404 - Page Not Found</h1>} />
    </Routes>
  );
}

export default AppRoutes;
