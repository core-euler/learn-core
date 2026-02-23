import { Navigate, Route, Routes } from 'react-router-dom';
import { AppLayout } from './layouts/AppLayout';
import { LoginPage } from './pages/LoginPage';
import { RegisterPage } from './pages/RegisterPage';
import { DashboardPage } from './pages/DashboardPage';
import { ModulesPage } from './pages/ModulesPage';
import { ModuleDetailsPage } from './pages/ModuleDetailsPage';
import { LessonWorkspacePage } from './pages/LessonWorkspacePage';
import { LectureModePage } from './pages/LectureModePage';
import { ExamModePage } from './pages/ExamModePage';
import { ConsultantModePage } from './pages/ConsultantModePage';
import { ProfilePage } from './pages/ProfilePage';
import { PrivateRoute, PublicOnlyRoute } from './router/guards';

function App() {
  return (
    <Routes>
      <Route element={<PublicOnlyRoute />}>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
      </Route>

      <Route element={<PrivateRoute />}>
        <Route element={<AppLayout />}>
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/modules" element={<ModulesPage />} />
          <Route path="/modules/:moduleId" element={<ModuleDetailsPage />} />
          <Route path="/lessons/:lessonId" element={<LessonWorkspacePage />}>
            <Route path="lecture" element={<LectureModePage />} />
            <Route path="exam" element={<ExamModePage />} />
            <Route path="consultant" element={<ConsultantModePage />} />
            <Route index element={<Navigate to="lecture" replace />} />
          </Route>
          <Route path="/profile" element={<ProfilePage />} />
        </Route>
      </Route>

      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  );
}

export default App;
