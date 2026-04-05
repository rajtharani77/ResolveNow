import { Route, Routes } from "react-router-dom";

import AdminDashboard from "../features/admin/AdminDashboard";
import FacultyAssignment from "../features/admin/FacultyAssignment";
import ViewComplaints from "../features/admin/ViewComplaints";
import ViewDepartments from "../features/admin/ViewDepartments";
import Login from "../features/auth/Login";
import Register from "../features/auth/Register";
import FacultyDashboard from "../features/faculty/FacultyDashboard";
import LandingPage from "../features/home/LandingPage";
import VerifyEmail from "../features/auth/VerifyEmail";
import StudentComplaintDashboard from "../features/complaints/StudentComplaintDashboard";

function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={<LandingPage />} />
      <Route path="/admin/dashboard" element={<AdminDashboard />} />
      <Route path="/admin/faculty-assignment" element={<FacultyAssignment />} />
      <Route path="/admin/complaints" element={<ViewComplaints />} />
      <Route path="/admin/departments" element={<ViewDepartments />} />
      <Route path="/register" element={<Register />} />
      <Route path="/login" element={<Login />} />
      <Route path="/verify-email" element={<VerifyEmail />} />
      <Route path="/dashboard" element={<StudentComplaintDashboard initialView="overview" />} />
      <Route path="/faculty/dashboard" element={<FacultyDashboard />} />
      <Route path="/complaint/create" element={<StudentComplaintDashboard initialView="create" />} />
      <Route path="/create-complaint" element={<StudentComplaintDashboard initialView="create" />} />
      <Route path="/my-complaints" element={<StudentComplaintDashboard initialView="list" />} />
    </Routes>
  );
}

export default AppRoutes;
